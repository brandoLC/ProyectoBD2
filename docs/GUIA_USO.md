# 🚀 Proyecto BD2 - Mini DBMS

## ✅ Estado Actual: PROYECTO CREADO EXITOSAMENTE

### 📁 Estructura Completa

```
✅ core/          - Módulos de almacenamiento, IO metrics, schema, table
✅ indexes/       - Sequential (funcional), ISAM, Hash, B+Tree, RTree (scaffolding)
✅ sql/           - Parser, AST, Planner, Executor
✅ api/           - FastAPI backend
✅ ui/            - Streamlit frontend
✅ data/          - CSV de ejemplo (restaurantes)
✅ tests/         - Test básico (passing ✅)
✅ experiments/   - Script de benchmarks
✅ Docker         - docker-compose.yml + Dockerfiles
```

---

## 🎯 Cómo Usar Tu Proyecto

### 1️⃣ **Activar el entorno virtual** (siempre primero)

```powershell
.venv\Scripts\Activate.ps1
```

### 2️⃣ **Correr el Backend (API)**

```powershell
.venv\Scripts\uvicorn api.main:app --reload --port 8000
```

✅ **API corriendo en:** http://localhost:8000/docs (Swagger UI automático)

### 3️⃣ **Correr el Frontend (UI)** - En otra terminal

```powershell
.venv\Scripts\streamlit run ui/app.py --server.port 8501
```

✅ **UI corriendo en:** http://localhost:8501

### 4️⃣ **Ejecutar Tests**

```powershell
.venv\Scripts\python -m pytest tests/ -v
```

### 5️⃣ **Correr Benchmarks** (cuando implementes los índices)

```powershell
.venv\Scripts\python experiments/benchmark.py
```

---

## 📝 Ejemplos de SQL Que Puedes Ejecutar (desde la UI o API)

```sql
-- 1. Crear tabla
CREATE TABLE Restaurantes(id, nombre, fecha, lat, lon) KEY(id)

-- 2. Cargar CSV
CREATE TABLE Restaurantes FROM FILE "data/sample_restaurantes.csv"

-- 3. Buscar por igualdad
SELECT * FROM Restaurantes WHERE id = 1

-- 4. Buscar por rango
SELECT * FROM Restaurantes WHERE id BETWEEN 1 AND 10

-- 5. Insertar registro
INSERT INTO Restaurantes(id, nombre, fecha, lat, lon) VALUES (100, "Nuevo", "2025-01-01", -12.0, -77.0)

-- 6. Eliminar registro
DELETE FROM Restaurantes WHERE id = 100
```

---

## 🛠️ Próximos Pasos (Implementación Pendiente)

### ✅ **Ya funciona:**

- ✅ Sequential Index (búsqueda, inserción, rango)
- ✅ Parser SQL básico
- ✅ API + UI completamente funcional

### 🚧 **A implementar (TU TRABAJO):**

#### 1. **ISAM** (`indexes/isam.py`)

- [ ] Construcción de 2-3 niveles estáticos
- [ ] Búsqueda por niveles (binaria)
- [ ] Inserción con overflow pages encadenadas
- [ ] Reconstrucción cuando overflow > K

#### 2. **Extendible Hash** (`indexes/ext_hash.py`)

- [ ] Split de buckets cuando rebasa `bucket_size`
- [ ] Duplicación de directorio cuando `local_depth == global_depth`
- [ ] Búsqueda O(1) por igualdad

#### 3. **B+Tree** (`indexes/bplustree.py`)

- [ ] Crear clases `BPlusNode` (interno/hoja)
- [ ] Implementar split recursivo
- [ ] Enlazar hojas con puntero `next`
- [ ] Búsqueda + rango eficiente

#### 4. **R-Tree** (`indexes/rtree_adapter.py`)

- [ ] Mejorar cálculo de distancia real (Haversine)
- [ ] Implementar `range(lat, lon, radius)` correctamente
- [ ] Implementar `knn(lat, lon, k)` para k vecinos más cercanos

