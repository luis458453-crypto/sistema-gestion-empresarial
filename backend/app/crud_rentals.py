from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from . import models_extended as models, schemas_extended as schemas


def generate_rental_number(db: Session, organization_id: int = None) -> str:
    """Genera un número de alquiler único e infinito por organización (ALQ-YYYYMMDD-01, 02, 03...)"""
    today = datetime.now()
    prefix = f"ALQ-{today.year}{today.month:02d}{today.day:02d}"
    
    # Construir query base - buscar TODOS los alquileres
    query = db.query(models.Rental).filter(
        models.Rental.rental_number.like("ALQ-%")
    )
    
    # Filtrar por organización si se proporciona
    if organization_id:
        query = query.filter(models.Rental.organization_id == organization_id)
    
    # Obtener todos los alquileres para encontrar el número más alto
    rentals = query.all()
    
    if rentals:
        # Extraer todos los números
        numbers = []
        for rental in rentals:
            try:
                num = int(rental.rental_number.split('-')[-1])
                numbers.append(num)
            except (ValueError, IndexError):
                continue
        
        new_number = max(numbers) + 1 if numbers else 1
    else:
        new_number = 1
    
    # Formato: 01, 02, 03... 99, 100, 101... (sin límite)
    candidate = f"{prefix}-{new_number:02d}"
    
    # Verificar que no exista
    existing = db.query(models.Rental).filter(
        models.Rental.rental_number == candidate,
        models.Rental.organization_id == organization_id
    ).first()
    
    if existing:
        while existing:
            new_number += 1
            candidate = f"{prefix}-{new_number:02d}"
            existing = db.query(models.Rental).filter(
                models.Rental.rental_number == candidate,
                models.Rental.organization_id == organization_id
            ).first()
    
    return candidate


def get_rental(db: Session, rental_id: int):
    return db.query(models.Rental).join(
        models.Client, models.Rental.client_id == models.Client.id, isouter=True
    ).join(
        models.Product, models.Rental.product_id == models.Product.id, isouter=True
    ).filter(models.Rental.id == rental_id).first()


def get_rentals(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    organization_id: Optional[int] = None
):
    # Hacer join con las tablas de clientes y productos para incluir toda la información
    query = db.query(models.Rental).join(
        models.Client, models.Rental.client_id == models.Client.id, isouter=True
    ).join(
        models.Product, models.Rental.product_id == models.Product.id, isouter=True
    )
    
    # Filtrar por organización (multi-tenant)
    if organization_id:
        query = query.filter(models.Rental.organization_id == organization_id)
    
    if client_id:
        query = query.filter(models.Rental.client_id == client_id)
    
    if product_id:
        query = query.filter(models.Rental.product_id == product_id)
    
    if status:
        query = query.filter(models.Rental.status == status)
    
    if start_date:
        query = query.filter(models.Rental.start_date >= start_date)
    
    if end_date:
        query = query.filter(models.Rental.start_date <= end_date)
    
    return query.order_by(desc(models.Rental.created_at)).offset(skip).limit(limit).all()


