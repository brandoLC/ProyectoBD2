"""
Script para limpiar completamente el storage
Elimina todas las tablas, índices y archivos de datos
"""

import os
import json
import shutil

def clean_storage():
    storage_dir = 'storage'
    
    print("🧹 Limpiando storage completo...")
    
    # 1. Limpiar catalog.json (dejar solo estructura vacía)
    catalog_path = os.path.join(storage_dir, 'catalog.json')
    if os.path.exists(catalog_path):
        with open(catalog_path, 'w') as f:
            json.dump({}, f, indent=2)
        print("   ✓ Catalog.json limpiado")
    
    # 2. Eliminar todos los archivos .dat
    deleted_dat = 0
    for file in os.listdir(storage_dir):
        if file.endswith('.dat'):
            os.remove(os.path.join(storage_dir, file))
            deleted_dat += 1
    print(f"   ✓ {deleted_dat} archivos .dat eliminados")
    
    # 3. Eliminar todos los archivos .idx
    deleted_idx = 0
    for file in os.listdir(storage_dir):
        if file.endswith('.idx'):
            os.remove(os.path.join(storage_dir, file))
            deleted_idx += 1
    print(f"   ✓ {deleted_idx} archivos .idx eliminados")
    
    # 4. Eliminar archivos de índices sin extensión
    deleted_other = 0
    for file in os.listdir(storage_dir):
        if file not in ['catalog.json', '.gitkeep']:
            try:
                file_path = os.path.join(storage_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_other += 1
            except:
                pass
    print(f"   ✓ {deleted_other} otros archivos eliminados")
    
    print("\n✅ Storage limpiado completamente")
    print("💡 Reinicia el API para aplicar cambios:")
    print("   Ctrl+C en la terminal del API y vuelve a ejecutar:")
    print("   .venv\\Scripts\\python -m uvicorn api.main:app --reload")

if __name__ == '__main__':
    clean_storage()
