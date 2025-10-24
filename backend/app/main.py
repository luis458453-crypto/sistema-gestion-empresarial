from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .database import engine, Base
from .routers import auth, products, categories, suppliers, inventory
from .routers import clients, quotations, sales, rentals, dashboard, organizations, summary, notifications, failures

# Importar modelos
from . import models_extended
from . import models_organization

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión Empresarial",
    description="API completa para gestión empresarial: inventario, ventas, cotizaciones, alquileres y más",
    version="2.0.0"
)

# Configurar CORS - Permitir frontend en producción y desarrollo
import os
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174", 
    "http://localhost:3000",
    FRONTEND_URL,
    "https://*.pages.dev",  # Cloudflare Pages preview
]

# Si hay una URL de frontend específica, agregarla
if FRONTEND_URL and FRONTEND_URL not in allowed_origins:
    allowed_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Incluir routers (ya tienen el prefijo /api en su definición)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(suppliers.router)
app.include_router(inventory.router)

# Nuevos routers empresariales
app.include_router(clients.router)
app.include_router(quotations.router)
app.include_router(sales.router)
app.include_router(rentals.router)
app.include_router(dashboard.router)

# Router SaaS Multi-tenant
app.include_router(organizations.router)

# Router de resumen y estadísticas
app.include_router(summary.router)

# Router de notificaciones
app.include_router(notifications.router)

# Router de fallas del sistema
app.include_router(failures.router)

# Crear directorio static si no existe
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# Montar archivos estáticos para servir logos
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return {
        "message": "Bienvenido al Sistema de Gestión Empresarial",
        "version": "2.0.0",
        "docs": "/docs",
        "features": [
            "Gestión de Inventario",
            "Cotizaciones",
            "Ventas y Facturación",
            "Alquileres de Equipos",
            "Gestión de Clientes",
            "Reportes y Análisis",
            "Control de Roles"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
