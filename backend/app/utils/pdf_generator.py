"""
Utilidad para generar PDFs de facturas, cotizaciones y contratos
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.company_name = "Sistema de Gestión Empresarial"
        self.company_address = "Av. Principal #123, Santo Domingo, RD"
        self.company_phone = "809-555-0000"
        self.company_email = "info@empresa.com"
        
    def _create_header(self):
        """Crea el encabezado del documento"""
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER,
            spaceAfter=12
        )
        return Paragraph(self.company_name, header_style)
    
    def _create_company_info(self):
        """Crea la información de la empresa"""
        info_style = ParagraphStyle(
            'CompanyInfo',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        info_text = f"{self.company_address}<br/>{self.company_phone} | {self.company_email}"
        return Paragraph(info_text, info_style)
    
    def generate_quotation_pdf(self, quotation, client, items, filename):
        """Genera PDF de cotización"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        
        # Header
        story.append(self._create_header())
        story.append(self._create_company_info())
        story.append(Spacer(1, 0.3*inch))
        
        # Título
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("COTIZACIÓN", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información de cotización y cliente
        info_data = [
            ['Cotización:', quotation.quotation_number, 'Cliente:', client.name],
            ['Fecha:', quotation.quotation_date.strftime('%d/%m/%Y'), 'RNC/Cédula:', client.rnc or 'N/A'],
            ['Válida hasta:', quotation.valid_until.strftime('%d/%m/%Y') if quotation.valid_until else 'N/A', 
             'Teléfono:', client.phone or 'N/A'],
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#1e40af')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Tabla de items
        items_data = [['#', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
        for idx, item in enumerate(items, 1):
            items_data.append([
                str(idx),
                item.product.name[:30],
                str(item.quantity),
                f"${item.unit_price:,.2f}",
                f"${item.subtotal:,.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 3.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Totales
        totals_data = [
            ['Subtotal:', f"${quotation.subtotal:,.2f}"],
            ['Descuento:', f"-${quotation.discount_amount:,.2f}"],
            ['ITBIS (18%):', f"${quotation.tax_amount:,.2f}"],
            ['TOTAL:', f"${quotation.total:,.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[5.5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1e40af')),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
        ]))
        story.append(totals_table)
        
        # Notas y condiciones
        if quotation.notes or quotation.terms_conditions:
            story.append(Spacer(1, 0.3*inch))
            if quotation.notes:
                story.append(Paragraph(f"<b>Notas:</b> {quotation.notes}", self.styles['Normal']))
            if quotation.terms_conditions:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(f"<b>Términos y Condiciones:</b> {quotation.terms_conditions}", self.styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph("Gracias por su preferencia", footer_style))
        
        doc.build(story)
        return filename
    
    def generate_invoice_pdf(self, sale, client, items, filename):
        """Genera PDF de factura"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        
        # Header
        story.append(self._create_header())
        story.append(self._create_company_info())
        story.append(Spacer(1, 0.3*inch))
        
        # Título
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#059669'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("FACTURA", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información de factura y cliente
        info_data = [
            ['Factura:', sale.invoice_number or sale.sale_number, 'Cliente:', client.name],
            ['Fecha:', sale.sale_date.strftime('%d/%m/%Y'), 'RNC/Cédula:', client.rnc or 'N/A'],
            ['Método de Pago:', sale.payment_method.upper(), 'Teléfono:', client.phone or 'N/A'],
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#059669')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#059669')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Tabla de items
        items_data = [['#', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
        for idx, item in enumerate(items, 1):
            items_data.append([
                str(idx),
                item.product.name[:30],
                str(item.quantity),
                f"${item.unit_price:,.2f}",
                f"${item.subtotal:,.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 3.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Totales
        totals_data = [
            ['Subtotal:', f"${sale.subtotal:,.2f}"],
            ['Descuento:', f"-${sale.discount_amount:,.2f}"],
            ['ITBIS (18%):', f"${sale.tax_amount:,.2f}"],
            ['TOTAL:', f"${sale.total:,.2f}"],
            ['Pagado:', f"${sale.paid_amount:,.2f}"],
        ]
        
        if sale.balance > 0:
            totals_data.append(['SALDO PENDIENTE:', f"${sale.balance:,.2f}"])
        
        totals_table = Table(totals_data, colWidths=[5.5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -2), (-1, -1), 12),
            ('TEXTCOLOR', (0, -2), (-1, -2), colors.HexColor('#059669')),
            ('LINEABOVE', (0, -2), (-1, -2), 2, colors.HexColor('#059669')),
            ('FONTSIZE', (0, 0), (-1, -3), 10),
        ]))
        
        if sale.balance > 0:
            totals_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.red),
            ]))
        
        story.append(totals_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph("Gracias por su compra", footer_style))
        
        doc.build(story)
        return filename
    
    def generate_rental_contract_pdf(self, rental, client, product, filename):
        """Genera PDF de contrato de alquiler"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        
        # Header
        story.append(self._create_header())
        story.append(self._create_company_info())
        story.append(Spacer(1, 0.3*inch))
        
        # Título
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#7c3aed'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("CONTRATO DE ALQUILER", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información del contrato
        info_data = [
            ['Contrato:', rental.rental_number, 'Cliente:', client.name],
            ['Fecha Inicio:', rental.start_date.strftime('%d/%m/%Y'), 'RNC/Cédula:', client.rnc or 'N/A'],
            ['Fecha Fin:', rental.end_date.strftime('%d/%m/%Y'), 'Teléfono:', client.phone or 'N/A'],
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#7c3aed')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Información del equipo
        equipment_data = [
            ['Equipo:', product.name],
            ['SKU:', product.sku],
            ['Descripción:', product.description or 'N/A'],
            ['Condición al Salir:', rental.condition_out or 'Buen estado'],
        ]
        
        equipment_table = Table(equipment_data, colWidths=[2*inch, 5.5*inch])
        equipment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        story.append(equipment_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Costos
        costs_data = [
            ['Período:', rental.rental_period],
            ['Precio de Alquiler:', f"${rental.rental_price:,.2f}"],
            ['Depósito:', f"${rental.deposit:,.2f}"],
            ['COSTO TOTAL:', f"${rental.total_cost:,.2f}"],
            ['Pagado:', f"${rental.paid_amount:,.2f}"],
        ]
        
        if rental.balance > 0:
            costs_data.append(['SALDO PENDIENTE:', f"${rental.balance:,.2f}"])
        
        costs_table = Table(costs_data, colWidths=[5.5*inch, 2*inch])
        costs_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -2), (-1, -1), 12),
            ('TEXTCOLOR', (0, -2), (-1, -2), colors.HexColor('#7c3aed')),
            ('LINEABOVE', (0, -2), (-1, -2), 2, colors.HexColor('#7c3aed')),
            ('FONTSIZE', (0, 0), (-1, -3), 10),
        ]))
        story.append(costs_table)
        
        # Términos y condiciones
        story.append(Spacer(1, 0.3*inch))
        terms_style = ParagraphStyle(
            'Terms',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT
        )
        terms_text = """
        <b>TÉRMINOS Y CONDICIONES:</b><br/>
        1. El equipo debe ser devuelto en las mismas condiciones en que fue entregado.<br/>
        2. El cliente es responsable de cualquier daño o pérdida del equipo.<br/>
        3. El depósito será reembolsado al momento de la devolución si el equipo está en buen estado.<br/>
        4. Cualquier retraso en la devolución generará cargos adicionales.<br/>
        5. El cliente acepta los términos de este contrato al firmar.
        """
        story.append(Paragraph(terms_text, terms_style))
        
        # Firmas
        story.append(Spacer(1, 0.5*inch))
        signatures_data = [
            ['_____________________', '_____________________'],
            ['Firma del Cliente', 'Firma Autorizada'],
            [client.name, self.company_name],
        ]
        
        signatures_table = Table(signatures_data, colWidths=[3.75*inch, 3.75*inch])
        signatures_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ]))
        story.append(signatures_table)
        
        doc.build(story)
        return filename


# Instancia global
pdf_generator = PDFGenerator()
