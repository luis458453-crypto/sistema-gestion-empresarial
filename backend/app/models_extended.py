from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum, Numeric, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from .timezone_utils import get_rd_now
import enum

# Importar Organization para las relaciones
from .models_organization import Organization


# Enums para estados y tipos
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VENDEDOR = "vendedor"
    ALMACEN = "almacen"
    EMPLEADO = "empleado"


class QuotationStatus(str, enum.Enum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    CONVERTIDA = "convertida"
    VENCIDA = "vencida"


class SaleStatus(str, enum.Enum):
    COMPLETADA = "completada"
    PENDIENTE_PAGO = "pendiente_pago"
    PARCIAL = "parcial"
    CANCELADA = "cancelada"


class PaymentMethod(str, enum.Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    TARJETA = "tarjeta"
    CHEQUE = "cheque"


class RentalStatus(str, enum.Enum):
    ACTIVO = "activo"
    DEVUELTO = "devuelto"
    VENCIDO = "vencido"
    RENOVADO = "renovado"
    CANCELADO = "cancelado"


class ProductType(str, enum.Enum):
    VENTA = "venta"
    ALQUILER = "alquiler"
    AMBOS = "ambos"


class ClientType(str, enum.Enum):
    HOSPITAL = "hospital"
    MEDICO = "medico"
    EMPRESA = "empresa"
    PARTICULAR = "particular"


class ClientStatus(str, enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"


# Modelo extendido de Usuario con roles
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.EMPLEADO)  # admin, vendedor, almacen, empleado
    is_active = Column(Boolean, default=True)
    phone = Column(String)
    avatar = Column(String)  # URL o path de imagen
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)
    
    # Multi-tenant: Organización a la que pertenece
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="users")
    movements = relationship("InventoryMovement", back_populates="user")
    quotations = relationship("Quotation", back_populates="created_by_user")
    sales = relationship("Sale", back_populates="created_by_user")
    rentals = relationship("Rental", back_populates="created_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")


# Modelo de Cliente
class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    client_type = Column(String, default=ClientType.PARTICULAR)  # hospital, medico, empresa, particular
    status = Column(String, default=ClientStatus.ACTIVO)  # activo, inactivo, suspendido
    rnc = Column(String, unique=True, index=True)  # RNC o cédula
    email = Column(String)
    phone = Column(String)
    mobile = Column(String)
    address = Column(Text)
    city = Column(String)
    country = Column(String, default="República Dominicana")
    contact_person = Column(String)  # Persona de contacto
    notes = Column(Text)
    credit_limit = Column(Float, default=0)
    credit_days = Column(Integer, default=0)
    is_recurrent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="clients")
    quotations = relationship("Quotation", back_populates="client")
    sales = relationship("Sale", back_populates="client")
    rentals = relationship("Rental", back_populates="client")


# Modelo de Producto extendido
class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        # SKU único por organización
        # UniqueConstraint('sku', 'organization_id', name='uq_product_sku_org'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, index=True, nullable=False)  # Quitado unique=True
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    product_type = Column(String, default=ProductType.VENTA)  # venta, alquiler, ambos
    category_id = Column(Integer, ForeignKey("categories.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    price = Column(Float, nullable=True)
    rental_price_daily = Column(Float)  # Precio por día de alquiler
    rental_price_weekly = Column(Float)  # Precio por semana
    rental_price_monthly = Column(Float)  # Precio por mes
    cost = Column(Float)
    stock = Column(Integer, default=0)
    stock_available = Column(Integer, default=0)  # Stock disponible (no alquilado)
    min_stock = Column(Integer, default=10)
    max_stock = Column(Integer, default=100)
    location = Column(String)
    barcode = Column(String, unique=True)
    image_url = Column(String)
    warranty_months = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="products")
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    movements = relationship("InventoryMovement", back_populates="product")
    quotation_items = relationship("QuotationItem", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    rentals = relationship("Rental", back_populates="product")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("categories.id"))  # Para subcategorías
    created_at = Column(DateTime, default=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="categories")
    products = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id])


class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    contact_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    rnc = Column(String)
    payment_terms = Column(String)  # Términos de pago
    created_at = Column(DateTime, default=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="suppliers")
    products = relationship("Product", back_populates="supplier")


