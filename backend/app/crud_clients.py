from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from . import models_extended as models, schemas_extended as schemas


def get_client(db: Session, client_id: int):
    return db.query(models.Client).filter(models.Client.id == client_id).first()


def get_client_by_rnc(db: Session, rnc: str):
    return db.query(models.Client).filter(models.Client.rnc == rnc).first()


def get_clients(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None, organization_id: Optional[int] = None):
    query = db.query(models.Client)
    
    # Filtrar por organización
    if organization_id:
        query = query.filter(models.Client.organization_id == organization_id)
    
    if search:
        query = query.filter(
            or_(
                models.Client.name.contains(search),
                models.Client.rnc.contains(search),
                models.Client.email.contains(search),
                models.Client.phone.contains(search)
            )
        )
    
    if status:
        query = query.filter(models.Client.status == status)
    
    return query.order_by(models.Client.created_at.desc()).offset(skip).limit(limit).all()


def create_client(db: Session, client: schemas.ClientCreate, organization_id: int):
    # Validar que no exista un cliente con el mismo email en la organización
    if client.email:
        existing_email = db.query(models.Client).filter(
            models.Client.email == client.email,
            models.Client.organization_id == organization_id
        ).first()
        if existing_email:
            raise ValueError(f"Ya existe un cliente con el correo electrónico: {client.email}")
    
    # Validar que no exista un cliente con el mismo RNC/Cédula en la organización
    if client.rnc:
        existing_rnc = db.query(models.Client).filter(
            models.Client.rnc == client.rnc,
            models.Client.organization_id == organization_id
        ).first()
        if existing_rnc:
            raise ValueError(f"Ya existe un cliente con el RNC/Cédula: {client.rnc}")
    
    client_data = client.model_dump()
    client_data['organization_id'] = organization_id
    db_client = models.Client(**client_data)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def update_client(db: Session, client_id: int, client: schemas.ClientUpdate):
    db_client = get_client(db, client_id)
    if db_client:
        update_data = client.model_dump(exclude_unset=True)
        
        # Validar email si se está actualizando
        if 'email' in update_data and update_data['email']:
            existing_email = db.query(models.Client).filter(
                models.Client.email == update_data['email'],
                models.Client.organization_id == db_client.organization_id,
                models.Client.id != client_id  # Excluir el cliente actual
            ).first()
            if existing_email:
                raise ValueError(f"Ya existe otro cliente con el correo electrónico: {update_data['email']}")
        
        # Validar RNC/Cédula si se está actualizando
        if 'rnc' in update_data and update_data['rnc']:
            existing_rnc = db.query(models.Client).filter(
                models.Client.rnc == update_data['rnc'],
                models.Client.organization_id == db_client.organization_id,
                models.Client.id != client_id  # Excluir el cliente actual
            ).first()
            if existing_rnc:
                raise ValueError(f"Ya existe otro cliente con el RNC/Cédula: {update_data['rnc']}")
        
        for field, value in update_data.items():
            setattr(db_client, field, value)
        db.commit()
        db.refresh(db_client)
    return db_client


def delete_client(db: Session, client_id: int):
    db_client = get_client(db, client_id)
    if db_client:
        db.delete(db_client)
        db.commit()
    return db_client


def get_client_stats(db: Session, client_id: int):
    """Obtiene estadísticas de un cliente"""
    client = get_client(db, client_id)
    if not client:
        return None
    
    total_quotations = db.query(func.count(models.Quotation.id)).filter(
        models.Quotation.client_id == client_id
    ).scalar()
    
    total_sales = db.query(func.count(models.Sale.id)).filter(
        models.Sale.client_id == client_id
    ).scalar()
    
    total_spent = db.query(func.sum(models.Sale.total)).filter(
        models.Sale.client_id == client_id,
        models.Sale.status == "completada"
    ).scalar() or 0
    
    pending_balance = db.query(func.sum(models.Sale.balance)).filter(
        models.Sale.client_id == client_id,
        models.Sale.balance > 0
    ).scalar() or 0
    
    active_rentals = db.query(func.count(models.Rental.id)).filter(
        models.Rental.client_id == client_id,
        models.Rental.status == "activo"
    ).scalar()
    
    return {
        "client": client,
        "total_quotations": total_quotations,
        "total_sales": total_sales,
        "total_spent": round(total_spent, 2),
        "pending_balance": round(pending_balance, 2),
        "active_rentals": active_rentals
    }
