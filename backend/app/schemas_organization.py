"""
Schemas para el sistema multi-tenant (SaaS)
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class OrganizationStatus(str, Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
    cancelled = "cancelled"


class Currency(str, Enum):
    USD = "USD"  # Dólar estadounidense
    EUR = "EUR"  # Euro
    DOP = "DOP"  # Peso dominicano


class SubscriptionPlan(str, Enum):
    free = "free"
    basic = "basic"
    premium = "premium"
    enterprise = "enterprise"


# Schemas de Organización

class OrganizationBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    primary_color: Optional[str] = "#0066cc"
    secondary_color: Optional[str] = "#00cc66"


class OrganizationRegister(OrganizationBase):
    """Schema para registro de nueva organización"""
    modules_requested: Dict[str, bool] = {
        "sales": True,
        "rentals": False,
        "quotations": True,
        "clients": True,
        "inventory": True,
        "categories": True,
        "suppliers": True,
        "dashboard": True
    }
    admin_username: str
    admin_email: EmailStr
    admin_password: str
    
    @validator('admin_password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v


class OrganizationCreate(OrganizationBase):
    slug: str
    modules_enabled: Optional[Dict[str, bool]] = None
    subscription_plan: SubscriptionPlan = SubscriptionPlan.free


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    modules_enabled: Optional[Dict[str, bool]] = None
    subscription_plan: Optional[SubscriptionPlan] = None
    status: Optional[OrganizationStatus] = None
    currency: Optional[Currency] = None
    notes: Optional[str] = None
    # Campos de facturación
    rnc: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    address_number: Optional[str] = None
    website: Optional[str] = None
    invoice_email: Optional[str] = None
    stamp_url: Optional[str] = None
    # Colores de módulos
    clients_start_color: Optional[str] = None
    clients_end_color: Optional[str] = None
    quotations_start_color: Optional[str] = None
    quotations_end_color: Optional[str] = None
    sales_start_color: Optional[str] = None
    sales_end_color: Optional[str] = None
    rentals_start_color: Optional[str] = None
    rentals_end_color: Optional[str] = None
    products_start_color: Optional[str] = None
    products_end_color: Optional[str] = None
    categories_start_color: Optional[str] = None
    categories_end_color: Optional[str] = None
    suppliers_start_color: Optional[str] = None
    suppliers_end_color: Optional[str] = None
    goals_start_color: Optional[str] = None
    goals_end_color: Optional[str] = None
    quick_actions_start_color: Optional[str] = None
    quick_actions_end_color: Optional[str] = None


class Organization(OrganizationBase):
    id: int
    slug: str
    logo_url: Optional[str] = None
    status: OrganizationStatus
    subscription_plan: SubscriptionPlan
    modules_enabled: Optional[Dict[str, bool]] = None
    max_users: int
    max_products: int
    max_storage_mb: int
    currency: Currency
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    # Campos de facturación
    rnc: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    address_number: Optional[str] = None
    website: Optional[str] = None
    invoice_email: Optional[str] = None
    stamp_url: Optional[str] = None
    # Colores de módulos
    clients_start_color: Optional[str] = None
    clients_end_color: Optional[str] = None
    quotations_start_color: Optional[str] = None
    quotations_end_color: Optional[str] = None
    sales_start_color: Optional[str] = None
    sales_end_color: Optional[str] = None
    rentals_start_color: Optional[str] = None
    rentals_end_color: Optional[str] = None
    products_start_color: Optional[str] = None
    products_end_color: Optional[str] = None
    categories_start_color: Optional[str] = None
    categories_end_color: Optional[str] = None
    suppliers_start_color: Optional[str] = None
    suppliers_end_color: Optional[str] = None
    goals_start_color: Optional[str] = None
    goals_end_color: Optional[str] = None
    quick_actions_start_color: Optional[str] = None
    quick_actions_end_color: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrganizationWithStats(Organization):
    """Organización con estadísticas de uso"""
    total_users: int = 0
    total_products: int = 0
    total_sales: int = 0
    storage_used_mb: float = 0


# Schemas de Configuración

class OrganizationSettings(BaseModel):
    """Configuración que el cliente puede cambiar"""
    name: str
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    modules_enabled: Optional[Dict[str, bool]] = None
    # Campos de facturación
    rnc: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    address_number: Optional[str] = None
    website: Optional[str] = None
    invoice_email: Optional[str] = None
    phone: Optional[str] = None
    stamp_url: Optional[str] = None
    # Colores de módulos (inicio y fin para gradientes)
    clients_start_color: Optional[str] = None
    clients_end_color: Optional[str] = None
    quotations_start_color: Optional[str] = None
    quotations_end_color: Optional[str] = None
    sales_start_color: Optional[str] = None
    sales_end_color: Optional[str] = None
    rentals_start_color: Optional[str] = None
    rentals_end_color: Optional[str] = None
    products_start_color: Optional[str] = None
    products_end_color: Optional[str] = None
    categories_start_color: Optional[str] = None
    categories_end_color: Optional[str] = None
    suppliers_start_color: Optional[str] = None
    suppliers_end_color: Optional[str] = None
    goals_start_color: Optional[str] = None
    goals_end_color: Optional[str] = None
    quick_actions_start_color: Optional[str] = None
    quick_actions_end_color: Optional[str] = None


class DashboardSettings(BaseModel):
    """Configuraciones del Dashboard"""
    monthly_sales_goal: Optional[float] = None


class OrganizationLimits(BaseModel):
    """Límites de la organización"""
    max_users: int
    max_products: int
    max_storage_mb: int
    current_users: int
    current_products: int
    storage_used_mb: float
    
    @property
    def users_remaining(self):
        if self.max_users == -1:
            return float('inf')
        return max(0, self.max_users - self.current_users)
    
    @property
    def products_remaining(self):
        if self.max_products == -1:
            return float('inf')
        return max(0, self.max_products - self.current_products)


# Schemas de Aprobación

class OrganizationApproval(BaseModel):
    """Para aprobar/rechazar una organización"""
    approved: bool
    modules_enabled: Optional[Dict[str, bool]] = None
    subscription_plan: Optional[SubscriptionPlan] = None
    notes: Optional[str] = None


# Schemas de Invitación

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = "vendedor"


class Invitation(BaseModel):
    id: int
    organization_id: int
    email: EmailStr
    role: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


