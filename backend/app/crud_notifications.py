from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from . import models_extended as models
from . import schemas_extended as schemas


def get_notifications(
    db: Session, 
    organization_id: int, 
    user_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[models.Notification]:
    """Obtiene las notificaciones de una organización"""
    query = db.query(models.Notification).filter(
        and_(
            models.Notification.organization_id == organization_id,
            models.Notification.is_deleted == False
        )
    )
    
    if user_id:
        query = query.filter(models.Notification.user_id == user_id)
    
    return query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


def get_notification(db: Session, notification_id: int, organization_id: int) -> Optional[models.Notification]:
    """Obtiene una notificación específica"""
    return db.query(models.Notification).filter(
        and_(
            models.Notification.id == notification_id,
            models.Notification.organization_id == organization_id
        )
    ).first()


def create_notification(db: Session, notification: schemas.NotificationCreate, organization_id: int, user_id: Optional[int] = None) -> models.Notification:
    """Crea una nueva notificación"""
    db_notification = models.Notification(
        **notification.dict(),
        organization_id=organization_id,
        user_id=user_id
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def update_notification(db: Session, notification_id: int, notification_update: schemas.NotificationUpdate, organization_id: int) -> Optional[models.Notification]:
    """Actualiza una notificación"""
    db_notification = get_notification(db, notification_id, organization_id)
    if not db_notification:
        return None
    
    update_data = notification_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_notification, field, value)
    
    db.commit()
    db.refresh(db_notification)
    return db_notification


def mark_notification_as_read(db: Session, notification_id: int, organization_id: int) -> Optional[models.Notification]:
    """Marca una notificación como leída"""
    return update_notification(db, notification_id, schemas.NotificationUpdate(is_read=True), organization_id)


def mark_all_notifications_as_read(db: Session, organization_id: int, user_id: Optional[int] = None) -> int:
    """Marca todas las notificaciones como leídas"""
    query = db.query(models.Notification).filter(
        and_(
            models.Notification.organization_id == organization_id,
            models.Notification.is_deleted == False,
            models.Notification.is_read == False
        )
    )
    
    if user_id:
        query = query.filter(models.Notification.user_id == user_id)
    
    updated_count = query.update({"is_read": True})
    db.commit()
    return updated_count


def delete_notification(db: Session, notification_id: int, organization_id: int) -> bool:
    """Elimina una notificación (marca como eliminada)"""
    db_notification = get_notification(db, notification_id, organization_id)
    if not db_notification:
        return False
    
    db_notification.is_deleted = True
    db.commit()
    return True


def get_or_create_notification(db: Session, notification_key: str, organization_id: int, notification_data: schemas.NotificationCreate) -> models.Notification:
    """Obtiene una notificación existente o crea una nueva basada en la clave"""
    # Buscar notificación existente que NO esté eliminada
    # Las notificaciones leídas SÍ se reutilizan (solo se actualiza el mensaje)
    existing = db.query(models.Notification).filter(
        and_(
            models.Notification.notification_key == notification_key,
            models.Notification.organization_id == organization_id,
            models.Notification.is_deleted == False  # Solo verificar que no esté eliminada
        )
    ).first()
    
    if existing:
        # Actualizar el mensaje y la fecha para reflejar datos actuales
        existing.message = notification_data.message
        existing.title = notification_data.title
        # NO cambiar is_read - mantener el estado actual
        db.commit()
        db.refresh(existing)
        return existing
    
    # Si no existe o fue eliminada, crear una nueva
    return create_notification(db, notification_data, organization_id)


def get_unread_count(db: Session, organization_id: int, user_id: Optional[int] = None) -> int:
    """Obtiene el número de notificaciones no leídas"""
    query = db.query(models.Notification).filter(
        and_(
            models.Notification.organization_id == organization_id,
            models.Notification.is_deleted == False,
            models.Notification.is_read == False
        )
    )
    
    if user_id:
        query = query.filter(models.Notification.user_id == user_id)
    
    return query.count()


