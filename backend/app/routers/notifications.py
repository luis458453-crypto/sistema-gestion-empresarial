from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models, schemas_extended as schemas
from ..crud_notifications import (
    get_notifications, get_notification, create_notification, update_notification,
    mark_notification_as_read, mark_all_notifications_as_read, delete_notification,
    get_unread_count
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=List[schemas.Notification])
def read_notifications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene las notificaciones del usuario/organización"""
    print(f"DEBUG: read_notifications called for org_id={current_user.organization_id}, user_id={current_user.id}")
    
    # Generar notificaciones automáticamente basadas en datos actuales
    from ..crud_notification_generator import generate_dashboard_notifications
    from ..crud_dashboard import get_dashboard_stats
    
    # Obtener estadísticas actuales y generar notificaciones
    stats = get_dashboard_stats(db, current_user.organization_id)
    print(f"DEBUG: Stats obtenidas: {stats}")
    
    generated = generate_dashboard_notifications(db, current_user.organization_id, stats)
    print(f"DEBUG: Notificaciones generadas: {len(generated)}")
    
    # Obtener notificaciones SIN filtrar por user_id (son a nivel de organización)
    notifications = get_notifications(db, current_user.organization_id, None, skip, limit)
    print(f"DEBUG: Notificaciones retornadas: {len(notifications)}")
    
    return notifications


@router.get("/unread-count")
def get_unread_notifications_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene el número de notificaciones no leídas"""
    # SIN filtrar por user_id (son a nivel de organización)
    count = get_unread_count(db, current_user.organization_id, None)
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=schemas.Notification)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene una notificación específica"""
    notification = get_notification(db, notification_id, current_user.organization_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notification


@router.post("/", response_model=schemas.Notification)
def create_new_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Crea una nueva notificación"""
    return create_notification(db, notification, current_user.organization_id, current_user.id)


@router.put("/{notification_id}", response_model=schemas.Notification)
def update_existing_notification(
    notification_id: int,
    notification_update: schemas.NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza una notificación"""
    notification = update_notification(db, notification_id, notification_update, current_user.organization_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notification


@router.put("/{notification_id}/read", response_model=schemas.Notification)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Marca una notificación como leída"""
    notification = mark_notification_as_read(db, notification_id, current_user.organization_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notification


@router.put("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Marca todas las notificaciones como leídas"""
    # SIN filtrar por user_id (son a nivel de organización)
    updated_count = mark_all_notifications_as_read(db, current_user.organization_id, None)
    return {"message": f"Se marcaron {updated_count} notificaciones como leídas"}


@router.delete("/{notification_id}")
def delete_existing_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elimina una notificación"""
    success = delete_notification(db, notification_id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"message": "Notificación eliminada correctamente"}


@router.post("/generate-test")
def generate_test_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Genera notificaciones de prueba"""
    from ..crud_notification_generator import generate_dashboard_notifications
    from ..crud_dashboard import get_dashboard_stats
    
    # Obtener estadísticas actuales
    stats = get_dashboard_stats(db, current_user.organization_id)
    
    # Generar notificaciones basadas en las estadísticas
    notifications = generate_dashboard_notifications(db, current_user.organization_id, stats)
    
    return {
        "message": f"Se generaron {len(notifications)} notificaciones",
        "notifications": len(notifications)
    }