def create_rental(db: Session, rental: schemas.RentalCreate, user_id: int):
    # Obtener el usuario para acceder a su organization_id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    # Calcular días
    days = (rental.end_date - rental.start_date).days
    if days <= 0:
        days = 1
    
    # Verificar si tiene items (nuevo formato) o product_id (formato antiguo)
    if rental.items and len(rental.items) > 0:
        # NUEVO: Múltiples items
        # Verificar disponibilidad de todos los productos
        for item in rental.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if not product:
                raise ValueError(f"Producto {item.product_id} no encontrado")
            
            if product.product_type not in ["alquiler", "ambos"]:
                raise ValueError(f"El producto {product.name} no está disponible para alquiler")
            
            if product.stock_available < item.quantity:
                raise ValueError(f"No hay suficiente stock de {product.name}. Disponible: {product.stock_available}, Solicitado: {item.quantity}")
        
        # Generar número de alquiler
        rental_number = generate_rental_number(db, user.organization_id)
        
        # Calcular subtotal de todos los items
        subtotal = sum(item.quantity * item.unit_price * days for item in rental.items)
        
        # Calcular impuestos y descuentos
        tax_amount = subtotal * (rental.tax_rate / 100) if rental.tax_rate else 0
        
        # Calcular descuento (priorizar discount_percent sobre discount)
        if hasattr(rental, 'discount_percent') and rental.discount_percent > 0:
            discount_amount = subtotal * (rental.discount_percent / 100)
        else:
            discount_amount = rental.discount if rental.discount else 0
        
        total_cost = subtotal + tax_amount - discount_amount
        
        # Determinar pagos y estado de pago
        paid_amount = rental.deposit
        balance = total_cost - paid_amount
        
        if paid_amount >= total_cost:
            payment_status = "pagado"
        elif paid_amount > 0:
            payment_status = "parcial"
        else:
            payment_status = "pendiente_pago"
        
        # Crear alquiler principal (sin product_id específico para múltiples items)
        db_rental = models.Rental(
            client_id=rental.client_id,
            product_id=None,  # NULL para alquileres con múltiples items
            start_date=rental.start_date,
            end_date=rental.end_date,
            rental_period=rental.rental_period,
            rental_price=None,  # NULL para alquileres con múltiples items
            deposit=rental.deposit,
            tax_rate=rental.tax_rate,
            discount=discount_amount,  # Guardar el monto calculado del descuento
            discount_percent=rental.discount_percent,  # Guardar el porcentaje del descuento
            payment_method=rental.payment_method,
            notes=rental.notes,
            condition_out=rental.condition_out,
            rental_number=rental_number,
            created_by=user_id,
            organization_id=user.organization_id,
            total_cost=total_cost,
            paid_amount=paid_amount,
            balance=balance,
            payment_status=payment_status
        )
        
        db.add(db_rental)
        db.flush()
        
        # Crear items del alquiler y actualizar stock
        for item in rental.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            
            # Crear item del alquiler
            db_item = models.RentalItem(
                rental_id=db_rental.id,
                product_id=item.product_id,
                product_name=product.name if product else None,  # Guardar nombre del producto
                quantity=item.quantity,
                rental_days=days,
                unit_price=item.unit_price,
                organization_id=user.organization_id
            )
            db.add(db_item)
            
            # Actualizar stock
            previous_stock = product.stock_available
            product.stock_available -= item.quantity
            
            # Si el producto es tipo "ambos", también actualizar stock
            if product.product_type == "ambos":
                product.stock -= item.quantity
            
            # Registrar movimiento de inventario
            movement = models.InventoryMovement(
                product_id=product.id,
                user_id=user_id,
                movement_type="alquiler",
                quantity=item.quantity,
                previous_stock=previous_stock,
                new_stock=product.stock_available,
                reference_type="rental",
                reference_id=db_rental.id,
                reason=f"Alquiler {rental_number}",
                organization_id=user.organization_id
            )
            db.add(movement)
        
        db.commit()
        db.refresh(db_rental)
        return db_rental
        
    else:
        # ANTIGUO: Un solo producto (compatibilidad hacia atrás)
        if not rental.product_id:
            raise ValueError("Debe especificar un producto o una lista de items")
        
        product = db.query(models.Product).filter(models.Product.id == rental.product_id).first()
        if not product:
            raise ValueError("Producto no encontrado")
        
        if product.product_type not in ["alquiler", "ambos"]:
            raise ValueError("Este producto no está disponible para alquiler")
        
        if product.stock_available <= 0:
            raise ValueError(f"No hay stock disponible para alquilar. Stock disponible: {product.stock_available}, Stock total: {product.stock}")
        
        # Generar número de alquiler
        rental_number = generate_rental_number(db, user.organization_id)
        
        # Calcular costo total
        if rental.rental_period == "daily":
            subtotal = rental.rental_price * days
        elif rental.rental_period == "weekly":
            weeks = days / 7
            subtotal = rental.rental_price * weeks
        elif rental.rental_period == "monthly":
            months = days / 30
            subtotal = rental.rental_price * months
        else:
            subtotal = rental.rental_price
        
        # Calcular impuestos y descuentos
        tax_amount = subtotal * (rental.tax_rate / 100) if rental.tax_rate else 0
        
        # Calcular descuento (priorizar discount_percent sobre discount)
        if hasattr(rental, 'discount_percent') and rental.discount_percent > 0:
            discount_amount = subtotal * (rental.discount_percent / 100)
        else:
            discount_amount = rental.discount if rental.discount else 0
        
        total_cost = subtotal + tax_amount - discount_amount
        
        # Determinar pagos y estado de pago
        paid_amount = rental.deposit
        balance = total_cost - paid_amount
        
        if paid_amount >= total_cost:
            payment_status = "pagado"
        elif paid_amount > 0:
            payment_status = "parcial"
        else:
            payment_status = "pendiente_pago"
        
        # Crear alquiler
        rental_dict = rental.model_dump(exclude={'items'})
        db_rental = models.Rental(
            **rental_dict,
            rental_number=rental_number,
            created_by=user_id,
            organization_id=user.organization_id,
            total_cost=total_cost,
            paid_amount=paid_amount,
            balance=balance,
            payment_status=payment_status
        )
        
        db.add(db_rental)
        db.flush()
        
        # Actualizar stock disponible del producto
        previous_stock = product.stock_available
        product.stock_available -= 1
        
        # Si el producto es tipo "ambos", también actualizar stock
        if product.product_type == "ambos":
            product.stock -= 1
        
        # Registrar movimiento de inventario
        movement = models.InventoryMovement(
            product_id=product.id,
            user_id=user_id,
            movement_type="alquiler",
            quantity=1,
            previous_stock=previous_stock,
            new_stock=product.stock_available,
            reference_type="rental",
            reference_id=db_rental.id,
            reason=f"Alquiler {rental_number}",
            organization_id=user.organization_id
        )
        db.add(movement)
        
        db.commit()
        db.refresh(db_rental)
        return db_rental


