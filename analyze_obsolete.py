"""
Script para analizar archivos obsoletos en el proyecto
"""

import os
from pathlib import Path
from datetime import datetime

def get_file_info(file_path):
    """Obtener información de un archivo"""
    stat = file_path.stat()
    return {
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'size_mb': stat.st_size / (1024 * 1024)
    }

def analyze_project():
    """Analizar proyecto y clasificar archivos"""
    
    root = Path(".")
    
    # Archivos ESENCIALES (mantener)
    essential = {
        # Core del sistema
        'core/': 'Motor de almacenamiento y gestión de I/O',
        'indexes/': 'Implementación de los 4 índices',
        'sql/': 'Parser y executor SQL',
        'api/': 'Backend FastAPI',
        'ui/': 'Frontend Streamlit',
        
        # Configuración
        'requirements.txt': 'Dependencias Python',
        'docker-compose.yml': 'Configuración Docker',
        'Dockerfile.api': 'Docker para API',
        'Dockerfile.ui': 'Docker para UI',
        'Makefile': 'Comandos útiles',
        
        # Documentación principal
        'README.md': 'Documentación principal',
        'INFORME.md': 'Informe del proyecto (CRÍTICO)',
        
        # Scripts principales
        'load_all_9k.py': 'Carga dataset de 9K registros',
        'benchmark_9k.py': 'Benchmark principal con 9K',
        'visualize_benchmark.py': 'Generación de gráficos',
        'clean_storage.py': 'Limpieza de storage',
        
        # Resultados del benchmark
        'benchmark_9k_results_1760929545.csv': 'Resultados FINALES del benchmark',
        'benchmark_visualization.png': 'Gráfico principal',
        'benchmark_comparison_chart.png': 'Gráfico comparativo',
        'benchmark_io_comparison.png': 'Gráfico de I/O',
        
        # Dataset principal
        'data/kaggle_Dataset .csv': 'Dataset completo (9.5K)',
        
        # Storage
        'storage/': 'Archivos de datos e índices persistentes',
    }
    
    # Archivos OBSOLETOS (pueden eliminarse)
    obsolete = {
        # Documentación redundante
        'bd_2_proyecto_skeleton_python_fast_api_streamlit.md': 'Skeleton inicial del proyecto (ya no se usa)',
        'GUIA_USO.md': 'Guía redundante (info ya está en README)',
        'QUERIES_KAGGLE.md': 'Ejemplos de queries (redundante)',
        'TESTING_GUIDE.md': 'Guía de testing (redundante)',
        
        # Scripts de inicialización obsoletos
        'init_db.py': 'Script antiguo de inicialización (reemplazado por load_all_9k.py)',
        'init_kaggle_db.py': 'Inicialización antigua (obsoleto)',
        'init_full_dataset.py': 'Script antiguo (reemplazado)',
        'setup_project.py': 'Setup inicial (ya no necesario)',
        
        # Benchmarks antiguos
        'benchmark_comparison.py': 'Benchmark con 100 registros (obsoleto, usar benchmark_9k.py)',
        'experiments/benchmark.py': 'Benchmark experimental (obsoleto)',
        'experiments/quick_compare.py': 'Comparación rápida (obsoleto)',
        
        # Resultados antiguos de benchmarks
        'benchmark_results_1760926265.csv': 'Resultados antiguos (100 reg)',
        'benchmark_results_1760926406.csv': 'Resultados antiguos (100 reg)',
        'benchmark_results_1760928151.csv': 'Resultados antiguos (100 reg)',
        'benchmark_9k_results_1760928291.csv': 'Resultados antiguos de 9K',
        
        # Datasets redundantes
        'data/kaggle_Dataset _100.csv': 'Dataset pequeño (redundante)',
        'data/kaggle_Dataset _1k.csv': 'Dataset mediano (redundante)',
        'data/restaurantes_100.csv': 'Dataset alternativo (no usado)',
        'data/restaurantes_1k.csv': 'Dataset alternativo (no usado)',
        'data/restaurantes_10k.csv': 'Dataset alternativo (no usado)',
        'data/sample_restaurantes.csv': 'Sample (no usado)',
        
        # Scripts de generación de datos
        'data/download_kaggle_data.py': 'Script de descarga (ya descargado)',
        'data/generate_data.py': 'Generador de datos sintéticos (no usado)',
        
        # Tests de depuración
        'test_delete_real_io.py': 'Test de debugging (ya validado)',
        'test_delete_sql.py': 'Test de debugging (ya validado)',
        'test_hash_debug.py': 'Test de debugging específico (ya validado)',
        
        # Postman collections
        'BD2_Postman_Collection_v2.json': 'Postman v2 (redundante)',
        'BD2_Proyecto_Postman_Collection.json': 'Postman alternativo (redundante)',
        
        # Storage de pruebas
        'storage_test/': 'Storage de pruebas (no usado)',
    }
    
    print("="*80)
    print("📊 ANÁLISIS DE ARCHIVOS DEL PROYECTO")
    print("="*80)
    
    # Calcular tamaños
    total_size = 0
    obsolete_size = 0
    
    for file_pattern, reason in obsolete.items():
        file_path = root / file_pattern
        if file_path.exists():
            if file_path.is_file():
                info = get_file_info(file_path)
                obsolete_size += info['size']
                total_size += info['size']
            elif file_path.is_dir():
                for f in file_path.rglob('*'):
                    if f.is_file():
                        info = get_file_info(f)
                        obsolete_size += info['size']
                        total_size += info['size']
    
    print(f"\n📦 Archivos ESENCIALES: {len(essential)} archivos/carpetas")
    print(f"🗑️  Archivos OBSOLETOS: {len(obsolete)} archivos/carpetas")
    print(f"💾 Espacio ocupado por obsoletos: {obsolete_size / (1024*1024):.2f} MB")
    
    # Listar archivos obsoletos
    print("\n" + "="*80)
    print("🗑️  ARCHIVOS OBSOLETOS QUE PUEDEN ELIMINARSE")
    print("="*80)
    
    for file_pattern, reason in sorted(obsolete.items()):
        file_path = root / file_pattern
        if file_path.exists():
            if file_path.is_file():
                info = get_file_info(file_path)
                print(f"\n📄 {file_pattern}")
                print(f"   Razón: {reason}")
                print(f"   Tamaño: {info['size_mb']:.2f} MB")
                print(f"   Última modificación: {info['modified'].strftime('%Y-%m-%d %H:%M')}")
            elif file_path.is_dir():
                file_count = len(list(file_path.rglob('*')))
                print(f"\n📁 {file_pattern}")
                print(f"   Razón: {reason}")
                print(f"   Archivos dentro: {file_count}")
    
    # Listar archivos esenciales
    print("\n" + "="*80)
    print("✅ ARCHIVOS ESENCIALES (MANTENER)")
    print("="*80)
    
    for file_pattern, description in sorted(essential.items()):
        print(f"\n✓ {file_pattern}")
        print(f"  {description}")
    
    # Resumen
    print("\n" + "="*80)
    print("📋 RESUMEN Y RECOMENDACIONES")
    print("="*80)
    
    print(f"""
✅ MANTENER ({len(essential)} items):
   - Core del sistema (core/, indexes/, sql/, api/, ui/)
   - Documentación crítica (README.md, INFORME.md)
   - Scripts principales (load_all_9k.py, benchmark_9k.py, visualize_benchmark.py)
   - Resultados finales del benchmark (CSV + 3 PNG)
   - Dataset principal (kaggle_Dataset .csv - 9.5K registros)
   - Configuración (requirements.txt, docker-compose.yml, Makefile)

🗑️  ELIMINAR ({len(obsolete)} items):
   - Documentación redundante (4 archivos .md)
   - Scripts obsoletos de inicialización (4 archivos)
   - Benchmarks antiguos (3 scripts + 4 CSVs viejos)
   - Datasets redundantes (7 archivos CSV)
   - Tests de debugging (3 archivos)
   - Postman collections (2 archivos)
   - storage_test/ (carpeta de pruebas)

💾 Espacio a liberar: ~{obsolete_size / (1024*1024):.2f} MB

🚀 Beneficios de limpiar:
   1. Proyecto más organizado y profesional
   2. Más fácil de navegar y entender
   3. Menos confusión sobre qué archivos usar
   4. Repositorio Git más limpio
   5. Documentación más clara
    """)
    
    print("\n" + "="*80)
    print("💡 COMANDOS PARA ELIMINAR (REVISAR ANTES DE EJECUTAR)")
    print("="*80)
    print("""
# Documentación redundante
Remove-Item "bd_2_proyecto_skeleton_python_fast_api_streamlit.md"
Remove-Item "GUIA_USO.md"
Remove-Item "QUERIES_KAGGLE.md"
Remove-Item "TESTING_GUIDE.md"

# Scripts obsoletos
Remove-Item "init_db.py"
Remove-Item "init_kaggle_db.py"
Remove-Item "init_full_dataset.py"
Remove-Item "setup_project.py"

# Benchmarks antiguos
Remove-Item "benchmark_comparison.py"
Remove-Item "experiments/" -Recurse
Remove-Item "benchmark_results_1760926265.csv"
Remove-Item "benchmark_results_1760926406.csv"
Remove-Item "benchmark_results_1760928151.csv"
Remove-Item "benchmark_9k_results_1760928291.csv"

# Datasets redundantes
Remove-Item "data/kaggle_Dataset _100.csv"
Remove-Item "data/kaggle_Dataset _1k.csv"
Remove-Item "data/restaurantes_*.csv"
Remove-Item "data/sample_restaurantes.csv"
Remove-Item "data/download_kaggle_data.py"
Remove-Item "data/generate_data.py"

# Tests de debugging
Remove-Item "test_delete_real_io.py"
Remove-Item "test_delete_sql.py"
Remove-Item "test_hash_debug.py"

# Postman
Remove-Item "BD2_Postman_Collection_v2.json"
Remove-Item "BD2_Proyecto_Postman_Collection.json"

# Storage de pruebas
Remove-Item "storage_test/" -Recurse
    """)

if __name__ == "__main__":
    analyze_project()
