# BD2 Proyecto — Database Storage Engine

**Sistema completo de almacenamiento en disco con 4 índices implementados y métricas de I/O real**

## 🎯 Características Completadas

✅ **4 Índices Implementados**

- **Sequential File** - Búsqueda secuencial con bloques
- **ISAM** - Índice multinivel (3 niveles: L1→L2→Buckets + Overflow)
- **Extendible Hash** - Hash dinámico con directorio extensible
- **B+ Tree** - Árbol B+ balanceado con hojas enlazadas

✅ **Operaciones CRUD Completas**

- `SELECT * FROM table` - Escaneo completo
- `SELECT * FROM table WHERE key = value` - Búsqueda por igualdad
- `SELECT * FROM table WHERE key BETWEEN a AND b` - Búsqueda por rango
- `INSERT INTO table (cols) VALUES (vals)` - Inserción de registros
- `DELETE FROM table WHERE key = value` - Eliminación con persistencia en disco

✅ **Métricas de I/O Real**

- Contador de reads/writes para todas las operaciones
- Persistencia en disco para ISAM, Ext Hash y B+ Tree
- Archivos separados para índices (buckets, overflow, directorio)
- Sistema de buffer pool configurable

✅ **Interfaz de Usuario Completa**

- Streamlit UI interactiva con 6 botones de consultas ejemplo
- Editor SQL con syntax highlighting
- Visualización de resultados en tabla
- Métricas de performance (tiempo, I/O operations)
- FastAPI backend con Swagger docs

## 🚀 Instalación y Ejecución

### Opción 1: Local (Desarrollo)

```bash
# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos (Kaggle dataset - 9.5K registros)
python scripts/load_all_9k.py

# Ejecutar Backend API (terminal 1)
uvicorn api.main:app --reload --port 8000

# Ejecutar UI (terminal 2)
streamlit run ui/app.py --server.port 8501
```

### Opción 2: Docker Compose (Recomendado para Producción)

```bash
# Clonar repositorio
git clone https://github.com/brandoLC/ProyectoBD2.git
cd ProyectoBD2

# Levantar todo el sistema
docker compose up --build
```

**Primera ejecución (~5 minutos):**

- 🏗️ Construye imágenes Docker
- 🗄️ Carga automáticamente 9,551 registros en 4 tablas
- ✅ Inicia API + UI

**Ejecuciones subsecuentes (~15 segundos):**

- ⚡ Usa datos ya cargados
- ⚡ Inicia directo

**Endpoints:**

- 🎨 UI Streamlit: http://localhost:8501
- 📡 API FastAPI: http://localhost:8000/docs
- ❤️ Health Check: http://localhost:8000/health

**Más detalles:** Ver [`DOCKER_GUIDE.md`](DOCKER_GUIDE.md)

## 📊 Resultados de Benchmark (100 registros)

| Índice         | BUILD          | SELECT=          | RANGE(10)       | INSERT         | DELETE             |
| -------------- | -------------- | ---------------- | --------------- | -------------- | ------------------ |
| **Sequential** | 137ms (5W)     | 13.27ms (2R)     | **0.18ms (1R)** | 6.57ms (1R/2W) | 10.72ms (1R/2W)    |
| **ISAM**       | 157ms (5W)     | **11.93ms (5R)** | 10.92ms (5R)    | 6.85ms (5R/1W) | **0.26ms (5R/1W)** |
| **Ext Hash**   | **128ms (4W)** | 45.27ms (3R)     | N/A             | 1.07ms (2R/2W) | 0.28ms (4R/4W)     |
| **B+ Tree**    | 153ms (5W)     | 14.90ms (4R)     | 5.11ms (4R)     | 7.13ms (4R/2W) | 0.27ms (4R/4W)     |

**Conclusiones:**

- **Ext Hash**: Más rápido en BUILD (menos writes), pero SELECT= es lento
- **ISAM**: Excelente para SELECT= y DELETE (acceso directo por índice)
- **Sequential**: Insuperable en RANGE pequeños (acceso contiguo en disco)
- **B+ Tree**: Balanceado en todas las operaciones, mejor para RANGE grandes

## 📖 Uso del Sistema

