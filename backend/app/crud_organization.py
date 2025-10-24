"""
CRUD operations para organizaciones (Sistema SaaS)
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import re

from .models_organization import Organization, OrganizationStatus, SubscriptionPlan, OrganizationInvitation
from . import schemas_organization as schemas
from .auth import get_password_hash


def generate_slug(name: str) -> str:
    """Genera un slug único desde el nombre"""
    # Convertir a minúsculas y reemplazar espacios
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


def get_organization(db: Session, organization_id: int):
    """Obtiene una organización por ID"""
    return db.query(Organization).filter(Organization.id == organization_id).first()


def get_organization_by_slug(db: Session, slug: str):
    """Obtiene una organización por slug"""
    return db.query(Organization).filter(Organization.slug == slug).first()


def get_organizations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrganizationStatus] = None
):
    """Obtiene lista de organizaciones con filtros"""
    query = db.query(Organization)
    
    if status:
        query = query.filter(Organization.status == status)
    
    return query.order_by(desc(Organization.created_at)).offset(skip).limit(limit).all()


def get_pending_organizations(db: Session):
    """Obtiene organizaciones pendientes de aprobación"""
    return db.query(Organization).filter(
        Organization.status == OrganizationStatus.pending
    ).order_by(Organization.created_at).all()


def create_organization(db: Session, org: schemas.OrganizationCreate):
    """Crea una nueva organización"""
    # Generar slug único
    base_slug = generate_slug(org.name)
    slug = base_slug
    counter = 1
    
    while get_organization_by_slug(db, slug):
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Crear organización
    db_org = Organization(
        name=org.name,
        slug=slug,
        email=org.email,
        phone=org.phone,
        primary_color=org.primary_color,
        secondary_color=org.secondary_color,
        modules_enabled=org.modules_enabled or {
            "sales": True,
            "rentals": True,
            "quotations": True,
            "clients": True,
            "inventory": True,
            "categories": True,
            "suppliers": True,
            "dashboard": True
        },
        subscription_plan=org.subscription_plan,
        status=OrganizationStatus.pending
    )
    
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def register_organization(db: Session, registration: schemas.OrganizationRegister):
    """
    Registra una nueva organización completa (con usuario admin)
    Esta es la función que usa el formulario de registro público
    """
    from .models_extended import User
    
    # Crear organización
    org_create = schemas.OrganizationCreate(
        name=registration.name,
        slug="",  # Se generará automáticamente
        email=registration.email,
        phone=registration.phone,
        primary_color=registration.primary_color,
        secondary_color=registration.secondary_color,
        modules_enabled=registration.modules_requested,
        subscription_plan=SubscriptionPlan.free  # Por defecto empieza en free
    )
    
    organization = create_organization(db, org_create)
    
    # Crear usuario administrador de la organización
    admin_user = User(
        username=registration.admin_username,
        email=registration.admin_email,
        hashed_password=get_password_hash(registration.admin_password),
        full_name=registration.name,  # Usar nombre de empresa como nombre completo por defecto
        role="admin",
        is_active=False,  # Inactivo hasta que se apruebe la organización
        organization_id=organization.id
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(organization)
    
    return organization


def update_organization(db: Session, organization_id: int, org_update: schemas.OrganizationUpdate):
    """Actualiza una organización"""
    db_org = get_organization(db, organization_id)
    if not db_org:
        return None
    
    update_data = org_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_org, field, value)
    
    db_org.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_org)
    return db_org


def approve_organization(
    db: Session,
    organization_id: int,
    approved_by_user_id: int,
    approval: schemas.OrganizationApproval
):
    """Aprueba o rechaza una organización"""
    from .models_extended import User
    
    db_org = get_organization(db, organization_id)
    if not db_org:
        return None
    
    if approval.approved:
        # Aprobar
        db_org.status = OrganizationStatus.active
        db_org.approved_at = datetime.utcnow()
        db_org.approved_by = approved_by_user_id
        
        # Actualizar módulos y plan si se especificaron
        if approval.modules_enabled:
            db_org.modules_enabled = approval.modules_enabled
        
        if approval.subscription_plan:
            db_org.subscription_plan = approval.subscription_plan
            # Actualizar límites según el plan
            limits = db_org.get_limits()
            db_org.max_users = limits["users"]
            db_org.max_products = limits["products"]
            db_org.max_storage_mb = limits["storage_mb"]
        
        # Activar usuarios de la organización
        users = db.query(User).filter(User.organization_id == organization_id).all()
        for user in users:
            user.is_active = True
    else:
        # Rechazar
        db_org.status = OrganizationStatus.cancelled
    
    if approval.notes:
        db_org.notes = approval.notes
    
    db.commit()
    db.refresh(db_org)
    return db_org


def suspend_organization(db: Session, organization_id: int, notes: str = None):
    """Suspende una organización"""
    from .models_extended import User
    
    db_org = get_organization(db, organization_id)
    if not db_org:
        return None
    
    db_org.status = OrganizationStatus.suspended
    if notes:
        db_org.notes = notes
    
    # Desactivar usuarios
    users = db.query(User).filter(User.organization_id == organization_id).all()
    for user in users:
        user.is_active = False
    
    db.commit()
    db.refresh(db_org)
    return db_org


def reactivate_organization(db: Session, organization_id: int):
    """Reactiva una organización suspendida"""
    from .models_extended import User
    
    db_org = get_organization(db, organization_id)
    if not db_org:
        return None
    
    db_org.status = OrganizationStatus.active
    
    # Reactivar usuarios
    users = db.query(User).filter(User.organization_id == organization_id).all()
    for user in users:
        user.is_active = True
    
    db.commit()
    db.refresh(db_org)
    return db_org


def delete_organization(db: Session, organization_id: int):
    """Elimina una organización y todos sus datos"""
    db_org = get_organization(db, organization_id)
    if db_org:
        db.delete(db_org)
        db.commit()
    return db_org


def get_organization_stats(db: Session, organization_id: int):
    """Obtiene estadísticas de uso de una organización"""
    from .models_extended import User, Product, Sale
    
    stats = {
        "total_users": db.query(User).filter(User.organization_id == organization_id).count(),
        "total_products": db.query(Product).filter(Product.organization_id == organization_id).count() if hasattr(Product, 'organization_id') else 0,
        "total_sales": db.query(Sale).filter(Sale.organization_id == organization_id).count() if hasattr(Sale, 'organization_id') else 0,
        "storage_used_mb": 0  # TODO: Calcular espacio usado
    }
    
    return stats


def update_organization_logo(db: Session, organization_id: int, logo_url: str):
    """Actualiza el logo de una organización"""
    db_org = get_organization(db, organization_id)
    if not db_org:
        return None
    
    db_org.logo_url = logo_url
    db_org.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_org)
    return db_org


def can_add_user(db: Session, organization_id: int) -> bool:
    """Verifica si la organización puede agregar más usuarios"""
    from .models_extended import User
    
    org = get_organization(db, organization_id)
    if not org:
        return False
    
    if org.max_users == -1:  # Ilimitado
        return True
    
    current_users = db.query(User).filter(User.organization_id == organization_id).count()
    return current_users < org.max_users


def can_add_product(db: Session, organization_id: int) -> bool:
    """Verifica si la organización puede agregar más productos"""
    from .models_extended import Product
    
    org = get_organization(db, organization_id)
    if not org:
        return False
    
    if org.max_products == -1:  # Ilimitado
        return True
    
    if not hasattr(Product, 'organization_id'):
        return True  # Si aún no está implementado el multi-tenant
    
    current_products = db.query(Product).filter(Product.organization_id == organization_id).count()
    return current_products < org.max_products








