"""
Benchmark con el dataset de 9.5K registros YA CARGADO
Usa las tablas existentes en storage (sin reconstruir)
"""

import time
from core.table import Table
from sql.executor import Catalog
from tabulate import tabulate
import pandas as pd

def benchmark_index(table_name: str, index_name: str):
    """Benchmark de un índice usando tabla ya cargada"""
    
    print(f"\n{'='*80}")
    print(f"BENCHMARK: {index_name.upper()}")
    print(f"Tabla: {table_name}")
    print(f"{'='*80}")
    
    # Cargar tabla desde catalog
    catalog = Catalog()
    
    if table_name not in catalog.tables:
        print(f"❌ Tabla {table_name} no encontrada en catalog")
        return None
    
    table = catalog.tables[table_name]
    index = table.indexes.get(table.schema.key)
    
    if not index:
        print(f"❌ No hay índice en la tabla")
        return None
    
    results = {
        'index_type': index_name,
        'table_name': table_name,
    }
    
    # Reset I/O
    index.reset_io_stats()
    
    # 1. SELECT por IGUALDAD
    print("\n1️⃣ SELECT por IGUALDAD...")
    test_keys = [6304287, 6317637, 6300002]  # Claves conocidas del dataset
    
    total_time = 0
    total_reads = 0
    found_count = 0
    
    for key in test_keys:
        index.reset_io_stats()
        start = time.perf_counter()
        result = index.search(key)
        elapsed = (time.perf_counter() - start) * 1000
        
        total_time += elapsed
        io_stats = index.get_io_stats()
        total_reads += io_stats['disk_reads']
        
        if result:
            found_count += 1
    
    avg_time = total_time / len(test_keys)
    avg_reads = total_reads / len(test_keys)
    
    results['select_eq_ms'] = round(avg_time, 2)
    results['select_eq_reads'] = round(avg_reads, 1)
    results['select_eq_found'] = found_count
    
    print(f"   ✓ Tests: {len(test_keys)} búsquedas")
    print(f"   ✓ Encontrados: {found_count}/{len(test_keys)}")
    print(f"   ✓ Tiempo promedio: {results['select_eq_ms']:.2f} ms")
    print(f"   ✓ Lecturas promedio: {results['select_eq_reads']:.1f} I/O")
    
    # 2. SELECT RANGE PEQUEÑO (10 registros)
    if hasattr(index, 'range_search'):
        print("\n2️⃣ SELECT RANGE PEQUEÑO (10 registros)...")
        index.reset_io_stats()
        start = time.perf_counter()
        result = index.range_search(6300000, 6300010)
        elapsed = (time.perf_counter() - start) * 1000
        io_stats = index.get_io_stats()
        
        results['range_10_ms'] = round(elapsed, 2)
        results['range_10_reads'] = io_stats['disk_reads']
        results['range_10_found'] = len(result)
        
        print(f"   ✓ Encontrados: {results['range_10_found']}")
        print(f"   ✓ Tiempo: {results['range_10_ms']:.2f} ms")
        print(f"   ✓ Lecturas I/O: {results['range_10_reads']}")
    else:
        results['range_10_ms'] = None
        results['range_10_reads'] = None
        results['range_10_found'] = 0
        print("\n2️⃣ RANGE no soportado por este índice")
    
    # 3. SELECT RANGE MEDIANO (100 registros)
    if hasattr(index, 'range_search'):
        print("\n3️⃣ SELECT RANGE MEDIANO (100 registros)...")
        index.reset_io_stats()
        start = time.perf_counter()
        result = index.range_search(6300000, 6300100)
        elapsed = (time.perf_counter() - start) * 1000
        io_stats = index.get_io_stats()
        
        results['range_100_ms'] = round(elapsed, 2)
        results['range_100_reads'] = io_stats['disk_reads']
        results['range_100_found'] = len(result)
        
        print(f"   ✓ Encontrados: {results['range_100_found']}")
        print(f"   ✓ Tiempo: {results['range_100_ms']:.2f} ms")
        print(f"   ✓ Lecturas I/O: {results['range_100_reads']}")
    else:
        results['range_100_ms'] = None
        results['range_100_reads'] = None
        results['range_100_found'] = 0
        print("\n3️⃣ RANGE no soportado")
    
    # 4. SELECT RANGE GRANDE (1000 registros)
    if hasattr(index, 'range_search'):
        print("\n4️⃣ SELECT RANGE GRANDE (1000 registros)...")
        index.reset_io_stats()
        start = time.perf_counter()
        result = index.range_search(6300000, 6301000)
        elapsed = (time.perf_counter() - start) * 1000
        io_stats = index.get_io_stats()
        
        results['range_1000_ms'] = round(elapsed, 2)
        results['range_1000_reads'] = io_stats['disk_reads']
        results['range_1000_found'] = len(result)
        
        print(f"   ✓ Encontrados: {results['range_1000_found']}")
        print(f"   ✓ Tiempo: {results['range_1000_ms']:.2f} ms")
        print(f"   ✓ Lecturas I/O: {results['range_1000_reads']}")
    else:
        results['range_1000_ms'] = None
        results['range_1000_reads'] = None
        results['range_1000_found'] = 0
        print("\n4️⃣ RANGE no soportado")
    
    # 5. INSERT
    print("\n5️⃣ INSERT...")
    new_record = {
        "Restaurant ID": 99999999,
        "Restaurant Name": "Benchmark Test Restaurant",
        "City": "Test City",
        "Aggregate rating": 4.5
    }
    
    index.reset_io_stats()
    start = time.perf_counter()
    index.add(new_record)
    elapsed = (time.perf_counter() - start) * 1000
    io_stats = index.get_io_stats()
    
    results['insert_ms'] = round(elapsed, 2)
    results['insert_writes'] = io_stats['disk_writes']
    
    print(f"   ✓ Tiempo: {results['insert_ms']:.2f} ms")
    print(f"   ✓ Escrituras I/O: {results['insert_writes']}")
    
    # 6. DELETE
    print("\n6️⃣ DELETE...")
    index.reset_io_stats()
    start = time.perf_counter()
    deleted = index.remove(99999999)
    elapsed = (time.perf_counter() - start) * 1000
    io_stats = index.get_io_stats()
    
    results['delete_ms'] = round(elapsed, 2)
    results['delete_reads'] = io_stats['disk_reads']
    results['delete_writes'] = io_stats['disk_writes']
    results['deleted_count'] = deleted
    
    print(f"   ✓ Eliminados: {deleted}")
    print(f"   ✓ Tiempo: {results['delete_ms']:.2f} ms")
    print(f"   ✓ I/O: {results['delete_reads']}R / {results['delete_writes']}W")
    
    return results