### 1. Cargar Datos desde CSV

```bash
# Cargar dataset completo de Kaggle (9,551 registros) en las 4 tablas
python scripts/load_all_9k.py

# Limpiar storage si necesitas empezar de cero
python scripts/clean_storage.py
```

### 2. Ejecutar Consultas SQL

#### En la UI (Streamlit):

- Botón **"🔍 Buscar"** → `SELECT * FROM restaurants_isam WHERE "Restaurant ID" = 6300002`
- Botón **"📊 Rango"** → `SELECT * FROM restaurants_isam WHERE "Restaurant ID" BETWEEN 6300000 AND 6300100`
- Botón **"➕ Insertar"** → Inserta nuevo registro
- Botón **"❌ Eliminar"** → `DELETE FROM restaurants WHERE "Restaurant ID" = 99999999`

#### Desde Python:

```python
from sql.parser import parse
from sql.executor import Executor

executor = Executor()

# SELECT con igualdad
result = executor.execute(parse("SELECT * FROM restaurants_hash WHERE \"Restaurant ID\" = 6300002"))
print(f"Tiempo: {result['execution_time_ms']:.2f}ms")
print(f"I/O: {result['io']['disk_reads']}R/{result['io']['disk_writes']}W")

# DELETE
result = executor.execute(parse("DELETE FROM restaurants_isam WHERE \"Restaurant ID\" = 6300002"))
print(f"Eliminados: {result['deleted']} registros")
```

### 3. Benchmark de Comparación

```bash
# Ejecutar benchmark completo con 9.5K registros
python scripts/benchmark_9k.py

# Generar gráficos de visualización
python scripts/visualize_benchmark.py
```

Genera tabla comparativa y CSV con resultados (guardados en `results/`):

```
Benchmark Results (100 records)
═══════════════════════════════════════════════════════════
Operation    Sequential    ISAM           Ext Hash       B+ Tree
───────────────────────────────────────────────────────────
BUILD        137ms (5W)    157ms (5W)     128ms (4W)     153ms (5W)
SELECT=      13ms (2R)     12ms (5R)      45ms (3R)      15ms (4R)
...
```

### 4. Limpiar Storage

```bash
python scripts/clean_storage.py
```

Elimina todos los archivos `.dat`, `.idx` y reinicia `catalog.json`.

## 🏗️ Arquitectura del Sistema

### Estructura de Directorios

```
Proyecto/
├── core/                   # Core engine
│   ├── disk_manager.py      # Gestión de páginas en disco
│   ├── buffer_pool.py       # Buffer pool con LRU
│   ├── io_metrics.py        # Contador de I/O
│   ├── table.py             # Abstracción de tabla
│   └── schema.py            # Definición de esquema
├── indexes/                # Índices implementados
│   ├── sequential.py        # Sequential File con bloques
│   ├── isam.py             # ISAM 3-level + overflow
│   ├── ext_hash.py         # Extendible Hash dinámico
│   └── bplustree.py        # B+ Tree balanceado
├── sql/                    # Motor SQL
│   ├── parser.py           # Parser SQL → AST
│   ├── planner.py          # Query planner
│   └── executor.py         # Executor con métricas
├── api/                    # FastAPI backend
│   └── main.py             # Endpoints REST
├── ui/                     # Streamlit frontend
│   └── app.py              # Interfaz interactiva
├── scripts/                # Scripts de utilidad
│   ├── load_all_9k.py      # Cargar dataset completo
│   ├── benchmark_9k.py     # Benchmark con 9.5K registros
│   ├── visualize_benchmark.py  # Generar gráficos
│   └── clean_storage.py    # Limpiar storage
├── results/                # Resultados de benchmarks
│   ├── benchmark_9k_results_*.csv  # Resultados en CSV
│   └── *.png               # Gráficos de comparación
├── tests/                  # Tests unitarios
│   ├── test_indexes_basic.py   # Tests básicos de índices
│   ├── test_delete_real_io.py  # Tests de DELETE con I/O
│   └── test_delete_sql.py      # Tests de DELETE SQL
├── docs/                   # Documentación adicional
│   ├── GUIA_USO.md         # Guía de uso detallada
│   ├── QUERIES_KAGGLE.md   # Ejemplos de queries
│   └── TESTING_GUIDE.md    # Guía de testing
├── storage/                # Archivos de datos persistentes
│   ├── *.dat               # Archivos de datos de tablas
│   ├── *_buckets.dat       # Buckets de ISAM/Hash
│   ├── *_l1.idx            # Índice L1 de ISAM
│   ├── *_l2.idx            # Índice L2 de ISAM
│   └── catalog.json        # Catálogo de tablas
└── data/                   # Datasets CSV
    └── kaggle_Dataset .csv # Dataset completo (9.5K registros)
```

