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

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("/", response_model=List[schemas.Category])
def read_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Obtiene lista de categorías de la organización del usuario"""
    # Filtrar por organización del usuario
    categories = crud.get_categories(db, skip=skip, limit=limit, organization_id=current_user.organization_id)
    return categories


@router.get("/{category_id}", response_model=schemas.Category)
def read_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_category = crud.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_category


@router.post("/", response_model=schemas.Category)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    return crud.create_category(db=db, category=category, organization_id=current_user.organization_id)


@router.put("/{category_id}", response_model=schemas.Category)
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_category = crud.update_category(db, category_id=category_id, category=category)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    db_category = crud.delete_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return {"message": "Categoría eliminada exitosamente"}
