"""
Disk Manager - Gestión de páginas en disco
Simula el almacenamiento en memoria secundaria con archivos binarios
"""
import os
import pickle
from typing import Any, Dict, Optional
from pathlib import Path

class Page:
    """Representa una página de disco (4KB por defecto)"""
    PAGE_SIZE = 4096  # 4KB - tamaño estándar
    
    def __init__(self, page_id: int, data: Any = None):
        self.page_id = page_id
        self.data = data if data is not None else []
        self.is_dirty = False  # Marca si necesita escribirse a disco
    
    def get_size(self) -> int:
        """Retorna el tamaño serializado de la página"""
        return len(pickle.dumps(self.data))
    
    def is_full(self) -> bool:
        """Verifica si la página está llena"""
        return self.get_size() >= self.PAGE_SIZE


class DiskManager:
    """
    Gestiona la lectura/escritura de páginas en archivos binarios.
    Simula el comportamiento de un sistema de archivos con páginas fijas.
    """
    
    def __init__(self, data_dir: str = "storage"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Contadores de I/O real
        self.disk_reads = 0
        self.disk_writes = 0
    
    def get_table_file(self, table_name: str) -> Path:
        """Retorna la ruta del archivo de una tabla"""
        return self.data_dir / f"{table_name}.dat"
    
    def read_page(self, table_name: str, page_id: int) -> Optional[Page]:
        """
        Lee una página específica del disco.
        Incrementa contador de disk_reads.
        """
        file_path = self.get_table_file(table_name)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                # Buscar la página específica
                f.seek(page_id * Page.PAGE_SIZE)
                data_bytes = f.read(Page.PAGE_SIZE)
                
                if not data_bytes:
                    return None
                
                # Deserializar
                data = pickle.loads(data_bytes.rstrip(b'\x00'))
                
                self.disk_reads += 1
                return Page(page_id, data)
                
        except (EOFError, pickle.UnpicklingError):
            return None
    
    def write_page(self, table_name: str, page: Page) -> None:
        """
        Escribe una página al disco.
        Incrementa contador de disk_writes.
        """
        file_path = self.get_table_file(table_name)
        
        # Serializar datos
        data_bytes = pickle.dumps(page.data)
        
        # Padding para llenar la página completa
        if len(data_bytes) < Page.PAGE_SIZE:
            data_bytes += b'\x00' * (Page.PAGE_SIZE - len(data_bytes))
        elif len(data_bytes) > Page.PAGE_SIZE:
            # Si excede, truncar (en un sistema real esto sería un error)
            data_bytes = data_bytes[:Page.PAGE_SIZE]
        
        # Escribir al archivo
        mode = 'r+b' if file_path.exists() else 'wb'
        with open(file_path, mode) as f:
            f.seek(page.page_id * Page.PAGE_SIZE)
            f.write(data_bytes)
        
        page.is_dirty = False
        self.disk_writes += 1
    
    def read_all_pages(self, table_name: str) -> list[Page]:
        """Lee todas las páginas de una tabla"""
        file_path = self.get_table_file(table_name)
        
        if not file_path.exists():
            return []
        
        pages = []
        page_id = 0
        
        with open(file_path, 'rb') as f:
            while True:
                data_bytes = f.read(Page.PAGE_SIZE)
                if not data_bytes:
                    break
                
                try:
                    data = pickle.loads(data_bytes.rstrip(b'\x00'))
                    pages.append(Page(page_id, data))
                    page_id += 1
                    self.disk_reads += 1
                except (EOFError, pickle.UnpicklingError):
                    break
        
        return pages
    
    def allocate_page(self, table_name: str) -> Page:
        """Reserva una nueva página para una tabla"""
        file_path = self.get_table_file(table_name)
        
        # Determinar el ID de la nueva página
        if file_path.exists():
            file_size = file_path.stat().st_size
            page_id = file_size // Page.PAGE_SIZE
        else:
            page_id = 0
        
        return Page(page_id)
    
    def delete_table(self, table_name: str) -> None:
        """Elimina el archivo de una tabla"""
        file_path = self.get_table_file(table_name)
        if file_path.exists():
            file_path.unlink()
    
    def get_table_size(self, table_name: str) -> int:
        """Retorna el tamaño en bytes del archivo de tabla"""
        file_path = self.get_table_file(table_name)
        return file_path.stat().st_size if file_path.exists() else 0
    
    def get_num_pages(self, table_name: str) -> int:
        """Retorna el número de páginas de una tabla"""
        size = self.get_table_size(table_name)
        return size // Page.PAGE_SIZE if size > 0 else 0
    
    def reset_counters(self) -> None:
        """Resetea los contadores de I/O"""
        self.disk_reads = 0
        self.disk_writes = 0
    
    def get_io_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de I/O"""
        return {
            "disk_reads": self.disk_reads,
            "disk_writes": self.disk_writes,
            "total_ios": self.disk_reads + self.disk_writes
        }
