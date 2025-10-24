# 🚀 GUÍA COMPLETA: DESPLIEGUE EN PRODUCCIÓN

## 📋 Tabla de Contenidos

1. [Resumen General](#resumen-general)
2. [Paso 1: Preparar el Código](#paso-1-preparar-el-código)
3. [Paso 2: Subir a GitHub](#paso-2-subir-a-github)
4. [Paso 3: Desplegar Backend en Railway](#paso-3-desplegar-backend-en-railway)
5. [Paso 4: Migrar Datos](#paso-4-migrar-datos-de-sqlite-a-postgresql)
6. [Paso 5: Desplegar Frontend en Cloudflare](#paso-5-desplegar-frontend-en-cloudflare-pages)
7. [Paso 6: Configurar CORS](#paso-6-configurar-cors)
8. [Paso 7: Verificar Funcionamiento](#paso-7-verificar-funcionamiento)
9. [Solución de Problemas](#solución-de-problemas)

---

## Resumen General

### Arquitectura Final

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIOS EN INTERNET                      │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ Cloudflare Pages │            │  Railway Backend │
│   (Frontend)     │            │   (FastAPI)      │
│  tu-app.pages.dev│            │ tu-app.railway.app
└──────────────────┘            └────────┬─────────┘
                                         │
                                         ▼
                                ┌──────────────────┐
                                │   PostgreSQL     │
                                │   (Railway)      │
                                └──────────────────┘
```

### Costos

- **Cloudflare Pages**: Gratis ✅
- **Railway**: $5 crédito mensual gratis (suficiente para empezar)
- **Total**: $0 inicialmente

---

## PASO 1: Preparar el Código

### 1.1 Actualizar Frontend para Variables de Entorno

**Crear archivo: `frontend/src/config/api.js`**

```javascript
// Obtener URL del API desde variables de entorno
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const getApiUrl = (path = '') => {
  return `${API_BASE_URL}${path}`;
};

export const getFullUrl = (path) => {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${API_BASE_URL}${path}`;
};

export default API_BASE_URL;
```

**Actualizar: `frontend/src/services/api.js`**

Reemplaza:
```javascript
const API_URL = 'http://localhost:8000/api';
```

Con:
```javascript
import API_BASE_URL from '../config/api';
const API_URL = `${API_BASE_URL}/api`;
```

**Actualizar: `frontend/src/services/authService.js`**

Reemplaza:
```javascript
const API_URL = 'http://localhost:8000/api/auth';
```

Con:
```javascript
import API_BASE_URL from '../config/api';
const API_URL = `${API_BASE_URL}/api/auth`;
```

**Crear archivo: `frontend/.env.example`**

```env
VITE_API_URL=http://localhost:8000
```

**Crear archivo: `frontend/public/_redirects`**

```
/* /index.html 200
```

Este archivo es importante para que las rutas del frontend funcionen correctamente en Cloudflare Pages.

### 1.2 Actualizar Backend para Producción

**Actualizar: `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./inventory.db"
    
    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Frontend URL for CORS
    FRONTEND_URL: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"


settings = Settings()
```

**Actualizar: `backend/.env.example`**

```env
# ========== DATABASE ==========
# Para desarrollo (SQLite):
DATABASE_URL=sqlite:///./inventory.db

# Para producción (PostgreSQL en Railway):
# DATABASE_URL=postgresql://user:password@host:port/database

# ========== SECURITY ==========
# IMPORTANTE: Generar una clave segura en producción
# Comando: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ========== FRONTEND URL ==========
# Para desarrollo:
FRONTEND_URL=http://localhost:5173

# Para producción:
# FRONTEND_URL=https://tu-app.pages.dev

# ========== ENVIRONMENT ==========
ENVIRONMENT=development
```

**Crear: `backend/Procfile`**

```
web: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

**Crear: `backend/railway.json`**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Actualizar: `backend/requirements.txt`**

Agrega estas líneas al final:

```txt
gunicorn==21.2.0
```

### 1.3 Crear Script de Migración de Datos

**Crear: `backend/migrate_to_postgres.py`**

```python
"""
Script para migrar datos de SQLite a PostgreSQL
Ejecutar DESPUÉS de configurar PostgreSQL en Railway
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración
SQLITE_DB = "inventory.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("❌ ERROR: No se encontró DATABASE_URL en .env")
    exit(1)

print("🔄 Iniciando migración de SQLite a PostgreSQL...")
print(f"📁 SQLite: {SQLITE_DB}")
print(f"🐘 PostgreSQL: {POSTGRES_URL[:50]}...")

try:
    # Conectar a ambas bases de datos
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    postgres_conn = psycopg2.connect(POSTGRES_URL)
    postgres_cursor = postgres_conn.cursor()

    # Obtener lista de tablas
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    print(f"\n📋 Tablas encontradas: {len(tables)}")
    for table in tables:
        print(f"  - {table}")

    # Migrar cada tabla
    for table in tables:
        print(f"\n🔄 Migrando tabla: {table}")
        
        # Obtener datos de SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  ⚠️  Tabla vacía, saltando...")
            continue
        
        # Obtener nombres de columnas
        columns = [description[0] for description in sqlite_cursor.description]
        
        # Preparar datos para PostgreSQL
        data = [tuple(dict(row).values()) for row in rows]
        
        # Limpiar tabla en PostgreSQL
        try:
            postgres_cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            print(f"  🗑️  Tabla limpiada")
        except Exception as e:
            print(f"  ⚠️  No se pudo limpiar: {e}")
            postgres_conn.rollback()
        
        # Insertar datos
        try:
            columns_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))
            query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            
            execute_values(postgres_cursor, query, data, template=None, page_size=100)
            postgres_conn.commit()
            
            print(f"  ✅ {len(rows)} registros migrados")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            postgres_conn.rollback()

    # Cerrar conexiones
    sqlite_conn.close()
    postgres_conn.close()

    print("\n✅ ¡Migración completada!")

except Exception as e:
    print(f"\n❌ Error fatal: {e}")
    exit(1)
```

---

## PASO 2: Subir a GitHub

### 2.1 Inicializar Git

```bash
# Abre terminal en la carpeta del proyecto
cd "g:\Nueva carpeta (4)\Nueva carpeta45"

# Inicializar repositorio
git init

# Agregar todos los archivos
git add .

# Hacer commit inicial
git commit -m "Initial commit - Sistema de Gestión Empresarial SaaS"
```

### 2.2 Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. **Repository name**: `sistema-gestion-empresarial` (o el que prefieras)
3. **Description**: Sistema de gestión empresarial multi-tenant
4. **Visibility**: Privado (recomendado) o Público
5. **NO** inicialices con README, .gitignore o licencia
6. Click en "Create repository"

### 2.3 Subir Código

```bash
# Agregar remote (copia la URL de tu repositorio)
git remote add origin https://github.com/TU-USUARIO/TU-REPOSITORIO.git

# Cambiar rama a main
git branch -M main

# Subir código
git push -u origin main
```

---

## PASO 3: Desplegar Backend en Railway

### 3.1 Crear Cuenta en Railway

1. Ve a https://railway.app
2. Click en "Start Free"
3. Regístrate con GitHub
4. Autoriza Railway a acceder a tu GitHub

### 3.2 Crear Nuevo Proyecto

1. En el dashboard, click en "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Busca tu repositorio `sistema-gestion-empresarial`
4. Click en "Deploy"

Railway comenzará a construir automáticamente.

### 3.3 Agregar PostgreSQL

1. En tu proyecto de Railway, click en "+ New"
2. Selecciona "Database"
3. Selecciona "PostgreSQL"
4. Railway creará la base de datos automáticamente

**Importante**: Copia la `DATABASE_URL` que aparece en las variables de entorno. La necesitarás.

### 3.4 Configurar Variables de Entorno

En Railway, ve a tu proyecto → "Variables":

Agrega estas variables:

```env
DATABASE_URL=postgresql://... (Railway lo genera automáticamente)
SECRET_KEY=genera-una-clave-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=https://tu-app.pages.dev (lo configurarás después)
ENVIRONMENT=production
PORT=8000
```

**Para generar SECRET_KEY segura**, abre terminal y ejecuta:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia el resultado y pégalo en `SECRET_KEY`.

### 3.5 Configurar Build y Deploy

Railway debería detectar automáticamente tu `Procfile`. Verifica:

1. Ve a "Settings" → "Deploy"
2. **Root Directory**: `backend`
3. **Build Command**: Debe estar vacío (Railway lo detecta del Procfile)
4. **Start Command**: Debe estar vacío (Railway lo detecta del Procfile)

### 3.6 Esperar Despliegue

1. Railway desplegará automáticamente
2. Espera a que termine (5-10 minutos)
3. Cuando termine, verás una URL como: `https://tu-app.up.railway.app`
4. **Copia esta URL**, la necesitarás

---

## PASO 4: Migrar Datos de SQLite a PostgreSQL

### 4.1 Preparar Migración Local

1. Copia la `DATABASE_URL` de Railway
2. Abre `backend/.env`
3. Reemplaza `DATABASE_URL` con la URL de PostgreSQL de Railway:

```env
DATABASE_URL=postgresql://postgres:password@containers-us-west-xxx.railway.app:7432/railway
```

### 4.2 Ejecutar Migración

```bash
# Abre terminal en la carpeta backend
cd backend

# Activar entorno virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias si no las tienes
pip install psycopg2-binary python-dotenv

# Ejecutar script de migración
python migrate_to_postgres.py
```

Verás algo como:

```
🔄 Iniciando migración de SQLite a PostgreSQL...
📁 SQLite: inventory.db
🐘 PostgreSQL: postgresql://postgres:password@...

📋 Tablas encontradas: 15
  - users
  - products
  - sales
  - ...

🔄 Migrando tabla: users
  🗑️  Tabla limpiada
  ✅ 5 registros migrados

...

✅ ¡Migración completada!
```

### 4.3 Verificar Migración

1. Ve a Railway → PostgreSQL → "Data"
2. Verifica que todas las tablas tienen datos
3. Verifica que los usuarios, productos, ventas, etc. están presentes

---

## PASO 5: Desplegar Frontend en Cloudflare Pages

### 5.1 Crear Cuenta en Cloudflare

1. Ve a https://dash.cloudflare.com
2. Regístrate o inicia sesión
3. Ve a "Pages" en el menú lateral

### 5.2 Crear Nuevo Proyecto

1. Click en "Create a project"
2. Selecciona "Connect to Git"
3. Autoriza Cloudflare a acceder a tu GitHub
4. Selecciona tu repositorio `sistema-gestion-empresarial`

### 5.3 Configurar Build

Cloudflare te pedirá la configuración de build:

- **Framework preset**: Vite
- **Build command**: `npm run build`
- **Build output directory**: `dist`
- **Root directory**: `frontend`

### 5.4 Configurar Variables de Entorno

Antes de desplegar, ve a "Settings" → "Environment variables":

Agrega:

```env
VITE_API_URL=https://tu-app.up.railway.app
```

(Usa la URL de tu backend de Railway del Paso 3)

### 5.5 Desplegar

1. Click en "Save and Deploy"
2. Cloudflare construirá y desplegará tu frontend
3. Espera a que termine (2-5 minutos)
4. Cuando termine, verás una URL como: `https://tu-app.pages.dev`
5. **Copia esta URL**, la necesitarás

---

## PASO 6: Configurar CORS

### 6.1 Actualizar Variable en Railway

Ahora que tienes la URL de Cloudflare Pages, actualiza Railway:

1. Ve a Railway → Tu proyecto → "Variables"
2. Actualiza `FRONTEND_URL`:

```env
FRONTEND_URL=https://tu-app.pages.dev
```

### 6.2 Redesplegar Backend

1. Railway redesplegará automáticamente
2. Espera a que termine

---

## PASO 7: Verificar Funcionamiento

### 7.1 Probar Frontend

1. Abre tu URL de Cloudflare Pages: `https://tu-app.pages.dev`
2. Deberías ver la página de login
3. Intenta iniciar sesión con tus credenciales:
   - **Usuario**: `admin`
   - **Contraseña**: `admin123`

### 7.2 Verificar Datos

1. Después de iniciar sesión, deberías ver el dashboard
2. Verifica que puedes ver:
   - Productos
   - Clientes
   - Ventas
   - Cotizaciones
   - Alquileres
   - Todos los datos migrados

### 7.3 Probar API

1. Abre `https://tu-app.up.railway.app/docs`
2. Verifica que la documentación de la API funciona
3. Prueba algunos endpoints

### 7.4 Probar Creación de Datos

1. En el frontend, intenta crear un nuevo producto
2. Intenta crear un nuevo cliente
3. Intenta crear una nueva venta
4. Verifica que los datos se guardan correctamente

---

## Solución de Problemas

### ❌ Error: "Cannot GET /api/..."

**Causa**: El frontend no puede conectarse al backend.

**Solución**:
1. Verifica que `VITE_API_URL` en Cloudflare Pages esté correcto
2. Verifica que tu backend en Railway está corriendo
3. Abre `https://tu-app.up.railway.app/health` en el navegador
4. Deberías ver: `{"status":"ok"}`

### ❌ Error: CORS

**Causa**: El backend rechaza requests del frontend.

**Solución**:
1. Verifica que `FRONTEND_URL` en Railway esté configurada correctamente
2. Verifica que NO tenga `/` al final
3. Redesplega el backend en Railway

### ❌ Error: "Database connection failed"

**Causa**: El backend no puede conectarse a PostgreSQL.

**Solución**:
1. Verifica que `DATABASE_URL` en Railway esté configurada
2. Verifica que el formato sea correcto: `postgresql://user:pass@host:port/db`
3. Verifica en Railway → PostgreSQL → "Data" que la base de datos existe
4. Verifica los logs en Railway → "Deployments" → "View Logs"

### ❌ Error: "404 Not Found" en rutas del frontend

**Causa**: Las rutas del frontend no funcionan en Cloudflare Pages.

**Solución**:
1. Verifica que el archivo `_redirects` esté en `frontend/public/`
2. Contenido debe ser: `/* /index.html 200`
3. Redeploya en Cloudflare Pages

### ❌ Error: "Build failed" en Cloudflare Pages

**Causa**: El build del frontend falló.

**Solución**:
1. Verifica que `Build command` sea `npm run build`
2. Verifica que `Build output directory` sea `dist`
3. Verifica que `Root directory` sea `frontend`
4. Ve a "Deployments" → Click en el deployment → "View build log"
5. Lee el error y corrígelo

### ❌ Error: Login no funciona

**Causa**: Las credenciales no son correctas o los datos no se migraron.

**Solución**:
1. Verifica que los datos se migraron correctamente
2. Ve a Railway → PostgreSQL → "Data" → Tabla `user`
3. Verifica que existe un usuario con username `admin`
4. Si no existe, crea uno manualmente o vuelve a ejecutar `migrate_to_postgres.py`

---

## Checklist Final

Antes de considerar que está completo:

- [ ] Código actualizado para usar variables de entorno
- [ ] Código subido a GitHub
- [ ] Backend desplegado en Railway
- [ ] PostgreSQL configurado en Railway
- [ ] Datos migrados de SQLite a PostgreSQL
- [ ] Frontend desplegado en Cloudflare Pages
- [ ] Variables de entorno configuradas en ambos lados
- [ ] CORS configurado correctamente
- [ ] Login funciona
- [ ] Datos se muestran correctamente
- [ ] Se pueden crear nuevos registros
- [ ] Imágenes (logos/sellos) funcionan
- [ ] API documentation funciona

---

## URLs Finales

Después del despliegue, tendrás:

- **Frontend**: `https://tu-app.pages.dev`
- **Backend API**: `https://tu-app.up.railway.app`
- **Documentación API**: `https://tu-app.up.railway.app/docs`
- **PostgreSQL**: Gestionado por Railway (no accesible públicamente)

---

## Próximos Pasos (Opcional)

### Dominio Personalizado

**Para Frontend**:
1. Ve a Cloudflare Pages → Tu proyecto → "Custom domains"
2. Agrega tu dominio (ej: `app.tuempresa.com`)
3. Sigue las instrucciones para configurar DNS

**Para Backend**:
1. Ve a Railway → Tu proyecto → "Settings" → "Domains"
2. Agrega tu dominio (ej: `api.tuempresa.com`)
3. Configura el registro CNAME en tu DNS

### Backups Automáticos

1. Ve a Railway → PostgreSQL → "Backups"
2. Configura backups automáticos diarios

### Monitoreo

**Railway**:
- Ve a "Metrics" para ver uso de CPU, memoria, etc.

**Cloudflare**:
- Ve a "Analytics" para ver tráfico, requests, etc.

---

## Soporte

Si tienes problemas:

1. Revisa los logs en Railway
2. Revisa los logs de build en Cloudflare Pages
3. Abre la consola del navegador (F12) para ver errores
4. Verifica que todas las variables de entorno están configuradas

---

**¡Felicidades! Tu aplicación está en producción y accesible desde cualquier parte del mundo! 🚀**