# Modelo de Cotización
class Quotation(Base):
    __tablename__ = "quotations"
    
    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String, index=True, nullable=False)
    quotation_type = Column(String, default="venta")  # "venta" o "alquiler"
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=QuotationStatus.PENDIENTE)
    
    # Fechas
    quotation_date = Column(DateTime, default=get_rd_now)
    valid_until = Column(DateTime)
    
    # Montos
    subtotal = Column(Float, default=0)
    tax_rate = Column(Float, default=18)  # ITBIS 18%
    tax_amount = Column(Float, default=0)
    discount_percent = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    total = Column(Float, default=0)
    
    # Detalles
    notes = Column(Text)
    terms_conditions = Column(Text)
    payment_conditions = Column(String)
    delivery_time = Column(String)
    payment_method = Column(String, default="efectivo")  # Método de pago predeterminado
    
    # PDF
    pdf_path = Column(String)
    
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="quotations")
    client = relationship("Client", back_populates="quotations")
    created_by_user = relationship("User", back_populates="quotations")
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")
    sale = relationship("Sale", back_populates="quotation", uselist=False)
    rental = relationship("Rental", back_populates="quotation", uselist=False)


# Items de Cotización
class QuotationItem(Base):
    __tablename__ = "quotation_items"
    
    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # Nullable para mantener historial
    product_name = Column(String, nullable=True)  # Guardar nombre en el momento de la cotización
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0)
    subtotal = Column(Float, nullable=False)
    notes = Column(Text)
    
    # Relaciones
    quotation = relationship("Quotation", back_populates="items")
    product = relationship("Product", back_populates="quotation_items")


# Modelo de Venta
class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_number = Column(String, index=True, nullable=False)
    invoice_number = Column(String, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"))
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=SaleStatus.PENDIENTE_PAGO)
    
    # Fechas
    sale_date = Column(DateTime, default=get_rd_now)
    due_date = Column(DateTime)
    
    # Montos
    subtotal = Column(Float, default=0)
    tax_rate = Column(Float, default=18)
    tax_amount = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    total = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    balance = Column(Float, default=0)
    
    # Pago
    payment_method = Column(String)  # efectivo, transferencia, tarjeta, credito
    payment_reference = Column(String)
    
    # Detalles
    notes = Column(Text)
    
    # PDF
    invoice_pdf_path = Column(String)
    
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="sales")
    client = relationship("Client", back_populates="sales")
    created_by_user = relationship("User", back_populates="sales")
    quotation = relationship("Quotation", back_populates="sale")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale")


# Items de Venta
class SaleItem(Base):
    __tablename__ = "sale_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # Nullable para mantener historial
    product_name = Column(String, nullable=True)  # Guardar nombre en el momento de la venta
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0)
    subtotal = Column(Float, nullable=False)
    
    # Relaciones
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


# Modelo de Pagos
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    payment_date = Column(DateTime, default=get_rd_now)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    reference = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=get_rd_now)
    
    # Relaciones
    sale = relationship("Sale", back_populates="payments")


# Modelo de Alquiler
class Rental(Base):
    __tablename__ = "rentals"
    
    id = Column(Integer, primary_key=True, index=True)
    rental_number = Column(String, index=True, nullable=False)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # Opcional para múltiples items
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=RentalStatus.ACTIVO)
    
    # Fechas
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    actual_return_date = Column(DateTime)
    
    # Costos
    rental_period = Column(String)  # daily, weekly, monthly
    rental_price = Column(Float, nullable=True)  # Opcional para múltiples items
    deposit = Column(Float, default=0)
    total_cost = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)
    balance = Column(Float, default=0)
    payment_status = Column(String, default="pendiente_pago")  # pendiente_pago, parcial, pagado
    payment_method = Column(String, default="efectivo")  # efectivo, transferencia, tarjeta, cheque
    
    # Impuestos y descuentos
    tax_rate = Column(Float, default=0)  # Tasa de impuesto en porcentaje
    discount = Column(Float, default=0)  # Descuento en monto fijo
    discount_percent = Column(Float, default=0)  # Descuento en porcentaje
    
    # Detalles
    notes = Column(Text)
    condition_out = Column(Text)  # Condición al salir
    condition_in = Column(Text)  # Condición al regresar
    
    # PDF
    contract_pdf_path = Column(String)
    
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="rentals")
    quotation = relationship("Quotation", back_populates="rental")
    client = relationship("Client", back_populates="rentals")
    product = relationship("Product", back_populates="rentals")
    created_by_user = relationship("User", back_populates="rentals")
    payments = relationship("RentalPayment", back_populates="rental", cascade="all, delete-orphan")
    items = relationship("RentalItem", back_populates="rental", cascade="all, delete-orphan")


