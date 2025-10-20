from typing import Any, Dict, List, Tuple, Optional
import pickle
import os
from bisect import bisect_left, bisect_right
from .base import IIndex

class SequentialIndex(IIndex):
    """
    Sequential File - Archivo secuencial ordenado con I/O REAL
    
    Características:
    - Datos ordenados por clave en bloques EN DISCO (archivo .dat)
    - Índice de claves en RAM (first/last key por bloque)
    - Búsqueda binaria sobre índice: O(log N) accesos
    - Cada acceso = lectura REAL del bloque desde disco
    - INSERT: Overflow primero, reorganiza si es necesario
    """
    
    def __init__(self, key: str, block_size: int = 20, table_name: Optional[str] = None) -> None:
        """
        Args:
            key: Nombre de la columna clave
            block_size: Número de registros por bloque
            table_name: Nombre de tabla para nombres de archivo consistentes
        """
        self.key = key
        self.block_size = block_size
        self.table_name = table_name
        
        # Índice de bloques en RAM: [(first_key, last_key), ...]
        self.block_index: List[Tuple[Any, Any]] = []
        
        # Archivo de datos en disco
        self.data_file: Optional[str] = None
        self.num_blocks: int = 0
        
        # Overflow para inserciones (no ordenado, en RAM)
        self.overflow: List[Dict[str, Any]] = []
        
        # Contador de I/O REAL
        self._io_reads = 0
        self._io_writes = 0
        
        # Umbral para reorganización (cuando overflow > 10% del total)
        self.reorganize_threshold = 0.1
    
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
        Construye el archivo secuencial con I/O REAL.
        
        Proceso:
        1. Ordenar datos por clave
        2. Particionar en bloques
        3. ESCRIBIR bloques a archivo .dat (I/O REAL)
        4. Construir índice de claves en RAM (first/last key por bloque)
        """
        if not rows:
            return
        
        # 1. Ordenar datos por clave
        rows_sorted = sorted(rows, key=lambda r: self._get_key_value(r))
        
        # 2. Particionar en bloques
        blocks_temp = []
        for i in range(0, len(rows_sorted), self.block_size):
            block = rows_sorted[i:i+self.block_size]
            blocks_temp.append(block)
        
        self.num_blocks = len(blocks_temp)
        
        # 3. ESCRIBIR bloques a disco (I/O REAL)
        if not self.data_file:
            # Generar nombre de archivo usando table_name si está disponible
            if self.table_name:
                self.data_file = f"storage/{self.table_name}_sequential_blocks.dat"
            else:
                # Fallback a ID temporal (para tests)
                self.data_file = f"storage/sequential_{id(self)}_blocks.dat"
        
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        with open(self.data_file, 'wb') as f:
            for block in blocks_temp:
                block_bytes = pickle.dumps(block)
                block_size = len(block_bytes)
                # Escribir: tamaño (4 bytes) + datos
                f.write(block_size.to_bytes(4, 'little'))
                f.write(block_bytes)
                self._io_writes += 1
        
        # 4. Construir índice de claves en RAM
        self.block_index = []
        for block in blocks_temp:
            first_key = self._get_key_value(block[0])
            last_key = self._get_key_value(block[-1])
            self.block_index.append((first_key, last_key))
        
        self.overflow = []
    
    def _read_block(self, block_idx: int) -> List[Dict[str, Any]]:
        """
        LEE bloque desde DISCO con fopen/fseek/fread (I/O REAL).
        
        Formato del archivo:
        [size_0 (4 bytes)][block_0 pickled][size_1 (4 bytes)][block_1 pickled]...
        """
        if not self.data_file or not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        # I/O REAL: Abrir archivo y leer bloque específico
        with open(self.data_file, 'rb') as f:
            # Saltar bloques anteriores para llegar al block_idx
            for i in range(block_idx):
                size_bytes = f.read(4)
                if len(size_bytes) < 4:
                    raise EOFError(f"Unexpected EOF while seeking block {block_idx}")
                size = int.from_bytes(size_bytes, 'little')
                f.seek(size, 1)  # Saltar los datos del bloque
            
            # Leer el bloque target
            size_bytes = f.read(4)
            if len(size_bytes) < 4:
                raise EOFError(f"Cannot read block {block_idx}")
            size = int.from_bytes(size_bytes, 'little')
            block_bytes = f.read(size)
            
            self._io_reads += 1  # Contar I/O REAL
            
            return pickle.loads(block_bytes)
    
    def _write_overflow_to_disk(self) -> None:
        """
        Escribe el overflow a un archivo separado en disco.
        
        Esto permite persistir las inserciones pendientes.
        """
        if not self.data_file:
            return
        
        overflow_file = self.data_file.replace('_blocks.dat', '_overflow.dat')
        
        with open(overflow_file, 'wb') as f:
            overflow_bytes = pickle.dumps(self.overflow)
            f.write(overflow_bytes)
            self._io_writes += 1  # Contar escritura a disco
    
    def _binary_search_block(self, value: Any) -> int:
        """
        Búsqueda binaria de bloque usando índice en RAM.
        
        El índice tiene (first_key, last_key) por bloque.
        Solo se lee el bloque final desde disco (1 I/O).
        """
        if self.num_blocks == 0:
            return 0
        
        left, right = 0, len(self.block_index) - 1
        result_block = 0
        
        while left <= right:
            mid = (left + right) // 2
            first_key, last_key = self.block_index[mid]
            
            if first_key <= value <= last_key:
                return mid
            elif value < first_key:
                right = mid - 1
                result_block = mid
            else:
                left = mid + 1
                result_block = min(mid + 1, len(self.block_index) - 1)
        
        return result_block
    
    def get_io_stats(self) -> Dict[str, int]:
        """Retorna y resetea estadísticas de I/O"""
        stats = {'disk_reads': self._io_reads, 'disk_writes': self._io_writes}
        self._io_reads = 0
        self._io_writes = 0
        return stats
    
    def search(self, value: Any) -> List[Dict[str, Any]]:
        """
        Búsqueda por igualdad con I/O REAL.
        
        Búsqueda binaria en índice (RAM, 0 I/O) + lectura de 1 bloque (DISCO, 1 I/O).
        """
        results = []
        
        if self.num_blocks == 0:
            return results
        
        # Búsqueda binaria sobre índice (RAM, 0 I/O)
        block_idx = self._binary_search_block(value)
        
        # Leer bloque desde DISCO (I/O REAL)
        block = self._read_block(block_idx)
        
        # Buscar en el bloque
        for record in block:
            if self._get_key_value(record) == value:
                results.append(record)
        
        # Buscar en overflow (RAM, 0 I/O)
        for record in self.overflow:
            if self._get_key_value(record) == value:
                results.append(record)
        
        return results
    
    def range_search(self, lo: Any, hi: Any) -> List[Dict[str, Any]]:
        """
        Búsqueda por rango con I/O REAL.
        
        Búsqueda binaria (RAM, 0 I/O) + lectura secuencial de K bloques (DISCO, K I/O).
        """
        results = []
        
        if self.num_blocks == 0:
            return results
        
        # Encontrar bloque inicial (búsqueda binaria en índice, RAM)
        start_block = self._binary_search_block(lo)
        
        # Leer bloques secuencialmente desde DISCO (I/O REAL)
        for block_idx in range(start_block, self.num_blocks):
            # Verificar con índice si el bloque puede contener datos
            first_key, last_key = self.block_index[block_idx]
            if first_key > hi:
                break
            
            # Leer bloque desde DISCO (I/O REAL)
            block = self._read_block(block_idx)
            
            for record in block:
                key_val = self._get_key_value(record)
                if lo <= key_val <= hi:
                    results.append(record)
                elif key_val > hi:
                    break
        
        # Buscar en overflow (RAM, 0 I/O)
        for record in self.overflow:
            key_val = self._get_key_value(record)
            if lo <= key_val <= hi:
                results.append(record)
        
        return results
    
    def add(self, row: Dict[str, Any]) -> None:
        """Inserta registro en overflow y persiste a disco"""
        self.overflow.append(row)
        
        # Escribir overflow a disco (I/O REAL)
        self._write_overflow_to_disk()
        
        # Reorganizar si overflow > umbral
        # Necesitamos contar registros leyendo los bloques desde disco
        total_in_blocks = self.num_blocks * self.block_size  # Aproximación
        if len(self.overflow) > total_in_blocks * self.reorganize_threshold:
            self._reorganize()
    
    def _reorganize(self) -> None:
        """
        Reorganiza: fusiona bloques + overflow, reordena.
        
        Lee todos los bloques desde DISCO, fusiona con overflow, y reconstruye.
        """
        all_records = []
        
        # Leer todos los bloques desde DISCO (I/O REAL)
        for block_idx in range(self.num_blocks):
            block = self._read_block(block_idx)
            all_records.extend(block)
        
        # Agregar overflow
        all_records.extend(self.overflow)
        
        # Reconstruir (escribe nuevos bloques a disco)
        self.build(all_records)
    
    def remove(self, value: Any) -> int:
        """
        Elimina registros con la clave dada.
        
        Estrategia: 
        1. Eliminar del overflow (RAM)
        2. Buscar en bloques de disco
        3. Si encuentra registros, reconstruir archivo sin esos registros
        
        Returns:
            Cantidad de registros eliminados
        """
        deleted = 0
        
        # 1. Eliminar del overflow (RAM)
        original_len = len(self.overflow)
        self.overflow = [r for r in self.overflow if self._get_key_value(r) != value]
        deleted = original_len - len(self.overflow)
        
        # 2. Buscar en bloques de disco
        if not self.data_file or not os.path.exists(self.data_file):
            return deleted
        
        found_in_disk = False
        new_blocks = []
        
        # Leer todos los bloques y filtrar registros
        num_blocks = len(self.block_index)
        for block_idx in range(num_blocks):
            block = self._read_block(block_idx)
            
            # Filtrar registros con la clave
            original_block_len = len(block)
            filtered_block = [r for r in block if self._get_key_value(r) != value]
            
            if len(filtered_block) < original_block_len:
                found_in_disk = True
                deleted += original_block_len - len(filtered_block)
            
            # Solo agregar bloque si tiene registros
            if filtered_block:
                new_blocks.append(filtered_block)
        
        # 3. Si se eliminó algo del disco, reconstruir archivo
        if found_in_disk:
            # Reconstruir todos los registros
            all_records = []
            for block in new_blocks:
                all_records.extend(block)
            all_records.extend(self.overflow)
            
            # Rebuild completo (esto resetea overflow también)
            self.build(all_records)
        
        return deleted
    
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
        self.block_index.clear()
        self.overflow.clear()
        self.num_blocks = 0
        if self.data_file and os.path.exists(self.data_file):
            os.remove(self.data_file)
        self.data_file = None
    
    def save(self, filepath: str) -> None:
        """Persiste el índice secuencial a disco"""
        data = {
            'key': self.key,
            'block_size': self.block_size,
            'block_index': self.block_index,
            'data_file': self.data_file,
            'num_blocks': self.num_blocks,
            'overflow': self.overflow,
            'reorganize_threshold': self.reorganize_threshold
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'SequentialIndex':
        """Restaura el índice secuencial desde disco"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        # Crear instancia y restaurar estado
        instance = cls(key=data['key'], block_size=data.get('block_size', 20))
        instance.block_index = data.get('block_index', [])
        instance.data_file = data.get('data_file')
        instance.num_blocks = data.get('num_blocks', 0)
        instance.overflow = data['overflow']
        instance.reorganize_threshold = data.get('reorganize_threshold', 0.1)
        
        return instance
