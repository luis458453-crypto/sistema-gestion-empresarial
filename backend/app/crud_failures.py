from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
from . import models_extended as models, schemas_extended as schemas
import json


def create_failure(db: Session, failure: schemas.SystemFailureCreate):
    """Registra una nueva falla en el sistema"""
    db_failure = models.SystemFailure(**failure.model_dump())
    db.add(db_failure)
    db.commit()
    db.refresh(db_failure)
    return db_failure


def get_failure(db: Session, failure_id: int):
    """Obtiene una falla por ID"""
    return db.query(models.SystemFailure).filter(models.SystemFailure.id == failure_id).first()


def get_failures(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    module: Optional[str] = None,
    error_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Obtiene lista de fallas con filtros opcionales"""
    query = db.query(models.SystemFailure)
    
    if organization_id:
        query = query.filter(models.SystemFailure.organization_id == organization_id)
    
    if module:
        query = query.filter(models.SystemFailure.module == module)
    
    if error_type:
        query = query.filter(models.SystemFailure.error_type == error_type)
    
    if severity:
        query = query.filter(models.SystemFailure.severity == severity)
    
    if is_resolved is not None:
        query = query.filter(models.SystemFailure.is_resolved == is_resolved)
    
    if start_date:
        query = query.filter(models.SystemFailure.created_at >= start_date)
    
    if end_date:
        query = query.filter(models.SystemFailure.created_at <= end_date)
    
    return query.order_by(desc(models.SystemFailure.created_at)).offset(skip).limit(limit).all()


def update_failure(db: Session, failure_id: int, failure_update: schemas.SystemFailureUpdate, user_id: int):
    """Actualiza una falla (principalmente para marcarla como resuelta)"""
    db_failure = get_failure(db, failure_id)
    if not db_failure:
        return None
    
    update_data = failure_update.model_dump(exclude_unset=True)
    
    if 'is_resolved' in update_data and update_data['is_resolved']:
        db_failure.resolved_at = datetime.utcnow()
        db_failure.resolved_by = user_id
    
    for field, value in update_data.items():
        setattr(db_failure, field, value)
    
    db.commit()
    db.refresh(db_failure)
    return db_failure


def delete_failure(db: Session, failure_id: int):
    """Elimina una falla del sistema"""
    db_failure = get_failure(db, failure_id)
    if db_failure:
        db.delete(db_failure)
        db.commit()
        return True
    return False


def get_failures_summary(db: Session, organization_id: Optional[int] = None, days: int = 30):
    """Genera un resumen completo de todas las fallas del sistema"""
    
    # Fecha de inicio para el análisis
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query base
    query = db.query(models.SystemFailure).filter(models.SystemFailure.created_at >= start_date)
    
    if organization_id:
        query = query.filter(models.SystemFailure.organization_id == organization_id)
    
    all_failures = query.all()
    
    # Contadores generales
    total_failures = len(all_failures)
    unresolved_failures = sum(1 for f in all_failures if not f.is_resolved)
    resolved_failures = sum(1 for f in all_failures if f.is_resolved)
    
    # Contadores por severidad
    critical_failures = sum(1 for f in all_failures if f.severity == "critical")
    high_failures = sum(1 for f in all_failures if f.severity == "high")
    medium_failures = sum(1 for f in all_failures if f.severity == "medium")
    low_failures = sum(1 for f in all_failures if f.severity == "low")
    
    # Fallas por módulo
    failures_by_module = {}
    for failure in all_failures:
        module = failure.module or "unknown"
        failures_by_module[module] = failures_by_module.get(module, 0) + 1
    
    # Fallas por tipo
    failures_by_type = {}
    for failure in all_failures:
        error_type = failure.error_type or "unknown"
        failures_by_type[error_type] = failures_by_type.get(error_type, 0) + 1
    
    # Fallas por día (últimos 30 días)
    failures_by_day = {}
    for failure in all_failures:
        day_key = failure.created_at.strftime("%Y-%m-%d")
        failures_by_day[day_key] = failures_by_day.get(day_key, 0) + 1
    
    # Fallas recientes (últimas 10)
    recent_failures = sorted(all_failures, key=lambda x: x.created_at, reverse=True)[:10]
    
    return schemas.SystemFailureSummary(
        total_failures=total_failures,
        unresolved_failures=unresolved_failures,
        resolved_failures=resolved_failures,
        critical_failures=critical_failures,
        high_failures=high_failures,
        medium_failures=medium_failures,
        low_failures=low_failures,
        failures_by_module=failures_by_module,
        failures_by_type=failures_by_type,
        failures_by_day=failures_by_day,
        recent_failures=[schemas.SystemFailure.model_validate(f) for f in recent_failures]
    )


def log_http_exception(
    db: Session,
    module: str,
    endpoint: str,
    method: str,
    status_code: int,
    error_message: str,
    error_detail: Optional[str] = None,
    organization_id: Optional[int] = None,
    user_id: Optional[int] = None,
    request_data: Optional[dict] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Helper para registrar excepciones HTTP"""
    
    # Determinar severidad basada en el código de estado
    if status_code >= 500:
        severity = "critical"
    elif status_code >= 400:
        severity = "medium"
    else:
        severity = "low"
    
    failure_data = schemas.SystemFailureCreate(
        organization_id=organization_id,
        user_id=user_id,
        error_type="http_exception",
        severity=severity,
        module=module,
        endpoint=endpoint,
        method=method,
        error_code=str(status_code),
        error_message=error_message,
        error_detail=error_detail,
        request_data=json.dumps(request_data) if request_data else None,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    return create_failure(db, failure_data)


def log_validation_error(
    db: Session,
    module: str,
    endpoint: str,
    error_message: str,
    error_detail: Optional[str] = None,
    organization_id: Optional[int] = None,
    user_id: Optional[int] = None,
    request_data: Optional[dict] = None
):
    """Helper para registrar errores de validación"""
    
    failure_data = schemas.SystemFailureCreate(
        organization_id=organization_id,
        user_id=user_id,
        error_type="validation_error",
        severity="low",
        module=module,
        endpoint=endpoint,
        error_code="400",
        error_message=error_message,
        error_detail=error_detail,
        request_data=json.dumps(request_data) if request_data else None
    )
    
    return create_failure(db, failure_data)


def log_database_error(
    db: Session,
    module: str,
    operation: str,
    error_message: str,
    stack_trace: Optional[str] = None,
    organization_id: Optional[int] = None,
    user_id: Optional[int] = None
):
    """Helper para registrar errores de base de datos"""
    
    failure_data = schemas.SystemFailureCreate(
        organization_id=organization_id,
        user_id=user_id,
        error_type="database_error",
        severity="high",
        module=module,
        endpoint=operation,
        error_code="DB_ERROR",
        error_message=error_message,
        stack_trace=stack_trace
    )
    
    return create_failure(db, failure_data)


def get_critical_failures(db: Session, organization_id: Optional[int] = None, limit: int = 10):
    """Obtiene las fallas críticas no resueltas"""
    query = db.query(models.SystemFailure).filter(
        and_(
            models.SystemFailure.severity == "critical",
            models.SystemFailure.is_resolved == False
        )
    )
    
    if organization_id:
        query = query.filter(models.SystemFailure.organization_id == organization_id)
    
    return query.order_by(desc(models.SystemFailure.created_at)).limit(limit).all()


def get_failure_trends(db: Session, organization_id: Optional[int] = None, days: int = 7):
    """Analiza tendencias de fallas en los últimos días"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(models.SystemFailure).filter(models.SystemFailure.created_at >= start_date)
    
    if organization_id:
        query = query.filter(models.SystemFailure.organization_id == organization_id)
    
    failures = query.all()
    
    # Agrupar por día y severidad
    trends = {}
    for failure in failures:
        day_key = failure.created_at.strftime("%Y-%m-%d")
        if day_key not in trends:
            trends[day_key] = {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        trends[day_key]["total"] += 1
        trends[day_key][failure.severity] += 1
    
    return trends
