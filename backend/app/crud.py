from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from .auth import get_password_hash

# Usar modelos extendidos por defecto
from . import models_extended as models
from . import schemas_extended as schemas


# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100, organization_id: Optional[int] = None):
    query = db.query(models.User)
    
    # Filtrar por organización si se proporciona
    if organization_id is not None:
        query = query.filter(models.User.organization_id == organization_id)
    
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Category CRUD
def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100, organization_id: Optional[int] = None):
    query = db.query(models.Category)
    
    # No filtrar si organization_id es None (superadmin ve todo)
    # Si tiene organization_id, filtrar por ese ID
    if organization_id:
        query = query.filter(models.Category.organization_id == organization_id)
    
    return query.offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate, organization_id: Optional[int] = None):
    category_data = category.model_dump()
    category_data['organization_id'] = organization_id
    db_category = models.Category(**category_data)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: schemas.CategoryUpdate):
    db_category = get_category(db, category_id)
    if db_category:
        update_data = category.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        db.commit()
        db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category


# Supplier CRUD
def get_supplier(db: Session, supplier_id: int):
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()


def get_suppliers(db: Session, skip: int = 0, limit: int = 100, organization_id: Optional[int] = None):
    query = db.query(models.Supplier)
    
    # No filtrar si organization_id es None (superadmin ve todo)
    if organization_id:
        query = query.filter(models.Supplier.organization_id == organization_id)
    
    return query.offset(skip).limit(limit).all()


def create_supplier(db: Session, supplier: schemas.SupplierCreate, organization_id: Optional[int] = None):
    supplier_data = supplier.model_dump()
    supplier_data['organization_id'] = organization_id
    db_supplier = models.Supplier(**supplier_data)
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def update_supplier(db: Session, supplier_id: int, supplier: schemas.SupplierUpdate):
    db_supplier = get_supplier(db, supplier_id)
    if db_supplier:
        update_data = supplier.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_supplier, field, value)
        db.commit()
        db.refresh(db_supplier)
    return db_supplier


def delete_supplier(db: Session, supplier_id: int):
    db_supplier = get_supplier(db, supplier_id)
    if db_supplier:
        db.delete(db_supplier)
        db.commit()
    return db_supplier


# Product CRUD
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_product_by_sku(db: Session, sku: str, organization_id: Optional[int] = None):
    query = db.query(models.Product).filter(
        models.Product.sku == sku,
        models.Product.is_active == True  # Solo buscar productos activos
    )
    if organization_id:
        query = query.filter(models.Product.organization_id == organization_id)
    return query.first()


def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, 
    organization_id: Optional[int] = None,
    product_type: Optional[str] = None,
    stock_available_gt: Optional[int] = None
):
    query = db.query(models.Product)
    
    # Filtrar por organización (igual que categorías)
    if organization_id:
        query = query.filter(models.Product.organization_id == organization_id)
    
    # Filtrar solo productos activos
    query = query.filter(models.Product.is_active == True)
    
    # SIMPLIFICADO: Solo filtros básicos
    return query.offset(skip).limit(limit).all()


def get_low_stock_products(db: Session):
    return db.query(models.Product).filter(
        models.Product.stock <= models.Product.min_stock,
        models.Product.is_active == True
    ).all()


def create_product(db: Session, product: schemas.ProductCreate, organization_id: int):
    product_data = product.model_dump()
    product_data['organization_id'] = organization_id
    
    # Para productos de solo alquiler, establecer price como 0 si es None o no está definido
    if product_data.get('product_type') == 'alquiler':
        if product_data.get('price') is None or product_data.get('price') == 0:
            product_data['price'] = 0.0
    
    # Inicializar stock_available igual al stock inicial
    if 'stock_available' not in product_data or product_data['stock_available'] is None:
        product_data['stock_available'] = product_data.get('stock', 0)
    
    db_product = models.Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if db_product:
        update_data = product.model_dump(exclude_unset=True)
        
        # Si se actualiza el stock, ajustar stock_available proporcionalmente
        if 'stock' in update_data:
            old_stock = db_product.stock
            new_stock = update_data['stock']
            
            # Calcular cuántos productos están alquilados
            # Asegurar que rented nunca sea negativo (stock_available no puede ser mayor que stock)
            rented = max(0, old_stock - db_product.stock_available)
            
            # Ajustar stock_available manteniendo la cantidad alquilada
            # Asegurar que stock_available nunca exceda el stock total
            update_data['stock_available'] = min(new_stock, max(0, new_stock - rented))
        
        for field, value in update_data.items():
            setattr(db_product, field, value)
        db.commit()
        db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if db_product:
        # Verificar si el producto tiene referencias en ventas, alquileres, cotizaciones, etc.
        has_sales = db.query(models.SaleItem).filter(models.SaleItem.product_id == product_id).first() is not None
        has_rentals = db.query(models.Rental).filter(models.Rental.product_id == product_id).first() is not None
        has_quotations = db.query(models.QuotationItem).filter(models.QuotationItem.product_id == product_id).first() is not None
        has_movements = db.query(models.InventoryMovement).filter(models.InventoryMovement.product_id == product_id).first() is not None
        
        # Si tiene referencias, solo desactivar para mantener datos históricos
        if has_sales or has_rentals or has_quotations or has_movements:
            db_product.is_active = False
            db.commit()
            db.refresh(db_product)
        else:
            # Si no tiene referencias, eliminar completamente
            db.delete(db_product)
            db.commit()
    return db_product


