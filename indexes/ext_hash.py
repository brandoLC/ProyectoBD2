from typing import Any, Dict, List, Optional
import pickle
import os
from .base import IIndex

class ExtendibleHashIndex(IIndex):
    """
    Extendible Hashing con I/O REAL
    
    Características:
    - Directorio en RAM (mapea hash → bucket_id)
    - Buckets en DISCO (archivo .dat)
    - Global depth y local depth por bucket
    - Split dinámico cuando bucket se llena
    - Duplicación de directorio cuando global_depth aumenta
    - Solo búsqueda por igualdad (no rangos)
    """
    
    def __init__(self, key: str, global_depth: int = 2, bucket_size: int = 20, table_name: Optional[str] = None) -> None:
        """
        Args:
            key: Nombre de la columna clave
            global_depth: Profundidad inicial del directorio (bits de hash)
            bucket_size: Capacidad máxima de registros por bucket
            table_name: Nombre de tabla para nombres de archivo consistentes
        """
        self.key = key
        self.global_depth = global_depth
        self.bucket_size = bucket_size
        self.table_name = table_name
        
        # Directorio en RAM: índice → bucket_id
        # Varios índices pueden apuntar al mismo bucket (sharing)
        self.directory: List[int] = list(range(2 ** global_depth))
        
        # Local depth por bucket (cuántos bits del hash usa)
        self.local_depths: Dict[int, int] = {i: global_depth for i in range(2 ** global_depth)}
        
        # Archivo de datos en disco
        self.data_file: Optional[str] = None
        self.num_buckets: int = 2 ** global_depth
        
        # Overflow para inserciones antes de reorganización (en RAM)
        self.overflow: List[Dict[str, Any]] = []
        
        # Mapeo de bucket_id a posición en archivo (para lectura eficiente)
        # Se construye después de build() o remove()
        self._bucket_positions: Dict[int, int] = {}
        
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
    
    def _hash(self, value: Any) -> int:
        """
        Función hash que retorna los primeros global_depth bits.
        """
        return hash(value) & ((1 << self.global_depth) - 1)
    
    def _hash_with_depth(self, value: Any, depth: int) -> int:
        """
        Hash con profundidad específica (para split).
        """
        return hash(value) & ((1 << depth) - 1)
    
    def build(self, rows: List[Dict[str, Any]]) -> None:
        """
        Construye el hash extensible con I/O REAL.
        
        Proceso:
        1. Distribuir datos en buckets según hash
        2. ESCRIBIR buckets a archivo .dat (I/O REAL)
        3. Manejar splits si buckets exceden capacidad
        """
        if not rows:
            return
        
        # Inicializar buckets temporales
        buckets_temp: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(2 ** self.global_depth)}
        
        # Distribuir datos por hash
        for row in rows:
            key_value = self._get_key_value(row)
            hash_val = self._hash(key_value)
            bucket_id = self.directory[hash_val]
            buckets_temp[bucket_id].append(row)
        
        # Manejar splits si es necesario
        for bucket_id in list(buckets_temp.keys()):
            while len(buckets_temp[bucket_id]) > self.bucket_size:
                # Necesita split
                self._split_bucket_during_build(buckets_temp, bucket_id)
        
        # IMPORTANTE: Después de los splits, redistribuir TODO de nuevo
        # porque el directorio cambió
        all_records = []
        for bucket in buckets_temp.values():
            all_records.extend(bucket)
        
        # Limpiar buckets y redistribuir con el directorio actualizado
        buckets_final: Dict[int, List[Dict[str, Any]]] = {}
        unique_bucket_ids = sorted(set(self.directory))
        for bucket_id in unique_bucket_ids:
            buckets_final[bucket_id] = []
        
        for row in all_records:
            key_value = self._get_key_value(row)
            hash_val = self._hash(key_value)
            bucket_id = self.directory[hash_val]
            buckets_final[bucket_id].append(row)
        
        # Escribir buckets a disco
        if not self.data_file:
            # Generar nombre de archivo usando table_name si está disponible
            if self.table_name:
                self.data_file = f"storage/{self.table_name}_exthash_buckets.dat"
            else:
                # Fallback a ID temporal (para tests)
                self.data_file = f"storage/exthash_{id(self)}_buckets.dat"
        
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # Crear mapeo de bucket_id a posición en archivo
        # IMPORTANTE: Solo escribir buckets que están realmente en uso (en el directorio)
        self._bucket_positions = {}
        unique_bucket_ids = sorted(set(self.directory))  # Solo IDs que están en el directorio
        
        for position, bucket_id in enumerate(unique_bucket_ids):
            self._bucket_positions[bucket_id] = position
        
        with open(self.data_file, 'wb') as f:
            for bucket_id in unique_bucket_ids:
                bucket = buckets_final.get(bucket_id, [])  # usar .get() por si acaso
                bucket_bytes = pickle.dumps(bucket)
                bucket_size = len(bucket_bytes)
                # Escribir: tamaño (4 bytes) + datos
                f.write(bucket_size.to_bytes(4, 'little'))
                f.write(bucket_bytes)
                self._io_writes += 1
        
        self.num_buckets = len(unique_bucket_ids)
    
    def _split_bucket_during_build(self, buckets_temp: Dict[int, List[Dict[str, Any]]], bucket_id: int) -> None:
        """
        Divide un bucket durante la construcción inicial.
        """
        local_depth = self.local_depths[bucket_id]
        
        # Si local_depth == global_depth, necesitamos duplicar directorio
        if local_depth == self.global_depth:
            self._double_directory()
            local_depth = self.local_depths[bucket_id]
        
        # Crear nuevo bucket
        new_bucket_id = self.num_buckets
        self.num_buckets += 1
        
        # Incrementar local depth
        new_local_depth = local_depth + 1
        self.local_depths[bucket_id] = new_local_depth
        self.local_depths[new_bucket_id] = new_local_depth
        
        # Redistribuir registros
        old_records = buckets_temp[bucket_id]
        buckets_temp[bucket_id] = []
        buckets_temp[new_bucket_id] = []
        
        for record in old_records:
            key_value = self._get_key_value(record)
            hash_val = self._hash_with_depth(key_value, new_local_depth)
            
            # Determinar a qué bucket va (bit adicional)
            if hash_val & (1 << (new_local_depth - 1)):
                buckets_temp[new_bucket_id].append(record)
            else:
                buckets_temp[bucket_id].append(record)
        
        # Actualizar directorio
        for i in range(len(self.directory)):
            if self.directory[i] == bucket_id:
                # Revisar si debe apuntar al nuevo bucket
                if i & (1 << (new_local_depth - 1)):
                    self.directory[i] = new_bucket_id
    
    def _double_directory(self) -> None:
        """
        Duplica el directorio cuando global_depth aumenta.
        """
        self.global_depth += 1
        new_dir = []
        for bucket_id in self.directory:
            new_dir.append(bucket_id)
            new_dir.append(bucket_id)  # Duplicar entrada
        self.directory = new_dir
    
    def _read_bucket_from_disk(self, bucket_id: int) -> List[Dict[str, Any]]:
        """
        Lee un bucket desde el archivo .dat en disco (I/O REAL).
        
        Args:
            bucket_id: Índice del bucket (0-based)
            
        Returns:
            Lista de registros en el bucket
        """
        if not self.data_file or not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        # Obtener posición física del bucket en el archivo
        if bucket_id not in self._bucket_positions:
            raise ValueError(f"Bucket {bucket_id} not found in position map")
        
        position = self._bucket_positions[bucket_id]
        
        # I/O REAL: Abrir archivo y leer bucket específico
        with open(self.data_file, 'rb') as f:
            # Saltar buckets anteriores (por posición física, no por ID)
            for i in range(position):
                size_bytes = f.read(4)
                if len(size_bytes) < 4:
                    raise EOFError(f"Unexpected EOF while seeking bucket {bucket_id} at position {position}")
                size = int.from_bytes(size_bytes, 'little')
                f.seek(size, 1)  # Saltar datos del bucket
            
            # Leer el bucket target
            size_bytes = f.read(4)
            if len(size_bytes) < 4:
                raise EOFError(f"Cannot read bucket {bucket_id}")
            size = int.from_bytes(size_bytes, 'little')
            bucket_bytes = f.read(size)
            
            self._io_reads += 1  # Contar I/O REAL
            
            return pickle.loads(bucket_bytes)
    
    def _write_overflow_to_disk(self) -> None:
        """
        Escribe el overflow a un archivo separado en disco.
        """
        if not self.data_file:
            return
        
        overflow_file = self.data_file.replace('_buckets.dat', '_overflow.dat')
        
        with open(overflow_file, 'wb') as f:
            overflow_bytes = pickle.dumps(self.overflow)
            f.write(overflow_bytes)
            self._io_writes += 1
    
    def search(self, value: Any) -> List[Dict[str, Any]]:
        """
        Búsqueda por igualdad con I/O REAL.
        
        Proceso:
        1. Calcular hash del valor
        2. Obtener bucket_id del directorio (RAM)
        3. LEER bucket desde disco (1 I/O)
        4. Buscar en overflow (RAM)
        """
        if self.num_buckets == 0:
            return []
        
        # 1. Hash del valor
        hash_val = self._hash(value)
        bucket_id = self.directory[hash_val]
        
        # 2. Leer bucket desde DISCO
        bucket = self._read_bucket_from_disk(bucket_id)
        
        # 3. Buscar en bucket
        results = [r for r in bucket if self._get_key_value(r) == value]
        
        # 4. Buscar en overflow (RAM)
        results.extend([r for r in self.overflow if self._get_key_value(r) == value])
        
        return results
    
    def range_search(self, lo: Any, hi: Any) -> List[Dict[str, Any]]:
        """
        Hash no soporta búsqueda por rango eficientemente.
        Se debe escanear TODOS los buckets (full scan).
        """
        if self.num_buckets == 0:
            return []
        
        results = []
        
        # Escanear todos los buckets únicos (evitar duplicados por sharing)
        scanned_buckets = set()
        
        for bucket_id in self.directory:
            if bucket_id not in scanned_buckets:
                bucket = self._read_bucket_from_disk(bucket_id)
                results.extend([r for r in bucket if lo <= self._get_key_value(r) <= hi])
                scanned_buckets.add(bucket_id)
        
        # Overflow
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
    
    def remove(self, value: Any) -> int:
        """
        Elimina registros con la clave dada.
        
        Estrategia:
        1. Eliminar del overflow (RAM)
        2. Leer TODOS los buckets del disco
        3. Eliminar del bucket correspondiente
        4. Reescribir TODO el archivo
        
        Returns:
            Cantidad de registros eliminados
        """
        deleted = 0
        
        # 1. Eliminar del overflow (RAM)
        original_len = len(self.overflow)
        self.overflow = [r for r in self.overflow if self._get_key_value(r) != value]
        deleted = original_len - len(self.overflow)
        
        # 2. Eliminar de disco
        if not self.data_file or not os.path.exists(self.data_file):
            return deleted
        
        # Leer TODOS los buckets primero
        unique_buckets = sorted(set(self.directory))
        all_buckets = {}
        
        for idx in unique_buckets:
            try:
                all_buckets[idx] = self._read_bucket_from_disk(idx)
            except (EOFError, Exception):
                all_buckets[idx] = []
        
        # Calcular en qué bucket está el registro
        record_for_hash = {self.key: value}
        hash_val = self._hash(self._get_key_value(record_for_hash))
        bucket_idx = self.directory[hash_val]
        
        # Filtrar registros del bucket correspondiente
        if bucket_idx in all_buckets:
            original_len = len(all_buckets[bucket_idx])
            all_buckets[bucket_idx] = [r for r in all_buckets[bucket_idx] 
                                       if self._get_key_value(r) != value]
            deleted += original_len - len(all_buckets[bucket_idx])
        
        # Reescribir TODO el archivo si hubo cambios
        if deleted > 0:
            # Reconstruir mapeo de posiciones
            self._bucket_positions = {}
            for position, bucket_id in enumerate(unique_buckets):
                self._bucket_positions[bucket_id] = position
            
            with open(self.data_file, 'wb') as f:
                for bucket_id in unique_buckets:
                    bucket = all_buckets[bucket_id]
                    bucket_bytes = pickle.dumps(bucket)
                    bucket_size = len(bucket_bytes)
                    f.write(bucket_size.to_bytes(4, 'little'))
                    f.write(bucket_bytes)
                    self._io_writes += 1
        
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
        self.directory = list(range(2 ** self.global_depth))
        self.local_depths = {i: self.global_depth for i in range(2 ** self.global_depth)}
        self.overflow.clear()
        self.num_buckets = 2 ** self.global_depth
        if self.data_file and os.path.exists(self.data_file):
            os.remove(self.data_file)
        self.data_file = None
    
    def save(self, filepath: str) -> None:
        """Persiste el índice a disco"""
        data = {
            'key': self.key,
            'global_depth': self.global_depth,
            'bucket_size': self.bucket_size,
            'directory': self.directory,
            'local_depths': self.local_depths,
            'data_file': self.data_file,
            'num_buckets': self.num_buckets,
            'overflow': self.overflow,
            'table_name': self.table_name,
            '_bucket_positions': self._bucket_positions
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, filepath: str) -> None:
        """Carga el índice desde disco"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.key = data['key']
        self.global_depth = data['global_depth']
        self.bucket_size = data['bucket_size']
        self.directory = data['directory']
        self.local_depths = data['local_depths']
        self.data_file = data['data_file']
        self.num_buckets = data['num_buckets']
        self.overflow = data['overflow']
        self.table_name = data.get('table_name')  # Compatible con versiones viejas
        self._bucket_positions = data.get('_bucket_positions', {})  # Compatible con versiones viejas
    
    @staticmethod
    def load_from(filepath: str) -> 'ExtendibleHashIndex':
        """Carga y retorna una instancia del índice"""
        idx = ExtendibleHashIndex(key='temp')
        idx.load(filepath)
        return idx
    
    def get_structure_info(self) -> dict:
        """Retorna información de la estructura del índice"""
        # Contar buckets únicos (sin sharing)
        unique_buckets = len(set(self.directory))
        
        return {
            'type': 'Extendible Hash',
            'global_depth': self.global_depth,
            'directory_size': len(self.directory),
            'unique_buckets': unique_buckets,
            'bucket_size': self.bucket_size,
            'num_buckets': self.num_buckets,
            'records_in_overflow': len(self.overflow)
        }
