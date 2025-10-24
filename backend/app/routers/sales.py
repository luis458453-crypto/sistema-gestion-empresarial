from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models, schemas_extended as schemas
from ..crud_sales import (
    get_sale, get_sales, create_sale, update_sale,
    add_payment, get_sales_report
)

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("/", response_model=List[schemas.Sale])
def read_sales(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene lista de ventas con filtros opcionales"""
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
            # Incluir todo el día final
            parsed_end_date = datetime.strptime(end_date, '%Y-%m-%d')
            parsed_end_date = parsed_end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    sales = get_sales(
        db, skip=skip, limit=limit, client_id=client_id,
        status=status, start_date=parsed_start_date, end_date=parsed_end_date,
        organization_id=current_user.organization_id
    )
    return sales


@router.get("/{sale_id}", response_model=schemas.Sale)
def read_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene una venta por ID"""
    sale = get_sale(db, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return sale


@router.post("/", response_model=schemas.Sale, status_code=status.HTTP_201_CREATED)
def create_new_sale(
    sale: schemas.SaleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Crea una nueva venta"""
    try:
        print(f"Creando venta para usuario {current_user.id}, organización {current_user.organization_id}")
        print(f"Datos de la venta: {sale.model_dump()}")
        result = create_sale(db, sale, current_user.id)
        print(f"Venta creada exitosamente: {result.id}")
        return result
    except ValueError as e:
        print(f"Error de validación: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{sale_id}", response_model=schemas.Sale)
def update_existing_sale(
    sale_id: int,
    sale: schemas.SaleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza una venta existente"""
    db_sale = update_sale(db, sale_id, sale)
    if not db_sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return db_sale


@router.post("/payments", response_model=schemas.Payment, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Registra un pago para una venta"""
    db_payment = add_payment(db, payment)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return db_payment


@router.patch("/{sale_id}/status", response_model=schemas.Sale)
def update_sale_status(
    sale_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza el estado de una venta"""
    sale = get_sale(db, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    # Verificar que la venta pertenece a la organización del usuario
    if sale.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta venta")
    
    new_status = status_data.get('status')
    paid_amount = status_data.get('paid_amount', sale.paid_amount)
    
    if new_status not in ['completada', 'parcial', 'pendiente_pago', 'cancelada']:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    # Actualizar estado y monto pagado
    sale.status = new_status
    
    # Si se cancela la venta, balance = 0
    if new_status == 'cancelada':
        sale.paid_amount = 0
        sale.balance = 0
    else:
        sale.paid_amount = paid_amount
        sale.balance = sale.total - paid_amount
    
    db.commit()
    db.refresh(sale)
    return sale


@router.get("/reports/summary")
def get_report(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Genera reporte de ventas"""
    if current_user.role not in ["admin", "vendedor"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para ver reportes"
        )
    
    return get_sales_report(db, start_date, end_date)