def cancel_rental(db: Session, rental_id: int, user_id: int):
    """Cancela un alquiler y devuelve el stock"""
    # Obtener el usuario
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    # Obtener el alquiler
    rental = db.query(models.Rental).filter(models.Rental.id == rental_id).first()
    if not rental:
        raise ValueError("Alquiler no encontrado")
    
    # Verificar permisos
    if rental.organization_id != user.organization_id:
        raise ValueError("No tienes permisos para cancelar este alquiler")
    
    # Verificar que no esté ya cancelado
    if rental.status == "cancelado":
        raise ValueError("El alquiler ya está cancelado")
    
    # Devolver stock de los items
    if rental.items and len(rental.items) > 0:
        # Nuevo formato: múltiples items
        for item in rental.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                previous_stock = product.stock_available
                product.stock_available += item.quantity
                
                # Si el producto es tipo "ambos", también restaurar stock
                if product.product_type == "ambos":
                    product.stock += item.quantity
                
                # Registrar movimiento de inventario
                movement = models.InventoryMovement(
                    product_id=product.id,
                    user_id=user_id,
                    movement_type="cancelacion_alquiler",
                    quantity=item.quantity,
                    previous_stock=previous_stock,
                    new_stock=product.stock_available,
                    reference_type="rental",
                    reference_id=rental.id,
                    reason=f"Cancelación de alquiler {rental.rental_number}",
                    organization_id=user.organization_id
                )
                db.add(movement)
    elif rental.product_id:
        # Formato antiguo: un solo producto
        product = db.query(models.Product).filter(models.Product.id == rental.product_id).first()
        if product:
            previous_stock = product.stock_available
            product.stock_available += 1
            
            # Si el producto es tipo "ambos", también restaurar stock
            if product.product_type == "ambos":
                product.stock += 1
            
            # Registrar movimiento de inventario
            movement = models.InventoryMovement(
                product_id=product.id,
                user_id=user_id,
                movement_type="cancelacion_alquiler",
                quantity=1,
                previous_stock=previous_stock,
                new_stock=product.stock_available,
                reference_type="rental",
                reference_id=rental.id,
                reason=f"Cancelación de alquiler {rental.rental_number}",
                organization_id=user.organization_id
            )
            db.add(movement)
    
    # Cambiar estado a cancelado
    rental.status = "cancelado"
    
    # Limpiar balance pendiente (ya que se cancela, no se espera pago)
    rental.balance = 0
    rental.payment_status = "cancelado"
    
    db.commit()
    db.refresh(rental)
    return rental


