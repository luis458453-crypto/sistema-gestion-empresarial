from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from . import models_extended as models, schemas_extended as schemas


def generate_quotation_number(db: Session, organization_id: int = None) -> str:
    """Genera un número de cotización único e infinito por organización (COT-YYYYMMDD-01, 02, 03...)"""
    today = datetime.now()
    prefix = f"COT-{today.year}{today.month:02d}{today.day:02d}"
    
    # Construir query base - buscar TODAS las cotizaciones (no solo del mes actual)
    query = db.query(models.Quotation).filter(
        models.Quotation.quotation_number.like("COT-%")
    )
    
    # Filtrar por organización si se proporciona
    if organization_id:
        query = query.filter(models.Quotation.organization_id == organization_id)
    
    # Obtener todas las cotizaciones para encontrar el número más alto
    quotations = query.all()
    
    if quotations:
        # Extraer todos los números (última parte después del último guión)
        numbers = []
        for quotation in quotations:
            try:
                # Extraer el número después del último guión
                num = int(quotation.quotation_number.split('-')[-1])
                numbers.append(num)
            except (ValueError, IndexError):
                continue
        
        new_number = max(numbers) + 1 if numbers else 1
    else:
        new_number = 1
    
    # Formato: 01, 02, 03... 99, 100, 101... (sin límite)
    candidate = f"{prefix}-{new_number:02d}"
    
    # Verificar que no exista (por seguridad adicional)
    existing = db.query(models.Quotation).filter(
        models.Quotation.quotation_number == candidate,
        models.Quotation.organization_id == organization_id
    ).first()
    
    if existing:
        # Si existe, incrementar hasta encontrar uno libre
        while existing:
            new_number += 1
            candidate = f"{prefix}-{new_number:02d}"
            existing = db.query(models.Quotation).filter(
                models.Quotation.quotation_number == candidate,
                models.Quotation.organization_id == organization_id
            ).first()
    
    return candidate


def get_quotation(db: Session, quotation_id: int):
    from sqlalchemy.orm import joinedload
    return db.query(models.Quotation)\
        .join(models.Client, models.Quotation.client_id == models.Client.id, isouter=True)\
        .options(joinedload(models.Quotation.sale), joinedload(models.Quotation.rental))\
        .filter(models.Quotation.id == quotation_id)\
        .first()


def get_quotations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    organization_id: Optional[int] = None
):
    # Hacer join con la tabla de clientes para incluir la información del cliente
    query = db.query(models.Quotation).join(models.Client, models.Quotation.client_id == models.Client.id, isouter=True)
    
    # Filtrar por organización (multi-tenant)
    if organization_id:
        query = query.filter(models.Quotation.organization_id == organization_id)
    
    if client_id:
        query = query.filter(models.Quotation.client_id == client_id)
    
    if status:
        query = query.filter(models.Quotation.status == status)
    
    if start_date:
        query = query.filter(models.Quotation.quotation_date >= start_date)
    
    if end_date:
        query = query.filter(models.Quotation.quotation_date <= end_date)
    
    return query.order_by(desc(models.Quotation.created_at)).offset(skip).limit(limit).all()


def create_quotation(db: Session, quotation: schemas.QuotationCreate, user_id: int):
    # Obtener el usuario para acceder a su organization_id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    # Generar número de cotización por organización
    quotation_number = generate_quotation_number(db, user.organization_id)
    
    # Calcular días si es cotización de alquiler
    days = 1
    if quotation.quotation_type == 'alquiler' and quotation.notes:
        # Extraer fechas de las notas
        import re
        start_match = re.search(r'Fecha Inicio: ([^\n]+)', quotation.notes)
        end_match = re.search(r'Fecha Fin: ([^\n]+)', quotation.notes)
        if start_match and end_match:
            try:
                start_date = datetime.strptime(start_match.group(1).strip(), '%Y-%m-%d')
                end_date = datetime.strptime(end_match.group(1).strip(), '%Y-%m-%d')
                days = max(1, (end_date - start_date).days)
            except:
                days = 1
    
    # Calcular totales
    subtotal = 0
    items_data = []
    
    for item in quotation.items:
        # Para alquileres: cantidad × precio × días
        # Para ventas: cantidad × precio
        item_subtotal = item.quantity * item.unit_price * days
        if item.discount_percent > 0:
            item_subtotal -= item_subtotal * (item.discount_percent / 100)
        subtotal += item_subtotal
        items_data.append({
            **item.model_dump(),
            "subtotal": item_subtotal
        })
    
    # Calcular descuento
    discount_amount = subtotal * (quotation.discount_percent / 100) if quotation.discount_percent > 0 else 0
    subtotal_after_discount = subtotal - discount_amount
    
    # Calcular impuesto
    tax_amount = subtotal_after_discount * (quotation.tax_rate / 100)
    
    # Total
    total = subtotal_after_discount + tax_amount
    
    # Crear cotización
    quotation_dict = quotation.model_dump(exclude={'items'})
    db_quotation = models.Quotation(
        **quotation_dict,
        quotation_number=quotation_number,
        created_by=user_id,
        organization_id=user.organization_id,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        total=total
    )
    
    db.add(db_quotation)
    db.flush()
    
    # Crear items
    for item_data in items_data:
        # Obtener el producto para guardar su nombre
        product = db.query(models.Product).filter(models.Product.id == item_data['product_id']).first()
        
        db_item = models.QuotationItem(
            quotation_id=db_quotation.id,
            product_name=product.name if product else None,  # Guardar nombre del producto
            **item_data
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_quotation)
    return db_quotation


