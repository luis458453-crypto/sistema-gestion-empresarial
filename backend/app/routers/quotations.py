from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models, schemas_extended as schemas
from ..crud_quotations import (
    get_quotation, get_quotations, create_quotation, update_quotation,
    delete_quotation, convert_quotation_to_sale, convert_quotation_to_rental, check_expired_quotations
)

router = APIRouter(prefix="/api/quotations", tags=["quotations"])


@router.get("/", response_model=List[schemas.Quotation])
def read_quotations(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene lista de cotizaciones con filtros opcionales"""
    # Convertir strings de fecha a datetime si existen y no están vacíos
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date and start_date.strip():
        try:
            parsed_start_date = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            pass
    
    if end_date and end_date.strip():
        try:
            parsed_end_date = datetime.strptime(end_date, '%Y-%m-%d')
            parsed_end_date = parsed_end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    quotations = get_quotations(
        db, skip=skip, limit=limit, client_id=client_id,
        status=status, start_date=parsed_start_date, end_date=parsed_end_date,
        organization_id=current_user.organization_id
    )
    return quotations


@router.get("/{quotation_id}/can-edit")
def check_can_edit_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Verifica si una cotización puede ser editada"""
    from ..crud_quotations import can_edit_quotation
    
    quotation = get_quotation(db, quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    can_edit = can_edit_quotation(quotation)
    
    return {
        "can_edit": can_edit,
        "reason": None if can_edit else (
            "Convertida a venta" if quotation.sale else "Convertida a alquiler"
        )
    }


@router.get("/{quotation_id}", response_model=schemas.Quotation)
def read_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene una cotización por ID"""
    quotation = get_quotation(db, quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return quotation


@router.post("/", response_model=schemas.Quotation, status_code=status.HTTP_201_CREATED)
def create_new_quotation(
    quotation: schemas.QuotationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Crea una nueva cotización"""
    try:
        return create_quotation(db, quotation, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{quotation_id}", response_model=schemas.Quotation)
def update_existing_quotation(
    quotation_id: int,
    quotation: schemas.QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza una cotización existente (solo si no ha sido convertida a venta o alquiler)"""
    try:
        db_quotation = update_quotation(db, quotation_id, quotation)
        if not db_quotation:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return db_quotation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{quotation_id}/status", response_model=schemas.Quotation)
def update_quotation_status(
    quotation_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza el estado de una cotización (pendiente, aceptada, rechazada)"""
    if status not in ["pendiente", "aceptada", "rechazada"]:
        raise HTTPException(
            status_code=400, 
            detail="Estado inválido. Debe ser: pendiente, aceptada o rechazada"
        )
    
    db_quotation = get_quotation(db, quotation_id)
    if not db_quotation:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    
    # Verificar que la cotización pertenece a la organización del usuario
    if db_quotation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta cotización")
    
    db_quotation.status = status
    db.commit()
    db.refresh(db_quotation)
    
    return db_quotation


@router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elimina una cotización (solo si no ha sido convertida a venta o alquiler)"""
    if current_user.role not in ["admin", "vendedor"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para eliminar cotizaciones"
        )
    
    try:
        quotation = delete_quotation(db, quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{quotation_id}/convert-to-sale", response_model=schemas.Sale)
def convert_to_sale(
    quotation_id: int,
    payment_method: str = Query(..., description="Método de pago"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Convierte una cotización en venta"""
    try:
        sale = convert_quotation_to_sale(db, quotation_id, current_user.id, payment_method)
        if not sale:
            raise HTTPException(
                status_code=400,
                detail="No se puede convertir esta cotización. Debe estar en estado 'aceptada'"
            )
        return sale
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{quotation_id}/convert-to-rental", response_model=schemas.Rental)
def convert_to_rental(
    quotation_id: int,
    rental_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Convierte una cotización de tipo alquiler en un alquiler
    
    rental_data debe contener:
    - start_date: fecha de inicio (datetime)
    - end_date: fecha de fin (datetime)
    - rental_period: periodo de alquiler (daily, weekly, monthly)
    - deposit: depósito inicial (float)
    - payment_method: método de pago (str)
    - condition_out: condición al salir (str, opcional)
    """
    try:
        # Convertir fechas de string a datetime si es necesario
        if isinstance(rental_data.get('start_date'), str):
            rental_data['start_date'] = datetime.fromisoformat(rental_data['start_date'].replace('Z', '+00:00'))
        if isinstance(rental_data.get('end_date'), str):
            rental_data['end_date'] = datetime.fromisoformat(rental_data['end_date'].replace('Z', '+00:00'))
        
        rental = convert_quotation_to_rental(db, quotation_id, current_user.id, rental_data)
        if not rental:
            raise HTTPException(
                status_code=400,
                detail="No se puede convertir esta cotización. Debe estar en estado 'aceptada' y ser de tipo 'alquiler'"
            )
        return rental
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-expired")
def check_expired(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Verifica y marca cotizaciones vencidas"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para esta acción"
        )
    
    count = check_expired_quotations(db)
    return {"message": f"{count} cotizaciones marcadas como vencidas"}