# Modelo de Items de Alquiler (para múltiples productos)
class RentalItem(Base):
    __tablename__ = "rental_items"
    
    id = Column(Integer, primary_key=True, index=True)
    rental_id = Column(Integer, ForeignKey("rentals.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # Nullable para mantener historial
    product_name = Column(String, nullable=True)  # Guardar nombre en el momento del alquiler
    quantity = Column(Integer, nullable=False, default=1)
    rental_days = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    rental = relationship("Rental", back_populates="items")
    product = relationship("Product")


# Modelo de Pagos de Alquiler
class RentalPayment(Base):
    __tablename__ = "rental_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    rental_id = Column(Integer, ForeignKey("rentals.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)  # efectivo, transferencia, tarjeta, credito, cheque
    payment_reference = Column(String)
    payment_date = Column(DateTime, default=get_rd_now)
    notes = Column(Text)
    created_at = Column(DateTime, default=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="rental_payments")
    rental = relationship("Rental", back_populates="payments")


# Modelo de Movimientos de Inventario
class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movement_type = Column(String, nullable=False)  # 'entrada', 'salida', 'ajuste', 'venta', 'alquiler', 'devolucion'
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    reference_type = Column(String)  # 'sale', 'rental', 'purchase', 'adjustment'
    reference_id = Column(Integer)  # ID de la venta, alquiler, etc.
    reason = Column(Text)
    created_at = Column(DateTime, default=get_rd_now)
    
    # Multi-tenant
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relaciones
    organization = relationship("Organization", back_populates="inventory_movements")
    product = relationship("Product", back_populates="movements")
    user = relationship("User", back_populates="movements")


# Modelo de Documentos Legales
class LegalDocument(Base):
    __tablename__ = "legal_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String, nullable=False)  # contrato, factura, permiso, certificado, etc.
    document_number = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String, nullable=False)
    issue_date = Column(Date)
    expiry_date = Column(Date)
    is_active = Column(Boolean, default=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    reference_type = Column(String)  # 'sale', 'rental', 'quotation'
    reference_id = Column(Integer)
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)


# Modelo de Auditoría
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # create, update, delete, login, logout
    entity_type = Column(String, nullable=False)  # user, product, sale, etc.
    entity_id = Column(Integer)
    old_values = Column(Text)  # JSON
    new_values = Column(Text)  # JSON
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=get_rd_now)
    
    # Relaciones
    user = relationship("User", back_populates="audit_logs")


# Modelo de Configuración del Sistema
class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    type = Column(String, nullable=False)  # warning, error, info, success
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    notification_key = Column(String, nullable=False)  # Clave única para identificar el tipo de notificación
    created_at = Column(DateTime, default=get_rd_now)
    updated_at = Column(DateTime, default=get_rd_now, onupdate=get_rd_now)
    
    # Relaciones
    organization = relationship("Organization")
    user = relationship("User")


class SystemFailure(Base):
    """Modelo para rastrear todas las fallas del sistema"""
    __tablename__ = "system_failures"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Información del error
    error_type = Column(String, nullable=False, index=True)  # http_exception, validation_error, database_error, etc.
    severity = Column(String, nullable=False, default="medium")  # low, medium, high, critical
    module = Column(String, nullable=False, index=True)  # sales, rentals, products, etc.
    endpoint = Column(String)  # API endpoint donde ocurrió el error
    method = Column(String)  # GET, POST, PUT, DELETE
    
    # Detalles del error
    error_code = Column(String)  # HTTP status code o código de error personalizado
    error_message = Column(Text, nullable=False)
    error_detail = Column(Text)  # Detalles adicionales del error
    stack_trace = Column(Text)  # Stack trace completo
    
    # Contexto
    request_data = Column(Text)  # Datos de la petición (JSON)
    user_agent = Column(String)
    ip_address = Column(String)
    
    # Estado
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=get_rd_now, index=True)
    
    # Relaciones
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
