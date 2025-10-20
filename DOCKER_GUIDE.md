# 🐳 Guía de Despliegue con Docker Compose

Esta guía explica cómo ejecutar el proyecto completo usando Docker Compose.

## 📋 Prerrequisitos

- **Docker Desktop** instalado y corriendo

  - Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Mac: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)

- **Docker Compose** (incluido en Docker Desktop)

## 🚀 Inicio Rápido

### 1. Clonar el repositorio

```bash
git clone https://github.com/brandoLC/ProyectoBD2.git
cd ProyectoBD2
```

### 2. Levantar el proyecto

```bash
docker compose up --build
```

**¿Qué sucede internamente?**

1. 🏗️ **Build** (primera vez: ~2-3 minutos)
   - Construye imagen del API (FastAPI)
   - Construye imagen de la UI (Streamlit)
2. 🗄️ **Inicialización de datos** (primera vez: ~2-3 minutos)
   - Detecta que `storage/` está vacío
   - Ejecuta `scripts/load_all_9k.py` automáticamente
   - Carga 9,551 registros en 4 tablas:
     - `restaurants_seq` (Sequential Index)
     - `restaurants_isam` (ISAM 3-level)
     - `restaurants_hash` (Extendible Hash)
     - `restaurants_bplustree` (B+ Tree)
3. ✅ **Inicio de servicios**
   - API corriendo en `http://localhost:8000`
   - UI corriendo en `http://localhost:8501`

### 3. Acceder a la aplicación

- **UI (Streamlit)**: http://localhost:8501
- **API (FastAPI Docs)**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

### 4. Detener el proyecto

```bash
# Detener contenedores (Ctrl+C en la terminal)
# O en otra terminal:
docker compose down
```

## 📊 Ejecuciones Subsecuentes

**La segunda vez que ejecutes el proyecto será MUCHO MÁS RÁPIDO:**

```bash
docker compose up
```

- ✅ No reconstruye las imágenes (usa cache)
- ✅ No recarga los datos (detecta que `storage/` ya tiene datos)
- ✅ Inicia directo en ~10-15 segundos

## 🔧 Comandos Útiles

### Ver logs en tiempo real

```bash
docker compose logs -f
```

### Ver logs solo del API

```bash
docker compose logs -f api
```

### Ver logs solo de la UI

```bash
docker compose logs -f ui
```

### Reconstruir desde cero

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

### Limpiar datos y empezar de nuevo

```bash
# Detener contenedores
docker compose down

# Limpiar storage local
rm -rf storage/*  # Linux/Mac
# o
Remove-Item storage/* -Recurse  # Windows PowerShell

# Reiniciar (cargará datos nuevamente)
docker compose up --build
```

## 🗂️ Persistencia de Datos

Los datos se persisten en tu máquina local:

```
ProyectoBD2/
├── storage/          # ← Datos persistentes (compartido con contenedores)
│   ├── catalog.json
│   ├── *.dat
│   └── *.idx
└── data/             # ← Dataset CSV (compartido con contenedores)
    └── kaggle_Dataset .csv
```

**Ventajas:**

- ✅ Los datos sobreviven a `docker compose down`
- ✅ No hay que recargar los datos cada vez
- ✅ Puedes inspeccionar los archivos directamente

## 🐛 Troubleshooting

### Puerto 8000 ya está en uso

```bash
# Cambiar puerto en docker-compose.yml:
ports:
  - '8001:8000'  # Usa 8001 en lugar de 8000
```

### Puerto 8501 ya está en uso

```bash
# Cambiar puerto en docker-compose.yml:
ports:
  - '8502:8501'  # Usa 8502 en lugar de 8501
```

### Los datos no se cargan

```bash
# Verificar que data/ tiene el CSV
ls data/kaggle_Dataset\ .csv

# Reiniciar limpio
docker compose down
rm -rf storage/*
docker compose up --build
```

### Error de permisos en Linux

```bash
# Dar permisos a los scripts
chmod +x docker-entrypoint-api.sh
chmod +x docker-entrypoint-ui.sh
```

### Ver qué está pasando dentro del contenedor

```bash
# Entrar al contenedor del API
docker exec -it bd2-api bash

# Entrar al contenedor de la UI
docker exec -it bd2-ui bash

# Dentro del contenedor puedes:
ls storage/         # Ver archivos
cat storage/catalog.json  # Ver metadata
python scripts/load_all_9k.py  # Recargar manualmente
```

## 📈 Performance

### Primera ejecución

- **Build**: ~2-3 minutos (descarga Python, instala dependencias)
- **Carga de datos**: ~2-3 minutos (9,551 registros × 4 tablas)
- **Total**: ~5-6 minutos

### Ejecuciones subsecuentes

- **Inicio**: ~10-15 segundos
- **Total**: ~10-15 segundos ⚡

## 🎯 Arquitectura Docker

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                      │
├──────────────────────────┬──────────────────────────┤
│  Container: bd2-api      │  Container: bd2-ui       │
│  Port: 8000              │  Port: 8501              │
│  Image: python:3.11      │  Image: python:3.11      │
│  ┌────────────────────┐  │  ┌────────────────────┐  │
│  │ FastAPI Backend    │  │  │ Streamlit Frontend │  │
│  │ - SQL Parser       │  │  │ - Query Editor     │  │
│  │ - Executor         │  │  │ - Results Table    │  │
│  │ - 4 Indexes        │  │  │ - Metrics Display  │  │
│  └────────────────────┘  │  └────────────────────┘  │
└──────────────────────────┴──────────────────────────┘
           │                        │
           └────────┬───────────────┘
                    │
            ┌───────▼───────┐
            │  Shared Volumes│
            ├────────────────┤
            │  ./storage/    │ ← Datos persistentes
            │  ./data/       │ ← Dataset CSV
            └────────────────┘
```

## ✅ Checklist de Entrega

Para demostrar que tu proyecto funciona con Docker Compose:

- [ ] Clonar repo limpio en otra carpeta
- [ ] Ejecutar `docker compose up --build`
- [ ] Esperar ~5 minutos (primera vez)
- [ ] Abrir http://localhost:8501
- [ ] Verificar que hay 4 tablas cargadas
- [ ] Ejecutar queries de ejemplo
- [ ] Tomar screenshots para la demostración
- [ ] Ejecutar `docker compose down`
- [ ] Ejecutar `docker compose up` nuevamente
- [ ] Verificar que inicia en ~15 segundos (sin recargar datos)

## 📚 Referencias

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Streamlit Deployment](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)

## 🎉 Resultado Final

Después de `docker compose up --build`:

```
✅ API corriendo: http://localhost:8000/docs
✅ UI corriendo: http://localhost:8501
✅ 4 tablas cargadas: restaurants_seq, restaurants_isam, restaurants_hash, restaurants_bplustree
✅ 9,551 registros por tabla
✅ Índices construidos y listos para usar
✅ Queries funcionan inmediatamente
✅ Benchmarks disponibles
```

**¡Tu proyecto está listo para demostrar!** 🚀