def can_edit_quotation(quotation: models.Quotation) -> bool:
    """Verifica si una cotización puede ser editada (no ha sido convertida)"""
    return quotation.sale is None and quotation.rental is None


def update_quotation(db: Session, quotation_id: int, quotation: schemas.QuotationUpdate):
    db_quotation = get_quotation(db, quotation_id)
    if not db_quotation:
        return None
    
    # Verificar si la cotización ya fue convertida a venta o alquiler
    if db_quotation.sale is not None:
        raise ValueError("No se puede editar: Esta cotización ya fue convertida a venta")
    
    if db_quotation.rental is not None:
        raise ValueError("No se puede editar: Esta cotización ya fue convertida a alquiler")
    
    # Actualizar campos básicos (excluyendo items)
    update_data = quotation.model_dump(exclude_unset=True, exclude={'items'})
    for field, value in update_data.items():
        setattr(db_quotation, field, value)
    
    # Si se enviaron items, actualizar los productos
    if hasattr(quotation, 'items') and quotation.items is not None:
        # Eliminar items antiguos
        db.query(models.QuotationItem).filter(
            models.QuotationItem.quotation_id == quotation_id
        ).delete()
        
        # Calcular días si es cotización de alquiler
        days = 1
        if db_quotation.quotation_type == 'alquiler' and db_quotation.notes:
            # Extraer fechas de las notas
            import re
            start_match = re.search(r'Fecha Inicio: ([^\n]+)', db_quotation.notes)
            end_match = re.search(r'Fecha Fin: ([^\n]+)', db_quotation.notes)
            if start_match and end_match:
                try:
                    start_date = datetime.strptime(start_match.group(1).strip(), '%Y-%m-%d')
                    end_date = datetime.strptime(end_match.group(1).strip(), '%Y-%m-%d')
                    days = max(1, (end_date - start_date).days)
                except:
                    days = 1
        
        # Recalcular totales
        subtotal = 0
        items_data = []
        
        for item in quotation.items:
            # Para alquileres: cantidad × precio × días
            # Para ventas: cantidad × precio
            item_subtotal = item.quantity * item.unit_price * days
            if item.discount_percent > 0:
                item_subtotal -= item_subtotal * (item.discount_percent / 100)
            subtotal += item_subtotal
            items_data.append({
                **item.model_dump(),
                "subtotal": item_subtotal
            })
        
        # Calcular descuento
        discount_amount = subtotal * (db_quotation.discount_percent / 100) if db_quotation.discount_percent > 0 else 0
        subtotal_after_discount = subtotal - discount_amount
        
        # Calcular impuesto
        tax_amount = subtotal_after_discount * (db_quotation.tax_rate / 100)
        
        # Total
        total = subtotal_after_discount + tax_amount
        
        # Actualizar totales
        db_quotation.subtotal = subtotal
        db_quotation.tax_amount = tax_amount
        db_quotation.discount_amount = discount_amount
        db_quotation.total = total
        
        # Crear nuevos items
        for item_data in items_data:
            # Obtener el producto para guardar su nombre
            product = db.query(models.Product).filter(models.Product.id == item_data['product_id']).first()
            
            db_item = models.QuotationItem(
                quotation_id=db_quotation.id,
                product_name=product.name if product else None,  # Guardar nombre del producto
                **item_data
            )
            db.add(db_item)
    
    db.commit()
    db.refresh(db_quotation)
    return db_quotation


def delete_quotation(db: Session, quotation_id: int):
    db_quotation = get_quotation(db, quotation_id)
    if db_quotation:
        # Verificar si la cotización ya fue convertida a venta o alquiler
        if db_quotation.sale is not None:
            raise ValueError("No se puede eliminar: Esta cotización ya fue convertida a venta")
        
        if db_quotation.rental is not None:
            raise ValueError("No se puede eliminar: Esta cotización ya fue convertida a alquiler")
        
        # Si no ha sido convertida, permitir la eliminación
        db.delete(db_quotation)
        db.commit()
    return db_quotation


def convert_quotation_to_sale(db: Session, quotation_id: int, user_id: int, payment_method: str):
    """Convierte una cotización en venta"""
    quotation = get_quotation(db, quotation_id)
    if not quotation or quotation.status != "aceptada":
        return None
    
    # Importar función de ventas
    from .crud_sales import create_sale_from_quotation
    
    sale = create_sale_from_quotation(db, quotation, user_id, payment_method)
    
    if sale:
        quotation.status = "convertida"
        db.commit()
    
    return sale


def convert_quotation_to_rental(db: Session, quotation_id: int, user_id: int, rental_data: dict):
    """Convierte una cotización de tipo alquiler en un alquiler"""
    quotation = get_quotation(db, quotation_id)
    if not quotation or quotation.status != "aceptada":
        return None
    
    # Verificar que sea una cotización de tipo alquiler
    if quotation.quotation_type != "alquiler":
        raise ValueError("Esta cotización no es de tipo alquiler")
    
    # Importar función de alquileres
    from .crud_rentals import create_rental_from_quotation
    
    rental = create_rental_from_quotation(db, quotation, user_id, rental_data)
    
    if rental:
        quotation.status = "convertida"
        db.commit()
    
    return rental


def check_expired_quotations(db: Session):
    """Marca cotizaciones vencidas"""
    today = datetime.now()
    expired = db.query(models.Quotation).filter(
        models.Quotation.status == "pendiente",
        models.Quotation.valid_until < today
    ).all()
    
    for quotation in expired:
        quotation.status = "vencida"
    
    db.commit()
    return len(expired)