# Inventory Movement CRUD
def create_inventory_movement(
    db: Session,
    product_id: int,
    user_id: int,
    movement_type: str,
    quantity: int,
    reason: Optional[str] = None,
    organization_id: Optional[int] = None
):
    product = get_product(db, product_id)
    if not product:
        return None
    
    previous_stock = product.stock
    previous_stock_available = product.stock_available
    
    if movement_type == "entrada":
        new_stock = previous_stock + quantity
        new_stock_available = previous_stock_available + quantity
    elif movement_type == "salida":
        new_stock = previous_stock - quantity
        new_stock_available = previous_stock_available - quantity
        if new_stock < 0:
            raise ValueError("Stock insuficiente")
        if new_stock_available < 0:
            raise ValueError("Stock disponible insuficiente")
    elif movement_type == "ajuste":
        # Para ajustes, mantener la proporción de productos alquilados
        rented = previous_stock - previous_stock_available
        new_stock = quantity
        new_stock_available = max(0, new_stock - rented)
    else:
        raise ValueError("Tipo de movimiento inválido")
    
    # Actualizar stock del producto
    product.stock = new_stock
    product.stock_available = new_stock_available
    
    # Crear movimiento
    db_movement = models.InventoryMovement(
        product_id=product_id,
        user_id=user_id,
        movement_type=movement_type,
        quantity=quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        reason=reason,
        organization_id=organization_id
    )
    
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement


def get_inventory_movements(db: Session, skip: int = 0, limit: int = 100, product_id: Optional[int] = None, organization_id: Optional[int] = None):
    query = db.query(models.InventoryMovement)
    
    # Filtrar por organización
    if organization_id:
        query = query.filter(models.InventoryMovement.organization_id == organization_id)
    
    if product_id:
        query = query.filter(models.InventoryMovement.product_id == product_id)
    
    return query.order_by(desc(models.InventoryMovement.created_at)).offset(skip).limit(limit).all()


# Dashboard Stats
def get_dashboard_stats(db: Session, organization_id: Optional[int] = None):
    # Query base para productos
    products_query = db.query(func.count(models.Product.id)).filter(models.Product.is_active == True)
    if organization_id is not None:
        products_query = products_query.filter(models.Product.organization_id == organization_id)
    total_products = products_query.scalar()
    
    # Query para valor total
    value_query = db.query(func.sum(models.Product.price * models.Product.stock)).filter(
        models.Product.is_active == True
    )
    if organization_id is not None:
        value_query = value_query.filter(models.Product.organization_id == organization_id)
    total_value = value_query.scalar() or 0
    
    # Query para productos con stock bajo
    low_stock_query = db.query(func.count(models.Product.id)).filter(
        models.Product.stock <= models.Product.min_stock,
        models.Product.is_active == True
    )
    if organization_id is not None:
        low_stock_query = low_stock_query.filter(models.Product.organization_id == organization_id)
    low_stock_products = low_stock_query.scalar()
    
    # Query para categorías
    categories_query = db.query(func.count(models.Category.id))
    if organization_id is not None:
        categories_query = categories_query.filter(models.Category.organization_id == organization_id)
    total_categories = categories_query.scalar()
    
    # Query para proveedores
    suppliers_query = db.query(func.count(models.Supplier.id))
    if organization_id is not None:
        suppliers_query = suppliers_query.filter(models.Supplier.organization_id == organization_id)
    total_suppliers = suppliers_query.scalar()
    
    # Movimientos de los últimos 7 días
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    movements_query = db.query(func.count(models.InventoryMovement.id)).filter(
        models.InventoryMovement.created_at >= seven_days_ago
    )
    if organization_id is not None:
        movements_query = movements_query.filter(models.InventoryMovement.organization_id == organization_id)
    recent_movements = movements_query.scalar()
    
    return {
        "total_products": total_products,
        "total_value": round(total_value, 2),
        "low_stock_products": low_stock_products,
        "total_categories": total_categories,
        "total_suppliers": total_suppliers,
        "recent_movements": recent_movements
    }
