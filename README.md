# 🏢 Sistema de Gestión Empresarial SaaS

Sistema completo de gestión empresarial multi-tenant con FastAPI y React. Incluye gestión de inventario, ventas, cotizaciones, alquileres, clientes y más.

## 🚀 Características Principales

### **Sistema Multi-Tenant (SaaS)**
- ✅ Organizaciones independientes con datos aislados
- ✅ Registro público de nuevas organizaciones
- ✅ Panel de administración para super admin
- ✅ Gestión de usuarios por organización
- ✅ Personalización (logo, colores, módulos)

### **Módulos de Negocio**
- ✅ **Ventas**: Gestión completa con facturación y pagos
- ✅ **Alquileres**: Control de equipos rentados con fechas y depósitos
- ✅ **Cotizaciones**: Creación y seguimiento de presupuestos
- ✅ **Clientes**: Base de datos de clientes con historial
- ✅ **Inventario**: Control de stock con alertas
- ✅ **Productos**: Gestión de productos para venta y/o alquiler
- ✅ **Dashboard**: Estadísticas y métricas en tiempo real
- ✅ **Reportes**: Resumen de negocio con análisis detallado

### **Seguridad y Autenticación**
- ✅ Autenticación JWT
- ✅ Roles de usuario (admin, vendedor, almacén, empleado)
- ✅ Filtrado automático por organización
- ✅ Protección de rutas en frontend y backend

## 📋 Requisitos

- **Python** 3.8+
- **Node.js** 16+
- **npm** o **yarn**

## 🛠️ Instalación Rápida

### **1. Clonar el Repositorio**
```bash
git clone <repository-url>
cd "Nueva carpeta"
```

### **2. Backend (FastAPI)**

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env
copy .env.example .env

# Inicializar base de datos
python init_db_final.py

# Iniciar servidor
uvicorn app.main:app --reload
```

El backend estará disponible en: **http://localhost:8000**  
Documentación API: **http://localhost:8000/docs**

### **3. Frontend (React)**

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en: **http://localhost:5173**

## 👤 Credenciales Iniciales

Después de ejecutar `init_db_final.py`, se creará un **super admin**:

- **Usuario**: `superadmin`
- **Contraseña**: `admin123`

## 📁 Estructura del Proyecto

```
├── backend/
│   ├── app/
│   │   ├── routers/          # Endpoints de la API
│   │   ├── models_extended.py    # Modelos de base de datos
│   │   ├── models_organization.py # Modelos SaaS
│   │   ├── schemas_extended.py    # Esquemas Pydantic
│   │   ├── crud*.py              # Operaciones CRUD
│   │   ├── auth.py               # Autenticación JWT
│   │   └── main.py               # Aplicación principal
│   ├── init_db_final.py      # Inicialización de BD
│   └── requirements.txt      # Dependencias Python
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   ├── pages/            # Páginas de la aplicación
│   │   ├── services/         # Servicios API
│   │   ├── hooks/            # Hooks personalizados
│   │   ├── store/            # Estado global (Zustand)
│   │   └── contexts/         # Context API
│   └── package.json          # Dependencias Node
│
├── README.md                 # Este archivo
└── ARQUITECTURA.md          # Documentación técnica
```

## 🔑 Endpoints Principales

### **Autenticación**
- `POST /api/auth/login` - Inicio de sesión
- `POST /api/auth/register` - Registro de usuario
- `GET /api/auth/me` - Usuario actual

### **Organizaciones (SaaS)**
- `POST /api/organizations/register` - Registro público de organización
- `GET /api/organizations/me` - Organización actual
- `GET /api/organizations/admin/all` - Todas las organizaciones (super admin)

### **Productos**
- `GET /api/products` - Listar productos
- `POST /api/products` - Crear producto
- `PUT /api/products/{id}` - Actualizar producto
- `DELETE /api/products/{id}` - Eliminar producto

### **Ventas**
- `GET /api/sales` - Listar ventas
- `POST /api/sales` - Crear venta
- `POST /api/sales/payments` - Registrar pago

### **Alquileres**
- `GET /api/rentals` - Listar alquileres
- `POST /api/rentals` - Crear alquiler
- `PUT /api/rentals/{id}/return` - Devolver equipo

### **Dashboard**
- `GET /api/dashboard/stats` - Estadísticas generales
- `GET /api/dashboard/sales-chart` - Gráfico de ventas
- `GET /api/summary/business-overview` - Resumen de negocio

## 🎨 Tecnologías Utilizadas

### **Backend**
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **Pydantic** - Validación de datos
- **Python-Jose** - JWT tokens
- **Passlib** - Hash de contraseñas
- **SQLite/PostgreSQL** - Base de datos

### **Frontend**
- **React 18** - Biblioteca UI
- **Vite** - Build tool
- **TailwindCSS** - Framework CSS
- **Lucide React** - Iconos
- **Zustand** - Gestión de estado
- **Axios** - Cliente HTTP
- **React Router** - Enrutamiento

## 🔒 Seguridad Multi-Tenant

El sistema implementa aislamiento de datos por organización:

1. **Filtrado Automático**: Todas las queries filtran por `organization_id`
2. **Validación de Acceso**: Los usuarios solo pueden acceder a datos de su organización
3. **Super Admin**: Puede gestionar todas las organizaciones
4. **Tokens JWT**: Incluyen información de la organización

## 📊 Funcionalidades Destacadas

### **Dashboard Profesional**
- Métricas en tiempo real
- Gráficos interactivos
- Selector de fechas personalizado
- Exportación a CSV/PDF
- Configuración de metas

### **Gestión de Productos**
- Productos para venta, alquiler o ambos
- Control de stock y stock disponible
- Alertas de stock bajo
- Categorías y proveedores
- Imágenes y códigos de barras

### **Sistema de Ventas**
- Facturación completa
- Múltiples métodos de pago
- Pagos parciales
- Conversión desde cotizaciones
- Historial de pagos

### **Alquileres de Equipos**
- Gestión de fechas de inicio/fin
- Control de depósitos
- Estado de equipos (salida/entrada)
- Renovaciones
- Pagos de alquiler

## 🚀 Despliegue en Producción

### **Backend**
1. Configurar base de datos PostgreSQL
2. Actualizar variables de entorno en `.env`
3. Ejecutar migraciones
4. Desplegar en Railway, Heroku o DigitalOcean

### **Frontend**
1. Construir: `npm run build`
2. Desplegar en Vercel, Netlify o similar
3. Configurar variable de entorno `VITE_API_URL`

## 📝 Cambios Recientes (Refactorización)

### **✅ Correcciones Implementadas**

1. **Eliminados archivos duplicados**:
   - 15+ scripts de inicialización obsoletos
   - 9 versiones duplicadas de componentes
   - 60+ archivos de documentación redundantes

2. **Seguridad mejorada**:
   - Filtrado consistente por organización en todos los CRUD
   - Eliminados fallbacks peligrosos en dashboard
   - Validación de acceso mejorada

3. **Código limpio**:
   - Eliminado `models.py` antiguo
   - Consolidadas importaciones a `models_extended.py`
   - Dependencias no usadas eliminadas

4. **Mejor mantenibilidad**:
   - Documentación consolidada
   - Estructura más clara
   - Menos confusión en el código

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 📧 Soporte

Para soporte o preguntas, abre un issue en el repositorio.

---

**Desarrollado con ❤️ usando FastAPI y React**
