"""
Test de DELETE en SQL
"""

from sql import parser, executor
import pandas as pd

# Limpiar storage
executor.catalog.tables.clear()

print("=" * 60)
print("TEST DELETE SQL")
print("=" * 60)

# 1. Crear tabla
print("\n1. Creando tabla...")
sql = "CREATE TABLE test_del USING sequential"
node = parser.parse(sql)
result = executor.execute(node)
print(f"   ✓ {result}")

# 2. Cargar datos
print("\n2. Cargando datos...")
sql = "LOAD FROM data/kaggle_Dataset _100.csv INTO test_del"
node = parser.parse(sql)
result = executor.execute(node)
print(f"   ✓ Cargados: {result.get('loaded', 0)} registros")
print(f"   ✓ I/O: {result.get('io_stats', {})}")

# 3. Buscar un registro específico para eliminar
print("\n3. Buscando registro para eliminar...")
sql = 'SELECT * FROM test_del WHERE "Restaurant ID" = 6304287'
node = parser.parse(sql)
result = executor.execute(node)
rows = result.get('rows', [])
print(f"   ✓ Encontrados: {len(rows)}")
if rows:
    print(f"   ✓ Registro: {rows[0].get('Restaurant Name', 'N/A')}")

# 4. DELETE
print("\n4. Ejecutando DELETE...")
sql = 'DELETE FROM test_del WHERE "Restaurant ID" = 6304287'
node = parser.parse(sql)
result = executor.execute(node)
print(f"   ✓ Eliminados: {result.get('deleted', 0)}")
print(f"   ✓ I/O: {result.get('io_stats', {})}")

# 5. Verificar que se eliminó
print("\n5. Verificando eliminación...")
sql = 'SELECT * FROM test_del WHERE "Restaurant ID" = 6304287'
node = parser.parse(sql)
result = executor.execute(node)
rows = result.get('rows', [])
print(f"   ✓ Encontrados: {len(rows)} (esperado: 0)")

if len(rows) == 0:
    print("\n✅ DELETE funcionó correctamente!")
else:
    print("\n❌ ERROR: El registro no se eliminó")

# 6. Verificar que otros registros siguen ahí
print("\n6. Verificando otros registros...")
sql = 'SELECT * FROM test_del WHERE "Restaurant ID" = 6318506'
node = parser.parse(sql)
result = executor.execute(node)
rows = result.get('rows', [])
print(f"   ✓ Encontrados: {len(rows)}")
if rows:
    print(f"   ✓ Registro intacto: {rows[0].get('Restaurant Name', 'N/A')}")
    print("\n✅ Otros registros mantienen integridad!")

print("\n" + "=" * 60)
