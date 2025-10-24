from typing import List
from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("/", response_model=List[schemas.Supplier])
def read_suppliers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Filtrar por organización del usuario
    suppliers = crud.get_suppliers(db, skip=skip, limit=limit, organization_id=current_user.organization_id)
    return suppliers


@router.get("/{supplier_id}", response_model=schemas.Supplier)
def read_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_supplier = crud.get_supplier(db, supplier_id=supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return db_supplier


@router.post("/", response_model=schemas.Supplier)
def create_supplier(
    supplier: schemas.SupplierCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return crud.create_supplier(db=db, supplier=supplier, organization_id=current_user.organization_id)


@router.put("/{supplier_id}", response_model=schemas.Supplier)
def update_supplier(
    supplier_id: int,
    supplier: schemas.SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_supplier = crud.update_supplier(db, supplier_id=supplier_id, supplier=supplier)
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return db_supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_supplier = crud.delete_supplier(db, supplier_id=supplier_id)
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return {"message": "Proveedor eliminado exitosamente"}
