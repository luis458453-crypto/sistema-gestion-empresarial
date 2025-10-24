from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..auth import get_current_active_user
from .. import models_extended as models, schemas_extended as schemas
from ..crud_failures import (
    get_failure, get_failures, create_failure, update_failure,
    delete_failure, get_failures_summary, get_critical_failures,
    get_failure_trends, log_http_exception
)

router = APIRouter(prefix="/api/failures", tags=["failures"])


@router.get("/", response_model=List[schemas.SystemFailure])
def read_failures(
    skip: int = 0,
    limit: int = 100,
    module: Optional[str] = None,
    error_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene lista de fallas del sistema con filtros opcionales"""
    
    failures = get_failures(
        db,
        skip=skip,
        limit=limit,
        organization_id=current_user.organization_id,
        module=module,
        error_type=error_type,
        severity=severity,
        is_resolved=is_resolved,
        start_date=start_date,
        end_date=end_date
    )
    return failures


@router.get("/summary", response_model=schemas.SystemFailureSummary)
def read_failures_summary(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene un resumen completo de todas las fallas del sistema"""
    
    summary = get_failures_summary(db, current_user.organization_id, days)
    return summary


@router.get("/critical", response_model=List[schemas.SystemFailure])
def read_critical_failures(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene las fallas críticas no resueltas"""
    
    failures = get_critical_failures(db, current_user.organization_id, limit)
    return failures


@router.get("/trends")
def read_failure_trends(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Analiza tendencias de fallas en los últimos días"""
    
    trends = get_failure_trends(db, current_user.organization_id, days)
    return trends


@router.get("/{failure_id}", response_model=schemas.SystemFailure)
def read_failure(
    failure_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Obtiene una falla específica por ID"""
    
    failure = get_failure(db, failure_id)
    if not failure:
        raise HTTPException(status_code=404, detail="Falla no encontrada")
    
    # Verificar que la falla pertenece a la organización del usuario
    if failure.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para ver esta falla"
        )
    
    return failure


@router.post("/", response_model=schemas.SystemFailure, status_code=status.HTTP_201_CREATED)
def create_new_failure(
    failure: schemas.SystemFailureCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Registra una nueva falla en el sistema"""
    
    # Asegurar que la falla se registre para la organización del usuario
    failure.organization_id = current_user.organization_id
    
    return create_failure(db, failure)


@router.put("/{failure_id}", response_model=schemas.SystemFailure)
def update_existing_failure(
    failure_id: int,
    failure_update: schemas.SystemFailureUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Actualiza una falla (principalmente para marcarla como resuelta)"""
    
    # Verificar que la falla existe y pertenece a la organización
    failure = get_failure(db, failure_id)
    if not failure:
        raise HTTPException(status_code=404, detail="Falla no encontrada")
    
    if failure.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para actualizar esta falla"
        )
    
    updated_failure = update_failure(db, failure_id, failure_update, current_user.id)
    return updated_failure


@router.delete("/{failure_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_failure(
    failure_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Elimina una falla del sistema"""
    
    # Verificar que la falla existe y pertenece a la organización
    failure = get_failure(db, failure_id)
    if not failure:
        raise HTTPException(status_code=404, detail="Falla no encontrada")
    
    if failure.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para eliminar esta falla"
        )
    
    success = delete_failure(db, failure_id)
    if not success:
        raise HTTPException(status_code=404, detail="Falla no encontrada")
    
    return None


@router.post("/log/http-exception")
async def log_http_error(
    request: Request,
    module: str,
    endpoint: str,
    method: str,
    status_code: int,
    error_message: str,
    error_detail: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Endpoint para registrar excepciones HTTP desde el frontend"""
    
    # Obtener información del request
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    failure = log_http_exception(
        db=db,
        module=module,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        error_message=error_message,
        error_detail=error_detail,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    return {"message": "Error registrado correctamente", "failure_id": failure.id}
