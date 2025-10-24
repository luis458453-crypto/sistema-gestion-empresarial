from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
# Usar modelos extendidos por defecto
from .. import schemas_extended as schemas
from .. import models_extended as models

from .. import crud, auth
from ..database import get_db

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.post("/movements", response_model=schemas.InventoryMovement)
def create_movement(
    movement: schemas.InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    try:
        db_movement = crud.create_inventory_movement(
            db=db,
            product_id=movement.product_id,
            user_id=current_user.id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            reason=movement.reason,
            organization_id=current_user.organization_id
        )
        if db_movement is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return db_movement
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/movements", response_model=List[schemas.InventoryMovement])
def read_movements(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    movements = crud.get_inventory_movements(
        db, 
        skip=skip, 
        limit=limit, 
        product_id=product_id,
        organization_id=current_user.organization_id
    )
    return movements


@router.get("/dashboard", response_model=schemas.DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    stats = crud.get_dashboard_stats(db)
    return stats
