"""
Disk Storage - Almacenamiento en disco con buffer pool
Versión mejorada de Storage que usa memoria secundaria real
"""
from typing import Any, Dict, List, Optional
import json
from pathlib import Path
from .disk_manager import DiskManager, Page
from .buffer_pool import BufferPool
from .io_metrics import IOMetrics


class DiskStorage:
    """
    Almacenamiento con persistencia en disco.
    Usa buffer pool para optimizar accesos y simular comportamiento real de DBMS.
    """
    
    def __init__(self, records_per_page: int = 10, pool_size: int = 50, data_dir: str = "storage"):
        """
        Args:
            records_per_page: Número de registros por página (reducido a 10 para datos grandes)
            pool_size: Tamaño del buffer pool en páginas
            data_dir: Directorio para archivos de datos
        """
        self.rpp = records_per_page
        self.disk_manager = DiskManager(data_dir)
        self.buffer_pool = BufferPool(pool_size, self.disk_manager)
        self.metrics = IOMetrics()
        self.data_dir = Path(data_dir)
        self.metadata_file = self.data_dir / "catalog.json"
        
        # Metadata: cuántos registros tiene cada tabla, schema, index_type, etc.
        self._table_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Cargar metadata desde disco si existe
        self._load_catalog()
    
    def create_table(self, name: str) -> None:
        """Crea una tabla (archivo vacío)"""
        if name not in self._table_metadata:
            self._table_metadata[name] = {
                "num_records": 0,
                "num_pages": 0,
                "schema": None,  # Se setea en load() o desde Catalog
                "index_type": "sequential"  # Default
            }
            # Crear archivo vacío
            self.disk_manager.get_table_file(name).touch()
            self._save_catalog()
    
    def _load_catalog(self) -> None:
        """Carga metadata desde catalog.json"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self._table_metadata = json.load(f)
            except Exception as e:
                print(f"Warning: No se pudo cargar catalog.json: {e}")
                self._table_metadata = {}
    
    def _save_catalog(self) -> None:
        """Guarda metadata en catalog.json"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self._table_metadata, f, indent=2, ensure_ascii=False)
    
    def set_table_metadata(self, name: str, schema: Optional[Dict] = None, index_type: Optional[str] = None) -> None:
        """Actualiza metadata de una tabla"""
        if name not in self._table_metadata:
            self.create_table(name)
        
        if schema is not None:
            self._table_metadata[name]["schema"] = schema
        if index_type is not None:
            self._table_metadata[name]["index_type"] = index_type
        
        self._save_catalog()
    
    def get_table_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtiene metadata de una tabla"""
        return self._table_metadata.get(name)
    
    def list_tables(self) -> List[str]:
        """Lista todas las tablas del catálogo"""
        return list(self._table_metadata.keys())
    
    def load(self, name: str, rows: List[Dict[str, Any]]) -> None:
        """
        Carga registros en páginas y escribe a disco.
        Actualiza métricas de I/O.
        """
        self.create_table(name)
        
        if not rows:
            return
        
        # Dividir registros en páginas
        pages_data = self._split_into_pages(rows)
        
        # Obtener el offset de páginas existentes
        current_num_pages = self._table_metadata[name]["num_pages"]
        
        # Escribir cada página
        for i, page_data in enumerate(pages_data):
            page_id = current_num_pages + i
            page = Page(page_id, page_data)
            
            # Escribir a través del buffer pool
            self.buffer_pool.put_page(name, page, write_through=True)
        
        # Actualizar metadata
        self._table_metadata[name]["num_records"] += len(rows)
        self._table_metadata[name]["num_pages"] += len(pages_data)
        
        # Guardar catálogo actualizado
        self._save_catalog()
        
        # Actualizar métricas legacy (para compatibilidad)
        self.metrics.write(len(pages_data))
    
    def read_all(self, name: str) -> List[Dict[str, Any]]:
        """
        Lee todos los registros de una tabla.
        Usa buffer pool para optimizar accesos.
        """
        if name not in self._table_metadata:
            return []
        
        num_pages = self._table_metadata[name]["num_pages"]
        all_records = []
        
        # Leer cada página
        for page_id in range(num_pages):
            page = self.buffer_pool.get_page(name, page_id)
            if page and page.data:
                all_records.extend(page.data)
        
        # Actualizar métricas legacy
        self.metrics.read(num_pages)
        
        return all_records
    
    def read_page(self, name: str, page_id: int) -> List[Dict[str, Any]]:
        """Lee una página específica"""
        page = self.buffer_pool.get_page(name, page_id)
        self.metrics.read(1)
        return page.data if page else []
    
    def write_page(self, name: str, page_id: int, records: List[Dict[str, Any]]) -> None:
        """Escribe una página específica"""
        page = Page(page_id, records)
        self.buffer_pool.put_page(name, page, write_through=False)
        self.metrics.write(1)
    
    def _split_into_pages(self, rows: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Divide registros en páginas según records_per_page"""
        pages = []
        for i in range(0, len(rows), self.rpp):
            page_data = rows[i:i + self.rpp]
            pages.append(page_data)
        return pages
    
    def get_num_pages(self, name: str) -> int:
        """Retorna el número de páginas de una tabla"""
        if name in self._table_metadata:
            return self._table_metadata[name]["num_pages"]
        return 0
    
    def flush_all(self) -> None:
        """Escribe todas las páginas dirty a disco"""
        self.buffer_pool.flush_all()
    
    def flush_table(self, name: str) -> None:
        """Escribe todas las páginas dirty de una tabla"""
        self.buffer_pool.flush_table(name)
    
    def clear_table(self, name: str) -> None:
        """Vacía una tabla (borra datos pero mantiene metadata)"""
        if name in self._table_metadata:
            # Limpiar buffer pool
            self.buffer_pool.clear_table(name)
            # Recrear archivo vacío
            self.disk_manager.get_table_file(name).write_bytes(b'')
            # Resetear metadata de registros/páginas
            self._table_metadata[name]["num_records"] = 0
            self._table_metadata[name]["num_pages"] = 0
            self._save_catalog()
    
    def delete_table(self, name: str) -> None:
        """Elimina una tabla"""
        if name in self._table_metadata:
            self.buffer_pool.clear_table(name)
            self.disk_manager.delete_table(name)
            del self._table_metadata[name]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas completas de I/O"""
        buffer_stats = self.buffer_pool.get_stats()
        disk_stats = self.disk_manager.get_io_stats()
        
        return {
            **buffer_stats,
            **disk_stats,
            "records_per_page": self.rpp,
            "tables": {
                name: {
                    "records": meta["num_records"],
                    "pages": meta["num_pages"],
                    "size_bytes": self.disk_manager.get_table_size(name)
                }
                for name, meta in self._table_metadata.items()
            }
        }
    
    def reset_metrics(self) -> None:
        """Resetea contadores de I/O y cache"""
        self.metrics.reset()
        self.buffer_pool.reset_stats()
