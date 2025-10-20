import streamlit as st
import requests
import pandas as pd
import time
import json
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

API_URL = "http://localhost:8000"

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
# ESTILOS CSS - TEMA CLARO PROFESIONAL
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Fondo general */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Header limpio */
    .header-container {
        background: white;
        padding: 2rem 2.5rem;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .header-container h1 {
        color: #1a1a1a;
        font-weight: 700;
        margin: 0;
        font-size: 1.8rem;
    }
    
    .header-container p {
        color: #666;
        margin: 0.5rem 0 0 0;
        font-size: 0.95rem;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #666;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a1a;
        margin: 0.3rem 0;
    }
    
    .metric-sublabel {
        font-size: 0.75rem;
        color: #999;
        margin-top: 0.3rem;
    }
    
    /* Botones limpios */
    .stButton button {
        border-radius: 6px;
        padding: 0.6rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
        border: 1px solid #e0e0e0;
        background: white;
        color: #1a1a1a;
    }
    
    .stButton button[kind="primary"] {
        background: #1a1a1a;
        color: white;
        border: none;
    }
    
    .stButton button:hover {
        background: #f0f0f0;
        border-color: #ccc;
    }
    
    .stButton button[kind="primary"]:hover {
        background: #333;
    }
    
    /* Área de texto */
    .stTextArea textarea {
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 13px;
        padding: 1rem;
        background: white;
    }
    
    .stTextArea textarea:focus {
        border-color: #1a1a1a;
        box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.1);
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        background: white;
    }
    
    /* Sidebar limpio */
    section[data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Mensajes */
    .success-box {
        background: #f0fdf4;
        border-left: 3px solid #22c55e;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        color: #166534;
    }
    
    .error-box {
        background: #fef2f2;
        border-left: 3px solid #ef4444;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        color: #991b1b;
    }
    
    .info-box {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        color: #1e40af;
    }
    
    /* DataFrame */
    div[data-testid="stDataFrame"] {
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        background: white;
    }
    
    /* Query templates */
    .query-template {
        background: #f8f9fa;
        padding: 0.7rem 1rem;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        margin: 0.3rem 0;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s;
    }
    
    .query-template:hover {
        background: white;
        border-color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="header-container">
    <h1>🗄️ BD2 Database Manager</h1>
    <p>Sistema de gestión de base de datos con índices avanzados</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 📊 Sistema")
    
    # Health check
    health = get_health()
    if health:
        st.success("Conectado al API")
        if "tables" in health:
            tables = health["tables"]
            st.info(f"{len(tables)} tabla(s) disponible(s)")
    else:
        st.error("API no disponible")
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
        st.caption("No hay tablas")
    
    st.markdown("---")
    
    # Dataset loader
    st.markdown("### 📂 Cargar Dataset")
    
    dataset = st.selectbox(
        "Dataset",
        ["kaggle_Dataset _100.csv", "kaggle_Dataset _1k.csv", "kaggle_Dataset .csv"],
        key="dataset_select"
    )
    
    index_type = st.selectbox(
        "Índice",
        ["ISAM", "Sequential", "B+Tree", "Extendible Hash"],
        key="index_select"
    )
    
    if st.button("Cargar", use_container_width=True, type="primary"):
        with st.spinner("Cargando..."):
            # Limpiar storage
            try:
                requests.delete(f"{API_URL}/storage")
            except:
                pass
            
            # Crear tabla
            create_sql = f"""
            CREATE TABLE restaurants (
                "Restaurant ID" INT,
                "Restaurant Name" TEXT,
                "Country Code" INT,
                "City" TEXT,
                "Address" TEXT,
                "Locality" TEXT,
                "Locality Verbose" TEXT,
                "Longitude" FLOAT,
                "Latitude" FLOAT,
                "Cuisines" TEXT,
                "Average Cost for two" INT,
                "Currency" TEXT,
                "Has Table booking" TEXT,
                "Has Online delivery" TEXT,
                "Is delivering now" TEXT,
                "Switch to order menu" TEXT,
                "Price range" INT,
                "Aggregate rating" FLOAT,
                "Rating color" TEXT,
                "Rating text" TEXT,
                "Votes" INT
            )
            INDEX {index_type} ON "Restaurant ID"
            """
            
            result = execute_query(create_sql)
            
            if "error" not in result:
                # Cargar datos
                load_sql = f'LOAD "data/{dataset}"'
                result = execute_query(load_sql)
                
                if "error" not in result:
                    st.success(f"✓ Dataset cargado con índice {index_type}")
                    st.rerun()
                else:
                    st.error(f"Error: {result['error']}")
            else:
                st.error(f"Error: {result['error']}")
    
    st.markdown("---")
    
    # Limpiar datos
    with st.expander("🗑️ Limpiar datos"):
        st.caption("Elimina todos los archivos de storage")
        if st.button("Confirmar limpieza", use_container_width=True):
            try:
                requests.delete(f"{API_URL}/storage")
                st.success("Storage limpiado")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Query templates (botones rápidos)
st.markdown("### 🔍 Consultas Rápidas")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔎 Buscar por ID", use_container_width=True):
        st.session_state['sql_query'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" = 6317637'

with col2:
    if st.button("📊 Primeros 10", use_container_width=True):
        st.session_state['sql_query'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" BETWEEN 53 AND 300'

with col3:
    if st.button("🌍 Por ciudad", use_container_width=True):
        st.session_state['sql_query'] = 'SELECT * FROM restaurants WHERE "City" = \'New Delhi\''

with col4:
    if st.button("⭐ Por rating", use_container_width=True):
        st.session_state['sql_query'] = 'SELECT * FROM restaurants WHERE "Aggregate rating" > 4.5'

st.markdown("<br>", unsafe_allow_html=True)

# Editor de queries
st.markdown("### 💻 Editor SQL")

sql = st.text_area(
    "Escribe tu consulta SQL:",
    value=st.session_state.get('sql_query', 'SELECT * FROM restaurants WHERE "Restaurant ID" BETWEEN 6317637 AND 6500000'),
    height=120,
    key="sql_editor"
)

# Botón ejecutar
execute_btn = st.button("▶️ Ejecutar", type="primary", use_container_width=False)

st.markdown("<br>", unsafe_allow_html=True)

# Ejecutar query
if execute_btn and sql.strip():
    with st.spinner("Ejecutando..."):
        result = execute_query(sql)
    
    if "error" in result:
        st.markdown(f"""
        <div class="error-box">
            <strong>Error:</strong> {result['error']}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mostrar resultados
        if "rows" in result:
            rows = result['rows']
            count = result.get('count', len(rows))
            io_stats = result.get('io', {})
            query_time = result.get('execution_time_ms', 0)
            
            # Métricas
            st.markdown("### 📈 Resultados")
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
                    <div class="metric-label">Tiempo</div>
                    <div class="metric-value">{query_time:.2f}ms</div>
                    <div class="metric-sublabel">ejecución</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                io_reads = io_stats.get('disk_reads', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Lecturas</div>
                    <div class="metric-value">{io_reads}</div>
                    <div class="metric-sublabel">disco I/O</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                io_writes = io_stats.get('disk_writes', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Escrituras</div>
                    <div class="metric-value">{io_writes}</div>
                    <div class="metric-sublabel">disco I/O</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mostrar datos
            if count > 0:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, height=400)
                
                # Descarga CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"query_result_{int(time.time())}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No se encontraron registros")
