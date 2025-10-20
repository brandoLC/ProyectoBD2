# Guía de Testing - BD2 Proyecto ISAM

## 📋 Opciones de Testing

Tienes **2 formas** de probar el sistema completo:

### 🐍 Opción 1: Script Python Exhaustivo (RECOMENDADO)

**Ventajas:**

- ✅ Automatizado completamente
- ✅ 15 tests exhaustivos
- ✅ Output con colores y detalles
- ✅ Verifica persistencia, índices, I/O, etc.
- ✅ No requiere API corriendo

**Cómo usar:**

```bash
python test_comprehensive.py
```

**Qué prueba:**

1. ✅ Limpieza de storage
2. ✅ Importación de módulos
3. ✅ Creación de tabla con ISAM
4. ✅ Archivos en disco (catalog.json, .dat, .idx)
5. ✅ Metadata completa en catalog
6. ✅ Estructura ISAM de 3 niveles (L2 → L1 → Buckets)
7. ✅ Búsqueda de registros existentes
8. ✅ Búsqueda de registros inexistentes
9. ✅ Búsqueda por rango
10. ✅ Simulación de reinicio del sistema
11. ✅ Restauración de estructura desde disco
12. ✅ Queries después de restaurar
13. ✅ Inserciones con overflow pages
14. ✅ Métricas de I/O optimizadas
15. ✅ Búsqueda multinivel (L2 → L1 → Bucket)

**Output esperado:**

```
======================================================================
                    TEST EXHAUSTIVO - BD2 PROYECTO
======================================================================

▶ Test 1: Limpiar storage
  ✓ PASSED

▶ Test 2: Importar módulos
  ✓ PASSED

...

======================================================================
                           RESUMEN DE TESTS
======================================================================

    Total tests: 15
    Passed: 15
    Failed: 0
    Success rate: 100.0%

                     🎉 TODOS LOS TESTS PASARON 🎉
```

---

### 📬 Opción 2: Colección Postman (MANUAL)

**Ventajas:**

- ✅ Visual e interactivo
- ✅ Prueba el API REST directamente
- ✅ Tests automatizados por request
- ✅ Fácil de compartir con el equipo

**Requisitos:**

1. API corriendo: `uvicorn api.main:app --reload --port 8000`
2. Postman instalado o usar Postman Web

**Cómo usar:**

1. **Importar colección en Postman:**

   - Abrir Postman
   - File → Import
   - Seleccionar `BD2_Proyecto_Postman_Collection.json`

2. **Ejecutar requests:**

   - Ejecutar cada request manualmente (uno por uno)
   - O usar "Run Collection" para ejecutar todos automáticamente

3. **Requests incluidos:**

   | #   | Request                 | Descripción                            |
   | --- | ----------------------- | -------------------------------------- |
   | 1   | Health Check            | Verifica servidor y lista tablas       |
   | 2   | Query - ID existe       | Busca Restaurant ID = 6317637          |
   | 3   | Query - ID no existe    | Busca Restaurant ID = 99999999         |
   | 4   | Query - Rango pequeño   | BETWEEN 6317637 AND 6500000            |
   | 5   | Query - Rango grande    | BETWEEN 6000000 AND 10000000           |
   | 6   | Query - Último registro | Restaurant ID = 17284390               |
   | 7   | Query - ID intermedio   | Restaurant ID = 6700846                |
   | 8   | Query - Todos           | BETWEEN 0 AND 99999999 (100 registros) |

4. **Tests automatizados:**
   - Cada request tiene tests que validan:
     - ✅ Status code 200
     - ✅ Número correcto de resultados
     - ✅ Datos correctos retornados
     - ✅ I/O optimizado (reads = 0)

**Output esperado:**

```json
{
  "rows": [
    {
      "Restaurant ID": 6317637,
      "Restaurant Name": "Le Petit Souffle",
      "City": "Makati City",
      "Cuisines": "French, Japanese, Desserts",
      "Aggregate rating": 4.8,
      ...
    }
  ],
  "count": 1,
  "io": {
    "reads": 0,
    "writes": 0
  }
}
```

---

## 🎯 Recomendación

**Para desarrollo y debugging:**

- Usa el **script Python** (`test_comprehensive.py`) porque es más completo y detallado

**Para demostración o presentación:**

- Usa **Postman** porque es visual y fácil de mostrar en vivo

**Para CI/CD o testing automatizado:**

- Usa el **script Python** en tu pipeline

---

## 📊 Qué Validan Ambos

✅ **Persistencia:** Datos sobreviven reinicio  
✅ **ISAM 3 niveles:** L2 (índice superior) → L1 (buckets) → Datos  
✅ **Búsqueda optimizada:** I/O reads = 0 (datos en índice)  
✅ **Overflow pages:** Inserciones nuevas van a overflow  
✅ **Factor de bloque:** fanout=20 (datos), fanout_l2=5 (índice)  
✅ **Búsquedas:** Por igualdad, por rango, inexistentes  
✅ **Restauración:** Schema + índices se cargan desde disco

---

## 🚀 Quick Start

### Opción más rápida (Script Python):

```bash
# Limpiar storage anterior
rm -rf storage/*  # Linux/Mac
Remove-Item storage/* -Force  # Windows

# Crear datos de prueba
python test_fix_pickle.py

# Ejecutar tests exhaustivos
python test_comprehensive.py
```

### Opción manual (Postman):

```bash
# 1. Crear datos
python test_fix_pickle.py

# 2. Iniciar API
uvicorn api.main:app --reload --port 8000

# 3. Importar colección en Postman
# 4. Run Collection
```

---

## 📁 Archivos de Testing

```
Proyecto/
├── test_comprehensive.py              # ⭐ Script exhaustivo (RECOMENDADO)
├── BD2_Proyecto_Postman_Collection.json  # Colección Postman
├── test_fix_pickle.py                 # Setup inicial de datos
├── test_restore.py                    # Test de restauración
├── test_query.py                      # Test de queries básicas
└── TESTING_GUIDE.md                   # Esta guía
```

---

## 🐛 Troubleshooting

**Error: "Tabla no encontrada"**

- Solución: Ejecutar `python test_fix_pickle.py` primero

**Error: "Connection refused" en Postman**

- Solución: Verificar que el API esté corriendo en puerto 8000

**Error: "Module not found"**

- Solución: Activar virtual environment (`.venv\Scripts\activate` en Windows)

**Tests fallan después de cambios**

- Solución: Limpiar storage con `Remove-Item storage/* -Force` y volver a crear

---

## ✅ Criterios de Éxito

El sistema funciona correctamente si:

1. ✅ Script Python: 15/15 tests passed (100%)
2. ✅ Postman: Todos los requests retornan status 200
3. ✅ Archivos en disco: `catalog.json`, `restaurants.dat`, `restaurants_isam.idx`
4. ✅ Índice ISAM: L2 con 2+ entradas, L1 con 5+ buckets
5. ✅ I/O optimizado: reads = 0 en búsquedas
6. ✅ Persistencia: Queries funcionan después de reiniciar API

---

**¡Listo para probar! 🚀**
