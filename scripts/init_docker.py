#!/usr/bin/env python3
"""
Script de inicialización para Docker
Verifica que el entorno esté listo, pero NO carga datos automáticamente.
El usuario debe cargar las tablas manualmente desde la UI.
"""
import os
from pathlib import Path

def main():
    print("\n" + "="*80)
    print("🐳 DOCKER INITIALIZATION SCRIPT")
    print("="*80)
    
    # Verificar que existe el directorio storage/
    storage_path = Path("storage")
    if not storage_path.exists():
        print("� Creando directorio storage/...")
        storage_path.mkdir(exist_ok=True)
    
    # Verificar que existe el CSV
    csv_path = Path("data/kaggle_Dataset .csv")
    if csv_path.exists():
        print(f"✅ Dataset encontrado: {csv_path}")
        print(f"   📊 {csv_path.stat().st_size / (1024*1024):.1f} MB")
    else:
        print(f"⚠️  Advertencia: Dataset no encontrado en {csv_path}")
    
    print("\n" + "="*80)
    print("✅ ENTORNO LISTO")
    print("="*80)
    print("\n💡 INSTRUCCIONES:")
    print("   1. Abre la UI en http://localhost:8501")
    print("   2. Ve a la sección 'Gestión de Tablas'")
    print("   3. Crea las tablas con diferentes índices:")
    print("      • Sequential")
    print("      • ISAM")
    print("      • Extendible Hash")
    print("      • B+ Tree")
    print("   4. Carga los datos del CSV en cada tabla")
    print("\n")

if __name__ == "__main__":
    main()
