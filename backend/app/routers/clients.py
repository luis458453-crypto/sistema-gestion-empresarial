from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models, schemas_extended as schemas
from ..crud_clients import (
    get_client, get_clients, create_client, update_client, 
    delete_client, get_client_by_rnc, get_client_stats
)

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("/", response_model=List[schemas.Client])
def read_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene lista de clientes con filtros opcionales"""
    clients = get_clients(db, skip=skip, limit=limit, search=search, status=status, organization_id=current_user.organization_id)
    return clients


@router.get("/{client_id}", response_model=schemas.Client)
def read_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene un cliente por ID"""
    client = get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.get("/{client_id}/stats")
def read_client_stats(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene estadísticas de un cliente"""
    stats = get_client_stats(db, client_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return stats


@router.post("/", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
def create_new_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Crea un nuevo cliente"""
    try:
        return create_client(db, client, current_user.organization_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.put("/{client_id}", response_model=schemas.Client)
def update_existing_client(
    client_id: int,
    client: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza un cliente existente"""
    try:
        db_client = update_client(db, client_id, client)
        if not db_client:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return db_client
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elimina un cliente"""
    # Verificar que el usuario sea admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para eliminar clientes"
        )
    
    client = delete_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return None
