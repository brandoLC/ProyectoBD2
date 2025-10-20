import streamlit as st
import requests
import pandas as pd
import time
import json
import os
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Use environment variable for API URL (defaults to localhost for local dev)
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="BD2 Database Manager",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def execute_query(sql: str):
    """Ejecuta query en el API"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"sql": sql},
            timeout=30
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "No se puede conectar al API. ¿Está corriendo en puerto 8000?"}
    except Exception as e:
        return {"error": str(e)}

def get_health():
    """Obtiene estado del sistema"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except:
        return None

# ============================================================================
# ESTILOS CSS
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.2);
    }
    
    .main-header h1 {
        color: white;
        font-weight: 700;
        margin: 0;
        font-size: 2.8rem;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.95);
        margin: 0.8rem 0 0 0;
        font-size: 1.15rem;
        font-weight: 400;
    }
    
    .metric-card {
        background: white;
        padding: 1.8rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-sublabel {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.3rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f9fafb;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 14px 28px;
        background-color: white;
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid #e5e7eb;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
    }
    
    .stButton button {
        border-radius: 10px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        padding: 1rem;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
    }
    
    .sidebar-table-btn {
        background: white;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        margin: 0.3rem 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .sidebar-table-btn:hover {
        background: #f9fafb;
        border-color: #667eea;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #10b981;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 4px solid #3b82f6;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="main-header">
    <h1>🗄️ BD2 Database Manager</h1>
    <p>Sistema de gestión con I/O real a disco • ISAM • Sequential • Extendible Hash</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 🏠 Sistema")
    
    # Health check
    health = get_health()
    if health:
        st.success(f"✅ Conectado")
        if "tables" in health:
            tables = health["tables"]
            st.info(f"📊 {len(tables)} tabla(s) disponible(s)")
    else:
        st.error("❌ API no disponible")
        tables = []
    
    st.markdown("---")
    
    # Tablas disponibles
    st.markdown("### 📋 Tablas")
    
    if tables:
        for table in tables:
            if st.button(f"📊 {table}", key=f"table_{table}", use_container_width=True):
                st.session_state['selected_table'] = table
                st.session_state['sql_query'] = f'SELECT * FROM {table} WHERE "Restaurant ID" BETWEEN 6300002 AND 6300010'
    else:
        st.caption("No hay tablas disponibles")
    
    st.markdown("---")
    
    # Dataset loader
    st.markdown("### 📂 Cargar Dataset")
    
    table_name = st.text_input(
        "Nombre de la tabla",
        value="restaurants",
        key="table_name_input",
        help="Nombre único para la tabla (ej: restaurants, clientes, productos)"
    )
    
    dataset = st.selectbox(
        "Dataset",
        ["kaggle_Dataset _100.csv", "kaggle_Dataset _1k.csv", "kaggle_Dataset .csv"],
        key="dataset_select"
    )
    
    index_type = st.selectbox(
        "Tipo de índice",
        ["ISAM", "Sequential", "Extendible Hash", "B+ Tree"],
        key="index_select"
    )
    
    if st.button("🚀 Cargar Dataset", use_container_width=True, type="primary"):
        with st.spinner("Preparando..."):
            # Paso 1: Limpiar storage (reiniciar limpio)
            st.info("🧹 Limpiando datos anteriores...")
            
            # Verificar que el API esté disponible
            health = get_health()
            if not health:
                st.error("❌ API no disponible. Asegúrate de que esté corriendo en el puerto 8000")
                st.stop()
            
            # Mostrar info del dataset
            dataset_info = {
                "kaggle_Dataset _100.csv": "100 registros • ~1 segundo",
                "kaggle_Dataset _1k.csv": "1,000 registros • ~3 segundos",
                "kaggle_Dataset .csv": "9,551 registros • ~20 segundos"
            }
            
            info_text = dataset_info.get(dataset, "Cargando...")
            st.info(f"📂 Cargando: {dataset}\n⏱️ Tiempo estimado: {info_text}")
            
        with st.spinner(f"Cargando {dataset}..."):
            # Paso 2: Crear tabla con índice especificado
            # Mapear nombres de UI a nombres de índices
            index_map = {
                "ISAM": "isam",
                "Sequential": "sequential",
                "Extendible Hash": "ext_hash",
                "B+ Tree": "bplustree"
            }
            idx_type = index_map.get(index_type, index_type.split()[0].lower())
            create_sql = f"CREATE TABLE {table_name} USING {idx_type}"
            
            result = execute_query(create_sql)
            
            # Si la tabla ya existe, no es error (la reemplazamos)
            if "error" in result and "already exists" not in result.get("error", "").lower():
                st.error(f"❌ Error al crear tabla: {result['error']}")
                st.stop()
            
            # Paso 3: Cargar CSV
            load_sql = f"LOAD FROM data/{dataset} INTO {table_name}"
            result = execute_query(load_sql)
            
            if "error" in result:
                st.error(f"❌ Error al cargar datos: {result['error']}")
            else:
                loaded = result.get('loaded', 0)
                st.success(f"""
                    ✅ **Dataset cargado exitosamente**
                    
                    - Registros: **{loaded:,}**
                    - Índice: **{index_type}**
                    - Archivo: {dataset}
                """)
                time.sleep(2)
                st.rerun()
    
    st.markdown("---")
    st.caption("💡 Tip: Los datasets grandes pueden tardar ~20 segundos")
    
    st.markdown("---")
    
    # Opciones avanzadas
    with st.expander("⚙️ Opciones Avanzadas"):
        st.markdown("##### Gestión del Sistema")
        
        if st.button("🗑️ Limpiar Todo", use_container_width=True, help="Elimina todas las tablas y reinicia el sistema"):
            # Esto requeriría un endpoint en el API o reiniciar manualmente
            st.warning("⚠️ Para limpiar completamente:")
            st.code("Remove-Item storage/* -Force", language="powershell")
            st.caption("Luego recarga la página")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("##### Información")
        st.caption("📊 Storage: `./storage/`")
        st.caption("🔧 API: `localhost:8000`")
        st.caption("🎨 UI: `localhost:8501`")

# ============================================================================
# MAIN CONTENT - TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Query Editor", "📊 Métricas", "🏗️ Estructura", "📖 Ayuda"])

# ============================================================================
# TAB 1: QUERY EDITOR
# ============================================================================

with tab1:
    st.markdown("### Editor SQL")
    
    # Query templates
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🔍 Buscar ID", use_container_width=True):
            st.session_state['sql_query'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" = 6300002'
    with col2:
        if st.button("📊 Rango", use_container_width=True):
            st.session_state['sql_query'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" BETWEEN 6300000 AND 6300010'
    with col3:
        if st.button("📋 Primeros 20", use_container_width=True):
            st.session_state['sql_query'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" BETWEEN 53 AND 300'
    with col4:
        if st.button("➕ Insertar", use_container_width=True):
            st.session_state['sql_query'] = 'INSERT INTO restaurants ("Restaurant ID", "Restaurant Name", "City", "Cuisines", "Average Cost for two", "Aggregate rating") VALUES (99999999, \'Nuevo Restaurant\', \'Lima\', \'Peruvian\', 50, 4.5)'
    with col5:
        if st.button("❌ Eliminar", use_container_width=True):
            st.session_state['sql_query'] = 'DELETE FROM restaurants WHERE "Restaurant ID" = 99999999'
    with col6:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state['sql_query'] = ''
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # SQL Editor
    default_query = st.session_state.get('sql_query', '')
    sql = st.text_area(
        "Consulta SQL",
        value=default_query,
        height=150,
        placeholder='SELECT * FROM restaurants WHERE "Restaurant ID" = 6300002',
        label_visibility="collapsed"
    )
    
    col_exec, col_clear = st.columns([1, 5])
    with col_exec:
        execute_btn = st.button("▶️ Ejecutar Query", type="primary", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Ejecutar query
    if execute_btn and sql.strip():
        with st.spinner("Ejecutando query..."):
            start_time = time.time()
            result = execute_query(sql)
            total_ui_time = (time.time() - start_time) * 1000  # ms (incluye network + rendering)
        
        if "error" in result:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Error</strong><br>
                {result['error']}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Mostrar resultados
            if "rows" in result:
                rows = result['rows']
                count = result.get('count', len(rows))
                io_stats = result.get('io', {})
                
                # Obtener tiempo real del API (si está disponible)
                query_time = result.get('execution_time_ms', 0)
                
                # Métricas de la query (solo 4 columnas)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Registros</div>
                        <div class="metric-value">{count}</div>
                        <div class="metric-sublabel">encontrados</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">⚡ Tiempo</div>
                        <div class="metric-value">{query_time:.2f}ms</div>
                        <div class="metric-sublabel">ejecución query</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    io_reads = io_stats.get('disk_reads', 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📖 Lecturas</div>
                        <div class="metric-value">{io_reads}</div>
                        <div class="metric-sublabel">I/O disco</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    io_writes = io_stats.get('disk_writes', 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">✍️ Escrituras</div>
                        <div class="metric-value">{io_writes}</div>
                        <div class="metric-sublabel">I/O disco</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Mostrar datos
                if count > 0:
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Opción de descarga
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"query_result_{int(time.time())}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("ℹ️ La query se ejecutó correctamente pero no retornó resultados")
            
            elif "ok" in result:
                # Operaciones de INSERT/UPDATE/DELETE - Mostrar métricas organizadas
                st.success("✅ Operación exitosa")
                
                inserted = result.get('inserted', 0)
                updated = result.get('updated', 0)
                deleted = result.get('deleted', 0)
                io_stats = result.get('io', {})
                exec_time = result.get('execution_time_ms', 0)
                
                # Métricas (4 columnas)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if inserted > 0:
                        label = "Insertados"
                        value = inserted
                    elif updated > 0:
                        label = "Actualizados"
                        value = updated
                    elif deleted > 0:
                        label = "Eliminados"
                        value = deleted
                    else:
                        label = "Registros"
                        value = 0
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}</div>
                        <div class="metric-sublabel">afectados</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">⚡ Tiempo</div>
                        <div class="metric-value">{exec_time:.2f}ms</div>
                        <div class="metric-sublabel">ejecución</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    io_reads = io_stats.get('disk_reads', 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📖 Lecturas</div>
                        <div class="metric-value">{io_reads}</div>
                        <div class="metric-sublabel">I/O disco</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    io_writes = io_stats.get('disk_writes', 0)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">✍️ Escrituras</div>
                        <div class="metric-value">{io_writes}</div>
                        <div class="metric-sublabel">I/O disco</div>
                    </div>
                    """, unsafe_allow_html=True)

# ============================================================================
# TAB 2: MÉTRICAS
# ============================================================================

with tab2:
    st.markdown("### 📊 Métricas del Sistema")
    
    if health and tables:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Tablas Activas</div>
                <div class="metric-value">{}</div>
                <div class="metric-sublabel">en el sistema</div>
            </div>
            """.format(len(tables)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Estado API</div>
                <div class="metric-value">✅</div>
                <div class="metric-sublabel">operativo</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Índices</div>
                <div class="metric-value">ISAM</div>
                <div class="metric-sublabel">3 niveles</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Gráfico de I/O (placeholder)
        st.markdown("#### 📈 Performance I/O")
        st.info("🚧 Próximamente: Gráficos de performance comparando diferentes índices")
    
    else:
        st.warning("⚠️ No hay datos disponibles. Carga un dataset primero.")

# ============================================================================
# TAB 3: ESTRUCTURA
# ============================================================================

with tab3:
    st.markdown("### 🏗️ Estructura del Índice")
    
    if tables:
        st.markdown("""
        <div class="info-box">
            <strong>📚 Índice ISAM de 3 Niveles</strong><br>
            El sistema utiliza un índice ISAM (Indexed Sequential Access Method) con arquitectura multinivel
            para búsquedas optimizadas.
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🔼 Nivel 1: L2 (Superior)**
            - Índice sobre grupos de buckets
            - Permite saltos grandes
            - Búsqueda binaria rápida
            """)
        
        with col2:
            st.markdown("""
            **🔽 Nivel 2: L1 (Buckets)**
            - Índice de buckets individuales
            - Primera clave de cada bucket
            - Navegación precisa
            """)
        
        with col3:
            st.markdown("""
            **📦 Nivel 3: Datos**
            - Buckets con registros
            - Overflow para inserciones
            - Factor de bloque: 20
            """)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Ejemplo visual
        st.code("""
🔍 Ejemplo de búsqueda: ID = 6300002

Paso 1: Búsqueda en L2 → log₂(96) ≈ 7 comparaciones
Paso 2: Búsqueda en L1 → log₂(5) ≈ 3 comparaciones  
Paso 3: Búsqueda en Bucket → log₂(20) ≈ 5 comparaciones

Total: ~15 comparaciones vs 9,551 si fuera secuencial
Mejora: 636x más rápido 🚀
        """, language="text")
    
    else:
        st.warning("⚠️ Carga un dataset para ver la estructura del índice")

# ============================================================================
# TAB 4: AYUDA
# ============================================================================

with tab4:
    st.markdown("### 📖 Guía de Uso")
    
    st.markdown("""
    #### 🚀 Inicio Rápido
    
    1. **Cargar Dataset**: 
       - En el panel izquierdo, selecciona un dataset
       - Elige el tipo de índice (ISAM recomendado)
       - Haz clic en "🚀 Cargar Dataset"
       - **Nota**: Si ya existe una tabla, se reemplazará automáticamente
    
    2. **Ejecutar Queries**: 
       - Usa el editor SQL en la pestaña "Query Editor"
       - O haz clic en los botones de ejemplo rápido
    
    3. **Ver Resultados**: 
       - Los resultados aparecen con métricas de performance (I/O, tiempo)
    
    #### 🔄 Cargar Otro Dataset
    
    **Opción 1: Reemplazar automáticamente**
    - Simplemente selecciona otro dataset y haz clic en "Cargar Dataset"
    - El sistema reemplazará la tabla anterior
    
    **Opción 2: Limpiar manualmente**
    ```powershell
    # En terminal PowerShell
    Remove-Item storage/* -Force
    ```
    Luego recarga la página en el navegador (F5)
    
    #### 📝 Sintaxis SQL Soportada
    
    ```sql
    -- Búsqueda por igualdad
    SELECT * FROM restaurants WHERE "Restaurant ID" = 6300002
    
    -- Búsqueda por rango
    SELECT * FROM restaurants WHERE "Restaurant ID" BETWEEN 6300000 AND 6300010
    
    -- Crear tabla con índice
    CREATE TABLE restaurants USING isam
    
    -- Cargar datos
    LOAD restaurants FROM 'data/kaggle_Dataset _100.csv'
    ```
    
    #### 🔧 Tipos de Índices
    
    - **ISAM**: Índice estático multinivel (3 niveles), óptimo para búsquedas y rangos
    - **Sequential**: Índice secuencial ordenado con búsqueda binaria, eficiente para rangos
    - **Extendible Hash**: Hash extensible con directorio dinámico, búsquedas O(1) por igualdad
    - **B+ Tree**: Árbol balanceado con hojas en disco, excelente para búsquedas y rangos
    
    #### 📊 Métricas I/O
    
    - **I/O Reads**: Número de lecturas de disco (menor = mejor)
    - **I/O Writes**: Número de escrituras de disco
    - **0 lecturas** = Los datos están en el índice (óptimo)
    
    #### 💡 Tips
    
    - Los datasets grandes (9K registros) tardan ~20 segundos en cargar
    - ISAM es óptimo para lecturas, no para inserciones frecuentes
    - Las búsquedas usan el índice automáticamente
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 1rem;'>
    <strong>BD2 Database Manager</strong> • Proyecto Base de Datos 2 • 2025
</div>
""", unsafe_allow_html=True)
