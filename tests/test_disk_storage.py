"""
Test de persistencia en disco
Verifica que DiskStorage funcione correctamente
"""
from core.disk_storage import DiskStorage
import time

def test_disk_persistence():
    print("=" * 80)
    print("TEST: PERSISTENCIA EN DISCO")
    print("=" * 80)
    
    # Crear storage con disco
    storage = DiskStorage(records_per_page=10, pool_size=5, data_dir="storage_test")
    
    # 1. Crear tabla y cargar datos
    print("\n1️⃣ Creando tabla y cargando 100 registros...")
    storage.create_table("test_table")
    
    records = [
        {"id": i, "name": f"Item {i}", "value": i * 10}
        for i in range(100)
    ]
    
    start = time.perf_counter()
    storage.load("test_table", records)
    load_time = time.perf_counter() - start
    
    print(f"   ✓ Cargados 100 registros en {load_time*1000:.2f} ms")
    print(f"   ✓ Páginas creadas: {storage.get_num_pages('test_table')}")
    
    # 2. Leer todos los datos
    print("\n2️⃣ Leyendo todos los registros...")
    start = time.perf_counter()
    loaded = storage.read_all("test_table")
    read_time = time.perf_counter() - start
    
    print(f"   ✓ Leídos {len(loaded)} registros en {read_time*1000:.2f} ms")
    print(f"   ✓ Primer registro: {loaded[0]}")
    print(f"   ✓ Último registro: {loaded[-1]}")
    
    # 3. Estadísticas
    print("\n3️⃣ Estadísticas de I/O:")
    stats = storage.get_stats()
    print(f"   • Disk Reads:  {stats['disk_reads']}")
    print(f"   • Disk Writes: {stats['disk_writes']}")
    print(f"   • Cache Hits:  {stats['cache_hits']}")
    print(f"   • Cache Misses: {stats['cache_misses']}")
    print(f"   • Hit Rate:    {stats['hit_rate']}")
    
    # 4. Flush y crear nuevo storage (simular reinicio)
    print("\n4️⃣ Simulando reinicio del sistema...")
    storage.flush_all()
    
    # Crear nuevo storage (como si reiniciáramos)
    new_storage = DiskStorage(records_per_page=10, pool_size=5, data_dir="storage_test")
    new_storage._table_metadata["test_table"] = {
        "num_records": 100,
        "num_pages": storage.get_num_pages("test_table")
    }
    
    # Leer datos persistidos
    start = time.perf_counter()
    persisted = new_storage.read_all("test_table")
    persist_read_time = time.perf_counter() - start
    
    print(f"   ✓ Datos recuperados del disco: {len(persisted)} registros")
    print(f"   ✓ Tiempo de lectura: {persist_read_time*1000:.2f} ms")
    print(f"   ✓ Datos correctos: {persisted[0] == records[0] and persisted[-1] == records[-1]}")
    
    # 5. Verificar archivos en disco
    print("\n5️⃣ Archivos en disco:")
    table_file = new_storage.disk_manager.get_table_file("test_table")
    print(f"   • Archivo: {table_file}")
    print(f"   • Existe: {table_file.exists()}")
    print(f"   • Tamaño: {table_file.stat().st_size / 1024:.2f} KB")
    
    # Cleanup
    storage.delete_table("test_table")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80)


def test_buffer_pool_lru():
    print("\n" + "=" * 80)
    print("TEST: BUFFER POOL LRU")
    print("=" * 80)
    
    # Storage con buffer pequeño (solo 3 páginas)
    storage = DiskStorage(records_per_page=5, pool_size=3, data_dir="storage_test")
    storage.create_table("lru_test")
    
    # Cargar 25 registros (5 páginas)
    records = [{"id": i, "value": i*10} for i in range(25)]
    storage.load("lru_test", records)
    
    print(f"\n📊 Configuración:")
    print(f"   • Registros por página: 5")
    print(f"   • Total registros: 25")
    print(f"   • Total páginas: 5")
    print(f"   • Buffer pool size: 3 páginas")
    
    # Resetear stats
    storage.buffer_pool.reset_stats()
    
    # Leer páginas en orden: 0, 1, 2, 3, 4
    print(f"\n🔄 Leyendo páginas 0-4 (debería haber eviction):")
    for page_id in range(5):
        records = storage.read_page("lru_test", page_id)
        print(f"   Página {page_id}: {len(records)} registros")
    
    stats = storage.buffer_pool.get_stats()
    print(f"\n📈 Resultados:")
    print(f"   • Cache Hits: {stats['cache_hits']}")
    print(f"   • Cache Misses: {stats['cache_misses']}")
    print(f"   • Páginas en cache: {stats['pages_in_cache']}/{stats['pool_size']}")
    print(f"   • Disk Reads: {stats['disk_reads']}")
    
    # Leer página 0 de nuevo (debería ser miss porque fue evictada)
    print(f"\n🔄 Leyendo página 0 de nuevo (debería ser Cache Miss):")
    storage.buffer_pool.reset_stats()
    storage.read_page("lru_test", 0)
    
    stats = storage.buffer_pool.get_stats()
    print(f"   • Cache Hits: {stats['cache_hits']}")
    print(f"   • Cache Misses: {stats['cache_misses']}")
    
    # Cleanup
    storage.delete_table("lru_test")
    
    print("\n" + "=" * 80)
    print("✅ TEST LRU COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    test_disk_persistence()
    test_buffer_pool_lru()
