from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import os
from .schema import TableSchema
from indexes.base import IIndex
from indexes.sequential import SequentialIndex
from indexes.isam import ISAMIndex
from indexes.ext_hash import ExtendibleHashIndex
from indexes.bplustree import BPlusTreeIndex

if TYPE_CHECKING:
    from .storage import Storage
    from .disk_storage import DiskStorage

@dataclass
class Table:
    schema: TableSchema
    storage: Any  # Storage or DiskStorage
    indexes: Dict[str, IIndex] = field(default_factory=dict)
    name: str = ""
    index_type: str = "sequential"  # Tipo de índice a usar
    rebuild_indexes: bool = False  # Si debe reconstruir índices desde disco

    def __post_init__(self) -> None:
        self.name = self.schema.name
        # Crear índice según el tipo especificado
        if self.schema.key not in self.indexes:
            if self.index_type == "isam":
                self.indexes[self.schema.key] = ISAMIndex(key=self.schema.key, table_name=self.name)
            elif self.index_type == "ext_hash":
                self.indexes[self.schema.key] = ExtendibleHashIndex(key=self.schema.key, table_name=self.name)
            elif self.index_type == "bplustree":
                self.indexes[self.schema.key] = BPlusTreeIndex(key=self.schema.key, table_name=self.name)
            else:  # default: sequential
                self.indexes[self.schema.key] = SequentialIndex(key=self.schema.key, table_name=self.name)
        
        # Si se está restaurando desde disco, reconstruir índices
        if self.rebuild_indexes:
            self._rebuild_indexes_from_storage()
    
    def _rebuild_indexes_from_storage(self) -> None:
        """Restaura índices desde disco o los reconstruye si no existen"""
        if not hasattr(self.storage, 'data_dir'):
            # Storage viejo, reconstruir manualmente
            all_rows = self.storage.read_all(self.name)
            for row in all_rows:
                for idx in self.indexes.values():
                    idx.add(row)
            return
        
        # Intentar cargar índices desde disco
        for col_name, idx in list(self.indexes.items()):
            index_filename = f"{self.name}_{type(idx).__name__.lower().replace('index', '')}.idx"
            # Usar pathlib para construcción de paths multi-plataforma
            from pathlib import Path
            index_path = Path(self.storage.data_dir) / index_filename
            
            # Para ISAM multinivel, buscar archivo L2 que es el punto de entrada
            index_exists = index_path.exists()
            if not index_exists and 'isam' in index_filename.lower():
                # Intentar con formato multinivel (_l2.idx)
                index_path_l2 = Path(self.storage.data_dir) / index_filename.replace('.idx', '_l2.idx')
                if index_path_l2.exists():
                    index_path = Path(str(index_path).replace('.idx', ''))  # Base path sin .idx
                    index_exists = True  # Marcar como existente
            
            if index_exists:
                # Cargar índice desde disco
                try:
                    loaded_idx = type(idx).load(str(index_path))
                    self.indexes[col_name] = loaded_idx
                except Exception as e:
                    print(f"Warning: Failed to load index from {index_path}: {e}")
                    # Fallback: reconstruir desde datos
                    all_rows = self.storage.read_all(self.name)
                    for row in all_rows:
                        idx.add(row)
            else:
                # No existe archivo de índice, reconstruir desde datos
                all_rows = self.storage.read_all(self.name)
                for row in all_rows:
                    idx.add(row)
    
    def _save_indexes(self) -> None:
        """Persiste todos los índices a disco"""
        if not hasattr(self.storage, 'data_dir'):
            return  # Storage viejo sin persistencia
        
        for col_name, idx in self.indexes.items():
            # Formato: storage/restaurants_isam (sin .idx, el índice agrega sufijos)
            index_type = type(idx).__name__.lower().replace('index', '')
            index_filename = f"{self.name}_{index_type}"
            index_path = f"{self.storage.data_dir}/{index_filename}"
            idx.save(index_path)

    def load(self, rows: List[Dict[str, Any]]) -> None:
        self.storage.load(self.name, rows)
        
        # Usar build() si el índice lo soporta (más eficiente que add múltiples veces)
        for idx in self.indexes.values():
            if hasattr(idx, 'build'):
                idx.build(rows)
            else:
                for r in rows:
                    idx.add(r)
        
        # Guardar índices después de cargar datos
        self._save_indexes()

    def insert(self, row: Dict[str, Any]) -> None:
        self.storage.load(self.name, [row])
        for idx in self.indexes.values():
            idx.add(row)
        # Guardar índices después de insertar
        self._save_indexes()

    def delete(self, key_value: Any) -> int:
        """
        Elimina registros con la clave dada usando index.remove()
        que elimina físicamente del disco.
        """
        # Usar el índice principal para eliminar
        idx = self.indexes.get(self.schema.key)
        if idx and hasattr(idx, 'remove'):
            # El índice se encarga de eliminar del disco
            deleted = idx.remove(key_value)
            return deleted
        
        # Fallback: implementación naive (solo si no hay índice)
        all_rows = self.storage.read_all(self.name)
        kept = [r for r in all_rows if r[self.schema.key] != key_value]
        deleted = len(all_rows) - len(kept)
        
        if hasattr(self.storage, 'clear_table'):
            self.storage.clear_table(self.name)
        else:
            self.storage._tables[self.name] = []
        
        self.storage.load(self.name, kept)
        
        for k in list(self.indexes.keys()):
            self.indexes[k].clear()
        for r in kept:
            for idx in self.indexes.values():
                idx.add(r)
        
        return deleted

    def select_eq(self, column: str, value: Any) -> List[Dict[str, Any]]:
        idx = self.indexes.get(column)
        if idx:
            return idx.search(value)
        return [r for r in self.storage.read_all(self.name) if r.get(column) == value]
    
    def get_index(self, column: str = None) -> Optional[IIndex]:
        """Obtiene el índice de una columna (o el índice principal si no se especifica)"""
        if column:
            return self.indexes.get(column)
        # Retornar el índice de la clave primaria
        return self.indexes.get(self.schema.key)

    def select_range(self, column: str, lo: Any, hi: Any) -> List[Dict[str, Any]]:
        idx = self.indexes.get(column)
        if idx and hasattr(idx, "range_search"):
            return idx.range_search(lo, hi)
        rows = self.storage.read_all(self.name)
        return [r for r in rows if lo <= r.get(column) <= hi]
