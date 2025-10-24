"""
Utilidad para exportar datos a Excel
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict


class ExcelExporter:
    
    @staticmethod
    def export_clients(clients: List, filename: str):
        """Exporta clientes a Excel"""
        data = []
        for client in clients:
            data.append({
                'ID': client.id,
                'Nombre': client.name,
                'Tipo': client.client_type,
                'Estado': client.status,
                'RNC/Cédula': client.rnc or '',
                'Email': client.email or '',
                'Teléfono': client.phone or '',
                'Móvil': client.mobile or '',
                'Ciudad': client.city or '',
                'Dirección': client.address or '',
                'Límite Crédito': client.credit_limit,
                'Días Crédito': client.credit_days,
                'Fecha Creación': client.created_at.strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, sheet_name='Clientes')
        return filename
    
    @staticmethod
    def export_products(products: List, filename: str):
        """Exporta productos a Excel"""
        data = []
        for product in products:
            data.append({
                'SKU': product.sku,
                'Nombre': product.name,
                'Tipo': product.product_type,
                'Categoría': product.category.name if product.category else '',
                'Proveedor': product.supplier.name if product.supplier else '',
                'Precio Venta': product.price,
                'Precio Alquiler Diario': product.rental_price_daily or 0,
                'Precio Alquiler Semanal': product.rental_price_weekly or 0,
                'Precio Alquiler Mensual': product.rental_price_monthly or 0,
                'Costo': product.cost or 0,
                'Stock': product.stock,
                'Stock Disponible': product.stock_available,
                'Stock Mínimo': product.min_stock,
                'Ubicación': product.location or '',
                'Activo': 'Sí' if product.is_active else 'No'
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, sheet_name='Productos')
        return filename
    
    @staticmethod
    def export_sales(sales: List, filename: str):
        """Exporta ventas a Excel"""
        data = []
        for sale in sales:
            data.append({
                'Número Venta': sale.sale_number,
                'Número Factura': sale.invoice_number or '',
                'Cliente': sale.client.name if sale.client else '',
                'Fecha': sale.sale_date.strftime('%Y-%m-%d'),
                'Estado': sale.status,
                'Método Pago': sale.payment_method,
                'Subtotal': sale.subtotal,
                'Descuento': sale.discount_amount,
                'Impuesto': sale.tax_amount,
                'Total': sale.total,
                'Pagado': sale.paid_amount,
                'Saldo': sale.balance,
                'Vendedor': sale.created_by_user.full_name if sale.created_by_user else ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, sheet_name='Ventas')
        return filename
    
    @staticmethod
    def export_quotations(quotations: List, filename: str):
        """Exporta cotizaciones a Excel"""
        data = []
        for quotation in quotations:
            data.append({
                'Número': quotation.quotation_number,
                'Cliente': quotation.client.name if quotation.client else '',
                'Fecha': quotation.quotation_date.strftime('%Y-%m-%d'),
                'Válida Hasta': quotation.valid_until.strftime('%Y-%m-%d') if quotation.valid_until else '',
                'Estado': quotation.status,
                'Subtotal': quotation.subtotal,
                'Descuento': quotation.discount_amount,
                'Impuesto': quotation.tax_amount,
                'Total': quotation.total,
                'Creado Por': quotation.created_by_user.full_name if quotation.created_by_user else ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, sheet_name='Cotizaciones')
        return filename
    
    @staticmethod
    def export_rentals(rentals: List, filename: str):
        """Exporta alquileres a Excel"""
        data = []
        for rental in rentals:
            data.append({
                'Número': rental.rental_number,
                'Cliente': rental.client.name if rental.client else '',
                'Producto': rental.product.name if rental.product else '',
                'Fecha Inicio': rental.start_date.strftime('%Y-%m-%d'),
                'Fecha Fin': rental.end_date.strftime('%Y-%m-%d'),
                'Fecha Devolución': rental.actual_return_date.strftime('%Y-%m-%d') if rental.actual_return_date else '',
                'Estado': rental.status,
                'Período': rental.rental_period,
                'Precio': rental.rental_price,
                'Depósito': rental.deposit,
                'Costo Total': rental.total_cost,
                'Pagado': rental.paid_amount,
                'Saldo': rental.balance,
                'Creado Por': rental.created_by_user.full_name if rental.created_by_user else ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, sheet_name='Alquileres')
        return filename
    
    @staticmethod
    def export_sales_report(report_data: Dict, filename: str):
        """Exporta reporte completo de ventas a Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Resumen
            summary_data = {
                'Métrica': ['Total Ventas', 'Monto Total', 'Total Pagado', 'Total Pendiente'],
                'Valor': [
                    report_data['total_sales'],
                    f"${report_data['total_amount']:,.2f}",
                    f"${report_data['total_paid']:,.2f}",
                    f"${report_data['total_pending']:,.2f}"
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Por Estado
            if report_data.get('by_status'):
                status_data = []
                for status, count in report_data['by_status'].items():
                    status_data.append({'Estado': status, 'Cantidad': count})
                df_status = pd.DataFrame(status_data)
                df_status.to_excel(writer, sheet_name='Por Estado', index=False)
            
            # Por Método de Pago
            if report_data.get('by_payment_method'):
                payment_data = []
                for method, count in report_data['by_payment_method'].items():
                    payment_data.append({'Método': method, 'Cantidad': count})
                df_payment = pd.DataFrame(payment_data)
                df_payment.to_excel(writer, sheet_name='Por Método Pago', index=False)
            
            # Detalle de Ventas
            if report_data.get('sales'):
                sales_data = []
                for sale in report_data['sales']:
                    sales_data.append({
                        'Número': sale.sale_number,
                        'Cliente': sale.client.name if sale.client else '',
                        'Fecha': sale.sale_date.strftime('%Y-%m-%d'),
                        'Total': sale.total,
                        'Estado': sale.status
                    })
                df_sales = pd.DataFrame(sales_data)
                df_sales.to_excel(writer, sheet_name='Detalle Ventas', index=False)
        
        return filename


# Instancia global
excel_exporter = ExcelExporter()
