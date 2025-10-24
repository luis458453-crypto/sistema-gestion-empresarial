from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime
from . import models_extended as models, schemas_extended as schemas


def generate_sale_number(db: Session, organization_id: int = None) -> str:
    """Genera un número de venta único e infinito por organización (VEN-YYYYMMDD-01, 02, 03...)"""
    today = datetime.now()
    prefix = f"VEN-{today.year}{today.month:02d}{today.day:02d}"
    
    # Construir query base - buscar TODAS las ventas
    query = db.query(models.Sale).filter(
        models.Sale.sale_number.like("VEN-%")
    )
    
    # Filtrar por organización si se proporciona
    if organization_id:
        query = query.filter(models.Sale.organization_id == organization_id)
    
    # Obtener todas las ventas para encontrar el número más alto
    sales = query.all()
    
    if sales:
        # Extraer todos los números
        numbers = []
        for sale in sales:
            try:
                num = int(sale.sale_number.split('-')[-1])
                numbers.append(num)
            except (ValueError, IndexError):
                continue
        
        new_number = max(numbers) + 1 if numbers else 1
    else:
        new_number = 1
    
    # Formato: 01, 02, 03... 99, 100, 101... (sin límite)
    candidate = f"{prefix}-{new_number:02d}"
    
    # Verificar que no exista
    existing = db.query(models.Sale).filter(
        models.Sale.sale_number == candidate,
        models.Sale.organization_id == organization_id
    ).first()
    
    if existing:
        while existing:
            new_number += 1
            candidate = f"{prefix}-{new_number:02d}"
            existing = db.query(models.Sale).filter(
                models.Sale.sale_number == candidate,
                models.Sale.organization_id == organization_id
            ).first()
    
    return candidate


def generate_invoice_number(db: Session, organization_id: int = None) -> str:
    """Genera un número de factura único e infinito por organización (FAC-YYYYMMDD-01, 02, 03...)"""
    today = datetime.now()
    prefix = f"FAC-{today.year}{today.month:02d}{today.day:02d}"
    
    # Construir query base - buscar TODAS las facturas
    query = db.query(models.Sale).filter(
        models.Sale.invoice_number.like("FAC-%"),
        models.Sale.invoice_number.isnot(None)
    )
    
    # Filtrar por organización si se proporciona
    if organization_id:
        query = query.filter(models.Sale.organization_id == organization_id)
    
    # Obtener todas las facturas para encontrar el número más alto
    invoices = query.all()
    
    if invoices:
        # Extraer todos los números
        numbers = []
        for invoice in invoices:
            if invoice.invoice_number:
                try:
                    num = int(invoice.invoice_number.split('-')[-1])
                    numbers.append(num)
                except (ValueError, IndexError):
                    continue
        
        new_number = max(numbers) + 1 if numbers else 1
    else:
        new_number = 1
    
    # Formato: 01, 02, 03... 99, 100, 101... (sin límite)
    candidate = f"{prefix}-{new_number:02d}"
    
    # Verificar que no exista
    existing = db.query(models.Sale).filter(
        models.Sale.invoice_number == candidate,
        models.Sale.organization_id == organization_id
    ).first()
    
    if existing:
        while existing:
            new_number += 1
            candidate = f"{prefix}-{new_number:02d}"
            existing = db.query(models.Sale).filter(
                models.Sale.invoice_number == candidate,
                models.Sale.organization_id == organization_id
            ).first()
    
    return candidate


def get_sale(db: Session, sale_id: int):
    return db.query(models.Sale).join(models.Client, models.Sale.client_id == models.Client.id, isouter=True).filter(models.Sale.id == sale_id).first()


