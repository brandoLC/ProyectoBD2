"""
Quick performance comparison: Sequential vs ISAM
"""
from indexes.sequential import SequentialIndex
from indexes.isam import ISAMIndex
import time

def generate_test_data(n=1000):
    """Generate test data as records (not tuples)"""
    return [{"id": i, "name": f"Item {i}", "value": i * 10} for i in range(1, n+1)]

def benchmark_sequential(data, operations):
    """Benchmark Sequential Index"""
    # Build index (Sequential uses add())
    start = time.perf_counter()
    idx = SequentialIndex(key="id")
    for row in data:
        idx.add(row)
    build_time = time.perf_counter() - start
    
    # Test search
    start = time.perf_counter()
    search_count = 0
    for key in operations["search"]:
        result = idx.search(key)
        if result:
            search_count += 1
    search_time = time.perf_counter() - start
    
    # Test range search
    start = time.perf_counter()
    range_count = 0
    for low, high in operations["range"]:
        results = idx.range_search(low, high)
        range_count += len(results)
    range_time = time.perf_counter() - start
    
    # Test insert
    start = time.perf_counter()
    for record in operations["insert"]:
        idx.add(record)
    insert_time = time.perf_counter() - start
    
    return {
        "build": {"time": build_time, "count": len(data)},
        "search": {"time": search_time, "count": search_count},
        "range": {"time": range_time, "count": range_count},
        "insert": {"time": insert_time, "count": len(operations["insert"])},
    }

def benchmark_isam(data, operations):
    """Benchmark ISAM Index"""
    # Build index (ISAM uses build())
    start = time.perf_counter()
    idx = ISAMIndex(key="id")
    idx.build(data)
    build_time = time.perf_counter() - start
    
    # Test search (ISAM search returns single record or None)
    start = time.perf_counter()
    search_count = 0
    for key in operations["search"]:
        result = idx.search(key)
        if result:
            search_count += 1
    search_time = time.perf_counter() - start
    
    # Test range search
    start = time.perf_counter()
    range_count = 0
    for low, high in operations["range"]:
        results = idx.range_search(low, high)
        range_count += len(results)
    range_time = time.perf_counter() - start
    
    # Test insert (ISAM uses add(row))
    start = time.perf_counter()
    for record in operations["insert"]:
        idx.add(record)
    insert_time = time.perf_counter() - start
    
    return {
        "build": {"time": build_time, "count": len(data)},
        "search": {"time": search_time, "count": search_count},
        "range": {"time": range_time, "count": range_count},
        "insert": {"time": insert_time, "count": len(operations["insert"])},
    }

def main():
    print("=" * 80)
    print("BENCHMARK: Sequential vs ISAM")
    print("=" * 80)
    
    # Generate data
    sizes = [100, 1000, 10000]
    
    for size in sizes:
        print(f"\n{'='*80}")
        print(f"Dataset Size: {size:,} records")
        print(f"{'='*80}")
        
        data = generate_test_data(size)
        
        # Define operations
        operations = {
            "search": [size // 4, size // 2, size * 3 // 4],  # 3 searches
            "range": [(size // 4, size // 2), (1, size // 10)],  # 2 range queries
            "insert": [{"id": size + i, "name": f"New {i}", "value": 99} for i in range(1, 11)]  # 10 inserts
        }
        
        # Benchmark Sequential
        print("\n--- SEQUENTIAL INDEX ---")
        seq_results = benchmark_sequential(data, operations)
        print(f"Build:  {seq_results['build']['time']*1000:8.3f} ms | Records: {seq_results['build']['count']:6,}")
        print(f"Search: {seq_results['search']['time']*1000:8.3f} ms | Found: {seq_results['search']['count']:6,}")
        print(f"Range:  {seq_results['range']['time']*1000:8.3f} ms | Found: {seq_results['range']['count']:6,}")
        print(f"Insert: {seq_results['insert']['time']*1000:8.3f} ms | Added: {seq_results['insert']['count']:6,}")
        
        # Benchmark ISAM
        print("\n--- ISAM INDEX ---")
        isam_results = benchmark_isam(data, operations)
        print(f"Build:  {isam_results['build']['time']*1000:8.3f} ms | Records: {isam_results['build']['count']:6,}")
        print(f"Search: {isam_results['search']['time']*1000:8.3f} ms | Found: {isam_results['search']['count']:6,}")
        print(f"Range:  {isam_results['range']['time']*1000:8.3f} ms | Found: {isam_results['range']['count']:6,}")
        print(f"Insert: {isam_results['insert']['time']*1000:8.3f} ms | Added: {isam_results['insert']['count']:6,}")
        
        # Speedup comparison
        print("\n--- SPEEDUP (Sequential / ISAM) ---")
        print(f"Build:  {seq_results['build']['time'] / isam_results['build']['time']:.2f}x")
        print(f"Search: {seq_results['search']['time'] / isam_results['search']['time']:.2f}x")
        print(f"Range:  {seq_results['range']['time'] / isam_results['range']['time']:.2f}x")
        print(f"Insert: {seq_results['insert']['time'] / isam_results['insert']['time']:.2f}x")

if __name__ == "__main__":
    main()
