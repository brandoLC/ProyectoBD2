"""
Debug Extendible Hash - Búsqueda por ID específico
"""

from sql import parser, executor
import pandas as pd

# Limpiar
executor.catalog.tables.clear()

print("=" * 60)
print("DEBUG: Extendible Hash Search")
print("=" * 60)

# 1. Crear tabla
print("\n1. Creando tabla con Extendible Hash...")
sql = "CREATE TABLE test_hash USING ext_hash"
node = parser.parse(sql)
result = executor.execute(node)
print(f"   ✓ {result}")

# 2. Cargar datos
print("\n2. Cargando datos...")
sql = "LOAD FROM data/kaggle_Dataset _100.csv INTO test_hash"
node = parser.parse(sql)
result = executor.execute(node)
print(f"   ✓ Cargados: {result.get('loaded', 0)} registros")

# 3. Obtener referencia al índice
table = executor.catalog.tables['test_hash']
idx = table.get_index('Restaurant ID')

print(f"\n3. Info del índice:")
print(f"   Global depth: {idx.global_depth}")
print(f"   Directorio: {idx.directory}")
print(f"   Buckets únicos: {sorted(set(idx.directory))}")
print(f"   Overflow (RAM): {len(idx.overflow)} registros")

# 4. Buscar ID específico
test_id = 6300002
print(f"\n4. Buscando ID {test_id}...")
print(f"   Hash: {idx._hash(test_id)}")
print(f"   Bucket ID: {idx.directory[idx._hash(test_id)]}")

# Buscar directamente en el índice
idx.reset_io_stats()
result_direct = idx.search(test_id)
print(f"   ✓ Encontrados (directo): {len(result_direct)}")
print(f"   ✓ I/O reads: {idx._io_reads}")

# 5. Buscar vía SQL
print(f"\n5. Buscando vía SQL...")
sql = f'SELECT * FROM test_hash WHERE "Restaurant ID" = {test_id}'
node = parser.parse(sql)
result = executor.execute(node)
rows = result.get('rows', [])
print(f"   ✓ Encontrados (SQL): {len(rows)}")
if rows:
    print(f"   ✓ Nombre: {rows[0].get('Restaurant Name', 'N/A')}")

# 6. Verificar si existe en los datos originales
print(f"\n6. Verificando en CSV original...")
df = pd.read_csv('data/kaggle_Dataset _100.csv')
matching = df[df['Restaurant ID'] == test_id]
print(f"   ✓ En CSV: {len(matching)} registro(s)")
if len(matching) > 0:
    print(f"   ✓ Nombre en CSV: {matching.iloc[0]['Restaurant Name']}")

# 7. Buscar en overflow
print(f"\n7. Buscando en overflow...")
overflow_matches = [r for r in idx.overflow if r.get('Restaurant ID') == test_id]
print(f"   ✓ En overflow: {len(overflow_matches)}")

# 8. Buscar en todos los buckets del disco
print(f"\n8. Escaneando todos los buckets del disco...")
unique_buckets = sorted(set(idx.directory))
for bucket_id in unique_buckets:
    try:
        bucket = idx._read_bucket_from_disk(bucket_id)
        matches = [r for r in bucket if r.get('Restaurant ID') == test_id]
        if matches:
            print(f"   ✓ Bucket {bucket_id}: {len(matches)} registro(s)")
            print(f"      Nombre: {matches[0].get('Restaurant Name', 'N/A')}")
    except Exception as e:
        print(f"   ✗ Error leyendo bucket {bucket_id}: {e}")

print("\n" + "=" * 60)
