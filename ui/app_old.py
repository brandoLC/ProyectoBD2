import streamlit as st
import requests
import pandas as pd
import time
import json

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="BD2 - ISAM Database",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ESTILOS CSS - MINIMALISTA Y MODERNO
# ============================================================================

st.markdown("""
<style>
    /* Fuentes y colores generales */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    
    .main-header h1 {
        color: white;
        font-weight: 700;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        font-weight: 300;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #666;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background-color: #f8f9fa;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Botones */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton button:hover {
        transform: scale(1.02);
    }
    
    /* Text areas */
    .stTextArea textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        font-family: 'Courier New', monospace;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Resultados */
    .result-success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .result-error {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* DataFrames */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="main-header">Mi SGBD</div>', unsafe_allow_html=True)

# Sidebar - Panel de Tablas
with st.sidebar:
    st.markdown("### 📊 Tables")
    
    # Intentar obtener lista de tablas (simulado por ahora)
    if st.button("� Refresh", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    # Lista de tablas (hardcoded por ahora)
    tables = ["Restaurantes"]
    for table in tables:
        if st.button(f"▪️ {table}", key=f"table_{table}", use_container_width=True):
            st.session_state['sql_query'] = f"SELECT * FROM {table} WHERE id BETWEEN 1 AND 10"
    
    st.markdown("---")
    st.markdown("### ⚙️ Opciones")
    st.markdown("**Índice actual:** Sequential")
    
    st.markdown("---")
    st.caption("📁 Archivos disponibles:")
    st.caption("• sample_restaurantes.csv (6)")
    st.caption("• restaurantes_100.csv (100)")
    st.caption("• restaurantes_1k.csv (1K)")
    st.caption("• restaurantes_10k.csv (10K)")

# Main content area
col_query, col_buttons = st.columns([5, 1])

with col_query:
    default_query = st.session_state.get('sql_query', 'SELECT * FROM Restaurantes WHERE id BETWEEN 1 AND 10')
    sql = st.text_area("", value=default_query, height=120, key="sql_input", 
                       placeholder="Escribe tu consulta SQL aquí...")

with col_buttons:
    st.markdown("<br>", unsafe_allow_html=True)
    execute_btn = st.button("▶️ Ejecutar", type="primary", use_container_width=True)
    st.button("⏹️ Detener", use_container_width=True, disabled=True)
    st.button("🧹 Limpiar", use_container_width=True)

# Ejecutar query
if execute_btn:
    start_time = time.time()
    try:
        r = requests.post(f"{API}/query", json={"sql": sql}, timeout=10)
        elapsed_time = time.time() - start_time
        
        if r.status_code == 200:
            result = r.json()
            
            # Tabs para Result / Explain / Transx
            tab1, tab2, tab3 = st.tabs(["📊 Result", "📋 Explain", "🔄 Transx"])
            
            with tab1:
                if "rows" in result and result["rows"]:
                    # Mostrar tabla de resultados
                    df = pd.DataFrame(result["rows"])
                    
                    # Header con info
                    col_info1, col_info2, col_info3 = st.columns([2, 1, 1])
                    with col_info1:
                        st.markdown(f"**Table: Restaurantes**")
                    with col_info2:
                        st.markdown(f"**{result['count']} records**")
                    with col_info3:
                        st.markdown(f"**{elapsed_time:.2f} sec**")
                    
                    # Tabla de datos (estilo spreadsheet)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=False,
                        column_config={
                            col: st.column_config.TextColumn(
                                col,
                                width="medium",
                            ) for col in df.columns
                        }
                    )
                    
                    # Footer con métricas I/O
                    if "io" in result:
                        st.markdown("---")
                        col_io1, col_io2, col_io3, col_io4 = st.columns(4)
                        with col_io1:
                            st.metric("📖 Lecturas", result["io"].get("reads", 0))
                        with col_io2:
                            st.metric("✍️ Escrituras", result["io"].get("writes", 0))
                        with col_io3:
                            st.metric("� Total I/O", result["io"].get("reads", 0) + result["io"].get("writes", 0))
                        with col_io4:
                            st.metric("⏱️ Tiempo", f"{elapsed_time:.3f}s")
                    
                elif "loaded" in result:
                    st.success(f"✅ **{result['loaded']}** registros cargados en {elapsed_time:.2f} segundos")
                    st.json(result)
                    
                elif "deleted" in result:
                    st.warning(f"�️ **{result['deleted']}** registros eliminados")
                    st.json(result)
                    
                else:
                    st.success(f"✅ Operación completada en {elapsed_time:.2f} segundos")
                    st.json(result)
            
            with tab2:
                st.info("🚧 Plan de ejecución (próximamente)")
                st.markdown("""
                **Query Plan:**
                ```
                1. Parse SQL
                2. Select index: Sequential
                3. Scan range [begin_key, end_key]
                4. Return results
                ```
                """)
                if "io" in result:
                    st.json(result["io"])
            
            with tab3:
                st.info("🚧 Información de transacción (próximamente)")
                st.code("Transaction ID: N/A\nIsolation Level: Read Committed\nDuration: {:.3f}s".format(elapsed_time))
        else:
            st.error(f"❌ Error {r.status_code}")
            st.code(r.text)
            
    except requests.exceptions.ConnectionError:
        st.error(f"❌ No se puede conectar a la API en {API}")
        st.info("🔧 Inicia el servidor: `uvicorn api.main:app --reload --port 8000`")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Footer con ejemplos rápidos
st.markdown("---")
with st.expander("📚 Ejemplos de Consultas SQL"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**� DDL/DML**")
        st.code('CREATE TABLE Restaurantes(id, nombre, fecha, lat, lon) KEY(id)', language='sql')
        st.code('CREATE TABLE Restaurantes FROM FILE "data/restaurantes_1k.csv"', language='sql')
        st.code("INSERT INTO Restaurantes(id, nombre, fecha, lat, lon) VALUES (999, 'Test', '2025-01-01', -12.0, -77.0)", language='sql')
        st.code('DELETE FROM Restaurantes WHERE id = 999', language='sql')
    
    with col2:
        st.markdown("**🔍 SELECT**")
        st.code('SELECT * FROM Restaurantes WHERE id = 100', language='sql')
        st.code('SELECT * FROM Restaurantes WHERE id BETWEEN 1 AND 100', language='sql')
        st.code('SELECT * FROM Restaurantes WHERE id BETWEEN 1 AND 1000', language='sql')
