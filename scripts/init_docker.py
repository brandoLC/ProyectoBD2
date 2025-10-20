#!/usr/bin/env python3
"""
Script de inicialización para Docker
Verifica si storage/ tiene datos, si no los carga automáticamente
"""
import os
import sys
from pathlib import Path
import json

def check_storage_initialized():
    """Verifica si storage/ tiene datos cargados"""
    storage_path = Path("storage")
    catalog_path = storage_path / "catalog.json"
    
    # Si no existe storage/, crear
    if not storage_path.exists():
        print("📁 Creando directorio storage/...")
        storage_path.mkdir(exist_ok=True)
        return False
    
    # Si no existe catalog.json, no hay datos
    if not catalog_path.exists():
        print("📋 catalog.json no encontrado")
        return False
    
    # Leer catalog y verificar que hay tablas
    try:
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
        
        if not catalog or len(catalog) == 0:
            print("📋 catalog.json vacío")
            return False
        
        # Verificar que existen las 4 tablas esperadas
        expected_tables = [
            "restaurants_seq",
            "restaurants_isam", 
            "restaurants_hash",
            "restaurants_bplustree"
        ]
        
        existing_tables = list(catalog.keys())
        missing_tables = [t for t in expected_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"⚠️  Faltan tablas: {', '.join(missing_tables)}")
            return False
        
        # Verificar que existen archivos de datos
        data_files = list(storage_path.glob("*.dat"))
        if len(data_files) < 4:  # Al menos 4 archivos .dat (uno por tabla)
            print(f"⚠️  Solo {len(data_files)} archivos .dat encontrados (esperados: 4+)")
            return False
        
        print("✅ Storage inicializado correctamente")
        print(f"   📊 Tablas encontradas: {len(existing_tables)}")
        print(f"   📁 Archivos de datos: {len(data_files)}")
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo catalog.json: {e}")
        return False

def initialize_data():
    """Ejecuta el script de carga de datos"""
    print("\n" + "="*80)
    print("🚀 INICIALIZANDO BASE DE DATOS")
    print("="*80)
    print("\n⏳ Este proceso tomará aproximadamente 2-3 minutos...")
    print("   Cargando 9,551 registros en 4 tablas con índices...\n")
    
    # Ejecutar load_all_9k.py
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/load_all_9k.py"],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print("\n❌ Error al cargar los datos")
        sys.exit(1)
    
    print("\n✅ Datos cargados exitosamente")
    return True

def main():
    print("\n" + "="*80)
    print("🐳 DOCKER INITIALIZATION SCRIPT")
    print("="*80)
    
    # Verificar si storage está inicializado
    if check_storage_initialized():
        print("\n✅ Base de datos ya inicializada, saltando carga de datos...")
    else:
        print("\n⚠️  Base de datos no inicializada, cargando datos...")
        if not initialize_data():
            print("\n❌ Falló la inicialización")
            sys.exit(1)
    
    print("\n" + "="*80)
    print("✅ INICIALIZACIÓN COMPLETA")
    print("="*80)
    print("\n🎉 Sistema listo para usar!")
    print("   📊 4 tablas con 9,551 registros cada una")
    print("   🔍 Índices: Sequential, ISAM, Extendible Hash, B+ Tree")
    print("\n")

if __name__ == "__main__":
    main()