def add_rental_payment(db: Session, rental_id: int, payment: schemas.RentalPaymentCreate, user_id: int):
    """Agrega un pago a un alquiler"""
    # Obtener el usuario para acceder a su organization_id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    # Verificar que el alquiler existe
    rental = db.query(models.Rental).filter(models.Rental.id == rental_id).first()
    if not rental:
        raise ValueError("Alquiler no encontrado")
    
    # Verificar que el alquiler pertenece a la organización del usuario
    if rental.organization_id != user.organization_id:
        raise ValueError("No tienes permisos para modificar este alquiler")
    
    # Crear el pago
    payment_dict = payment.model_dump()
    db_payment = models.RentalPayment(
        **payment_dict,
        organization_id=user.organization_id
    )
    
    db.add(db_payment)
    db.flush()
    
    # Actualizar el alquiler
    rental.paid_amount += payment.amount
    rental.balance = rental.total_cost - rental.paid_amount
    
    # Actualizar estado de pago
    if rental.paid_amount >= rental.total_cost:
        rental.payment_status = "pagado"
    elif rental.paid_amount > 0:
        rental.payment_status = "parcial"
    else:
        rental.payment_status = "pendiente_pago"
    
    db.commit()
    db.refresh(rental)
    db.refresh(db_payment)
    
    return db_payment


def update_rental_status_automatically(db: Session, organization_id: int = None):
    """Actualiza automáticamente el estado de los alquileres vencidos"""
    from datetime import datetime
    
    query = db.query(models.Rental)
    
    if organization_id:
        query = query.filter(models.Rental.organization_id == organization_id)
    
    # Buscar alquileres activos que ya pasaron su fecha de fin
    expired_rentals = query.filter(
        models.Rental.status == "activo",
        models.Rental.end_date < datetime.utcnow()
    ).all()
    
    updated_count = 0
    for rental in expired_rentals:
        rental.status = "vencido"
        updated_count += 1
    
    db.commit()
    return updated_count


