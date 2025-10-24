from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from . import models_extended as models


def get_dashboard_stats(db: Session, organization_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Obtiene todas las estadísticas del dashboard para una organización específica"""
    print(f"DEBUG: get_dashboard_stats called with org_id={organization_id}, start_date={start_date}, end_date={end_date}")
    
    today = datetime.now()
    start_of_day = datetime(today.year, today.month, today.day)
    start_of_month = datetime(today.year, today.month, 1)
    start_of_year = datetime(today.year, 1, 1)
    
    # Procesar fechas de filtro si se proporcionan
    filter_start_date = None
    filter_end_date = None
    
    if start_date:
        try:
            filter_start_date = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            pass
    
    if end_date:
        try:
            filter_end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Incluir todo el día final
            filter_end_date = filter_end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    # Función auxiliar para aplicar filtros de fecha
    def apply_date_filter(query, date_field):
        if filter_start_date:
            query = query.filter(date_field >= filter_start_date)
        if filter_end_date:
            query = query.filter(date_field <= filter_end_date)
        return query
    
    # VENTAS
    # Si hay filtros de fecha, usar esos; si no, usar los rangos predefinidos
    if filter_start_date or filter_end_date:
        # Usar filtros de fecha personalizados - CORREGIDO: usar paid_amount y created_at
        print(f"DEBUG VENTAS: Filtrando por created_at entre {filter_start_date} y {filter_end_date}")
        
        # Primero ver qué ventas hay
        all_sales = db.query(models.Sale).filter(
            models.Sale.organization_id == organization_id,
            models.Sale.status.in_(["completada", "parcial"])
        ).all()
        print(f"DEBUG: Total ventas completadas/parciales: {len(all_sales)}")
        for sale in all_sales:
            print(f"  - Venta {sale.sale_number}: created_at={sale.created_at}, sale_date={sale.sale_date}, paid=${sale.paid_amount}")
        
        sales_query = db.query(func.sum(models.Sale.paid_amount)).filter(
            models.Sale.organization_id == organization_id,
            models.Sale.status.in_(["completada", "parcial"])
        )
        sales_query = apply_date_filter(sales_query, models.Sale.created_at)
        total_sales_today = sales_query.scalar() or 0
        print(f"DEBUG VENTAS: Total ventas filtradas = {total_sales_today}")
        total_sales_month = total_sales_today  # Mismo valor cuando hay filtro personalizado
        total_sales_year = total_sales_today   # Mismo valor cuando hay filtro personalizado
    else:
        # Usar rangos predefinidos (comportamiento original) - CORREGIDO: usar paid_amount y created_at
        total_sales_today = db.query(func.sum(models.Sale.paid_amount)).filter(
            models.Sale.created_at >= start_of_day,
            models.Sale.organization_id == organization_id,
            models.Sale.status.in_(["completada", "parcial"])
        ).scalar() or 0
        
        total_sales_month = db.query(func.sum(models.Sale.paid_amount)).filter(
            models.Sale.created_at >= start_of_month,
            models.Sale.organization_id == organization_id,
            models.Sale.status.in_(["completada", "parcial"])
        ).scalar() or 0
        
        total_sales_year = db.query(func.sum(models.Sale.paid_amount)).filter(
            models.Sale.created_at >= start_of_year,
            models.Sale.organization_id == organization_id,
            models.Sale.status.in_(["completada", "parcial"])
        ).scalar() or 0
    
    # Ventas pendientes (siempre sin filtro de fecha ya que son pendientes actuales)
    pending_sales = db.query(func.count(models.Sale.id)).filter(
        models.Sale.status == "pendiente_pago",
        models.Sale.organization_id == organization_id
    ).scalar()
    
    # INVENTARIO
    total_products = db.query(func.count(models.Product.id)).filter(
        models.Product.is_active == True,
        models.Product.organization_id == organization_id
    ).scalar()
    
    total_value = db.query(func.sum(models.Product.price * models.Product.stock)).filter(
        models.Product.is_active == True,
        models.Product.organization_id == organization_id
    ).scalar() or 0
    
    # Productos con stock bajo (stock actual menor o igual al mínimo)
    low_stock_products = db.query(func.count(models.Product.id)).filter(
        models.Product.stock <= models.Product.min_stock,
        models.Product.min_stock > 0,  # Asegurar que min_stock esté definido
        models.Product.is_active == True,
        models.Product.organization_id == organization_id
    ).scalar() or 0
    
    # Productos alquilados (aplicar filtro de fecha si existe)
    if filter_start_date or filter_end_date:
        rental_query = db.query(func.count(models.Rental.id)).filter(
            models.Rental.status == "activo",
            models.Rental.organization_id == organization_id
        )
        rental_query = apply_date_filter(rental_query, models.Rental.created_at)
        products_rented = rental_query.scalar()
    else:
        products_rented = db.query(func.count(models.Rental.id)).filter(
            models.Rental.status == "activo",
            models.Rental.organization_id == organization_id
        ).scalar()
    
    # CLIENTES
    total_clients = db.query(func.count(models.Client.id)).filter(
        models.Client.organization_id == organization_id
    ).scalar()
    
    active_clients = db.query(func.count(models.Client.id)).filter(
        models.Client.status == "activo",
        models.Client.organization_id == organization_id
    ).scalar()
    
    new_clients_month = db.query(func.count(models.Client.id)).filter(
        models.Client.created_at >= start_of_month,
        models.Client.organization_id == organization_id
    ).scalar()
    
    # COTIZACIONES
    # Cotizaciones pendientes y aceptadas (sin filtro de fecha ya que son estados actuales)
    pending_quotations = db.query(func.count(models.Quotation.id)).filter(
        models.Quotation.status == "pendiente",
        models.Quotation.organization_id == organization_id
    ).scalar()
    
    accepted_quotations = db.query(func.count(models.Quotation.id)).filter(
        models.Quotation.status == "aceptada",
        models.Quotation.organization_id == organization_id
    ).scalar()
    
    # Cotizaciones del período (aplicar filtro de fecha si existe)
    if filter_start_date or filter_end_date:
        quotation_query = db.query(func.count(models.Quotation.id)).filter(
            models.Quotation.organization_id == organization_id
        )
        quotation_query = apply_date_filter(quotation_query, models.Quotation.quotation_date)
        quotations_this_month = quotation_query.scalar()
    else:
        quotations_this_month = db.query(func.count(models.Quotation.id)).filter(
            models.Quotation.quotation_date >= start_of_month,
            models.Quotation.organization_id == organization_id
        ).scalar()
    
    # ALQUILERES
    # Alquileres activos y vencidos (sin filtro de fecha ya que son estados actuales)
    active_rentals = db.query(func.count(models.Rental.id)).filter(
        models.Rental.status == "activo",
        models.Rental.organization_id == organization_id
    ).scalar()
    
    overdue_rentals = db.query(func.count(models.Rental.id)).filter(
        models.Rental.status == "vencido",
        models.Rental.organization_id == organization_id
    ).scalar()
    
    # Alquileres del período (aplicar filtro de fecha si existe)
    if filter_start_date or filter_end_date:
        rental_period_query = db.query(func.count(models.Rental.id)).filter(
            models.Rental.organization_id == organization_id
        )
        rental_period_query = apply_date_filter(rental_period_query, models.Rental.created_at)
        rentals_this_month = rental_period_query.scalar()
    else:
        rentals_this_month = db.query(func.count(models.Rental.id)).filter(
            models.Rental.created_at >= start_of_month,
            models.Rental.organization_id == organization_id
        ).scalar()
    
    # FINANCIERO
    # Pagos pendientes (sin filtro de fecha ya que son pendientes actuales)
    pending_payments = db.query(func.sum(models.Sale.balance)).filter(
        models.Sale.balance > 0,
        models.Sale.status != "cancelada",  # Excluir ventas canceladas
        models.Sale.organization_id == organization_id
    ).scalar() or 0
    
    # Ingresos de alquileres - Usar pagos reales de RentalPayment (aplicar filtro de fecha si existe)
    if filter_start_date or filter_end_date:
        rental_income_query = db.query(func.sum(models.RentalPayment.amount)).filter(
            models.RentalPayment.organization_id == organization_id
        )
        rental_income_query = apply_date_filter(rental_income_query, models.RentalPayment.payment_date)
        rental_income_today = rental_income_query.scalar() or 0
        rental_income_month = rental_income_today  # Mismo valor cuando hay filtro personalizado
        rental_income_year = rental_income_today   # Mismo valor cuando hay filtro personalizado
    else:
        rental_income_today = db.query(func.sum(models.RentalPayment.amount)).filter(
            models.RentalPayment.payment_date >= start_of_day,
            models.RentalPayment.organization_id == organization_id
        ).scalar() or 0
        
        rental_income_month = db.query(func.sum(models.RentalPayment.amount)).filter(
            models.RentalPayment.payment_date >= start_of_month,
            models.RentalPayment.organization_id == organization_id
        ).scalar() or 0
        
        rental_income_year = db.query(func.sum(models.RentalPayment.amount)).filter(
            models.RentalPayment.payment_date >= start_of_year,
            models.RentalPayment.organization_id == organization_id
        ).scalar() or 0
    
    # Pagos pendientes de alquileres - Incluir TODOS los que tengan balance pendiente
    pending_rental_payments = db.query(func.sum(models.Rental.balance)).filter(
        models.Rental.balance > 0,
        models.Rental.organization_id == organization_id
    ).scalar() or 0
    
    total_revenue_month = total_sales_month + rental_income_month
    
    # TOTALES HISTÓRICOS (sin filtros de fecha) - Solo ventas completadas y pagos de alquileres reales
    total_sales_all_time = db.query(func.sum(models.Sale.paid_amount)).filter(
        models.Sale.organization_id == organization_id,
        models.Sale.status.in_(["completada", "parcial"])  # Solo ventas completadas o con pago parcial
    ).scalar() or 0
    
    # Para alquileres, sumar todos los pagos registrados en RentalPayment
    total_rentals_all_time = db.query(func.sum(models.RentalPayment.amount)).filter(
        models.RentalPayment.organization_id == organization_id
    ).scalar() or 0
    
    # Debug: imprimir algunos valores clave
    print(f"DEBUG: total_sales_all_time={total_sales_all_time}, total_rentals_all_time={total_rentals_all_time}")
    print(f"DEBUG: total_sales_month={total_sales_month}, rental_income_month={rental_income_month}")
    print(f"DEBUG: active_clients={active_clients}, total_products={total_products}")
    
    return {
        # Ventas
        "total_sales_today": round(total_sales_today, 2),
        "total_sales_month": round(total_sales_month, 2),
        "total_sales_year": round(total_sales_year, 2),
        "total_sales_all_time": round(total_sales_all_time, 2),
        "pending_sales": pending_sales,
        
        # Inventario
        "total_products": total_products,
        "total_value": round(total_value, 2),
        "low_stock_products": low_stock_products,
        "products_rented": products_rented,
        
        # Clientes
        "total_clients": total_clients,
        "active_clients": active_clients,
        "new_clients_month": new_clients_month,
        
        # Cotizaciones
        "pending_quotations": pending_quotations,
        "accepted_quotations": accepted_quotations,
        "quotations_this_month": quotations_this_month,
        
        # Alquileres
        "active_rentals": active_rentals,
        "overdue_rentals": overdue_rentals,
        "rentals_this_month": rentals_this_month,
        
        # Financiero
        "pending_payments": round(pending_payments, 2),
        "total_revenue_month": round(total_revenue_month, 2),
        
        # Ingresos de alquileres
        "rental_income_today": round(rental_income_today, 2),
        "rental_income_month": round(rental_income_month, 2),
        "rental_income_year": round(rental_income_year, 2),
        "total_rentals_all_time": round(total_rentals_all_time, 2),
        "pending_rental_payments": round(pending_rental_payments, 2)
    }


def get_sales_chart_data(db: Session, organization_id: int, days: int = 30, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None):
    """Obtiene datos para gráfico de ventas de una organización específica"""
    if start_date_str and end_date_str:
        # Usar fechas específicas del filtro
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
    else:
        # Usar días desde hoy hacia atrás
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
    
    sales_by_day = db.query(
        func.date(models.Sale.sale_date).label('date'),
        func.sum(models.Sale.paid_amount).label('total'),  # Solo monto pagado
        func.count(models.Sale.id).label('count')
    ).filter(
        models.Sale.sale_date >= start_date,
        models.Sale.sale_date <= end_date,
        models.Sale.status.in_(["completada", "parcial"]),
        models.Sale.organization_id == organization_id
    ).group_by(
        func.date(models.Sale.sale_date)
    ).all()
    
    return [
        {
            "date": str(row.date),
            "total": round(float(row.total or 0), 2),  # Manejar None
            "count": row.count
        }
        for row in sales_by_day
    ]


def get_rentals_chart_data(db: Session, organization_id: int, days: int = 30, start_date_str: Optional[str] = None, end_date_str: Optional[str] = None):
    """Obtiene datos para gráfico de alquileres de una organización específica"""
    if start_date_str and end_date_str:
        # Usar fechas específicas del filtro
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
    else:
        # Usar días desde hoy hacia atrás
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
    
    rentals_by_day = db.query(
        func.date(models.Rental.created_at).label('date'),
        func.sum(models.Rental.paid_amount).label('total'),  # Solo monto pagado
        func.count(models.Rental.id).label('count')
    ).filter(
        models.Rental.created_at >= start_date,
        models.Rental.created_at <= end_date,
        models.Rental.organization_id == organization_id
    ).group_by(
        func.date(models.Rental.created_at)
    ).all()
    
    return [
        {
            "date": str(row.date),
            "total": round(float(row.total or 0), 2),  # Manejar None
            "count": row.count
        }
        for row in rentals_by_day
    ]


def get_top_products(db: Session, organization_id: int, limit: int = 10):
    """Obtiene los productos más vendidos de una organización específica"""
    top_products = db.query(
        models.Product.id,
        models.Product.name,
        models.Product.sku,
        func.sum(models.SaleItem.quantity).label('total_sold'),
        func.sum(models.SaleItem.subtotal).label('total_revenue')
    ).join(
        models.SaleItem, models.Product.id == models.SaleItem.product_id
    ).join(
        models.Sale, models.SaleItem.sale_id == models.Sale.id
    ).filter(
        models.Product.organization_id == organization_id,
        models.Sale.organization_id == organization_id
    ).group_by(
        models.Product.id, models.Product.name, models.Product.sku
    ).order_by(
        func.sum(models.SaleItem.quantity).desc()
    ).limit(limit).all()
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "sku": row.sku,
            "total_sold": row.total_sold,
            "total_revenue": round(float(row.total_revenue), 2)
        }
        for row in top_products
    ]


def get_top_clients(db: Session, organization_id: int, limit: int = 10):
    """Obtiene los clientes que más compran de una organización específica"""
    top_clients = db.query(
        models.Client.id,
        models.Client.name,
        models.Client.client_type,
        func.count(models.Sale.id).label('total_purchases'),
        func.sum(models.Sale.total).label('total_spent')
    ).join(
        models.Sale, models.Client.id == models.Sale.client_id
    ).filter(
        models.Client.organization_id == organization_id,
        models.Sale.organization_id == organization_id
    ).group_by(
        models.Client.id, models.Client.name, models.Client.client_type
    ).order_by(
        func.sum(models.Sale.total).desc()
    ).limit(limit).all()
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "client_type": row.client_type,
            "total_purchases": row.total_purchases,
            "total_spent": round(float(row.total_spent), 2)
        }
        for row in top_clients
    ]


def get_recent_activities(db: Session, organization_id: int, limit: int = 10):
    """Obtiene actividades recientes de una organización específica - solo datos reales"""
    from datetime import datetime, timedelta
    from sqlalchemy.orm import joinedload
    
    activities = []
    
    # Solo mostrar actividades de los últimos 30 días
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Ventas recientes (últimos 30 días) - con cliente cargado
    recent_sales = db.query(models.Sale).options(
        joinedload(models.Sale.client)
    ).filter(
        models.Sale.organization_id == organization_id,
        models.Sale.created_at >= thirty_days_ago
    ).order_by(
        models.Sale.created_at.desc()
    ).limit(5).all()
    
    for sale in recent_sales:
        client_name = sale.client.name if sale.client else "Cliente directo"
        activities.append({
            "type": "sale",
            "id": sale.id,
            "description": f"Venta #{sale.sale_number} a {client_name} por ${sale.total:.2f}",
            "date": sale.created_at.isoformat(),
            "status": sale.status,
            "icon": "💰"
        })
    
    # Alquileres recientes (últimos 30 días) - con cliente cargado
    recent_rentals = db.query(models.Rental).options(
        joinedload(models.Rental.client)
    ).filter(
        models.Rental.organization_id == organization_id,
        models.Rental.created_at >= thirty_days_ago
    ).order_by(
        models.Rental.created_at.desc()
    ).limit(4).all()
    
    for rental in recent_rentals:
        client_name = rental.client.name if rental.client else "Cliente directo"
        activities.append({
            "type": "rental",
            "id": rental.id,
            "description": f"Alquiler a {client_name} por ${rental.total:.2f}",
            "date": rental.created_at.isoformat(),
            "status": rental.status,
            "icon": "📅"
        })
    
    # Cotizaciones recientes (últimos 30 días) - con cliente cargado
    recent_quotations = db.query(models.Quotation).options(
        joinedload(models.Quotation.client)
    ).filter(
        models.Quotation.organization_id == organization_id,
        models.Quotation.created_at >= thirty_days_ago
    ).order_by(
        models.Quotation.created_at.desc()
    ).limit(3).all()
    
    for quotation in recent_quotations:
        client_name = quotation.client.name if quotation.client else "Cliente directo"
        activities.append({
            "type": "quotation",
            "id": quotation.id,
            "description": f"Cotización #{quotation.quotation_number} para {client_name} - ${quotation.total:.2f}",
            "date": quotation.created_at.isoformat(),
            "status": quotation.status,
            "icon": "📋"
        })
    
    # Clientes nuevos (últimos 30 días)
    new_clients = db.query(models.Client).filter(
        models.Client.organization_id == organization_id,
        models.Client.created_at >= thirty_days_ago
    ).order_by(
        models.Client.created_at.desc()
    ).limit(2).all()
    
    for client in new_clients:
        activities.append({
            "type": "client",
            "id": client.id,
            "description": f"Nuevo cliente registrado: {client.name}",
            "date": client.created_at.isoformat(),
            "status": client.status,
            "icon": "👤"
        })
    
    # Ordenar por fecha (más recientes primero)
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    # Si no hay actividades recientes, mostrar mensaje informativo
    if not activities:
        return [{
            "type": "info",
            "id": 0,
            "description": "No hay actividades recientes. ¡Empieza registrando clientes y productos!",
            "date": datetime.utcnow(),
            "status": "info",
            "icon": "ℹ️"
        }]
    
    return activities[:limit]