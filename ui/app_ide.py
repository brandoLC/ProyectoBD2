import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# ============================================================================
# CONFIG
# ============================================================================

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="BD2 Database Manager",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES
# ============================================================================

def execute_query(sql: str):
    try:
        response = requests.post(f"{API_URL}/query", json={"sql": sql}, timeout=30)
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "API no disponible en puerto 8000"}
    except Exception as e:
        return {"error": str(e)}

def get_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except:
        return None

# ============================================================================
# ESTILOS - ESTILO PGADMIN/DATAGRIP
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Roboto:wght@300;400;500;700&display=swap');
    
    * {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Fondo general tipo IDE */
    .main {
        background-color: #f5f5f5;
    }
    
    /* Sidebar - Panel de navegación estilo IDE */
    section[data-testid="stSidebar"] {
        background-color: #2b2b2b !important;
        color: #e8e8e8 !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #e8e8e8 !important;
    }
    
    /* Botones del sidebar - estilo árbol de archivos */
    section[data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: none !important;
        text-align: left !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        color: #e8e8e8 !important;
        transition: background-color 0.15s !important;
        border-radius: 4px !important;
        font-family: 'Roboto', sans-serif !important;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background-color: #3c3c3c !important;
    }
    
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #0d7377 !important;
        color: white !important;
    }
    
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #0a5d5f !important;
    }
    
    /* Títulos del sidebar */
    section[data-testid="stSidebar"] h3 {
        color: #bbbbbb !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-weight: 600 !important;
        margin-top: 20px !important;
        margin-bottom: 8px !important;
    }
    
    /* Header principal - barra superior tipo IDE */
    .ide-header {
        background-color: #2b2b2b;
        padding: 12px 20px;
        border-bottom: 1px solid #3c3c3c;
        margin: -1rem -1rem 1rem -1rem;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .ide-header h1 {
        color: #e8e8e8;
        font-size: 16px;
        margin: 0;
        font-weight: 500;
    }
    
    .ide-header .status {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #4ade80;
        margin-left: auto;
    }
    
    /* Panel de queries - Editor estilo IDE */
    .query-panel {
        background-color: white;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .query-panel-header {
        background-color: #f9fafb;
        padding: 10px 16px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        gap: 10px;
        border-radius: 6px 6px 0 0;
    }
    
    .query-panel-title {
        font-size: 13px;
        font-weight: 600;
        color: #374151;
        margin: 0;
    }
    
    /* Text area - Editor tipo código */
    .stTextArea textarea {
        background-color: #1e1e1e !important;
        color: #d4d4d4 !important;
        border: 1px solid #3c3c3c !important;
        border-radius: 0 0 6px 6px !important;
        font-family: 'JetBrains Mono', 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        padding: 16px !important;
    }
    
    .stTextArea label {
        display: none !important;
    }
    
    /* Botones de acción - estilo IDE */
    .action-buttons button {
        background-color: #0d7377 !important;
        color: white !important;
        border: none !important;
        padding: 8px 20px !important;
        border-radius: 4px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        transition: background-color 0.15s !important;
    }
    
    .action-buttons button:hover {
        background-color: #0a5d5f !important;
    }
    
    /* Panel de resultados - tipo DataGrip */
    .results-panel {
        background-color: white;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .results-header {
        background-color: #f9fafb;
        padding: 10px 16px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .results-title {
        font-size: 13px;
        font-weight: 600;
        color: #374151;
    }
    
    .results-meta {
        font-size: 12px;
        color: #6b7280;
    }
    
    /* Tabla de resultados */
    div[data-testid="stDataFrame"] {
        border: none !important;
        font-size: 13px !important;
    }
    
    div[data-testid="stDataFrame"] table {
        border-collapse: collapse !important;
    }
    
    div[data-testid="stDataFrame"] th {
        background-color: #f9fafb !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        color: #374151 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 10px !important;
        border-bottom: 2px solid #e5e7eb !important;
    }
    
    div[data-testid="stDataFrame"] td {
        padding: 8px 10px !important;
        border-bottom: 1px solid #f3f4f6 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
    }
    
    /* Métricas estilo IDE */
    .metrics-bar {
        background-color: #2b2b2b;
        color: #e8e8e8;
        padding: 8px 16px;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        border-radius: 0 0 6px 6px;
        display: flex;
        gap: 20px;
    }
    
    .metric-item {
        display: flex;
        gap: 6px;
    }
    
    .metric-label {
        color: #999;
    }
    
    .metric-value {
        color: #4ade80;
        font-weight: 600;
    }
    
    /* Expander - estilo acordeón IDE */
    .streamlit-expanderHeader {
        background-color: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background-color: #2b2b2b !important;
        color: #e8e8e8 !important;
        border: 1px solid #3c3c3c !important;
        border-radius: 4px !important;
    }
    
    /* Mensajes de estado */
    .stSuccess, .stError, .stWarning, .stInfo {
        font-size: 13px !important;
        border-radius: 4px !important;
    }
    
    /* Tabs - estilo pestañas de editor */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f9fafb;
        border-bottom: 1px solid #e5e7eb;
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 13px;
        font-weight: 500;
        color: #6b7280;
        border-radius: 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        color: #0d7377;
        border-bottom: 2px solid #0d7377;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER TIPO IDE
# ============================================================================

health = get_health()
status_dot = "🟢" if health else "🔴"

st.markdown(f"""
<div class="ide-header">
    <h1>🗄️ BD2 Database Manager</h1>
    <span style="color: #999; font-size: 13px;">localhost:8000</span>
    <span style="margin-left: auto; font-size: 12px; color: #999;">
        {status_dot} {'Connected' if health else 'Disconnected'}
    </span>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - PANEL DE NAVEGACIÓN (ESTILO PGADMIN)
# ============================================================================

with st.sidebar:
    # Logo/Título
    st.markdown("### 🗄️ DATABASES")
    
    # Servidor
    st.markdown("#### 📡 Server: localhost")
    
    if health and "tables" in health:
        tables = health["tables"]
        
        # Árbol de base de datos
        st.markdown("#### 📊 Tables")
        
        for table in tables:
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(f"▸ {table}", key=f"tbl_{table}", use_container_width=True):
                    st.session_state['selected_table'] = table
            with col2:
                if st.button("🔄", key=f"ref_{table}", help="Ver estructura"):
                    st.session_state['show_structure'] = table
        
        # Información de la tabla seleccionada
        if 'selected_table' in st.session_state:
            with st.expander(f"ℹ️ Info: {st.session_state['selected_table']}", expanded=True):
                st.caption("**Columnas:**")
                st.caption("• Restaurant ID (INT)")
                st.caption("• Restaurant Name (TEXT)")
                st.caption("• City (TEXT)")
                st.caption("• Rating (FLOAT)")
                st.caption("• ... y 17 más")
                
                st.caption("\n**Índice:** ISAM (3 niveles)")
                st.caption("**Registros:** ~9.5K")
    else:
        st.markdown("#### ⚠️ No connection")
        st.caption("API not available")
    
    st.markdown("---")
    
    # Herramientas
    st.markdown("### 🛠️ TOOLS")
    
    with st.expander("📂 Load Dataset", expanded=False):
        dataset = st.selectbox(
            "Select file",
            ["kaggle_Dataset _100.csv", "kaggle_Dataset _1k.csv", "kaggle_Dataset .csv"],
            key="dataset",
            label_visibility="collapsed"
        )
        
        index_type = st.selectbox(
            "Index type",
            ["ISAM", "Sequential"],
            key="index",
            label_visibility="collapsed"
        )
        
        if st.button("▶️ Load", use_container_width=True, type="primary"):
            with st.spinner("Loading..."):
                idx_type = index_type.lower()
                execute_query(f"CREATE TABLE restaurants USING {idx_type}")
                result = execute_query(f"LOAD restaurants FROM 'data/{dataset}'")
                
                if "error" not in result:
                    st.success(f"✓ Loaded {result.get('loaded', 0)} rows")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("✗ Error loading")
    
    with st.expander("🗑️ Clear Data"):
        st.caption("Remove all data:")
        st.code("Remove-Item storage/* -Force", language="powershell")

# ============================================================================
# MAIN - QUERY EDITOR (ESTILO DATAGRIP)
# ============================================================================

# Panel superior con pestañas
tab1, tab2 = st.tabs(["📝 Query Console", "🏗️ Structure"])

with tab1:
    # Query templates / snippets
    st.markdown("#### Quick Templates")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🔍 Find by ID", use_container_width=True):
            st.session_state['sql'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" = 6300002'
    with col2:
        if st.button("📊 Range", use_container_width=True):
            st.session_state['sql'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" BETWEEN 6300000 AND 6300020'
    with col3:
        if st.button("🔝 First 10", use_container_width=True):
            st.session_state['sql'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" BETWEEN 53 AND 200'
    with col4:
        if st.button("⭐ Top Rated", use_container_width=True):
            st.session_state['sql'] = 'SELECT * FROM restaurants WHERE "Restaurant ID" > 6000000'
    with col5:
        if st.button("🆕 New Query", use_container_width=True):
            st.session_state['sql'] = ''
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Editor de queries
    st.markdown('<div class="query-panel">', unsafe_allow_html=True)
    st.markdown('<div class="query-panel-header"><span class="query-panel-title">Query Editor</span></div>', unsafe_allow_html=True)
    
    sql = st.text_area(
        "sql_editor",
        value=st.session_state.get('sql', ''),
        height=180,
        placeholder='-- Type your SQL query here\nSELECT * FROM restaurants WHERE "Restaurant ID" = 6300002',
        label_visibility="collapsed",
        key="sql_input"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Botones de acción
    col1, col2, col3 = st.columns([1, 1, 8])
    
    with col1:
        st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
        execute_btn = st.button("▶️ Execute", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("⏹️ Stop", disabled=True, use_container_width=True):
            pass
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Resultados
    if execute_btn and sql.strip():
        with st.spinner("Executing query..."):
            start = time.time()
            result = execute_query(sql)
            exec_time = (time.time() - start) * 1000
        
        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
        
        elif "rows" in result:
            rows = result['rows']
            count = result.get('count', len(rows))
            io_stats = result.get('io', {})
            
            # Panel de resultados
            st.markdown(f"""
            <div class="results-panel">
                <div class="results-header">
                    <span class="results-title">Query Results</span>
                    <span class="results-meta">{count} rows • {exec_time:.1f}ms</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if count > 0:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, height=400)
                
                # Barra de métricas inferior
                st.markdown(f"""
                <div class="metrics-bar">
                    <div class="metric-item">
                        <span class="metric-label">Rows:</span>
                        <span class="metric-value">{count}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">Time:</span>
                        <span class="metric-value">{exec_time:.2f}ms</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">I/O Reads:</span>
                        <span class="metric-value">{io_stats.get('disk_reads', 0)}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-label">I/O Writes:</span>
                        <span class="metric-value">{io_stats.get('disk_writes', 0)}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Botón de descarga
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Export CSV",
                    csv,
                    f"query_{int(time.time())}.csv",
                    "text/csv"
                )
            else:
                st.info("Query executed successfully. No rows returned.")
        
        elif "ok" in result:
            st.success(f"✅ Operation completed successfully")

with tab2:
    st.markdown("#### Database Structure")
    
    if health and tables:
        st.markdown("##### Table: restaurants")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Index Information**")
            st.code("""
Type: ISAM (3-level)
Levels:
  - L2: 96 entries (superior index)
  - L1: 478 buckets
  - Data: ~20 records/bucket
            
Fanout: 20
Fanout L2: 5
Overflow: 0 records
            """, language="text")
        
        with col2:
            st.markdown("**📁 Storage Files**")
            st.code("""
storage/
├── catalog.json (1.94 KB)
├── restaurants.dat (3.73 MB)
├── restaurants_isam_l2.idx (506 B)
├── restaurants_isam_l1.idx (2.22 KB)
└── restaurants_isam_overflow.dat (3.30 MB)
            """, language="text")
        
        st.markdown("**📋 Schema**")
        
        schema_data = {
            "Column": ["Restaurant ID", "Restaurant Name", "City", "Aggregate rating", "Cuisines", "..."],
            "Type": ["INT", "TEXT", "TEXT", "FLOAT", "TEXT", "..."],
            "Key": ["PRIMARY", "", "", "", "", ""]
        }
        st.dataframe(pd.DataFrame(schema_data), use_container_width=True, hide_index=True)
    
    else:
        st.warning("No tables available. Load a dataset first.")
