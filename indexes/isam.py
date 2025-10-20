from typing import Any, Dict, List, Optional
from bisect import bisect_left, bisect_right
import pickle
import os
from .base import IIndex

class ISAMIndex(IIndex):
    """
    ISAM (Indexed Sequential Access Method) - 3 niveles con I/O REAL
    
    Arquitectura:
    - Nivel 1 (L2): Índice superior en RAM
    - Nivel 2 (L1): Índice de buckets en RAM  
    - Nivel 3 (Datos): Buckets en DISCO (archivo .dat con fseek/fread)
    
    Flujo de búsqueda:
    1. Buscar en L2 (RAM) - 0 I/O
    2. Buscar en L1 (RAM) - 0 I/O
    3. Leer bucket del DISCO con fopen/fseek/fread - 1 I/O READ real
    4. Buscar en bucket (RAM) - 0 I/O
    """
    def __init__(self, key: str, fanout: int = 20, fanout_l2: int = 5, table_name: Optional[str] = None) -> None:
        self.key = key
        self.fanout = fanout
        self.fanout_l2 = fanout_l2
        self.table_name = table_name  # Nombre de tabla para generar nombres de archivo consistentes
        
        # Índices en RAM (solo claves, no datos completos)
        self.index_l1: List[Any] = []  # Primera clave de cada bucket
        self.index_l2: List[Any] = []  # Primera clave cada fanout_l2 buckets
        
        # Archivo de datos en disco (buckets)
        self.data_file: Optional[str] = None
        self.num_buckets: int = 0
        
        # Overflow en RAM (inserciones post-build)
        self.overflow: Dict[int, List[Dict[str, Any]]] = {}
        
        # Contador de I/O REAL
        self._io_reads = 0
        self._io_writes = 0
        
    def build(self, rows: List[Dict[str, Any]]) -> None:
        """
        Construye el índice ISAM de 3 niveles con I/O REAL.
        
        Proceso:
        1. Ordenar datos por clave
        2. Particionar en buckets
        3. ESCRIBIR buckets a archivo .dat (I/O REAL)
        4. Construir L1 (primera clave de cada bucket) en RAM
        5. Construir L2 (primera clave cada fanout_l2 buckets) en RAM
        """
        if not rows:
            return
            
        # 1. Ordenar datos por clave
        rows_sorted = sorted(rows, key=lambda r: self._get_key_value(r))
        
        # 2. Particionar en buckets
        buckets_temp = []
        for i in range(0, len(rows_sorted), self.fanout):
            bucket = rows_sorted[i:i+self.fanout]
            buckets_temp.append(bucket)
        
        self.num_buckets = len(buckets_temp)
        
        # 3. ESCRIBIR buckets a disco (I/O REAL)
        if not self.data_file:
            # Generar nombre de archivo usando table_name si está disponible
            if self.table_name:
                self.data_file = f"storage/{self.table_name}_isam_buckets.dat"
            else:
                # Fallback a ID temporal (para tests)
                self.data_file = f"storage/isam_{id(self)}_buckets.dat"
        
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        with open(self.data_file, 'wb') as f:
            for bucket in buckets_temp:
                bucket_bytes = pickle.dumps(bucket)
                bucket_size = len(bucket_bytes)
                # Escribir: tamaño (4 bytes) + datos
                f.write(bucket_size.to_bytes(4, 'little'))
                f.write(bucket_bytes)
                self._io_writes += 1
        
        # 4. Construir L1: primera clave de cada bucket (EN RAM)
        self.index_l1 = [self._get_key_value(bucket[0]) for bucket in buckets_temp]
        
        # 5. Construir L2: primera clave cada fanout_l2 buckets (EN RAM)
        self.index_l2 = []
        for i in range(0, len(self.index_l1), self.fanout_l2):
            self.index_l2.append(self.index_l1[i])
        
        # Si solo hay 1 entrada en L2, agregar al menos 2
        if len(self.index_l2) == 1 and len(self.index_l1) > 1:
            self.index_l2 = [self.index_l1[0], self.index_l1[-1]]
        
        # 6. Inicializar overflow vacío
        self.overflow = {i: [] for i in range(self.num_buckets)}
    
    def _find_bucket_index(self, value: Any) -> int:
        """
        Encuentra el índice del bucket usando búsqueda en 2 niveles (L2 → L1).
        """
        if not self.index_l1:
            return 0
        
        # Si hay L2, buscar primero ahí
        if self.index_l2 and len(self.index_l2) > 1:
            # Paso 1: Búsqueda en L2
            l2_idx = bisect_right(self.index_l2, value) - 1
            l2_idx = max(0, l2_idx)
            
            # Calcular rango en L1
            start_l1 = l2_idx * self.fanout_l2
            end_l1 = min(start_l1 + self.fanout_l2, len(self.index_l1))
            
            # Paso 2: Búsqueda en L1
            l1_range = self.index_l1[start_l1:end_l1]
            if not l1_range:
                return max(0, self.num_buckets - 1)
            
            relative_idx = bisect_right(l1_range, value) - 1
            relative_idx = max(0, relative_idx)
            idx = start_l1 + relative_idx
        else:
            # Búsqueda directa en L1
            idx = bisect_right(self.index_l1, value) - 1
            idx = max(0, idx)
        
        return min(idx, self.num_buckets - 1)
    
    def _read_bucket_from_disk(self, bucket_idx: int) -> List[Dict[str, Any]]:
        """
        LEE bucket desde DISCO con fopen/fseek/fread (I/O REAL).
        
        Formato del archivo:
        [size_0 (4 bytes)][bucket_0 pickled][size_1 (4 bytes)][bucket_1 pickled]...
        """
        if not self.data_file or not os.path.exists(self.data_file):
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        # I/O REAL: Abrir archivo y leer bucket específico
        with open(self.data_file, 'rb') as f:
            # Saltar buckets anteriores para llegar al bucket_idx
            for i in range(bucket_idx):
                size_bytes = f.read(4)
                if len(size_bytes) < 4:
                    raise EOFError(f"Unexpected EOF while seeking bucket {bucket_idx}")
                size = int.from_bytes(size_bytes, 'little')
                f.seek(size, 1)  # Saltar los datos del bucket
            
            # Leer el bucket target
            size_bytes = f.read(4)
            if len(size_bytes) < 4:
                raise EOFError(f"Cannot read bucket {bucket_idx}")
            size = int.from_bytes(size_bytes, 'little')
            bucket_bytes = f.read(size)
            
            self._io_reads += 1  # Contar I/O REAL
            
            return pickle.loads(bucket_bytes)
    
    def _write_overflow_to_disk(self) -> None:
        """
        Escribe el overflow a un archivo separado en disco.
        
        Esto permite persistir las inserciones pendientes.
        """
        if not self.data_file:
            return
        
        overflow_file = self.data_file.replace('_buckets.dat', '_overflow.dat')
        
        with open(overflow_file, 'wb') as f:
            overflow_bytes = pickle.dumps(self.overflow)
            f.write(overflow_bytes)
            self._io_writes += 1  # Contar escritura a disco
    
    def _get_key_value(self, row: Dict[str, Any]) -> Any:
        """
        Obtiene el valor de la clave del registro.
        Maneja claves con espacios, comillas o diferencias de mayúsculas.
        """
        # Primero intentar directo
        if self.key in row:
            return row[self.key]
        
        # Normalizar claves para buscar (eliminar comillas, espacios, guiones bajos)
        def normalize_key(k: str) -> str:
            return k.lower().replace('"', '').replace("'", "").replace(" ", "").replace("_", "")
        
        key_normalized = normalize_key(self.key)
        
        for k, v in row.items():
            if normalize_key(k) == key_normalized:
                return v
        
        raise KeyError(f"Key '{self.key}' not found in row. Available keys: {list(row.keys())}")
    
    def get_io_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de I/O REAL"""
        stats = {
            'disk_reads': self._io_reads,
            'disk_writes': self._io_writes
        }
        self._io_reads = 0  # Reset después de leer
        self._io_writes = 0
        return stats
    
    def search(self, value: Any) -> List[Dict[str, Any]]:
        """
        Búsqueda por igualdad con I/O REAL.
        
        Flujo:
        1. Buscar en índices (RAM) - 0 I/O
        2. Leer bucket del DISCO - 1 I/O READ REAL
        3. Buscar en bucket
        """
        if self.num_buckets == 0:
            return []
        
        results = []
        
        # 1. Encontrar bucket usando índices (RAM, 0 I/O)
        bucket_idx = self._find_bucket_index(value)
        
        # 2. Leer bucket del DISCO (I/O REAL)
        bucket = self._read_bucket_from_disk(bucket_idx)
        
        # 3. Buscar en el bucket
        for record in bucket:
            if self._get_key_value(record) == value:
                results.append(record)
        
        # 4. Buscar en overflow (RAM, 0 I/O)
        if bucket_idx in self.overflow:
            for record in self.overflow[bucket_idx]:
                if self._get_key_value(record) == value:
                    results.append(record)
        
        return results
    
    def range_search(self, lo: Any, hi: Any) -> List[Dict[str, Any]]:
        """
        Búsqueda por rango OPTIMIZADA.
        
        Verifica en L1 (RAM) antes de leer del disco para evitar lecturas innecesarias.
        Lee múltiples buckets del DISCO solo si es necesario (N I/O reads REALES).
        """
        if self.num_buckets == 0:
            return []
        
        results = []
        
        # 1. Encontrar bucket inicial
        start_bucket = self._find_bucket_index(lo)
        
        # 2. Recorrer buckets desde start_bucket
        for bucket_idx in range(start_bucket, self.num_buckets):
            # OPTIMIZACIÓN: Verificar en L1 (RAM) ANTES de leer del disco
            # Si la primera clave del bucket > hi, no hay necesidad de leer
            if bucket_idx < len(self.index_l1) and self.index_l1[bucket_idx] > hi:
                break  # ✅ Termina sin leer este bucket (ahorra 1 I/O)
            
            # Leer bucket del DISCO (I/O REAL)
            bucket = self._read_bucket_from_disk(bucket_idx)
            
            # Buscar en el bucket
            for record in bucket:
                key_val = self._get_key_value(record)
                if lo <= key_val <= hi:
                    results.append(record)
                elif key_val > hi:
                    break
            
            # Buscar en overflow
            if bucket_idx in self.overflow:
                for record in self.overflow[bucket_idx]:
                    key_val = self._get_key_value(record)
                    if lo <= key_val <= hi:
                        results.append(record)
                    elif key_val > hi:
                        break
        
        return results
    
    def add(self, row: Dict[str, Any]) -> None:
        """
        Inserta un registro en overflow y persiste a disco.
        
        Con I/O real, las inserciones van SIEMPRE a overflow (RAM).
        Pero ahora se escriben a disco para persistencia.
        """
        if self.num_buckets == 0:
            self.build([row])
            return
        
        key_value = self._get_key_value(row)
        bucket_idx = self._find_bucket_index(key_value)
        
        # Insertar en overflow (RAM)
        if bucket_idx not in self.overflow:
            self.overflow[bucket_idx] = []
        
        overflow_list = self.overflow[bucket_idx]
        insert_pos = bisect_right([self._get_key_value(r) for r in overflow_list], key_value)
        overflow_list.insert(insert_pos, row)
        
        # Escribir overflow a disco (I/O REAL)
        self._write_overflow_to_disk()
    
    def remove(self, value: Any) -> int:
        """
        Elimina registros con la clave dada.
        
        Estrategia:
        1. Eliminar del overflow (RAM)
        2. Buscar en buckets de disco
        3. Reescribir buckets modificados (I/O real)
        
        Returns:
            Cantidad de registros eliminados
        """
        deleted = 0
        
        # 1. Eliminar del overflow (RAM)
        for bucket_idx in self.overflow:
            overflow = self.overflow[bucket_idx]
            original_len = len(overflow)
            self.overflow[bucket_idx] = [r for r in overflow if self._get_key_value(r) != value]
            deleted += original_len - len(self.overflow[bucket_idx])
        
        # 2. Buscar en buckets de disco y reescribir si es necesario
        if not self.data_file or not os.path.exists(self.data_file):
            return deleted
        
        # Buscar el bucket correcto usando índices
        bucket_idx = self._find_bucket_index(value)
        
        # Leer el bucket desde disco
        bucket = self._read_bucket_from_disk(bucket_idx)
        
        # Filtrar registros
        original_len = len(bucket)
        filtered_bucket = [r for r in bucket if self._get_key_value(r) != value]
        
        if len(filtered_bucket) < original_len:
            deleted += original_len - len(filtered_bucket)
            
            # Reescribir el bucket modificado
            self._rewrite_bucket(bucket_idx, filtered_bucket)
        
        return deleted
    
    def _rewrite_bucket(self, bucket_idx: int, new_bucket: List[Dict[str, Any]]) -> None:
        """
        Reescribe un bucket específico en disco.
        
        NOTA: Como los buckets tienen tamaño variable, necesitamos
        reescribir TODO el archivo para mantener la estructura.
        """
        if not self.data_file or not os.path.exists(self.data_file):
            return
        
        # Leer todos los buckets
        all_buckets = []
        num_buckets = len(self.index_l1)
        
        for i in range(num_buckets):
            if i == bucket_idx:
                all_buckets.append(new_bucket)
            else:
                all_buckets.append(self._read_bucket_from_disk(i))
        
        # Reescribir archivo completo
        with open(self.data_file, 'wb') as f:
            for bucket in all_buckets:
                bucket_bytes = pickle.dumps(bucket)
                bucket_size = len(bucket_bytes)
                f.write(bucket_size.to_bytes(4, 'little'))
                f.write(bucket_bytes)
                self._io_writes += 1
    
    def save(self, filepath: str) -> None:
        """
        Persiste el índice ISAM a disco.
        
        Archivos:
        - _l2.idx: Índice L2 (RAM)
        - _l1.idx: Índice L1 (RAM)
        - _buckets.dat: Buckets (DISCO, ya escrito en build)
        - _overflow.dat: Overflow (RAM)
        """
        base_path = filepath.replace('.idx', '')
        
        # Guardar L2
        l2_data = {
            'keys': self.index_l2,
            'fanout_l2': self.fanout_l2
        }
        with open(f"{base_path}_l2.idx", 'wb') as f:
            pickle.dump(l2_data, f)
        
        # Guardar L1
        l1_data = {
            'keys': self.index_l1,
            'key_field': self.key
        }
        with open(f"{base_path}_l1.idx", 'wb') as f:
            pickle.dump(l1_data, f)
        
        # Guardar metadata + overflow
        data = {
            'data_file': self.data_file,
            'num_buckets': self.num_buckets,
            'overflow': self.overflow,
            'fanout': self.fanout
        }
        with open(f"{base_path}_overflow.dat", 'wb') as f:
            pickle.dump(data, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'ISAMIndex':
        """
        Carga el índice ISAM desde disco.
        
        Carga L2, L1 y metadata en RAM.
        Los buckets permanecen en archivo .dat (I/O real).
        """
        base_path = filepath.replace('.idx', '')
        
        # Cargar L2
        with open(f"{base_path}_l2.idx", 'rb') as f:
            l2_data = pickle.load(f)
        
        # Cargar L1
        with open(f"{base_path}_l1.idx", 'rb') as f:
            l1_data = pickle.load(f)
        
        # Cargar metadata + overflow
        with open(f"{base_path}_overflow.dat", 'rb') as f:
            data = pickle.load(f)
        
        # Crear índice
        idx = cls(
            key=l1_data['key_field'],
            fanout=data['fanout'],
            fanout_l2=l2_data['fanout_l2']
        )
        
        idx.index_l2 = l2_data['keys']
        idx.index_l1 = l1_data['keys']
        idx.data_file = data['data_file']
        idx.num_buckets = data['num_buckets']
        idx.overflow = data['overflow']
        
        return idx
    
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
    
    def get_structure_info(self) -> dict:
        """Retorna información de la estructura del índice"""
        total_in_overflow = sum(len(ov) for ov in self.overflow.values())
        
        return {
            'type': 'ISAM',
            'levels': 3,
            'l2_entries': len(self.index_l2),
            'l1_entries': len(self.index_l1),
            'num_buckets': self.num_buckets,
            'records_in_overflow': total_in_overflow,
            'fanout': self.fanout,
            'fanout_l2': self.fanout_l2,
            'data_file': self.data_file
        }
    
    def get_storage_info(self, base_path: str) -> dict:
        """Retorna información de los archivos en disco"""
        files = {}
        
        for suffix in ['_l2.idx', '_l1.idx', '_overflow.dat']:
            path = f"{base_path}{suffix}"
            if os.path.exists(path):
                files[suffix] = os.path.getsize(path)
        
        return {
            'files': files,
            'total_size': sum(files.values())
        }
