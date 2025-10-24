from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import Optional
from datetime import datetime, timedelta
from . import models_extended as models


def get_complete_business_summary(
    db: Session,
    organization_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Genera un resumen completo del negocio con todas las métricas importantes
    """
    try:
        # Si no se especifican fechas, usar valores muy amplios para obtener todo
        if not start_date:
            start_date = datetime(2000, 1, 1)  # Fecha muy antigua para obtener todo
        if not end_date:
            end_date = datetime.now()
        
        # ==================== VENTAS ====================
        sales_query = db.query(models.Sale).filter(
            models.Sale.organization_id == organization_id,
            models.Sale.created_at >= start_date,
            models.Sale.created_at <= end_date
        )
        
        total_sales = sales_query.count()
        sales_list = sales_query.all()
        
        # Ventas por estado
        sales_by_status = {}
        for sale in sales_list:
            status = sale.status
            if status not in sales_by_status:
                sales_by_status[status] = {'count': 0, 'total_amount': 0}
            sales_by_status[status]['count'] += 1
            sales_by_status[status]['total_amount'] += float(sale.total or 0)
        
        # Ventas por método de pago - Solo montos pagados y NO canceladas
        sales_by_payment = {}
        for sale in sales_list:
            # Excluir ventas canceladas
            if sale.status == 'cancelada':
                continue
            method = sale.payment_method
            if method not in sales_by_payment:
                sales_by_payment[method] = {'count': 0, 'total_amount': 0}
            sales_by_payment[method]['count'] += 1
            sales_by_payment[method]['total_amount'] += float(sale.paid_amount or 0)
        
        # Totales de ventas - Excluir canceladas
        total_sales_amount = sum(float(s.total or 0) for s in sales_list if s.status != 'cancelada')
        total_sales_paid = sum(float(s.paid_amount or 0) for s in sales_list if s.status != 'cancelada')
        # Calcular pendiente como la diferencia entre total y pagado
        total_sales_pending = sum(float(s.total or 0) - float(s.paid_amount or 0) for s in sales_list if s.status != 'cancelada' and float(s.total or 0) > float(s.paid_amount or 0))
        
        print(f"DEBUG RESUMEN - Ventas: total_amount={total_sales_amount}, total_paid={total_sales_paid}, pending={total_sales_pending}")
        
        # ==================== ALQUILERES ====================
        rentals_query = db.query(models.Rental).filter(
            models.Rental.organization_id == organization_id,
            models.Rental.created_at >= start_date,
            models.Rental.created_at <= end_date
        )
        
        total_rentals = rentals_query.count()
        rentals_list = rentals_query.all()
        
        # Alquileres por estado
        rentals_by_status = {}
        for rental in rentals_list:
            status = rental.status
            if status not in rentals_by_status:
                rentals_by_status[status] = {'count': 0, 'total_amount': 0}
            rentals_by_status[status]['count'] += 1
            rentals_by_status[status]['total_amount'] += float(rental.total_cost or 0)
        
        # Alquileres por método de pago - Usar pagos reales de RentalPayment
        rentals_by_payment = {}
        # Obtener todos los pagos de alquileres
        rental_payments = db.query(models.RentalPayment).filter(
            models.RentalPayment.organization_id == organization_id
        ).all()
        
        for payment in rental_payments:
            method = payment.payment_method
            if method not in rentals_by_payment:
                rentals_by_payment[method] = {'count': 0, 'total_amount': 0}
            rentals_by_payment[method]['count'] += 1
            rentals_by_payment[method]['total_amount'] += float(payment.amount or 0)
        
        # Totales de alquileres - Usar pagos reales de RentalPayment
        total_rentals_amount = sum(float(p.amount or 0) for p in rental_payments)
        total_rentals_paid = sum(float(p.amount or 0) for p in rental_payments)
        
        # Calcular pendiente: total_cost de alquileres activos/vencidos menos los pagos recibidos
        # Crear un mapa de pagos por rental_id
        payments_by_rental = {}
        for payment in rental_payments:
            rental_id = payment.rental_id
            if rental_id not in payments_by_rental:
                payments_by_rental[rental_id] = 0
            payments_by_rental[rental_id] += float(payment.amount or 0)
        
        # Calcular pendiente por cada alquiler
        total_rentals_pending = 0
        for rental in rentals_list:
            if rental.status in ['activo', 'vencido']:  # Solo activos y vencidos tienen pendientes
                total_cost = float(rental.total_cost or 0)
                paid = payments_by_rental.get(rental.id, 0)
                pending = total_cost - paid
                if pending > 0:
                    total_rentals_pending += pending
        
        print(f"DEBUG RESUMEN - Alquileres: total_amount={total_rentals_amount}, total_paid={total_rentals_paid}, pending={total_rentals_pending}")
        
        # ==================== COTIZACIONES ====================
        quotations_query = db.query(models.Quotation).filter(
            models.Quotation.organization_id == organization_id,
            models.Quotation.created_at >= start_date,
            models.Quotation.created_at <= end_date
        )
        
        total_quotations = quotations_query.count()
        pending_quotations = quotations_query.filter(models.Quotation.status == 'pendiente').count()
        accepted_quotations = quotations_query.filter(models.Quotation.status == 'aceptada').count()
        converted_quotations = quotations_query.filter(models.Quotation.status == 'convertida').count()
        
        # ==================== CLIENTES ====================
        total_clients = db.query(models.Client).filter(
            models.Client.organization_id == organization_id
        ).count()
        
        active_clients = db.query(models.Client).filter(
            models.Client.organization_id == organization_id,
            models.Client.status == 'activo'
        ).count()
        
        # Clientes nuevos en el período
        new_clients = db.query(models.Client).filter(
            models.Client.organization_id == organization_id,
            models.Client.created_at >= start_date,
            models.Client.created_at <= end_date
        ).count()
        
        # ==================== PRODUCTOS ====================
        total_products = db.query(models.Product).filter(
            models.Product.organization_id == organization_id,
            models.Product.is_active == True
        ).count()
        
        low_stock_products = db.query(models.Product).filter(
            models.Product.organization_id == organization_id,
            models.Product.is_active == True,
            models.Product.stock <= models.Product.min_stock
        ).count()
        
        # Productos más vendidos
        top_products = db.query(
            models.SaleItem.product_id,
            models.Product.name,
            func.sum(models.SaleItem.quantity).label('total_quantity'),
            func.sum(models.SaleItem.subtotal).label('total_revenue')
        ).join(
            models.Product, models.SaleItem.product_id == models.Product.id
        ).join(
            models.Sale, models.SaleItem.sale_id == models.Sale.id
        ).filter(
            models.Sale.organization_id == organization_id,
            models.Sale.created_at >= start_date,
            models.Sale.created_at <= end_date
        ).group_by(
            models.SaleItem.product_id, models.Product.name
        ).order_by(
            desc('total_quantity')
        ).limit(5).all()
        
        # ==================== MÉTODOS DE PAGO CONSOLIDADOS ====================
        payment_methods_summary = {}
        
        # Combinar ventas y alquileres por método de pago
        all_methods = set(sales_by_payment.keys()) | set(rentals_by_payment.keys())
        
        for method in all_methods:
            sales_data = sales_by_payment.get(method, {'count': 0, 'total_amount': 0})
            rentals_data = rentals_by_payment.get(method, {'count': 0, 'total_amount': 0})
            
            payment_methods_summary[method] = {
                'method': method,
                'sales_count': sales_data['count'],
                'sales_amount': sales_data['total_amount'],
                'rentals_count': rentals_data['count'],
                'rentals_amount': rentals_data['total_amount'],
                'total_count': sales_data['count'] + rentals_data['count'],
                'total_amount': sales_data['total_amount'] + rentals_data['total_amount']
            }
        
        # ==================== RESUMEN FINANCIERO ====================
        # Usar solo montos pagados para el ingreso total (igual que el dashboard)
        total_revenue = total_sales_paid + total_rentals_paid
        total_paid = total_sales_paid + total_rentals_paid
        total_pending = total_sales_pending + total_rentals_pending
        
        print(f"DEBUG RESUMEN - Financial: total_revenue={total_revenue}, total_paid={total_paid}, total_pending={total_pending}")
        
        # Calcular tasa de cobro
        total_amount_with_pending = total_sales_amount + total_rentals_amount
        collection_rate = (total_paid / total_amount_with_pending * 100) if total_amount_with_pending > 0 else 0
        
        # ==================== TENDENCIAS (últimos 7 días) ====================
        last_7_days = datetime.now() - timedelta(days=7)
        
        daily_sales = {}
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_sales[day] = {'sales': 0, 'rentals': 0, 'revenue': 0}
        
        # Ventas por día
        for sale in db.query(models.Sale).filter(
            models.Sale.organization_id == organization_id,
            models.Sale.created_at >= last_7_days
        ).all():
            day = sale.created_at.strftime('%Y-%m-%d')
            if day in daily_sales:
                daily_sales[day]['sales'] += 1
                daily_sales[day]['revenue'] += float(sale.total or 0)
        
        # Alquileres por día
        for rental in db.query(models.Rental).filter(
            models.Rental.organization_id == organization_id,
            models.Rental.created_at >= last_7_days
        ).all():
            day = rental.created_at.strftime('%Y-%m-%d')
            if day in daily_sales:
                daily_sales[day]['rentals'] += 1
                daily_sales[day]['revenue'] += float(rental.total_cost or 0)
        
        # ==================== CONSTRUIR RESPUESTA ====================
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'sales': {
                'total_count': total_sales,
                'total_amount': round(total_sales_paid, 2),  # Mostrar solo lo pagado
                'total_paid': round(total_sales_paid, 2),
                'total_pending': round(total_sales_pending, 2),
                'by_status': [
                    {'status': k, 'count': v['count'], 'total_amount': round(v['total_amount'], 2)}
                    for k, v in sales_by_status.items()
                ],
                'by_payment_method': [
                    {'method': k, 'count': v['count'], 'total_amount': round(v['total_amount'], 2)}
                    for k, v in sales_by_payment.items()
                ]
            },
            'rentals': {
                'total_count': total_rentals,
                'total_amount': round(total_rentals_paid, 2),  # Mostrar solo lo pagado
                'total_paid': round(total_rentals_paid, 2),
                'total_pending': round(total_rentals_pending, 2),
                'by_status': [
                    {'status': k, 'count': v['count'], 'total_amount': round(v['total_amount'], 2)}
                    for k, v in rentals_by_status.items()
                ],
                'by_payment_method': [
                    {'method': k, 'count': v['count'], 'total_amount': round(v['total_amount'], 2)}
                    for k, v in rentals_by_payment.items()
                ]
            },
            'quotations': {
                'total': total_quotations,
                'pending': pending_quotations,
                'accepted': accepted_quotations,
                'converted': converted_quotations,
                'conversion_rate': round((converted_quotations / total_quotations * 100) if total_quotations > 0 else 0, 2)
            },
            'clients': {
                'total': total_clients,
                'active': active_clients,
                'new_this_period': new_clients
            },
            'products': {
                'total': total_products,
                'low_stock': low_stock_products,
                'top_selling': [
                    {
                        'product_id': p.product_id,
                        'product_name': p.name,
                        'quantity_sold': int(p.total_quantity),
                        'revenue': round(float(p.total_revenue), 2)
                    }
                    for p in top_products
                ]
            },
            'payment_methods': list(payment_methods_summary.values()),
            'financial_summary': {
                'total_revenue': round(total_revenue, 2),
                'total_paid': round(total_paid, 2),
                'total_pending': round(total_pending, 2),
                'collection_rate': round(collection_rate, 2)
            },
            'trends': {
                'daily_data': [
                    {
                        'date': k,
                        'sales_count': v['sales'],
                        'rentals_count': v['rentals'],
                        'revenue': round(v['revenue'], 2)
                    }
                    for k, v in sorted(daily_sales.items())
                ]
            }
        }
    
    except Exception as e:
        print(f"Error en get_complete_business_summary: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Retornar estructura vacía en caso de error
        return {
            'period': {
                'start_date': start_date.isoformat() if start_date else datetime.now().isoformat(),
                'end_date': end_date.isoformat() if end_date else datetime.now().isoformat()
            },
            'sales': {
                'total_count': 0,
                'total_amount': 0,
                'total_paid': 0,
                'total_pending': 0,
                'by_status': [],
                'by_payment_method': []
            },
            'rentals': {
                'total_count': 0,
                'total_amount': 0,
                'total_paid': 0,
                'total_pending': 0,
                'by_status': [],
                'by_payment_method': []
            },
            'quotations': {
                'total': 0,
                'pending': 0,
                'accepted': 0,
                'converted': 0,
                'conversion_rate': 0
            },
            'clients': {
                'total': 0,
                'active': 0,
                'new_this_period': 0
            },
            'products': {
                'total': 0,
                'low_stock': 0,
                'top_selling': []
            },
            'payment_methods': [],
            'financial_summary': {
                'total_revenue': 0,
                'total_paid': 0,
                'total_pending': 0,
                'collection_rate': 0
            },
            'trends': {
                'daily_data': []
            }
        }
