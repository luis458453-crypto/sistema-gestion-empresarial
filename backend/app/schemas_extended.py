from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    VENDEDOR = "vendedor"
    ALMACEN = "almacen"
    EMPLEADO = "empleado"


class ClientType(str, Enum):
    HOSPITAL = "hospital"
    MEDICO = "medico"
    EMPRESA = "empresa"
    PARTICULAR = "particular"


class ClientStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"


class QuotationStatus(str, Enum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    CONVERTIDA = "convertida"
    VENCIDA = "vencida"


class SaleStatus(str, Enum):
    COMPLETADA = "completada"
    PENDIENTE_PAGO = "pendiente_pago"
    PARCIAL = "parcial"
    CANCELADA = "cancelada"


class PaymentMethod(str, Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    TARJETA = "tarjeta"
    CHEQUE = "cheque"


class RentalStatus(str, Enum):
    ACTIVO = "activo"
    DEVUELTO = "devuelto"
    VENCIDO = "vencido"
    RENOVADO = "renovado"
    CANCELADO = "cancelado"


class ProductType(str, Enum):
    VENTA = "venta"
    ALQUILER = "alquiler"
    AMBOS = "ambos"


# Authentication Schemas
class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# User Schemas Extendidos
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.EMPLEADO
    phone: Optional[str] = None
    organization_id: Optional[int] = None  # NULL para super admin


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    avatar: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Client Schemas
class ClientBase(BaseModel):
    name: str
    client_type: ClientType = ClientType.PARTICULAR
    status: ClientStatus = ClientStatus.ACTIVO
    rnc: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "República Dominicana"
    contact_person: Optional[str] = None
    notes: Optional[str] = None
    credit_limit: float = 0
    credit_days: int = 0


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    client_type: Optional[ClientType] = None
    status: Optional[ClientStatus] = None
    rnc: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None
    credit_limit: Optional[float] = None
    credit_days: Optional[int] = None
    is_recurrent: Optional[bool] = None


class Client(ClientBase):
    id: int
    is_recurrent: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Product Schemas Extendidos
class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    product_type: str = "venta"
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    price: Optional[float] = Field(default=0, ge=0)
    rental_price_daily: Optional[float] = Field(default=None, ge=0)
    rental_price_weekly: Optional[float] = Field(default=None, ge=0)
    rental_price_monthly: Optional[float] = Field(default=None, ge=0)
    cost: Optional[float] = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=10, ge=0)
    max_stock: int = Field(default=100, ge=0)
    location: Optional[str] = None
    barcode: Optional[str] = None
    warranty_months: int = 0
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_type: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    price: Optional[float] = Field(default=None, ge=0)
    rental_price_daily: Optional[float] = None
    rental_price_weekly: Optional[float] = None
    rental_price_monthly: Optional[float] = None
    cost: Optional[float] = Field(default=None, ge=0)
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    location: Optional[str] = None
    barcode: Optional[str] = None
    warranty_months: Optional[int] = None
    is_active: Optional[bool] = None


# Quotation Item Schema
class QuotationItemBase(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    discount_percent: float = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationItem(QuotationItemBase):
    id: int
    quotation_id: int
    subtotal: float
    product_name: Optional[str] = None
    product: Optional['ProductSimple'] = None
    
    class Config:
        from_attributes = True


# Quotation Schemas
class QuotationBase(BaseModel):
    quotation_type: str = "venta"  # "venta" o "alquiler"
    client_id: int
    valid_until: Optional[datetime] = None
    tax_rate: float = 18.0
    discount_percent: float = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    payment_conditions: Optional[str] = None
    delivery_time: Optional[str] = None
    payment_method: Optional[str] = "efectivo"


class QuotationCreate(QuotationBase):
    items: List[QuotationItemCreate]


class QuotationUpdate(BaseModel):
    quotation_type: Optional[str] = None
    client_id: Optional[int] = None
    status: Optional[QuotationStatus] = None
    valid_until: Optional[datetime] = None
    tax_rate: Optional[float] = None
    discount_percent: Optional[float] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    payment_conditions: Optional[str] = None
    delivery_time: Optional[str] = None
    payment_method: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None


class Quotation(QuotationBase):
    id: int
    quotation_number: str
    quotation_type: str = "venta"
    created_by: int
    status: QuotationStatus
    quotation_date: datetime
    subtotal: float
    tax_amount: float
    discount_amount: float
    total: float
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = None
    items: List[QuotationItem] = []
    client: Optional[Client] = None  # Información del cliente
    payment_method: Optional[str] = "efectivo"
    
    class Config:
        from_attributes = True


# Product Simple Schema (para items)
class ProductSimple(BaseModel):
    id: int
    name: str
    sku: Optional[str] = None
    
    class Config:
        from_attributes = True


# Sale Item Schema
class SaleItemBase(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    discount_percent: float = Field(default=0, ge=0, le=100)


class SaleItemCreate(SaleItemBase):
    pass


class SaleItem(SaleItemBase):
    id: int
    sale_id: int
    subtotal: float
    product_name: Optional[str] = None
    product: Optional['ProductSimple'] = None
    
    class Config:
        from_attributes = True


# Sale Schemas
class SaleBase(BaseModel):
    client_id: int
    quotation_id: Optional[int] = None
    tax_rate: float = 18.0
    discount_amount: float = 0
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None


class SaleCreate(SaleBase):
    items: List[SaleItemCreate]
    status: Optional[SaleStatus] = SaleStatus.PENDIENTE_PAGO
    paid_amount: Optional[float] = 0


class SaleUpdate(BaseModel):
    status: Optional[SaleStatus] = None
    paid_amount: Optional[float] = None
    notes: Optional[str] = None


class Sale(SaleBase):
    id: int
    sale_number: str
    invoice_number: Optional[str] = None
    created_by: int
    status: SaleStatus
    sale_date: datetime
    subtotal: float
    tax_amount: float
    total: float
    paid_amount: float
    balance: float
    invoice_pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = None
    items: List[SaleItem] = []
    client: Optional[Client] = None  # Información del cliente
    
    class Config:
        from_attributes = True


# Payment Schema
class PaymentBase(BaseModel):
    sale_id: int
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase):
    id: int
    payment_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Rental Item Schema (para múltiples productos en un alquiler)
class RentalItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)


class RentalItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    rental_days: int
    unit_price: float
    product: Optional['Product'] = None
    
    class Config:
        from_attributes = True


# Rental Schemas
class RentalBase(BaseModel):
    client_id: int
    product_id: Optional[int] = None  # Opcional para compatibilidad con items
    start_date: datetime
    end_date: datetime
    rental_period: str = "daily"  # daily, weekly, monthly
    rental_price: Optional[float] = None  # Opcional para compatibilidad con items
    deposit: float = 0
    tax_rate: float = 0  # Tasa de impuesto en porcentaje
    discount: float = 0  # Descuento en monto fijo (compatibilidad hacia atrás)
    discount_percent: float = 0  # Descuento en porcentaje
    payment_method: str = "efectivo"  # efectivo, transferencia, tarjeta, cheque
    notes: Optional[str] = None
    condition_out: Optional[str] = None


class RentalCreate(RentalBase):
    items: Optional[List[RentalItemCreate]] = None  # Nuevo: array de items


class RentalUpdate(BaseModel):
    status: Optional[RentalStatus] = None
    actual_return_date: Optional[datetime] = None
    condition_in: Optional[str] = None
    paid_amount: Optional[float] = None
    notes: Optional[str] = None


class Rental(RentalBase):
    id: int
    rental_number: str
    created_by: int
    status: RentalStatus
    actual_return_date: Optional[datetime] = None
    total_cost: float
    paid_amount: float
    balance: float
    payment_status: str
    payment_method: str
    condition_in: Optional[str] = None
    contract_pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = None
    payments: List['RentalPayment'] = []
    items: List[RentalItem] = []  # Items del alquiler
    client: Optional[Client] = None  # Información del cliente
    product: Optional['Product'] = None  # Información del producto (compatibilidad)
    
    class Config:
        from_attributes = True


# Rental Payment Schemas
class RentalPaymentBase(BaseModel):
    rental_id: int
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None


class RentalPaymentCreate(RentalPaymentBase):
    pass


class RentalPayment(RentalPaymentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class DashboardStats(BaseModel):
    # Ventas
    total_sales_today: float
    total_sales_month: float
    total_sales_year: float
    total_sales_all_time: float
    pending_sales: int
    
    # Inventario
    total_products: int
    total_value: float
    low_stock_products: int
    products_rented: int
    
    # Clientes
    total_clients: int
    active_clients: int
    new_clients_month: int
    
    # Cotizaciones
    pending_quotations: int
    accepted_quotations: int
    quotations_this_month: int
    
    # Alquileres
    active_rentals: int
    overdue_rentals: int
    rentals_this_month: int
    
    # Financiero
    pending_payments: float
    total_revenue_month: float
    
    # Ingresos de alquileres
    rental_income_today: float
    rental_income_month: float
    rental_income_year: float
    total_rentals_all_time: float
    pending_rental_payments: float


class ReportFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# Notification Schemas
class NotificationBase(BaseModel):
    type: str
    title: str
    message: str
    notification_key: str


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_deleted: Optional[bool] = None


class Notification(NotificationBase):
    id: int
    organization_id: Optional[int] = None
    user_id: Optional[int] = None
    is_read: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Audit Log Schema
class AuditLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None


class AuditLog(AuditLogBase):
    id: int
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# System Config Schema
class SystemConfigBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None


class SystemConfig(SystemConfigBase):
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard Schemas adicionales
class LowStockAlert(BaseModel):
    product_id: int
    sku: str
    name: str
    current_stock: int
    min_stock: int
    category: Optional[str] = None


# Inventory Movement Schemas (definidos después de Product)


# Category Schemas (para compatibilidad con código antiguo)
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Category(CategoryBase):
    id: int
    organization_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Supplier Schemas (para compatibilidad con código antiguo)
class SupplierBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class Supplier(SupplierBase):
    id: int
    organization_id: Optional[int] = None
    rnc: Optional[str] = None
    payment_terms: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Product Schema (definido después de Category y Supplier)
class Product(ProductBase):
    id: int
    stock_available: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None
    supplier: Optional[Supplier] = None
    
    class Config:
        from_attributes = True


# Product Schema para compatibilidad con código antiguo
class ProductOld(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None
    supplier: Optional[Supplier] = None
    
    class Config:
        from_attributes = True


# Inventory Movement Schemas (definidos después de Product)
class InventoryMovementBase(BaseModel):
    product_id: int
    movement_type: str  # 'entrada', 'salida', 'ajuste', 'venta', 'alquiler', 'devolucion'
    quantity: int
    reason: Optional[str] = None


class InventoryMovementCreate(InventoryMovementBase):
    pass


class InventoryMovement(InventoryMovementBase):
    id: int
    user_id: int
    previous_stock: int
    new_stock: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_at: datetime
    product: Optional[Product] = None
    
    class Config:
        from_attributes = True


# System Failure Schemas
class SystemFailureBase(BaseModel):
    error_type: str
    severity: str = "medium"
    module: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    error_code: Optional[str] = None
    error_message: str
    error_detail: Optional[str] = None
    stack_trace: Optional[str] = None
    request_data: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class SystemFailureCreate(SystemFailureBase):
    organization_id: Optional[int] = None
    user_id: Optional[int] = None


class SystemFailureUpdate(BaseModel):
    is_resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None


class SystemFailure(SystemFailureBase):
    id: int
    organization_id: Optional[int] = None
    user_id: Optional[int] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SystemFailureSummary(BaseModel):
    """Resumen de fallas del sistema"""
    total_failures: int
    unresolved_failures: int
    resolved_failures: int
    critical_failures: int
    high_failures: int
    medium_failures: int
    low_failures: int
    failures_by_module: dict
    failures_by_type: dict
    failures_by_day: dict
    recent_failures: List[SystemFailure]