#### 5. **Ampliar Parser SQL** (`sql/parser.py`)

- [ ] Soportar múltiples índices por columna
- [ ] Agregar consultas espaciales: `WHERE ubicacion IN (point, radius)`
- [ ] Agregar k-NN: `WHERE ubicacion KNN (point, k)`

#### 6. **Benchmarks** (`experiments/benchmark.py`)

- [ ] Comparar las 5 técnicas
- [ ] Generar gráficos con matplotlib (tiempo + I/O)
- [ ] Probar con datasets de diferentes tamaños (100, 1K, 10K, 50K)

---

## 🐳 Docker (Opcional)

```powershell
# Levantar todo el stack
docker compose up --build

# Parar servicios
docker compose down
```

- API: http://localhost:8000
- UI: http://localhost:8501

---

## 📊 Testing del Proyecto

### Ver métricas de I/O

Cada consulta retorna:

```json
{
  "rows": [...],
  "count": 5,
  "io": {
    "reads": 1,
    "writes": 0
  }
}
```

### Probar la API manualmente

```powershell
# Health check
curl http://localhost:8000/health

# Ejecutar query
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"sql": "SELECT * FROM Restaurantes WHERE id = 1"}'
```

---

## 🎓 Tips para el Informe

### Métricas a comparar:

1. **Tiempo de ejecución** (milisegundos)
2. **Accesos a disco** (reads + writes)
3. **Operaciones:**
   - Inserción masiva (1K, 10K, 50K registros)
   - Búsqueda por igualdad
   - Búsqueda por rango
   - Eliminación

### Gráficos sugeridos:

- Tiempo vs Tamaño del dataset (líneas)
- I/O vs Tamaño del dataset (barras)
- Comparación entre técnicas (radar chart)

---

## 📚 Archivos Importantes

| Archivo                 | Descripción                         |
| ----------------------- | ----------------------------------- |
| `core/storage.py`       | Simulador de disco con contador I/O |
| `core/table.py`         | Clase Table que usa índices         |
| `indexes/sequential.py` | ✅ Índice funcional de referencia   |
| `sql/parser.py`         | Parser SQL con regex                |
| `sql/executor.py`       | Ejecutor de queries                 |
| `api/main.py`           | FastAPI endpoints                   |
| `ui/app.py`             | Streamlit UI                        |

---

## 🆘 Troubleshooting

### Problema: "Module not found"

```powershell
.venv\Scripts\pip install <nombre-paquete>
```

### Problema: Puerto ocupado

```powershell
# Cambiar puerto del API
.venv\Scripts\uvicorn api.main:app --port 8001

# Cambiar puerto del UI
.venv\Scripts\streamlit run ui/app.py --server.port 8502
```

### Problema: Necesito rtree para R-Tree

```powershell
# Instalar dependencias para rtree en Windows
.venv\Scripts\pip install rtree shapely
```

---

## ✅ Checklist del Proyecto

- [x] Estructura de carpetas creada
- [x] Todos los archivos generados
- [x] Dependencias instaladas
- [x] Sequential Index funcional
- [x] Parser SQL básico funcional
- [x] API funcional
- [x] UI funcional
- [x] Test básico passing
- [ ] Implementar ISAM
- [ ] Implementar Extendible Hash
- [ ] Implementar B+Tree
- [ ] Integrar R-Tree
- [ ] Ampliar parser SQL
- [ ] Crear benchmarks
- [ ] Escribir informe
- [ ] Grabar video (<15 min)

---

## 🚀 ¡Empieza por aquí!

1. **Lee el código de `indexes/sequential.py`** → Es tu referencia
2. **Implementa ISAM** → El más sencillo después de Sequential
3. **Implementa Hash** → Solo igualdad, más directo
4. **Implementa B+Tree** → El más complejo pero más versátil
5. **Integra R-Tree** → Usa librería existente
6. **Haz benchmarks** → Compara todo
7. **Documenta** → Informe + video

---

**¡Éxito con tu proyecto! 🎓🚀**
