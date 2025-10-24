from sqlalchemy.orm import Session
from typing import List
from . import models_extended as models
from . import schemas_extended as schemas
from .crud_notifications import get_or_create_notification


def generate_dashboard_notifications(db: Session, organization_id: int, stats: dict) -> List[models.Notification]:
    """Genera notificaciones basadas en las estadísticas del dashboard"""
    notifications = []
    
    print(f"DEBUG: Generando notificaciones con stats: {stats}")
    
    # 1. Stock Bajo - ALERTA CRÍTICA
    low_stock_count = stats.get('low_stock_products', 0)
    print(f"DEBUG: low_stock_products = {low_stock_count}")
    
    if low_stock_count > 0:
        notification_data = schemas.NotificationCreate(
            type='warning',
            title='⚠️ Stock Bajo',
            message=f"{low_stock_count} producto{'s' if low_stock_count > 1 else ''} {'tienen' if low_stock_count > 1 else 'tiene'} stock bajo. Revisa tu inventario.",
            notification_key='stock-bajo'
        )
        notification = get_or_create_notification(db, 'stock-bajo', organization_id, notification_data)
        notifications.append(notification)
        print(f"DEBUG: Notificación de stock bajo creada: {notification.id}")
    
    # 2. Alquileres Próximos a Vencer - ALERTA CRÍTICA
    overdue_count = stats.get('overdue_rentals', 0)
    if overdue_count > 0:
        notification_data = schemas.NotificationCreate(
            type='error',
            title='📅 Alquileres Próximos a Vencer',
            message=f"{overdue_count} alquiler{'es' if overdue_count > 1 else ''} {'vencen' if overdue_count > 1 else 'vence'} esta semana. Contacta a los clientes.",
            notification_key='alquileres-vencidos'
        )
        notification = get_or_create_notification(db, 'alquileres-vencidos', organization_id, notification_data)
        notifications.append(notification)
        print(f"DEBUG: Notificación de alquileres vencidos creada: {notification.id}")
    
    # Las demás notificaciones están disponibles en el Dashboard
    # No se generan aquí para evitar saturación
    
    return notifications