def get_sales(
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
    query = db.query(models.Sale).join(models.Client, models.Sale.client_id == models.Client.id, isouter=True)
    
    # Filtrar por organización
    if organization_id:
        query = query.filter(models.Sale.organization_id == organization_id)
    
    if client_id:
        query = query.filter(models.Sale.client_id == client_id)
    
    if status:
        query = query.filter(models.Sale.status == status)
    
    if start_date:
        query = query.filter(models.Sale.sale_date >= start_date)
    
    if end_date:
        query = query.filter(models.Sale.sale_date <= end_date)
    
    return query.order_by(desc(models.Sale.created_at)).offset(skip).limit(limit).all()


def create_sale(db: Session, sale: schemas.SaleCreate, user_id: int):
    # Obtener el usuario para acceder a su organization_id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    # Generar números por organización
    sale_number = generate_sale_number(db, user.organization_id)
    invoice_number = generate_invoice_number(db, user.organization_id)
    
    # Calcular totales
    subtotal = 0
    items_data = []
    
    for item in sale.items:
        # Verificar stock
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product or product.stock < item.quantity:
            raise ValueError(f"Stock insuficiente para el producto {product.name if product else 'desconocido'}")
        
        item_subtotal = item.quantity * item.unit_price
        if item.discount_percent > 0:
            item_subtotal -= item_subtotal * (item.discount_percent / 100)
        subtotal += item_subtotal
        items_data.append({
            **item.model_dump(),
            "subtotal": item_subtotal
        })
    
    # Calcular impuesto
    subtotal_after_discount = subtotal - sale.discount_amount
    tax_amount = subtotal_after_discount * (sale.tax_rate / 100)
    
    # Total
    total = subtotal_after_discount + tax_amount
    
    # Usar el estado que viene del frontend, pero validar coherencia
    if hasattr(sale.status, 'value'):
        # Si es un enum, obtener su valor
        status = sale.status.value
    else:
        # Si es string, usar directamente
        status = str(sale.status) if sale.status else "pendiente_pago"
    
    # Determinar balance basado en el estado y monto pagado
    if status == "completada":
        paid_amount = total
        balance = 0
    elif status == "parcial":
        paid_amount = sale.paid_amount if hasattr(sale, 'paid_amount') and sale.paid_amount > 0 else 0
        balance = total - paid_amount
    elif status == "pendiente_pago":
        paid_amount = 0
        balance = total
    elif status == "cancelada":
        paid_amount = 0
        balance = 0
    else:
        # Fallback: determinar automáticamente si el estado no es válido
        if str(sale.payment_method) == "credito":
            status = "pendiente_pago"
            paid_amount = 0
            balance = total
        else:
            status = "completada"
            paid_amount = total
            balance = 0
    
    # Crear venta
    sale_dict = sale.model_dump(exclude={'items'})
    # Actualizar el status en el diccionario para evitar duplicados
    sale_dict['status'] = status
    sale_dict['paid_amount'] = paid_amount
    
    db_sale = models.Sale(
        **sale_dict,
        sale_number=sale_number,
        invoice_number=invoice_number,
        created_by=user_id,
        organization_id=user.organization_id,  # Asignar organization_id del usuario
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        balance=balance
    )
    
    db.add(db_sale)
    db.flush()
    
    # Crear items y actualizar stock
    for item_data in items_data:
        # Obtener el producto para guardar su nombre
        product = db.query(models.Product).filter(models.Product.id == item_data['product_id']).first()
        
        db_item = models.SaleItem(
            sale_id=db_sale.id,
            product_name=product.name if product else None,  # Guardar nombre del producto
            **item_data
        )
        db.add(db_item)
        
        # Actualizar stock del producto
        previous_stock = product.stock
        product.stock -= item_data['quantity']
        
        # Si el producto es tipo "ambos", también actualizar stock_available
        if product.product_type == "ambos":
            product.stock_available -= item_data['quantity']
        
        # Registrar movimiento de inventario
        movement = models.InventoryMovement(
            product_id=product.id,
            user_id=user_id,
            movement_type="venta",
            quantity=item_data['quantity'],
            previous_stock=previous_stock,
            new_stock=product.stock,
            reference_type="sale",
            reference_id=db_sale.id,
            reason=f"Venta {sale_number}",
            organization_id=user.organization_id
        )
        db.add(movement)
    
    db.commit()
    db.refresh(db_sale)
    return db_sale


def create_sale_from_quotation(db: Session, quotation: models.Quotation, user_id: int, payment_method: str):
    """Crea una venta desde una cotización"""
    # Crear items desde la cotización
    items = []
    for item in quotation.items:
        items.append(schemas.SaleItemCreate(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_percent=item.discount_percent
        ))
    
    # Usar el método de pago de la cotización si no se especifica uno
    final_payment_method = payment_method if payment_method else quotation.payment_method
    
    # SIEMPRE crear la venta en estado pendiente_pago
    # El usuario debe confirmar el pago manualmente en la sección de ventas
    initial_status = "pendiente_pago"
    
    # Crear venta
    sale_data = schemas.SaleCreate(
        client_id=quotation.client_id,
        quotation_id=quotation.id,
        tax_rate=quotation.tax_rate,
        discount_amount=quotation.discount_amount,
        payment_method=final_payment_method,
        status=initial_status,
        items=items
    )
    
    return create_sale(db, sale_data, user_id)


def update_sale(db: Session, sale_id: int, sale: schemas.SaleUpdate):
    db_sale = get_sale(db, sale_id)
    if db_sale:
        update_data = sale.model_dump(exclude_unset=True)
        
        # Si se actualiza el estado a cancelada, devolver stock y registrar movimientos
        if 'status' in update_data and update_data['status'] == 'cancelada':
            # Solo devolver stock si la venta no estaba previamente cancelada
            if db_sale.status != 'cancelada':
                # Devolver stock de todos los items de la venta
                for item in db_sale.items:
                    product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
                    if product:
                        previous_stock = product.stock
                        product.stock += item.quantity  # Devolver la cantidad al stock
                        
                        # Si el producto es tipo "ambos", también devolver stock_available
                        if product.product_type == "ambos":
                            product.stock_available += item.quantity
                        
                        # Registrar movimiento de inventario por cancelación
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            user_id=db_sale.created_by,
                            movement_type="devolucion",
                            quantity=item.quantity,
                            previous_stock=previous_stock,
                            new_stock=product.stock,
                            reference_type="sale_cancellation",
                            reference_id=db_sale.id,
                            reason=f"Cancelación de venta {db_sale.sale_number}",
                            organization_id=db_sale.organization_id
                        )
                        db.add(movement)
            
            db_sale.paid_amount = 0
            db_sale.balance = 0
        
        # Si se actualiza el monto pagado, recalcular balance y estado
        elif 'paid_amount' in update_data:
            db_sale.paid_amount = update_data['paid_amount']
            db_sale.balance = db_sale.total - db_sale.paid_amount
            
            if db_sale.balance == 0:
                db_sale.status = "completada"
            elif db_sale.paid_amount > 0:
                db_sale.status = "parcial"
            else:
                db_sale.status = "pendiente_pago"
        
        for field, value in update_data.items():
            if field != 'paid_amount':
                setattr(db_sale, field, value)
        
        db.commit()
        db.refresh(db_sale)
    return db_sale


