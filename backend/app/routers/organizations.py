"""
Router para gestión de organizaciones (Sistema SaaS)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import shutil
import os
from pathlib import Path

from ..database import get_db
from .. import models_extended
from .. import models_organization
from .. import schemas_organization as schemas
from .. import crud_organization as crud
from ..auth import get_current_active_user, get_current_admin_user
from ..models_organization import OrganizationStatus

# Alias para facilitar el uso
models = models_extended
Organization = models_organization.Organization

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


# ============================================================================
# RUTAS PÚBLICAS (Sin autenticación)
# ============================================================================

@router.post("/register", response_model=schemas.Organization, status_code=status.HTTP_201_CREATED)
def register_organization(
    registration: schemas.OrganizationRegister,
    db: Session = Depends(get_db)
):
    """
    Registro público de nueva organización
    No requiere autenticación - es la primera pantalla que ve el cliente
    """
    # Verificar que el email no esté en uso
    existing_org = db.query(Organization).filter(
        Organization.email == registration.email
    ).first()
    
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una organización con este email"
        )
    
    # Verificar que el username no esté en uso
    existing_user = db.query(models.User).filter(
        models.User.username == registration.admin_username
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Este nombre de usuario ya está en uso"
        )
    
    # Crear organización
    organization = crud.register_organization(db, registration)
    
    return organization


# ============================================================================
# RUTAS AUTENTICADAS (Usuario de una organización)
# ============================================================================

@router.get("/me", response_model=schemas.OrganizationWithStats)
def get_my_organization(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene la organización del usuario actual"""
    # Verificar que el usuario tenga una organización asignada
    if not current_user.organization_id:
        raise HTTPException(
            status_code=400, 
            detail="El usuario no tiene una organización asignada. Por favor contacta al administrador."
        )
    
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(
            status_code=404, 
            detail=f"Organización con ID {current_user.organization_id} no encontrada"
        )
    
    # Agregar estadísticas
    try:
        stats = crud.get_organization_stats(db, organization.id)
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        # Si falla, usar valores por defecto
        stats = {
            "total_users": 0,
            "total_clients": 0,
            "total_products": 0,
            "total_sales": 0,
            "total_rentals": 0
        }
    
    org_dict = {
        **organization.__dict__,
        **stats
    }
    
    return org_dict