def print_comparison_table(all_results):
    """Imprime tabla comparativa formateada"""
    
    print("\n" + "="*100)
    print("📊 TABLA COMPARATIVA DE RENDIMIENTO - DATASET 9.5K REGISTROS")
    print("="*100)
    
    # Tabla de tiempos
    print("\n⏱️  TIEMPOS DE EJECUCIÓN (ms)")
    print("-"*100)
    
    time_data = []
    for r in all_results:
        time_data.append([
            r['index_type'],
            f"{r['select_eq_ms']:.2f}",
            f"{r['range_10_ms']:.2f}" if r['range_10_ms'] else "N/A",
            f"{r['range_100_ms']:.2f}" if r['range_100_ms'] else "N/A",
            f"{r['range_1000_ms']:.2f}" if r['range_1000_ms'] else "N/A",
            f"{r['insert_ms']:.2f}",
            f"{r['delete_ms']:.2f}",
        ])
    
    print(tabulate(time_data, 
                   headers=['Índice', 'SELECT =', 'RANGE (10)', 'RANGE (100)', 'RANGE (1K)', 'INSERT', 'DELETE'],
                   tablefmt='grid'))
    
    # Tabla de I/O
    print("\n💾 OPERACIONES DE I/O")
    print("-"*100)
    
    io_data = []
    for r in all_results:
        io_data.append([
            r['index_type'],
            f"{r['select_eq_reads']:.1f}",
            f"{r['range_10_reads']}" if r['range_10_reads'] else "N/A",
            f"{r['range_100_reads']}" if r['range_100_reads'] else "N/A",
            f"{r['range_1000_reads']}" if r['range_1000_reads'] else "N/A",
            f"{r['insert_writes']}",
            f"{r['delete_reads']}R / {r['delete_writes']}W",
        ])
    
    print(tabulate(io_data,
                   headers=['Índice', 'SELECT = (R)', 'RANGE 10 (R)', 'RANGE 100 (R)', 'RANGE 1K (R)', 'INSERT (W)', 'DELETE (R/W)'],
                   tablefmt='grid'))
    
    # Análisis de mejores
    print("\n🏆 ANÁLISIS DE RENDIMIENTO")
    print("-"*100)
    
    best_eq = min(all_results, key=lambda x: x['select_eq_ms'])
    print(f"✅ SELECT = más rápido: {best_eq['index_type'].upper()} ({best_eq['select_eq_ms']:.2f} ms, {best_eq['select_eq_reads']:.1f} I/O)")
    
    range_results = [r for r in all_results if r['range_100_ms'] is not None]
    if range_results:
        best_range = min(range_results, key=lambda x: x['range_100_ms'])
        print(f"✅ RANGE más rápido: {best_range['index_type'].upper()} ({best_range['range_100_ms']:.2f} ms)")
    
    best_insert = min(all_results, key=lambda x: x['insert_ms'])
    print(f"✅ INSERT más rápido: {best_insert['index_type'].upper()} ({best_insert['insert_ms']:.2f} ms)")
    
    best_delete = min(all_results, key=lambda x: x['delete_ms'])
    print(f"✅ DELETE más rápido: {best_delete['index_type'].upper()} ({best_delete['delete_ms']:.2f} ms)")

def main():
    print("="*100)
    print("🚀 BENCHMARK CON DATASET DE 9.5K REGISTROS")
    print("   Usando tablas ya cargadas en storage")
    print("="*100)
    
    # Tablas a benchmarkear (ya cargadas en storage)
    tables = [
        ('restaurants_seq', 'Sequential'),
        ('restaurants_isam', 'ISAM'),
        ('restaurants_hash', 'ExtHash'),
        ('restaurants_bplustree', 'BPlusTree'),
    ]
    
    all_results = []
    
    for table_name, index_name in tables:
        try:
            results = benchmark_index(table_name, index_name)
            if results:
                all_results.append(results)
        except Exception as e:
            print(f"❌ Error en {table_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Imprimir comparación
    if all_results:
        print_comparison_table(all_results)
        
        # Guardar resultados
        df = pd.DataFrame(all_results)
        output_file = f"benchmark_9k_results_{int(time.time())}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n💾 Resultados guardados en: {output_file}")
    
    print("\n" + "="*100)
    print("✅ BENCHMARK COMPLETADO")
    print("="*100)

if __name__ == '__main__':
    main()
