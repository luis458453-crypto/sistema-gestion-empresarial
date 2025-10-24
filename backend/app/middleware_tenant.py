"""
Middleware para Multi-Tenancy
Filtra automáticamente las consultas por organization_id
"""
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TenantContext:
    """Contexto global para el tenant actual"""
    organization_id: Optional[int] = None
    user_id: Optional[int] = None


def get_organization_from_user(user) -> Optional[int]:
    """Extrae el organization_id del usuario autenticado"""
    if user and hasattr(user, 'organization_id'):
        return user.organization_id
    return None


def apply_tenant_filter(query, model_class, organization_id: Optional[int]):
    """
    Aplica filtro de organización a una consulta si el modelo lo soporta
    """
    # Si es super admin (sin organization_id), no filtrar
    if organization_id is None:
        return query
    
    # Verificar si el modelo tiene el campo organization_id
    if hasattr(model_class, 'organization_id'):
        query = query.filter(model_class.organization_id == organization_id)
    
    return query


def auto_set_organization(obj, organization_id: Optional[int]):
    """
    Establece automáticamente el organization_id en objetos nuevos
    """
    if organization_id is not None and hasattr(obj, 'organization_id'):
        # Solo establecer si aún no tiene valor
        if obj.organization_id is None:
            obj.organization_id = organization_id


# ============================================================================
# Funciones helper para usar en CRUD
# ============================================================================

def get_query_with_tenant(db: Session, model_class, organization_id: Optional[int]):
    """
    Crea una query con filtro de tenant automático
    
    Uso en CRUD:
        from .middleware_tenant import get_query_with_tenant
        
        def get_products(db: Session, user_org_id: int):
            query = get_query_with_tenant(db, Product, user_org_id)
            return query.all()
    """
    query = db.query(model_class)
    return apply_tenant_filter(query, model_class, organization_id)


def create_with_tenant(db: Session, model_instance, organization_id: Optional[int]):
    """
    Crea un objeto asegurando que tenga el organization_id correcto
    
    Uso en CRUD:
        from .middleware_tenant import create_with_tenant
        
        def create_product(db: Session, product_data, user_org_id: int):
            product = Product(**product_data.dict())
            create_with_tenant(db, product, user_org_id)
            db.commit()
            db.refresh(product)
            return product
    """
    auto_set_organization(model_instance, organization_id)
    db.add(model_instance)
    return model_instance


def verify_tenant_access(db: Session, model_instance, organization_id: Optional[int]) -> bool:
    """
    Verifica que un objeto pertenece a la organización del usuario
    
    Retorna True si:
    - El usuario es super admin (organization_id is None)
    - El objeto pertenece a la organización del usuario
    - El modelo no tiene organization_id (legacy)
    
    Retorna False si:
    - El objeto pertenece a otra organización
    """
    # Super admin puede acceder a todo
    if organization_id is None:
        return True
    
    # Si el modelo no tiene organization_id, permitir acceso (legacy)
    if not hasattr(model_instance, 'organization_id'):
        return True
    
    # Verificar que pertenece a la organización
    return model_instance.organization_id == organization_id


# ============================================================================
# Decoradores para funciones CRUD
# ============================================================================

def with_tenant_filter(func):
    """
    Decorador que automáticamente filtra por organización
    
    IMPORTANTE: La función debe recibir organization_id como parámetro
    
    Ejemplo:
        @with_tenant_filter
        def get_products(db: Session, organization_id: int, skip: int = 0):
            return db.query(Product).offset(skip).all()
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Si el resultado es una query, aplicar filtro
        if hasattr(result, 'filter'):
            organization_id = kwargs.get('organization_id')
            if organization_id is not None:
                # Intentar detectar el modelo
                if hasattr(result, 'column_descriptions'):
                    model_class = result.column_descriptions[0]['type']
                    result = apply_tenant_filter(result, model_class, organization_id)
        
        return result
    
    return wrapper


# ============================================================================
# Helper para validar permisos
# ============================================================================

def require_same_organization(user_org_id: Optional[int], target_org_id: Optional[int]) -> bool:
    """
    Valida que el usuario pueda acceder al recurso
    
    Lanza HTTPException si no tiene permiso
    """
    # Super admin puede todo
    if user_org_id is None:
        return True
    
    # Usuarios normales solo pueden acceder a su organización
    if user_org_id != target_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a recursos de otra organización"
        )
    
    return True


def is_super_admin(organization_id: Optional[int]) -> bool:
    """
    Verifica si el usuario es super admin del sistema
    """
    return organization_id is None


def can_manage_organizations(organization_id: Optional[int]) -> bool:
    """
    Verifica si el usuario puede gestionar organizaciones
    Solo el super admin puede
    """
    if not is_super_admin(organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador del sistema puede gestionar organizaciones"
        )
    return True


# ============================================================================
# Event listeners de SQLAlchemy (Experimental)
# ============================================================================

def setup_tenant_listeners():
    """
    Configura listeners de SQLAlchemy para aplicar filtros automáticamente
    
    NOTA: Esto es experimental. Prefiere usar las funciones helper directamente.
    """
    from sqlalchemy import event
    from sqlalchemy.orm import Session as SQLAlchemySession
    
    @event.listens_for(SQLAlchemySession, 'after_attach')
    def receive_after_attach(session, instance):
        """Cuando se adjunta un objeto a la sesión"""
        if TenantContext.organization_id is not None:
            auto_set_organization(instance, TenantContext.organization_id)


# ============================================================================
# Funciones para actualizar contexto (usar en dependencies)
# ============================================================================

def set_tenant_context(organization_id: Optional[int], user_id: Optional[int] = None):
    """
    Establece el contexto del tenant actual
    
    Usar en dependency de FastAPI:
    
    def get_current_user_with_context(current_user = Depends(get_current_user)):
        set_tenant_context(current_user.organization_id, current_user.id)
        return current_user
    """
    TenantContext.organization_id = organization_id
    TenantContext.user_id = user_id


def clear_tenant_context():
    """Limpia el contexto del tenant"""
    TenantContext.organization_id = None
    TenantContext.user_id = None


def get_current_tenant() -> Optional[int]:
    """Obtiene el organization_id del contexto actual"""
    return TenantContext.organization_id








