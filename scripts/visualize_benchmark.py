"""
Visualización de resultados del benchmark
Genera gráficos comparativos de los 4 índices
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configurar estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10

def load_benchmark_data():
    """Cargar datos del benchmark más reciente"""
    # Buscar el CSV más reciente
    csv_files = list(Path(".").glob("benchmark_9k_results_*.csv"))
    if not csv_files:
        print("❌ No se encontraron archivos de benchmark")
        return None
    
    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Cargando: {latest_csv}")
    
    df = pd.read_csv(latest_csv)
    return df

def create_visualizations(df):
    """Crear gráficos comparativos"""
    
    # Preparar datos
    indices = df['index_type'].tolist()
    
    # Crear figura con 6 subplots
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('🚀 Benchmark Comparativo de Índices - Dataset 9.5K Registros', 
                 fontsize=16, fontweight='bold')
    
    # 1. SELECT = (Tiempo)
    ax1 = axes[0, 0]
    bars1 = ax1.bar(indices, df['select_eq_ms'], color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax1.set_title('⚡ SELECT por Igualdad (ms)', fontweight='bold')
    ax1.set_ylabel('Tiempo (ms)')
    ax1.grid(axis='y', alpha=0.3)
    # Añadir valores en las barras
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    # 2. RANGE 100 (Tiempo)
    ax2 = axes[0, 1]
    bars2 = ax2.bar(indices, df['range_100_ms'], color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax2.set_title('📊 SELECT RANGE (100 reg) - Tiempo (ms)', fontweight='bold')
    ax2.set_ylabel('Tiempo (ms)')
    ax2.grid(axis='y', alpha=0.3)
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    # 3. RANGE 1000 (Tiempo)
    ax3 = axes[0, 2]
    bars3 = ax3.bar(indices, df['range_1000_ms'], color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax3.set_title('📈 SELECT RANGE (1K reg) - Tiempo (ms)', fontweight='bold')
    ax3.set_ylabel('Tiempo (ms)')
    ax3.grid(axis='y', alpha=0.3)
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    # 4. INSERT (Tiempo)
    ax4 = axes[1, 0]
    bars4 = ax4.bar(indices, df['insert_ms'], color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax4.set_title('➕ INSERT - Tiempo (ms)', fontweight='bold')
    ax4.set_ylabel('Tiempo (ms)')
    ax4.grid(axis='y', alpha=0.3)
    for bar in bars4:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    # 5. DELETE (Tiempo) - Escala logarítmica por la gran diferencia
    ax5 = axes[1, 1]
    bars5 = ax5.bar(indices, df['delete_ms'], color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax5.set_title('❌ DELETE - Tiempo (ms)', fontweight='bold')
    ax5.set_ylabel('Tiempo (ms)')
    ax5.set_yscale('log')  # Escala logarítmica
    ax5.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars5, df['delete_ms']):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}',
                ha='center', va='bottom', fontsize=9)
    
    # 6. I/O Reads Promedio
    ax6 = axes[1, 2]
    io_reads = df['select_eq_reads'].tolist()
    bars6 = ax6.bar(indices, io_reads, color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax6.set_title('💾 I/O Reads (SELECT =)', fontweight='bold')
    ax6.set_ylabel('Número de Reads')
    ax6.grid(axis='y', alpha=0.3)
    for bar in bars6:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Guardar
    output_file = "benchmark_visualization.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico guardado: {output_file}")
    
    return output_file

def create_comparison_chart(df):
    """Crear gráfico de comparación general"""
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Preparar datos (normalizar para comparar)
    operations = ['SELECT =', 'RANGE (100)', 'RANGE (1K)', 'INSERT', 'DELETE']
    
    # Extraer tiempos y normalizar (DELETE tiene valores muy grandes)
    data = {
        'Sequential': [
            df.loc[0, 'select_eq_ms'],
            df.loc[0, 'range_100_ms'],
            df.loc[0, 'range_1000_ms'],
            df.loc[0, 'insert_ms'],
            df.loc[0, 'delete_ms'] / 100  # Escalar para visualizar
        ],
        'ISAM': [
            df.loc[1, 'select_eq_ms'],
            df.loc[1, 'range_100_ms'],
            df.loc[1, 'range_1000_ms'],
            df.loc[1, 'insert_ms'],
            df.loc[1, 'delete_ms']
        ],
        'ExtHash': [
            df.loc[2, 'select_eq_ms'],
            df.loc[2, 'range_100_ms'],
            df.loc[2, 'range_1000_ms'],
            df.loc[2, 'insert_ms'],
            df.loc[2, 'delete_ms'] / 100
        ],
        'BPlusTree': [
            df.loc[3, 'select_eq_ms'],
            df.loc[3, 'range_100_ms'],
            df.loc[3, 'range_1000_ms'],
            df.loc[3, 'insert_ms'],
            df.loc[3, 'delete_ms']
        ]
    }
    
    x = range(len(operations))
    width = 0.2
    
    # Crear barras agrupadas
    ax.bar([i - 1.5*width for i in x], data['Sequential'], width, label='Sequential', color='#3498db')
    ax.bar([i - 0.5*width for i in x], data['ISAM'], width, label='ISAM', color='#e74c3c')
    ax.bar([i + 0.5*width for i in x], data['ExtHash'], width, label='ExtHash', color='#f39c12')
    ax.bar([i + 1.5*width for i in x], data['BPlusTree'], width, label='BPlusTree', color='#2ecc71')
    
    ax.set_xlabel('Operaciones', fontweight='bold')
    ax.set_ylabel('Tiempo (ms)', fontweight='bold')
    ax.set_title('⚡ Comparación de Performance por Operación (9.5K registros)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(operations)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Nota sobre DELETE
    ax.text(0.5, 0.95, '* DELETE de Sequential/ExtHash escalado ÷100 para visualización', 
            transform=ax.transAxes, ha='center', fontsize=9, style='italic',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    
    output_file = "benchmark_comparison_chart.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico comparativo guardado: {output_file}")
    
    return output_file

def create_io_comparison(df):
    """Gráfico de comparación de I/O"""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('💾 Comparación de Operaciones I/O', fontsize=14, fontweight='bold')
    
    indices = df['index_type'].tolist()
    
    # I/O Reads (SELECT =)
    ax1 = axes[0]
    bars1 = ax1.bar(indices, df['select_eq_reads'], color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax1.set_title('Lecturas en SELECT = (avg)', fontweight='bold')
    ax1.set_ylabel('Disk Reads')
    ax1.grid(axis='y', alpha=0.3)
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=10)
    
    # I/O Writes (INSERT)
    ax2 = axes[1]
    bars2 = ax2.bar(indices, df['insert_writes'], color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
    ax2.set_title('Escrituras en INSERT', fontweight='bold')
    ax2.set_ylabel('Disk Writes')
    ax2.grid(axis='y', alpha=0.3)
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    output_file = "benchmark_io_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico I/O guardado: {output_file}")
    
    return output_file

def main():
    print("="*80)
    print("📊 GENERANDO VISUALIZACIONES DEL BENCHMARK")
    print("="*80)
    
    # Cargar datos
    df = load_benchmark_data()
    if df is None:
        return
    
    print(f"\n✓ Dataset: {len(df)} índices")
    print(f"✓ Índices: {', '.join(df['index_type'].tolist())}")
    
    # Generar gráficos
    print("\n📈 Generando gráficos...")
    
    file1 = create_visualizations(df)
    file2 = create_comparison_chart(df)
    file3 = create_io_comparison(df)
    
    print("\n" + "="*80)
    print("✅ VISUALIZACIONES CREADAS")
    print("="*80)
    print(f"\n📁 Archivos generados:")
    print(f"   • {file1}")
    print(f"   • {file2}")
    print(f"   • {file3}")
    print("\n💡 Ahora puedes:")
    print("   1. Revisar los gráficos generados")
    print("   2. Actualizar el README.md con estos resultados")
    print("   3. Incluir las imágenes en tu presentación")

if __name__ == '__main__':
    main()