def update_rental(db: Session, rental_id: int, rental: schemas.RentalUpdate, user_id: int):
    db_rental = get_rental(db, rental_id)
    if not db_rental:
        return None
    
    # Obtener el usuario para acceder a su organization_id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    update_data = rental.model_dump(exclude_unset=True)
    
    # Si se marca como devuelto, actualizar stock
    if 'status' in update_data and update_data['status'] == 'devuelto' and db_rental.status != 'devuelto':
        # Verificar si tiene múltiples items o un solo producto
        if db_rental.items and len(db_rental.items) > 0:
            # NUEVO: Alquiler con múltiples items
            for item in db_rental.items:
                product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
                if product:
                    previous_stock = product.stock_available
                    product.stock_available += item.quantity
                    
                    # Si el producto es tipo "ambos", también restaurar stock
                    if product.product_type == "ambos":
                        product.stock += item.quantity
                    
                    # Registrar movimiento de devolución
                    movement = models.InventoryMovement(
                        product_id=product.id,
                        user_id=user_id,
                        movement_type="devolucion",
                        quantity=item.quantity,
                        previous_stock=previous_stock,
                        new_stock=product.stock_available,
                        reference_type="rental",
                        reference_id=db_rental.id,
                        reason=f"Devolución de alquiler {db_rental.rental_number} - {product.name}",
                        organization_id=user.organization_id
                    )
                    db.add(movement)
        elif db_rental.product_id:
            # ANTIGUO: Alquiler con un solo producto
            product = db.query(models.Product).filter(models.Product.id == db_rental.product_id).first()
            if product:
                previous_stock = product.stock_available
                product.stock_available += 1
                
                # Si el producto es tipo "ambos", también restaurar stock
                if product.product_type == "ambos":
                    product.stock += 1
                
                # Registrar movimiento de devolución
                movement = models.InventoryMovement(
                    product_id=product.id,
                    user_id=user_id,
                    movement_type="devolucion",
                    quantity=1,
                    previous_stock=previous_stock,
                    new_stock=product.stock_available,
                    reference_type="rental",
                    reference_id=db_rental.id,
                    reason=f"Devolución de alquiler {db_rental.rental_number}",
                    organization_id=user.organization_id
                )
                db.add(movement)
        
        # Establecer la fecha de devolución si no está en los datos de actualización
        if 'actual_return_date' not in update_data:
            db_rental.actual_return_date = datetime.now()
    
    # Actualizar pagos si se especifica
    if 'paid_amount' in update_data:
        db_rental.paid_amount = update_data['paid_amount']
        db_rental.balance = db_rental.total_cost - db_rental.paid_amount
        
        # Actualizar estado de pago
        if db_rental.paid_amount >= db_rental.total_cost:
            db_rental.payment_status = "pagado"
        elif db_rental.paid_amount > 0:
            db_rental.payment_status = "parcial"
        else:
            db_rental.payment_status = "pendiente_pago"
    
    for field, value in update_data.items():
        if field != 'paid_amount':
            setattr(db_rental, field, value)
    
    db.commit()
    db.refresh(db_rental)
    return db_rental


def check_overdue_rentals(db: Session):
    """Marca alquileres vencidos"""
    today = datetime.now()
    overdue = db.query(models.Rental).filter(
        models.Rental.status == "activo",
        models.Rental.end_date < today
    ).all()
    
    for rental in overdue:
        rental.status = "vencido"
    
    db.commit()
    return len(overdue)


def get_rental_history(db: Session, product_id: int):
    """Obtiene el historial de alquileres de un producto"""
    return db.query(models.Rental).filter(
        models.Rental.product_id == product_id
    ).order_by(desc(models.Rental.created_at)).all()


def get_client_rental_history(db: Session, client_id: int):
    """Obtiene el historial de alquileres de un cliente"""
    return db.query(models.Rental).filter(
        models.Rental.client_id == client_id
    ).order_by(desc(models.Rental.created_at)).all()


def get_active_rentals_report(db: Session):
    """Genera reporte de alquileres activos"""
    active_rentals = get_rentals(db, status="activo", limit=10000)
    overdue_rentals = get_rentals(db, status="vencido", limit=10000)
    
    total_active = len(active_rentals)
    total_overdue = len(overdue_rentals)
    total_revenue = sum(rental.paid_amount for rental in active_rentals + overdue_rentals)
    total_pending = sum(rental.balance for rental in active_rentals + overdue_rentals)
    
    return {
        "total_active": total_active,
        "total_overdue": total_overdue,
        "total_revenue": round(total_revenue, 2),
        "total_pending": round(total_pending, 2),
        "active_rentals": active_rentals,
        "overdue_rentals": overdue_rentals
    }


