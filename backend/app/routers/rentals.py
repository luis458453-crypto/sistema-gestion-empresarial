from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models, schemas_extended as schemas
from ..crud_rentals import (
    get_rental, get_rentals, create_rental, update_rental, cancel_rental,
    check_overdue_rentals, get_rental_history, get_client_rental_history,
    get_active_rentals_report, add_rental_payment, update_rental_status_automatically
)

router = APIRouter(prefix="/api/rentals", tags=["rentals"])


@router.get("/", response_model=List[schemas.Rental])
def read_rentals(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene lista de alquileres con filtros opcionales"""
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
    
    rentals = get_rentals(
        db, skip=skip, limit=limit, client_id=client_id,
        product_id=product_id, status=status,
        start_date=parsed_start_date, end_date=parsed_end_date,
        organization_id=current_user.organization_id
    )
    return rentals


@router.get("/{rental_id}", response_model=schemas.Rental)
def read_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene un alquiler por ID"""
    rental = get_rental(db, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Alquiler no encontrado")
    return rental


@router.post("/", response_model=schemas.Rental, status_code=status.HTTP_201_CREATED)
def create_new_rental(
    rental: schemas.RentalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Crea un nuevo alquiler"""
    if current_user.role not in ["admin", "almacen", "vendedor"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para crear alquileres"
        )
    
    try:
        print(f"🔵 Creando alquiler con items: {rental.items}")
        result = create_rental(db, rental, current_user.id)
        print(f"✅ Alquiler creado: {result.rental_number}")
        return result
    except ValueError as e:
        print(f"❌ ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{rental_id}", response_model=schemas.Rental)
def update_existing_rental(
    rental_id: int,
    rental: schemas.RentalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza un alquiler existente"""
    if current_user.role not in ["admin", "almacen"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para actualizar alquileres"
        )
    
    db_rental = update_rental(db, rental_id, rental, current_user.id)
    if not db_rental:
        raise HTTPException(status_code=404, detail="Alquiler no encontrado")
    return db_rental


@router.post("/{rental_id}/cancel", response_model=schemas.Rental)
def cancel_existing_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cancela un alquiler y devuelve el stock"""
    if current_user.role not in ["admin", "almacen", "vendedor"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para cancelar alquileres"
        )
    
    try:
        return cancel_rental(db, rental_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/product/{product_id}/history", response_model=List[schemas.Rental])
def read_product_rental_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene el historial de alquileres de un producto"""
    return get_rental_history(db, product_id)


@router.get("/client/{client_id}/history", response_model=List[schemas.Rental])
def read_client_rental_history(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene el historial de alquileres de un cliente"""
    return get_client_rental_history(db, client_id)


@router.post("/check-overdue")
def check_overdue(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Verifica y marca alquileres vencidos"""
    if current_user.role not in ["admin", "almacen"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para esta acción"
        )
    
    count = check_overdue_rentals(db)
    return {"message": f"{count} alquileres marcados como vencidos"}


@router.get("/reports/active")
def get_active_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Genera reporte de alquileres activos"""
    if current_user.role not in ["admin", "almacen"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para ver reportes"
        )
    
    return get_active_rentals_report(db)


@router.post("/{rental_id}/payments", response_model=schemas.RentalPayment, status_code=status.HTTP_201_CREATED)
def add_payment_to_rental(
    rental_id: int,
    payment: schemas.RentalPaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Agrega un pago a un alquiler"""
    try:
        payment_result = add_rental_payment(db, rental_id, payment, current_user.id)
        return payment_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/update-status", response_model=dict)
def update_rental_statuses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza automáticamente el estado de alquileres vencidos"""
    try:
        updated_count = update_rental_status_automatically(db, current_user.organization_id)
        return {
            "message": f"Se actualizaron {updated_count} alquileres vencidos",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
