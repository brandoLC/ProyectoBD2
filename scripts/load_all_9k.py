"""
Script para cargar las 4 tablas con el dataset completo (9.5K registros)
"""
import csv
import time
from pathlib import Path
from core.schema import TableSchema, Column
from core.table import Table
from sql.executor import Catalog
from indexes.sequential import SequentialIndex
from indexes.isam import ISAMIndex
from indexes.ext_hash import ExtendibleHashIndex
from indexes.bplustree import BPlusTreeIndex

CSV_PATH = Path("data") / "kaggle_Dataset .csv"

def infer_type(value: str) -> str:
    """Inferir tipo de dato"""
    if not value or value == "":
        return "TEXT"
    try:
        int(value)
        return "INT"
    except ValueError:
        pass
    try:
        float(value)
        return "FLOAT"
    except ValueError:
        pass
    return "TEXT"

def load_csv_data():
    """Cargar CSV y crear schema"""
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"✓ CSV cargado: {len(rows)} registros")
    
    if not rows:
        raise ValueError("CSV vacío")
    
    # Inferir schema
    sample_row = rows[0]
    columns = []
    for col_name, val in sample_row.items():
        col_type = infer_type(val)
        columns.append(Column(name=col_name, type=col_type))
    
    key_col = "Restaurant ID"
    schema = TableSchema(name="restaurants_temp", key=key_col, columns=columns)
    
    print(f"✓ Schema: {len(columns)} columnas, key={key_col}")
    
    # Convertir tipos
    converted_rows = []
    for row in rows:
        converted = {}
        for col in schema.columns:
            val = row.get(col.name, "")
            if val == "" or val is None:
                converted[col.name] = None
            elif col.type == "INT":
                converted[col.name] = int(val)
            elif col.type == "FLOAT":
                converted[col.name] = float(val)
            else:
                converted[col.name] = val
        converted_rows.append(converted)
    
    return converted_rows, schema

def create_table_with_index(table_name: str, index_type: str, index_class, rows, schema):
    """Crear una tabla con un índice específico"""
    print(f"\n{'='*80}")
    print(f"📦 Creando: {table_name} ({index_type})")
    print(f"{'='*80}")
    
    # Crear catalog
    catalog = Catalog()
    
    # Crear tabla en storage
    catalog.storage.create_table(table_name)
    
    # Crear schema para esta tabla
    table_schema = TableSchema(name=table_name, key=schema.key, columns=schema.columns)
    
    # Guardar metadata
    schema_dict = {
        'name': table_schema.name,
        'key': table_schema.key,
        'columns': [{'name': c.name, 'type': c.type} for c in table_schema.columns]
    }
    catalog.storage.set_table_metadata(table_name, schema=schema_dict, index_type=index_type)
    
    # Crear tabla con índice
    table = Table(schema=table_schema, storage=catalog.storage, index_type=index_type)
    catalog.tables[table_name] = table
    
    # Cargar datos
    print(f"📥 Cargando {len(rows)} registros...")
    start = time.time()
    table.load(rows)
    elapsed = time.time() - start
    
    print(f"✓ Cargado en {elapsed:.2f}s ({len(rows)/elapsed:.0f} reg/s)")
    
    # Obtener stats del índice
    idx = list(table.indexes.values())[0] if table.indexes else None
    if idx:
        io_stats = idx.get_io_stats()
        print(f"  💾 I/O: {io_stats['disk_reads']}R / {io_stats['disk_writes']}W")
    
    return table

def main():
    print("="*80)
    print("🚀 CARGANDO 4 TABLAS CON DATASET COMPLETO (9.5K)")
    print("="*80)
    
    # Limpiar storage
    print("\n🧹 Limpiando storage...")
    storage_path = Path("storage")
    if storage_path.exists():
        for file in storage_path.glob("*"):
            if file.name != "catalog.json":  # Mantener catalog para no perder metadata
                file.unlink()
    else:
        storage_path.mkdir(exist_ok=True)
    print("✓ Storage limpiado")
    
    # Cargar datos
    print("\n📂 Cargando CSV...")
    rows, schema = load_csv_data()
    
    # Las 4 tablas a crear
    tables_config = [
        ("restaurants_seq", "sequential", SequentialIndex),
        ("restaurants_isam", "isam", ISAMIndex),
        ("restaurants_hash", "extendiblehash", ExtendibleHashIndex),
        ("restaurants_bplustree", "bplustree", BPlusTreeIndex),
    ]
    
    total_start = time.time()
    
    for table_name, index_type, index_class in tables_config:
        try:
            create_table_with_index(table_name, index_type, index_class, rows, schema)
        except Exception as e:
            print(f"❌ Error creando {table_name}: {e}")
            import traceback
            traceback.print_exc()
    
    total_time = time.time() - total_start
    
    print("\n" + "="*80)
    print(f"✅ 4 TABLAS CREADAS en {total_time:.2f}s")
    print("="*80)
    print("\n📊 Tablas disponibles:")
    print(f"   • restaurants_seq       → Sequential File (~{len(rows)} registros)")
    print(f"   • restaurants_isam      → ISAM 3-level (~{len(rows)} registros)")
    print(f"   • restaurants_hash      → Extendible Hash (~{len(rows)} registros)")
    print(f"   • restaurants_bplustree → B+ Tree (~{len(rows)} registros)")
    print("\n💡 Ahora ejecuta el benchmark:")
    print("   python benchmark_9k.py")

if __name__ == "__main__":
    main()