def create_rental_from_quotation(db: Session, quotation: models.Quotation, user_id: int, rental_data: dict):
    """Crea un alquiler desde una cotización"""
    # Obtener el usuario para acceder a su organization_id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    # Generar número de alquiler
    rental_number = generate_rental_number(db, user.organization_id)
    
    # Extraer datos del rental_data
    start_date = rental_data.get('start_date')
    end_date = rental_data.get('end_date')
    rental_period = rental_data.get('rental_period', 'daily')
    deposit = rental_data.get('deposit', 0)
    payment_method = rental_data.get('payment_method', quotation.payment_method)
    
    if not start_date or not end_date:
        raise ValueError("Debe especificar fechas de inicio y fin para el alquiler")
    
    # Calcular días
    days = (end_date - start_date).days
    if days <= 0:
        days = 1
    
    # Crear items del alquiler desde los items de la cotización
    items_data = []
    for item in quotation.items:
        # Verificar disponibilidad del producto
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise ValueError(f"Producto {item.product_id} no encontrado")
        
        if product.product_type not in ["alquiler", "ambos"]:
            raise ValueError(f"El producto {product.name} no está disponible para alquiler")
        
        if product.stock_available < item.quantity:
            raise ValueError(f"No hay suficiente stock de {product.name}. Disponible: {product.stock_available}, Solicitado: {item.quantity}")
        
        items_data.append({
            'product_id': item.product_id,
            'quantity': item.quantity,
            'unit_price': item.unit_price
        })
    
    # Calcular subtotal de todos los items
    subtotal = sum(item['quantity'] * item['unit_price'] * days for item in items_data)
    
    # Calcular impuestos (usar la tasa de la cotización)
    tax_amount = subtotal * (quotation.tax_rate / 100) if quotation.tax_rate else 0
    
    # Calcular descuento (convertir porcentaje de cotización a monto)
    discount_amount = subtotal * (quotation.discount_percent / 100) if quotation.discount_percent else 0
    
    # Total
    total_cost = subtotal + tax_amount - discount_amount
    
    # Determinar pagos y estado de pago
    paid_amount = deposit
    balance = total_cost - paid_amount
    
    if paid_amount >= total_cost:
        payment_status = "pagado"
    elif paid_amount > 0:
        payment_status = "parcial"
    else:
        payment_status = "pendiente_pago"
    
    # Crear alquiler principal
    db_rental = models.Rental(
        rental_number=rental_number,
        quotation_id=quotation.id,
        client_id=quotation.client_id,
        product_id=None,  # NULL para alquileres con múltiples items
        start_date=start_date,
        end_date=end_date,
        rental_period=rental_period,
        rental_price=None,  # NULL para alquileres con múltiples items
        deposit=deposit,
        tax_rate=quotation.tax_rate,
        discount=discount_amount,
        payment_method=payment_method,
        notes=quotation.notes,
        condition_out=rental_data.get('condition_out'),
        created_by=user_id,
        organization_id=user.organization_id,
        total_cost=total_cost,
        paid_amount=paid_amount,
        balance=balance,
        payment_status=payment_status
    )
    
    db.add(db_rental)
    db.flush()
    
    # Crear items del alquiler y actualizar stock
    for item_data in items_data:
        product = db.query(models.Product).filter(models.Product.id == item_data['product_id']).first()
        
        # Crear item del alquiler
        db_item = models.RentalItem(
            rental_id=db_rental.id,
            product_id=item_data['product_id'],
            product_name=product.name if product else None,  # Guardar nombre del producto
            quantity=item_data['quantity'],
            rental_days=days,
            unit_price=item_data['unit_price'],
            organization_id=user.organization_id
        )
        db.add(db_item)
        
        # Actualizar stock
        previous_stock = product.stock_available
        product.stock_available -= item_data['quantity']
        
        # Si el producto es tipo "ambos", también actualizar stock
        if product.product_type == "ambos":
            product.stock -= item_data['quantity']
        
        # Registrar movimiento de inventario
        movement = models.InventoryMovement(
            product_id=product.id,
            user_id=user_id,
            movement_type="alquiler",
            quantity=item_data['quantity'],
            previous_stock=previous_stock,
            new_stock=product.stock_available,
            reference_type="rental",
            reference_id=db_rental.id,
            reason=f"Alquiler {rental_number} (desde cotización {quotation.quotation_number})",
            organization_id=user.organization_id
        )
        db.add(movement)
    
    db.commit()
    db.refresh(db_rental)
    return db_rental
