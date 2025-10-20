# 📋 QUERIES PARA PROBAR EN LA UI

# Copia y pega estas queries en http://localhost:8501

## 1️⃣ CREAR TABLA CON SEQUENTIAL INDEX

CREATE TABLE restaurants_seq USING sequential

## 2️⃣ CARGAR DATOS DE KAGGLE (100 restaurantes reales)

LOAD restaurants_seq FROM 'data/kaggle_Dataset \_100.csv'

## 3️⃣ BUSCAR RESTAURANTE POR ID

SELECT \* FROM restaurants_seq WHERE Restaurant ID = 6317637

## 4️⃣ BUSCAR POR CIUDAD

SELECT \* FROM restaurants_seq WHERE City = 'Makati City'

## 5️⃣ BUSCAR POR RATING (rango)

SELECT \* FROM restaurants_seq WHERE Aggregate rating BETWEEN 4.0 AND 5.0

---

## 🚀 AHORA CON ISAM (más rápido)

## 6️⃣ CREAR TABLA CON ISAM INDEX

CREATE TABLE restaurants_isam USING isam

## 7️⃣ CARGAR DATOS

LOAD restaurants_isam FROM 'data/kaggle_Dataset \_100.csv'

## 8️⃣ BUSCAR RESTAURANTE POR ID (nota la velocidad)

SELECT \* FROM restaurants_isam WHERE Restaurant ID = 6317637

## 9️⃣ BUSCAR POR RATING (compara I/O con sequential)

SELECT \* FROM restaurants_isam WHERE Aggregate rating BETWEEN 4.0 AND 5.0

---

## 📊 COMPARACIÓN

# Ejecuta las queries #5 y #9 y compara:

# - Tiempo de ejecución

# - Disk Reads / Disk Writes

# ISAM debería ser mucho más rápido!

---

## 🔍 DATOS DISPONIBLES

# El dataset de Kaggle tiene estas columnas:

# - Restaurant ID (único)

# - Restaurant Name

# - City

# - Cuisines

# - Aggregate rating

# - Price range

# - Latitude, Longitude

# - Y más...

## 💡 QUERIES ADICIONALES PARA PROBAR

# Buscar restaurantes con reserva de mesa

SELECT \* FROM restaurants_seq WHERE Has Table booking = 'Yes'

# Buscar restaurantes baratos (price range = 1)

SELECT \* FROM restaurants_seq WHERE Price range = 1

# Buscar restaurantes con entrega online

SELECT \* FROM restaurants_seq WHERE Has Online delivery = 'Yes'
