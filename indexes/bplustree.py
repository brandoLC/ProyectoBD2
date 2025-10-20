from typing import Any, Dict, List, Optional, Tuple
import pickle
import os
from .base import IIndex

class BPlusTreeIndex(IIndex):
    """
    B+ Tree con I/O REAL
    
    Características:
    - Nodos internos en RAM (solo claves)
    - Nodos hoja en DISCO (archivo .dat con datos completos)
    - Balanceado automático
    - Eficiente para búsquedas Y rangos
    - Todas las hojas al mismo nivel
    
    Simplificación: Build estático desde datos ordenados (sin insert dinámico)
    """
    
    def __init__(self, key: str, order: int = 20, table_name: Optional[str] = None) -> None:
        """
        Args:
            key: Nombre de la columna clave
            order: Orden del árbol (max claves por nodo)
            table_name: Nombre de tabla para nombres de archivo consistentes
        """
        self.key = key
        self.order = order
        self.table_name = table_name
        
        # Nodos internos en RAM (árbol de navegación)
        # Cada nodo: {'keys': [...], 'children': [...]}
        self.root = None
        
        # Archivo de hojas en disco
        self.data_file: Optional[str] = None
        self.num_leaves: int = 0
        
        # Índice de hojas en RAM: [(first_key, last_key), ...]
        self.leaf_index: List[Tuple[Any, Any]] = []
        
        # Overflow para inserciones (en RAM)
        self.overflow: List[Dict[str, Any]] = []
        
        # Contador de I/O REAL
        self._io_reads = 0
        self._io_writes = 0
    
    def _get_key_value(self, row: Dict[str, Any]) -> Any:
        """
        Obtiene el valor de la clave del registro.
        Maneja claves con espacios, comillas o diferencias de mayúsculas.
        """
        if self.key in row:
            return row[self.key]
        
        def normalize_key(k: str) -> str:
            return k.lower().replace('"', '').replace("'", "").replace(" ", "").replace("_", "")
        
        key_normalized = normalize_key(self.key)
        
        for k, v in row.items():
            if normalize_key(k) == key_normalized:
                return v
        
        raise KeyError(f"Key '{self.key}' not found in row. Available keys: {list(row.keys())}")
    
    def build(self, rows: List[Dict[str, Any]]) -> None:
        """
        Construye el B+ Tree con I/O REAL.
        
        Proceso:
        1. Ordenar datos por clave
        2. Crear hojas en disco
        3. Construir árbol interno en RAM
        """
        if not rows:
            return
        
        # 1. Ordenar datos por clave
        rows_sorted = sorted(rows, key=lambda r: self._get_key_value(r))
        
        # 2. Crear hojas (cada hoja tiene hasta 'order' registros)
        leaves_temp = []
        for i in range(0, len(rows_sorted), self.order):
            leaf = rows_sorted[i:i+self.order]
            leaves_temp.append(leaf)
        
        self.num_leaves = len(leaves_temp)
        
        # 3. ESCRIBIR hojas a disco (I/O REAL)
        if not self.data_file:
            if self.table_name:
                self.data_file = f"storage/{self.table_name}_bplustree_leaves.dat"
            else:
                self.data_file = f"storage/bplustree_{id(self)}_leaves.dat"
        
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        with open(self.data_file, 'wb') as f:
            for leaf in leaves_temp:
                leaf_bytes = pickle.dumps(leaf)
                leaf_size = len(leaf_bytes)
                # Escribir: tamaño (4 bytes) + datos
                f.write(leaf_size.to_bytes(4, 'little'))
                f.write(leaf_bytes)
                self._io_writes += 1
        
        # 4. Construir índice de hojas en RAM (first_key, last_key)
        self.leaf_index = []
        for leaf in leaves_temp:
            first_key = self._get_key_value(leaf[0])
            last_key = self._get_key_value(leaf[-1])
            self.leaf_index.append((first_key, last_key))
        
        # 5. Construir árbol interno en RAM (simplificado: solo 1 nivel)
        # Para un B+ Tree completo se necesitarían múltiples niveles
        self.root = {
            'keys': [first_key for first_key, _ in self.leaf_index[1:]],
            'is_leaf': False
        }
        
        # 6. Limpiar overflow
        self.overflow = []
    
    def _read_leaf_from_disk(self, leaf_idx: int) -> List[Dict[str, Any]]:
        """
        Lee una hoja desde el archivo .dat en disco (I/O REAL).
        
        Args:
            leaf_idx: Índice de la hoja (0-based)
            
        Returns:
            Lista de registros en la hoja
        """
        if not self.data_file or not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        # I/O REAL: Abrir archivo y leer hoja específica
        with open(self.data_file, 'rb') as f:
            # Saltar hojas anteriores
            for i in range(leaf_idx):
                size_bytes = f.read(4)
                if len(size_bytes) < 4:
                    raise EOFError(f"Unexpected EOF while seeking leaf {leaf_idx}")
                size = int.from_bytes(size_bytes, 'little')
                f.seek(size, 1)  # Saltar datos de la hoja
            
            # Leer la hoja target
            size_bytes = f.read(4)
            if len(size_bytes) < 4:
                raise EOFError(f"Cannot read leaf {leaf_idx}")
            size = int.from_bytes(size_bytes, 'little')
            leaf_bytes = f.read(size)
            
            self._io_reads += 1  # Contar I/O REAL
            
            return pickle.loads(leaf_bytes)
    
    def _find_leaf_index(self, value: Any) -> int:
        """
        Encuentra el índice de la hoja usando el árbol interno (RAM).
        
        Búsqueda binaria sobre leaf_index.
        """
        if self.num_leaves == 0:
            return 0
        
        # Búsqueda binaria sobre el índice de hojas
        left, right = 0, len(self.leaf_index) - 1
        result_leaf = 0
        
        while left <= right:
            mid = (left + right) // 2
            first_key, last_key = self.leaf_index[mid]
            
            if value < first_key:
                right = mid - 1
            elif value > last_key:
                left = mid + 1
            else:
                # Valor está en este rango
                return mid
        
        # Si no encontró exactamente, retornar el índice más cercano
        return min(max(left, 0), len(self.leaf_index) - 1)
    
    def search(self, value: Any) -> List[Dict[str, Any]]:
        """
        Búsqueda por igualdad con I/O REAL.
        
        Proceso:
        1. Navegar árbol interno (RAM) para encontrar hoja
        2. LEER hoja desde disco (1 I/O)
        3. Buscar en hoja
        4. Buscar en overflow (RAM)
        """
        if self.num_leaves == 0:
            # Solo buscar en overflow
            return [r for r in self.overflow if self._get_key_value(r) == value]
        
        # 1. Encontrar hoja usando índice en RAM
        leaf_idx = self._find_leaf_index(value)
        
        # 2. Leer hoja desde DISCO
        leaf = self._read_leaf_from_disk(leaf_idx)
        
        # 3. Buscar en hoja
        results = [r for r in leaf if self._get_key_value(r) == value]
        
        # 4. Buscar en overflow (RAM)
        results.extend([r for r in self.overflow if self._get_key_value(r) == value])
        
        return results
    
    def range_search(self, lo: Any, hi: Any) -> List[Dict[str, Any]]:
        """
        Búsqueda por rango con I/O REAL.
        
        Lee solo las hojas que contienen claves en el rango.
        """
        if self.num_leaves == 0:
            # Solo buscar en overflow
            return sorted([r for r in self.overflow if lo <= self._get_key_value(r) <= hi],
                         key=lambda r: self._get_key_value(r))
        
        results = []
        
        # Recorrer hojas relevantes
        for leaf_idx in range(self.num_leaves):
            first_key, last_key = self.leaf_index[leaf_idx]
            
            # Optimización: Saltar hojas fuera del rango
            if last_key < lo:
                continue  # Hoja completamente antes del rango
            if first_key > hi:
                break  # Hojas restantes están después del rango
            
            # Leer hoja desde DISCO
            leaf = self._read_leaf_from_disk(leaf_idx)
            
            # Filtrar registros en rango
            results.extend([r for r in leaf if lo <= self._get_key_value(r) <= hi])
        
        # Agregar overflow
        results.extend([r for r in self.overflow if lo <= self._get_key_value(r) <= hi])
        
        return sorted(results, key=lambda r: self._get_key_value(r))
    
    def add(self, row: Dict[str, Any]) -> None:
        """
        Inserta registro en overflow y persiste a disco.
        
        Con I/O real, las inserciones van a overflow (RAM).
        Se requiere rebuild para reorganizar.
        """
        self.overflow.append(row)
        
        # Escribir overflow a disco
        self._write_overflow_to_disk()
    
    def _write_overflow_to_disk(self) -> None:
        """
        Escribe el overflow a un archivo separado en disco.
        """
        if not self.data_file:
            return
        
        overflow_file = self.data_file.replace('_leaves.dat', '_overflow.dat')
        
        with open(overflow_file, 'wb') as f:
            overflow_bytes = pickle.dumps(self.overflow)
            f.write(overflow_bytes)
            self._io_writes += 1
    
    def remove(self, value: Any) -> int:
        """
        Elimina registros con la clave dada.
        
        Estrategia:
        1. Eliminar del overflow (RAM)
        2. Buscar en hojas de disco usando índice
        3. Leer hoja, filtrar, reescribir
        
        Returns:
            Cantidad de registros eliminados
        """
        deleted = 0
        
        # 1. Eliminar del overflow (RAM)
        original_len = len(self.overflow)
        self.overflow = [r for r in self.overflow if self._get_key_value(r) != value]
        deleted = original_len - len(self.overflow)
        
        # 2. Buscar en hojas de disco
        if not self.data_file or not os.path.exists(self.data_file):
            return deleted
        
        # Encontrar la hoja que podría contener el valor
        leaf_idx = self._find_leaf_index(value)
        
        if leaf_idx is None:
            return deleted
        
        # Leer la hoja desde disco
        leaf = self._read_leaf_from_disk(leaf_idx)
        
        # Filtrar registros
        original_len = len(leaf)
        filtered_leaf = [r for r in leaf if self._get_key_value(r) != value]
        
        if len(filtered_leaf) < original_len:
            deleted += original_len - len(filtered_leaf)
            
            # Reescribir la hoja modificada
            self._rewrite_leaf(leaf_idx, filtered_leaf)
            
            # Actualizar leaf_index con nuevos límites
            if filtered_leaf:
                first_key = self._get_key_value(filtered_leaf[0])
                last_key = self._get_key_value(filtered_leaf[-1])
                self.leaf_index[leaf_idx] = (first_key, last_key)
            else:
                # Hoja vacía: podríamos eliminarla del índice
                # Por simplicidad, la dejamos con límites inválidos
                self.leaf_index[leaf_idx] = (float('inf'), float('inf'))
        
        return deleted
    
    def _rewrite_leaf(self, leaf_idx: int, new_leaf: List[Dict[str, Any]]) -> None:
        """
        Reescribe una hoja específica en disco.
        
        Como las hojas tienen tamaño variable, necesitamos
        reescribir TODO el archivo.
        """
        if not self.data_file or not os.path.exists(self.data_file):
            return
        
        # Leer todas las hojas
        all_leaves = []
        for i in range(self.num_leaves):
            if i == leaf_idx:
                all_leaves.append(new_leaf)
            else:
                all_leaves.append(self._read_leaf_from_disk(i))
        
        # Reescribir archivo completo
        with open(self.data_file, 'wb') as f:
            for leaf in all_leaves:
                leaf_bytes = pickle.dumps(leaf)
                leaf_size = len(leaf_bytes)
                f.write(leaf_size.to_bytes(4, 'little'))
                f.write(leaf_bytes)
                self._io_writes += 1
    
    def get_io_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de I/O"""
        return {
            'disk_reads': self._io_reads,
            'disk_writes': self._io_writes
        }
    
    def reset_io_stats(self) -> None:
        """Resetea contadores de I/O"""
        self._io_reads = 0
        self._io_writes = 0
    
    def clear(self) -> None:
        """Limpia el índice"""
        self.root = None
        self.leaf_index.clear()
        self.overflow.clear()
        self.num_leaves = 0
        if self.data_file and os.path.exists(self.data_file):
            os.remove(self.data_file)
        self.data_file = None
    
    def save(self, filepath: str) -> None:
        """Persiste el índice a disco"""
        data = {
            'key': self.key,
            'order': self.order,
            'table_name': self.table_name,
            'root': self.root,
            'leaf_index': self.leaf_index,
            'data_file': self.data_file,
            'num_leaves': self.num_leaves,
            'overflow': self.overflow
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, filepath: str) -> None:
        """Carga el índice desde disco"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.key = data['key']
        self.order = data['order']
        self.table_name = data.get('table_name')
        self.root = data['root']
        self.leaf_index = data['leaf_index']
        self.data_file = data['data_file']
        self.num_leaves = data['num_leaves']
        self.overflow = data['overflow']
    
    @staticmethod
    def load_from(filepath: str) -> 'BPlusTreeIndex':
        """Carga y retorna una instancia del índice"""
        idx = BPlusTreeIndex(key='temp')
        idx.load(filepath)
        return idx
    
    def get_structure_info(self) -> dict:
        """Retorna información de la estructura del índice"""
        return {
            'type': 'B+ Tree',
            'order': self.order,
            'num_leaves': self.num_leaves,
            'records_in_overflow': len(self.overflow),
            'height': 2 if self.root else 0  # Simplificado: 2 niveles (root + hojas)
        }
