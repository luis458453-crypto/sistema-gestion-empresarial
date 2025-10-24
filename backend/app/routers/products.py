from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
# Intentar importar modelos extendidos, si no, usar los básicos
try:
    from .. import schemas_extended as schemas
    from .. import models_extended as models
    USE_EXTENDED = True
except ImportError:
    from .. import schemas, models
    USE_EXTENDED = False

from .. import crud, auth
from ..database import get_db

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=List[schemas.Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    product_type: Optional[str] = None,
    stock_available_gt: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    products = crud.get_products(
        db, 
        skip=skip, 
        limit=limit, 
        search=search, 
        organization_id=current_user.organization_id,
        product_type=product_type,
        stock_available_gt=stock_available_gt
    )
    return products


@router.get("/low-stock", response_model=List[schemas.LowStockAlert])
def read_low_stock_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    products = crud.get_low_stock_products(db)
    alerts = []
    for product in products:
        alerts.append({
            "product_id": product.id,
            "sku": product.sku,
            "name": product.name,
            "current_stock": product.stock,
            "min_stock": product.min_stock,
            "category": product.category.name if product.category else None
        })
    return alerts


@router.get("/{product_id}", response_model=schemas.Product)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_product


@router.post("/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Verificar si el SKU/Código ya existe en la organización del usuario
    db_product = crud.get_product_by_sku(db, sku=product.sku, organization_id=current_user.organization_id)
    if db_product:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe un producto con el código '{product.sku}'. Por favor usa un código diferente."
        )
    return crud.create_product(db=db, product=product, organization_id=current_user.organization_id)


@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_product = crud.update_product(db, product_id=product_id, product=product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_product = crud.delete_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado exitosamente"}