### Flujo de una Consulta

```
Usuario (SQL) → Parser → AST → Planner → Executor
                                            ↓
                                      Table.search()
                                            ↓
                                    Index.search(key)
                                            ↓
                                    DiskManager.read()
                                            ↓
                                    BufferPool (cache)
                                            ↓
                                    IOMetrics.count()
                                            ↓
                                    Resultado + Métricas
```

## 🔧 Detalles de Implementación

### ISAM (3 niveles)

- **L1**: Índice principal (primeras claves de L2)
- **L2**: Índice secundario (primeras claves de buckets)
- **Buckets**: Datos ordenados por clave
- **Overflow**: Registros insertados después del build
- **Archivos**: `table_isam_l1.idx`, `table_isam_l2.idx`, `table_isam_buckets.dat`, `table_isam_overflow.dat`

### Extendible Hash

- **Directorio**: Array de bucket_ids con profundidad global
- **Buckets**: Registros hash con profundidad local
- **Splits**: Duplicación de directorio cuando bucket lleno
- **Hash**: `hash(key) % (2 ** depth)`
- **Archivos**: `table_extendiblehash`, `table_exthash_buckets.dat`, `table_exthash_overflow.dat`

### B+ Tree

- **Nodos internos**: Solo claves (order=4)
- **Hojas**: Claves + datos, enlazadas para range queries
- **Balanceo**: Split al insertar si lleno
- **Archivos**: `table_bplustree`, `table_bplustree_leaves.dat`, `table_bplustree_overflow.dat`

### Sequential

- **Bloques**: Registros agrupados en bloques de tamaño fijo
- **Búsqueda**: Escaneo secuencial de bloques
- **Overflow**: Registros insertados al final
- **Archivos**: `table_sequential`, `table_sequential_blocks.dat`, `table_sequential_overflow.dat`

## 🧪 Testing

```bash
# Test DELETE en los 4 índices
python tests/test_delete_sql.py

# Test de I/O real con DELETE
python tests/test_delete_real_io.py

# Tests básicos de índices
pytest tests/test_indexes_basic.py -v
```

## 📈 Benchmark con Dataset Completo

```bash
# Cargar datos (9,551 registros)
python scripts/load_all_9k.py

# Ejecutar benchmark
python scripts/benchmark_9k.py

# Generar gráficos
python scripts/visualize_benchmark.py
```

Ver resultados en la carpeta `results/`
python init_kaggle_db.py # Modificar para usar kaggle_Dataset.csv
python benchmark_comparison.py

````

## 🐛 Troubleshooting

### Error: "No such file or directory"

```bash
python clean_storage.py
python init_kaggle_db.py
````

### Error: "Key not found"

- Verificar que el registro existe: `SELECT * FROM table`
- Revisar formato de clave (string vs int)

### Performance lento

- Revisar dataset size con `wc -l data/kaggle_Dataset_*.csv`
- Aumentar buffer pool size en `core/buffer_pool.py`
- Usar índice apropiado (ISAM para igualdad, Sequential para ranges)

## 📝 Próximas Mejoras

- [ ] R-Tree para búsquedas espaciales
- [ ] Soporte para múltiples índices por tabla
- [ ] Transactions y ACID properties
- [ ] Query optimizer con estadísticas
- [ ] Visualización de estructura de índices
- [ ] Gráficos de performance con matplotlib
- [ ] Tests de concurrencia

## 👥 Autores

Universidad - Bases de Datos 2 (2025-2)

---

**Estado del Proyecto**: ✅ **COMPLETO** - 4 índices implementados, CRUD funcional, benchmarks validados