def add_payment(db: Session, payment: schemas.PaymentCreate):
    """Registra un pago para una venta"""
    sale = get_sale(db, payment.sale_id)
    if not sale:
        return None
    
    # Crear pago
    db_payment = models.Payment(**payment.model_dump())
    db.add(db_payment)
    
    # Actualizar venta
    sale.paid_amount += payment.amount
    sale.balance = sale.total - sale.paid_amount
    
    if sale.balance == 0:
        sale.status = "completada"
    elif sale.paid_amount > 0:
        sale.status = "parcial"
    
    db.commit()
    db.refresh(db_payment)
    return db_payment


def get_sales_report(db: Session, start_date: datetime, end_date: datetime):
    """Genera reporte de ventas"""
    sales = get_sales(db, start_date=start_date, end_date=end_date, limit=10000)
    
    total_sales = len(sales)
    total_amount = sum(sale.total for sale in sales)
    total_paid = sum(sale.paid_amount for sale in sales)
    total_pending = sum(sale.balance for sale in sales)
    
    # Ventas por estado
    by_status = {}
    for sale in sales:
        by_status[sale.status] = by_status.get(sale.status, 0) + 1
    
    # Ventas por método de pago
    by_payment = {}
    for sale in sales:
        by_payment[sale.payment_method] = by_payment.get(sale.payment_method, 0) + 1
    
    return {
        "total_sales": total_sales,
        "total_amount": round(total_amount, 2),
        "total_paid": round(total_paid, 2),
        "total_pending": round(total_pending, 2),
        "by_status": by_status,
        "by_payment_method": by_payment,
        "sales": sales
    }
