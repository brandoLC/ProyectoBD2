"""
Buffer Pool Manager - Gestión de caché de páginas en memoria
Implementa política LRU (Least Recently Used) para evicción
"""
from typing import Dict, Optional, Tuple
from collections import OrderedDict
from .disk_manager import DiskManager, Page


class BufferPool:
    """
    Pool de buffers que mantiene páginas en memoria.
    Implementa LRU para decidir qué páginas evictar cuando se llena.
    """
    
    def __init__(self, pool_size: int = 50, disk_manager: Optional[DiskManager] = None):
        """
        Args:
            pool_size: Número máximo de páginas en memoria
            disk_manager: Gestor de disco para I/O
        """
        self.pool_size = pool_size
        self.disk_manager = disk_manager or DiskManager()
        
        # Cache: (table_name, page_id) -> Page
        # OrderedDict mantiene orden de inserción para LRU
        self.cache: OrderedDict[Tuple[str, int], Page] = OrderedDict()
        
        # Estadísticas
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_page(self, table_name: str, page_id: int) -> Optional[Page]:
        """
        Obtiene una página del buffer pool o del disco.
        Implementa LRU: mueve la página al final del OrderedDict.
        """
        key = (table_name, page_id)
        
        # Cache hit
        if key in self.cache:
            self.cache_hits += 1
            # Mover al final (más recientemente usado)
            self.cache.move_to_end(key)
            return self.cache[key]
        
        # Cache miss - leer del disco
        self.cache_misses += 1
        page = self.disk_manager.read_page(table_name, page_id)
        
        if page is None:
            return None
        
        # Agregar al cache
        self._add_to_cache(key, page)
        return page
    
    def put_page(self, table_name: str, page: Page, write_through: bool = False) -> None:
        """
        Coloca una página en el buffer pool.
        
        Args:
            table_name: Nombre de la tabla
            page: Página a guardar
            write_through: Si True, escribe inmediatamente a disco
        """
        key = (table_name, page.page_id)
        
        # Marcar como dirty (necesita escribirse)
        page.is_dirty = True
        
        # Agregar/actualizar en cache
        self._add_to_cache(key, page)
        
        # Write-through: escribir inmediatamente a disco
        if write_through:
            self.flush_page(table_name, page.page_id)
    
    def _add_to_cache(self, key: Tuple[str, int], page: Page) -> None:
        """Agrega una página al cache, evictando si es necesario"""
        # Si ya existe, moverla al final
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = page
            return
        
        # Si el cache está lleno, evictar la página LRU (la primera)
        if len(self.cache) >= self.pool_size:
            self._evict_page()
        
        # Agregar nueva página
        self.cache[key] = page
    
    def _evict_page(self) -> None:
        """Evicta la página menos recientemente usada (LRU)"""
        if not self.cache:
            return
        
        # Obtener la primera página (LRU)
        lru_key, lru_page = self.cache.popitem(last=False)
        
        # Si está dirty, escribir a disco antes de evictar
        if lru_page.is_dirty:
            table_name, page_id = lru_key
            self.disk_manager.write_page(table_name, lru_page)
    
    def flush_page(self, table_name: str, page_id: int) -> None:
        """Escribe una página específica a disco si está dirty"""
        key = (table_name, page_id)
        
        if key in self.cache:
            page = self.cache[key]
            if page.is_dirty:
                self.disk_manager.write_page(table_name, page)
    
    def flush_table(self, table_name: str) -> None:
        """Escribe todas las páginas dirty de una tabla a disco"""
        keys_to_flush = [k for k in self.cache.keys() if k[0] == table_name]
        
        for key in keys_to_flush:
            page = self.cache[key]
            if page.is_dirty:
                self.disk_manager.write_page(table_name, page)
    
    def flush_all(self) -> None:
        """Escribe todas las páginas dirty a disco"""
        for (table_name, page_id), page in self.cache.items():
            if page.is_dirty:
                self.disk_manager.write_page(table_name, page)
    
    def clear_table(self, table_name: str) -> None:
        """Elimina todas las páginas de una tabla del cache"""
        # Primero hacer flush
        self.flush_table(table_name)
        
        # Eliminar del cache
        keys_to_remove = [k for k in self.cache.keys() if k[0] == table_name]
        for key in keys_to_remove:
            del self.cache[key]
    
    def clear_all(self) -> None:
        """Limpia todo el buffer pool (con flush)"""
        self.flush_all()
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, any]:
        """Retorna estadísticas del buffer pool"""
        total_accesses = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_accesses * 100) if total_accesses > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "pages_in_cache": len(self.cache),
            "pool_size": self.pool_size,
            "disk_reads": self.disk_manager.disk_reads,
            "disk_writes": self.disk_manager.disk_writes
        }
    
    def reset_stats(self) -> None:
        """Resetea las estadísticas"""
        self.cache_hits = 0
        self.cache_misses = 0
        self.disk_manager.reset_counters()
