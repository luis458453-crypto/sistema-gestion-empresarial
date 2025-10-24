from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models, schemas_extended as schemas
from ..crud_dashboard import (
    get_dashboard_stats, get_sales_chart_data, get_rentals_chart_data, get_top_products,
    get_top_clients, get_recent_activities
)
from ..crud_notification_generator import generate_dashboard_notifications

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def read_dashboard_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene todas las estadísticas del dashboard para la organización del usuario"""
    # Super admins (sin organization_id) ven datos globales (None)
    # Usuarios normales solo ven datos de su organización
    org_id = current_user.organization_id
    
    stats = get_dashboard_stats(db, org_id, start_date, end_date)
    
    # Generar notificaciones basadas en las estadísticas
    if org_id:
        generate_dashboard_notifications(db, org_id, stats)
    
    return stats


@router.get("/sales-chart")
def read_sales_chart(
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene datos del gráfico de ventas para la organización del usuario"""
    org_id = current_user.organization_id
    
    return {
        "data": get_sales_chart_data(db, org_id, days, start_date, end_date),
        "period": f"{days} días"
    }


@router.get("/rentals-chart")
def read_rentals_chart(
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene datos del gráfico de alquileres para la organización del usuario"""
    org_id = current_user.organization_id
    
    return {
        "data": get_rentals_chart_data(db, org_id, days, start_date, end_date),
        "period": f"{days} días"
    }


@router.get("/top-products")
def read_top_products(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene los productos más vendidos de la organización del usuario"""
    org_id = current_user.organization_id
    return get_top_products(db, org_id, limit)


@router.get("/top-clients")
def read_top_clients(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene los clientes que más compran de la organización del usuario"""
    org_id = current_user.organization_id
    return get_top_clients(db, org_id, limit)


@router.get("/recent-activities")
def read_recent_activities(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene actividades recientes de la organización del usuario"""
    org_id = current_user.organization_id
    return get_recent_activities(db, org_id, limit)