@router.get("/current", response_model=schemas.Organization)
def get_current_organization(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información básica de la organización actual
    """
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return organization


@router.put("/me/settings", response_model=schemas.Organization)
def update_my_organization_settings(
    settings: schemas.OrganizationSettings,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la configuración de la organización del usuario
    Solo admin de la organización puede hacer esto
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador de la organización puede cambiar la configuración"
        )
    
    update_data = schemas.OrganizationUpdate(
        name=settings.name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        modules_enabled=settings.modules_enabled,
        rnc=settings.rnc,
        address=settings.address,
        city=settings.city,
        address_number=settings.address_number,
        website=settings.website,
        invoice_email=settings.invoice_email,
        phone=settings.phone,
        stamp_url=settings.stamp_url,
        clients_start_color=settings.clients_start_color,
        clients_end_color=settings.clients_end_color,
        quotations_start_color=settings.quotations_start_color,
        quotations_end_color=settings.quotations_end_color,
        sales_start_color=settings.sales_start_color,
        sales_end_color=settings.sales_end_color,
        rentals_start_color=settings.rentals_start_color,
        rentals_end_color=settings.rentals_end_color,
        products_start_color=settings.products_start_color,
        products_end_color=settings.products_end_color,
        categories_start_color=settings.categories_start_color,
        categories_end_color=settings.categories_end_color,
        suppliers_start_color=settings.suppliers_start_color,
        suppliers_end_color=settings.suppliers_end_color,
        goals_start_color=settings.goals_start_color,
        goals_end_color=settings.goals_end_color,
        quick_actions_start_color=settings.quick_actions_start_color,
        quick_actions_end_color=settings.quick_actions_end_color
    )
    
    organization = crud.update_organization(db, current_user.organization_id, update_data)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return organization


@router.post("/me/upload-logo")
async def upload_organization_logo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sube el logo de la organización"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede cambiar el logo"
        )
    
    # Validar tipo de archivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )
    
    # Crear directorio para logos si no existe
    upload_dir = Path("static/logos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre único para el archivo
    file_extension = file.filename.split(".")[-1]
    filename = f"org_{current_user.organization_id}_{int(datetime.now().timestamp())}.{file_extension}"
    file_path = upload_dir / filename
    
    # Guardar archivo
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Actualizar URL del logo en la organización
    logo_url = f"/static/logos/{filename}"
    organization = crud.update_organization_logo(db, current_user.organization_id, logo_url)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return {"logo_url": logo_url, "message": "Logo actualizado correctamente"}


@router.delete("/me/logo")
def delete_organization_logo(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Elimina el logo de la organización"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede eliminar el logo"
        )
    
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    # Eliminar archivo físico si existe
    if organization.logo_url:
        logo_path = Path(f"static/logos/{organization.logo_url.split('/')[-1]}")
        if logo_path.exists():
            logo_path.unlink()
            print(f"Logo eliminado: {logo_path}")
    
    # Actualizar la organización para quitar el logo
    organization.logo_url = None
    db.commit()
    db.refresh(organization)
    
    return {"message": "Logo eliminado correctamente"}


@router.post("/me/upload-stamp")
async def upload_organization_stamp(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Sube el sello/firma de la organización para facturas"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede cambiar el sello"
        )
    
    # Validar tipo de archivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )
    
    # Crear directorio para sellos si no existe
    upload_dir = Path("static/stamps")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre único para el archivo
    file_extension = file.filename.split(".")[-1]
    filename = f"stamp_{current_user.organization_id}_{int(datetime.now().timestamp())}.{file_extension}"
    file_path = upload_dir / filename
    
    # Guardar archivo
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Actualizar URL del sello en la organización
    stamp_url = f"/static/stamps/{filename}"
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    organization.stamp_url = stamp_url
    db.commit()
    db.refresh(organization)
    
    return {"stamp_url": stamp_url, "message": "Sello actualizado correctamente"}


@router.delete("/me/stamp")
def delete_organization_stamp(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Elimina el sello de la organización"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede eliminar el sello"
        )
    
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    # Eliminar archivo físico si existe
    if organization.stamp_url:
        stamp_path = Path(f"static/stamps/{organization.stamp_url.split('/')[-1]}")
        if stamp_path.exists():
            stamp_path.unlink()
            print(f"Sello eliminado: {stamp_path}")
    
    # Actualizar la organización para quitar el sello
    organization.stamp_url = None
    db.commit()
    db.refresh(organization)
    
    return {"message": "Sello eliminado correctamente"}


@router.get("/me/limits", response_model=schemas.OrganizationLimits)
def get_my_organization_limits(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene los límites y uso actual de la organización"""
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    stats = crud.get_organization_stats(db, organization.id)
    
    limits = schemas.OrganizationLimits(
        max_users=organization.max_users,
        max_products=organization.max_products,
        max_storage_mb=organization.max_storage_mb,
        current_users=stats["total_users"],
        current_products=stats["total_products"],
        storage_used_mb=stats["storage_used_mb"]
    )
    
    return limits


@router.get("/me/dashboard-settings", response_model=schemas.DashboardSettings)
def get_dashboard_settings(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene las configuraciones del Dashboard"""
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return schemas.DashboardSettings(
        monthly_sales_goal=organization.monthly_sales_goal
    )


@router.put("/me/dashboard-settings", response_model=schemas.DashboardSettings)
def update_dashboard_settings(
    settings: schemas.DashboardSettings,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza las configuraciones del Dashboard"""
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    # Actualizar configuraciones
    if settings.monthly_sales_goal is not None:
        organization.monthly_sales_goal = settings.monthly_sales_goal
    
    db.commit()
    db.refresh(organization)
    
    return schemas.DashboardSettings(
        monthly_sales_goal=organization.monthly_sales_goal
    )


@router.get("/me/currency", response_model=dict)
def get_organization_currency(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene la moneda configurada para la organización"""
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return {
        "currency": organization.currency,
        "currency_symbol": get_currency_symbol(organization.currency)
    }


@router.put("/me/currency", response_model=dict)
def update_organization_currency(
    currency_data: dict,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza la moneda de la organización"""
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    new_currency = currency_data.get("currency")
    if new_currency not in ["USD", "EUR", "DOP"]:
        raise HTTPException(status_code=400, detail="Moneda no válida")
    
    organization.currency = new_currency
    db.commit()
    db.refresh(organization)
    
    return {
        "currency": organization.currency,
        "currency_symbol": get_currency_symbol(organization.currency)
    }


@router.put("/modules", response_model=dict)
def update_organization_modules(
    modules_data: dict,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza los módulos habilitados de la organización"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador de la organización puede cambiar los módulos"
        )
    
    organization = crud.get_organization(db, current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    modules_enabled = modules_data.get("modules_enabled")
    if not modules_enabled:
        raise HTTPException(status_code=400, detail="modules_enabled es requerido")
    
    # Validar que el dashboard siempre esté activo
    if not modules_enabled.get("dashboard", True):
        raise HTTPException(status_code=400, detail="El módulo Dashboard no puede ser desactivado")
    
    organization.modules_enabled = modules_enabled
    db.commit()
    db.refresh(organization)
    
    return {
        "modules_enabled": organization.modules_enabled,
        "message": "Módulos actualizados correctamente"
    }


def get_currency_symbol(currency: str) -> str:
    """Obtiene el símbolo de la moneda"""
    symbols = {
        "USD": "$",
        "EUR": "€",
        "DOP": ""  # Para DOP, no mostrar símbolo
    }
    return symbols.get(currency, "$")


@router.delete("/me/reset-data")
def reset_organization_data(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Resetea todos los datos de la organización (ventas, alquileres, cotizaciones, productos, clientes, etc.)
    MANTIENE: La organización, usuarios y configuraciones básicas
    ELIMINA: Todos los datos de negocio
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="Usuario no pertenece a ninguna organización")
        
        print(f"Iniciando reset para organización {organization_id}")
        
        # Contar registros antes del reset
        counts_before = {
            'movements': db.query(models.InventoryMovement).filter(models.InventoryMovement.organization_id == organization_id).count(),
            'sales': db.query(models.Sale).filter(models.Sale.organization_id == organization_id).count(),
            'quotations': db.query(models.Quotation).filter(models.Quotation.organization_id == organization_id).count(),
            'rentals': db.query(models.Rental).filter(models.Rental.organization_id == organization_id).count(),
            'products': db.query(models.Product).filter(models.Product.organization_id == organization_id).count(),
            'clients': db.query(models.Client).filter(models.Client.organization_id == organization_id).count(),
            'categories': db.query(models.Category).filter(models.Category.organization_id == organization_id).count(),
            'suppliers': db.query(models.Supplier).filter(models.Supplier.organization_id == organization_id).count()
        }
        
        print(f"Registros antes del reset: {counts_before}")
        
        # Eliminar en orden para respetar las foreign keys
        # NOTA: También eliminamos registros con organization_id = NULL para limpiar completamente
        
        # 1. Eliminar movimientos de inventario
        movements_deleted = db.query(models.InventoryMovement).filter(
            models.InventoryMovement.organization_id == organization_id
        ).delete(synchronize_session=False)
        print(f"Movimientos eliminados: {movements_deleted}")
        
        # 2. Eliminar items de ventas
        sales = db.query(models.Sale).filter(models.Sale.organization_id == organization_id).all()
        sale_items_deleted = 0
        for sale in sales:
            deleted = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale.id).delete()
            sale_items_deleted += deleted
        print(f"Items de ventas eliminados: {sale_items_deleted}")
        
        # 3. Eliminar ventas
        sales_deleted = db.query(models.Sale).filter(models.Sale.organization_id == organization_id).delete(synchronize_session=False)
        print(f"Ventas eliminadas: {sales_deleted}")
        
        # 4. Eliminar items de cotizaciones
        quotations = db.query(models.Quotation).filter(models.Quotation.organization_id == organization_id).all()
        quotation_items_deleted = 0
        for quotation in quotations:
            deleted = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quotation.id).delete()
            quotation_items_deleted += deleted
        print(f"Items de cotizaciones eliminados: {quotation_items_deleted}")
        
        # 5. Eliminar cotizaciones
        quotations_deleted = db.query(models.Quotation).filter(models.Quotation.organization_id == organization_id).delete(synchronize_session=False)
        print(f"Cotizaciones eliminadas: {quotations_deleted}")
        
        # 6. Eliminar pagos de alquileres
        rentals = db.query(models.Rental).filter(models.Rental.organization_id == organization_id).all()
        rental_payments_deleted = 0
        for rental in rentals:
            deleted = db.query(models.RentalPayment).filter(models.RentalPayment.rental_id == rental.id).delete()
            rental_payments_deleted += deleted
        print(f"Pagos de alquileres eliminados: {rental_payments_deleted}")
        
        # 7. Eliminar alquileres
        rentals_deleted = db.query(models.Rental).filter(models.Rental.organization_id == organization_id).delete(synchronize_session=False)
        print(f"Alquileres eliminados: {rentals_deleted}")
        
        # 8. Eliminar productos
        products_deleted = db.query(models.Product).filter(models.Product.organization_id == organization_id).delete(synchronize_session=False)
        print(f"Productos eliminados: {products_deleted}")
        
        # 9. Eliminar clientes
        clients_deleted = db.query(models.Client).filter(models.Client.organization_id == organization_id).delete(synchronize_session=False)
        print(f"Clientes eliminados: {clients_deleted}")
        
        # 10. Eliminar categorías (solo las de esta organización)
        categories_deleted = db.query(models.Category).filter(models.Category.organization_id == organization_id).delete(synchronize_session=False)
        print(f"Categorías eliminadas: {categories_deleted}")
        
        # 11. Eliminar proveedores (solo los de esta organización)
        suppliers_deleted = db.query(models.Supplier).filter(models.Supplier.organization_id == organization_id).delete(synchronize_session=False)
        print(f"Proveedores eliminados: {suppliers_deleted}")
        
        # 11. LIMPIEZA ADICIONAL: Eliminar registros huérfanos (organization_id = NULL)
        # Esto es para limpiar registros que no tienen organization_id asignado
        print("Iniciando limpieza de registros huérfanos...")
        
        # Eliminar registros huérfanos
        orphan_movements = db.query(models.InventoryMovement).filter(models.InventoryMovement.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Movimientos huérfanos eliminados: {orphan_movements}")
        
        # Eliminar items de ventas huérfanas
        orphan_sales = db.query(models.Sale).filter(models.Sale.organization_id.is_(None)).all()
        orphan_sale_items = 0
        for sale in orphan_sales:
            deleted = db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale.id).delete()
            orphan_sale_items += deleted
        print(f"Items de ventas huérfanas eliminados: {orphan_sale_items}")
        
        # Eliminar ventas huérfanas
        orphan_sales_deleted = db.query(models.Sale).filter(models.Sale.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Ventas huérfanas eliminadas: {orphan_sales_deleted}")
        
        # Eliminar items de cotizaciones huérfanas
        orphan_quotations = db.query(models.Quotation).filter(models.Quotation.organization_id.is_(None)).all()
        orphan_quotation_items = 0
        for quotation in orphan_quotations:
            deleted = db.query(models.QuotationItem).filter(models.QuotationItem.quotation_id == quotation.id).delete()
            orphan_quotation_items += deleted
        print(f"Items de cotizaciones huérfanas eliminados: {orphan_quotation_items}")
        
        # Eliminar cotizaciones huérfanas
        orphan_quotations_deleted = db.query(models.Quotation).filter(models.Quotation.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Cotizaciones huérfanas eliminadas: {orphan_quotations_deleted}")
        
        # Eliminar pagos de alquileres huérfanos
        orphan_rentals = db.query(models.Rental).filter(models.Rental.organization_id.is_(None)).all()
        orphan_rental_payments = 0
        for rental in orphan_rentals:
            deleted = db.query(models.RentalPayment).filter(models.RentalPayment.rental_id == rental.id).delete()
            orphan_rental_payments += deleted
        print(f"Pagos de alquileres huérfanos eliminados: {orphan_rental_payments}")
        
        # Eliminar alquileres huérfanos
        orphan_rentals_deleted = db.query(models.Rental).filter(models.Rental.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Alquileres huérfanos eliminados: {orphan_rentals_deleted}")
        
        # Eliminar productos huérfanos
        orphan_products_deleted = db.query(models.Product).filter(models.Product.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Productos huérfanos eliminados: {orphan_products_deleted}")
        
        # Eliminar clientes huérfanos
        orphan_clients_deleted = db.query(models.Client).filter(models.Client.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Clientes huérfanos eliminados: {orphan_clients_deleted}")
        
        # Eliminar categorías huérfanas
        orphan_categories_deleted = db.query(models.Category).filter(models.Category.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Categorías huérfanas eliminadas: {orphan_categories_deleted}")
        
        # Eliminar proveedores huérfanos
        orphan_suppliers_deleted = db.query(models.Supplier).filter(models.Supplier.organization_id.is_(None)).delete(synchronize_session=False)
        print(f"Proveedores huérfanos eliminados: {orphan_suppliers_deleted}")
        
        # Resetear configuraciones del dashboard
        organization = crud.get_organization(db, organization_id)
        if organization:
            organization.monthly_sales_goal = 0
            organization.monthly_growth_target = 0
            organization.conversion_rate_target = 0
            print("Configuraciones del dashboard reseteadas")
        
        db.commit()
        print("Commit realizado exitosamente")
        
        # Verificar que se eliminaron los registros
        counts_after = {
            'movements': db.query(models.InventoryMovement).filter(models.InventoryMovement.organization_id == organization_id).count(),
            'sales': db.query(models.Sale).filter(models.Sale.organization_id == organization_id).count(),
            'quotations': db.query(models.Quotation).filter(models.Quotation.organization_id == organization_id).count(),
            'rentals': db.query(models.Rental).filter(models.Rental.organization_id == organization_id).count(),
            'products': db.query(models.Product).filter(models.Product.organization_id == organization_id).count(),
            'clients': db.query(models.Client).filter(models.Client.organization_id == organization_id).count(),
            'categories': db.query(models.Category).filter(models.Category.organization_id == organization_id).count(),
            'suppliers': db.query(models.Supplier).filter(models.Supplier.organization_id == organization_id).count()
        }
        
        print(f"Registros después del reset: {counts_after}")
        
        return {
            "message": "Datos de la organización reseteados exitosamente",
            "reset_at": datetime.utcnow().isoformat(),
            "organization_id": organization_id,
            "deleted_counts": {
                "movements": movements_deleted,
                "sales": sales_deleted,
                "quotations": quotations_deleted,
                "rental_payments": rental_payments_deleted,
                "rentals": rentals_deleted,
                "products": products_deleted,
                "clients": clients_deleted,
                "categories": categories_deleted,
                "suppliers": suppliers_deleted
            },
            "orphan_counts": {
                "movements": orphan_movements,
                "sales": orphan_sales_deleted,
                "quotations": orphan_quotations_deleted,
                "rental_payments": orphan_rental_payments,
                "rentals": orphan_rentals_deleted,
                "products": orphan_products_deleted,
                "clients": orphan_clients_deleted,
                "categories": orphan_categories_deleted,
                "suppliers": orphan_suppliers_deleted
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error al resetear datos de la organización: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================================
# RUTAS DE ADMINISTRADOR (Solo para el super admin del sistema)
# ============================================================================

@router.get("/admin/all", response_model=List[schemas.Organization])
def get_all_organizations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrganizationStatus] = None,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las organizaciones (admin o super admin)
    """
    # Permitir tanto super admins como admins de organizaciones
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden ver todas las organizaciones"
        )
    
    try:
        organizations = crud.get_organizations(db, skip=skip, limit=limit, status=status)
        return organizations
    except Exception as e:
        print(f"Error en get_all_organizations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/admin/pending", response_model=List[schemas.Organization])
def get_pending_organizations(
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene organizaciones pendientes de aprobación (admin o super admin)
    """
    # Permitir tanto super admins como admins de organizaciones
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden ver solicitudes pendientes"
        )
    
    try:
        organizations = crud.get_pending_organizations(db)
        return organizations
    except Exception as e:
        print(f"Error en get_pending_organizations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/admin/users", response_model=List[dict])
def get_all_users(
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los usuarios del sistema (solo super admin)
    """
    if current_user.organization_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador del sistema puede ver todos los usuarios"
        )
    
    try:
        users = db.query(models.User).all()
        users_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "organization_id": user.organization_id,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            users_data.append(user_dict)
        
        return users_data
    except Exception as e:
        print(f"Error en get_all_users: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/admin/{organization_id}/approve", response_model=schemas.Organization)
def approve_organization(
    organization_id: int,
    approval: schemas.OrganizationApproval,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Aprueba o rechaza una organización (solo super admin)
    """
    if current_user.organization_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador del sistema puede aprobar organizaciones"
        )
    
    organization = crud.approve_organization(
        db, organization_id, current_user.id, approval
    )
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return organization


@router.post("/admin/{organization_id}/suspend", response_model=schemas.Organization)
def suspend_organization(
    organization_id: int,
    notes: str = None,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Suspende una organización (solo super admin)
    """
    if current_user.organization_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador del sistema puede suspender organizaciones"
        )
    
    organization = crud.suspend_organization(db, organization_id, notes)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return organization


@router.post("/admin/{organization_id}/reactivate", response_model=schemas.Organization)
def reactivate_organization(
    organization_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reactiva una organización suspendida (solo super admin)
    """
    if current_user.organization_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador del sistema puede reactivar organizaciones"
        )
    
    organization = crud.reactivate_organization(db, organization_id)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return organization


@router.put("/admin/{organization_id}", response_model=schemas.Organization)
def update_organization_admin(
    organization_id: int,
    org_update: schemas.OrganizationUpdate,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza cualquier campo de una organización (solo super admin)
    """
    if current_user.organization_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador del sistema puede editar organizaciones"
        )
    
    organization = crud.update_organization(db, organization_id, org_update)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return organization


@router.delete("/admin/{organization_id}")
def delete_organization(
    organization_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Elimina una organización y todos sus datos (solo super admin)
    ⚠️ ACCIÓN DESTRUCTIVA - Elimina TODO
    """
    if current_user.organization_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador del sistema puede eliminar organizaciones"
        )
    
    organization = crud.delete_organization(db, organization_id)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return {"message": "Organización eliminada correctamente"}


@router.get("/stats", response_model=dict)
def get_organization_stats(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de la organización actual
    """
    from sqlalchemy import func
    
    organization_id = current_user.organization_id
    
    # Verificar que el usuario tenga una organización asignada
    if not organization_id:
        raise HTTPException(
            status_code=400,
            detail="El usuario no tiene una organización asignada"
        )
    
    # Contar usuarios
    total_users = db.query(func.count(models.User.id)).filter(
        models.User.organization_id == organization_id
    ).scalar() or 0
    
    # Contar clientes
    total_clients = db.query(func.count(models.Client.id)).filter(
        models.Client.organization_id == organization_id
    ).scalar() or 0
    
    # Contar productos
    total_products = db.query(func.count(models.Product.id)).filter(
        models.Product.organization_id == organization_id
    ).scalar() or 0
    
    # Contar ventas
    total_sales = db.query(func.count(models.Sale.id)).filter(
        models.Sale.organization_id == organization_id
    ).scalar() or 0
    
    # Contar alquileres activos
    total_rentals = db.query(func.count(models.Rental.id)).filter(
        models.Rental.organization_id == organization_id,
        models.Rental.status == "activo"
    ).scalar() or 0
    
    # Obtener información de la organización
    organization = crud.get_organization(db, organization_id)
    
    return {
        "total_users": total_users,
        "total_clients": total_clients,
        "total_products": total_products,
        "total_sales": total_sales,
        "total_rentals": total_rentals,
        "organization_created_at": organization.created_at if organization else None,
        "organization_status": organization.status if organization else None,
        "subscription_plan": organization.subscription_plan if organization else None
    }

