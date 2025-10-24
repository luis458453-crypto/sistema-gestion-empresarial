"""
Modelos para el sistema multi-tenant (SaaS)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class OrganizationStatus(str, enum.Enum):
    """Estados de una organización"""
    pending = "pending"  # Esperando aprobación
    active = "active"    # Activa y operando
    suspended = "suspended"  # Suspendida
    cancelled = "cancelled"  # Cancelada


class SubscriptionPlan(str, enum.Enum):
    """Planes de suscripción"""
    free = "free"
    basic = "basic"
    premium = "premium"
    enterprise = "enterprise"


class Currency(str, enum.Enum):
    """Monedas soportadas"""
    USD = "USD"  # Dólar estadounidense
    EUR = "EUR"  # Euro
    DOP = "DOP"  # Peso dominicano


class Organization(Base):
    """
    Modelo de Organización/Empresa
    Cada cliente que se registra crea una organización
    """
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información básica
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)  # URL amigable
    email = Column(String, nullable=False)
    phone = Column(String)
    
    # Personalización
    logo_url = Column(String)  # URL del logo subido
    primary_color = Column(String, default="#0066cc")  # Color principal
    secondary_color = Column(String, default="#00cc66")  # Color secundario
    
    # Datos para facturación
    rnc = Column(String)  # RNC o número de identificación fiscal
    address = Column(String)  # Dirección completa
    city = Column(String)  # Ciudad
    address_number = Column(String)  # Número de dirección
    website = Column(String)  # Página web
    invoice_email = Column(String)  # Email para facturas (puede ser diferente al principal)
    stamp_url = Column(String)  # URL del sello/firma para facturas
    
    # Colores de módulos (gradientes)
    clients_start_color = Column(String, default="#10b981")
    clients_end_color = Column(String, default="#059669")
    quotations_start_color = Column(String, default="#f59e0b")
    quotations_end_color = Column(String, default="#d97706")
    sales_start_color = Column(String, default="#3b82f6")
    sales_end_color = Column(String, default="#2563eb")
    rentals_start_color = Column(String, default="#8b5cf6")
    rentals_end_color = Column(String, default="#7c3aed")
    products_start_color = Column(String, default="#06b6d4")
    products_end_color = Column(String, default="#0891b2")
    categories_start_color = Column(String, default="#ec4899")
    categories_end_color = Column(String, default="#db2777")
    suppliers_start_color = Column(String, default="#f97316")
    suppliers_end_color = Column(String, default="#ea580c")
    goals_start_color = Column(String, default="#14b8a6")
    goals_end_color = Column(String, default="#0d9488")
    quick_actions_start_color = Column(String, default="#6366f1")
    quick_actions_end_color = Column(String, default="#4f46e5")
    
    # Estado y suscripción
    status = Column(SQLEnum(OrganizationStatus), default=OrganizationStatus.pending)
    subscription_plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.free)
    
    # Módulos habilitados (JSON)
    modules_enabled = Column(JSON, default={
        "sales": True,
        "rentals": True,
        "quotations": True,
        "clients": True,
        "inventory": True,
        "categories": True,
        "suppliers": True,
        "dashboard": True
    })
    
    # Límites según plan
    max_users = Column(Integer, default=1)
    max_products = Column(Integer, default=100)
    max_storage_mb = Column(Integer, default=100)
    
    # Configuraciones del Dashboard
    monthly_sales_goal = Column(Float, default=0)  # Meta de ventas mensual
    monthly_growth_target = Column(Float, default=0)  # Meta de crecimiento mensual (%)
    conversion_rate_target = Column(Float, default=0)  # Meta de tasa de conversión (%)
    
    # Configuración de moneda
    currency = Column(SQLEnum(Currency), default=Currency.USD)  # Moneda principal
    
    # Metadata
    notes = Column(Text)  # Notas internas (para el admin)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)  # Cuando fue aprobada
    approved_by = Column(Integer)  # ID del admin que aprobó
    
    # Relaciones (con cascade para eliminar en cascada)
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="organization", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="organization", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="organization", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="organization", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="organization", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="organization", cascade="all, delete-orphan")
    rentals = relationship("Rental", back_populates="organization", cascade="all, delete-orphan")
    rental_payments = relationship("RentalPayment", back_populates="organization", cascade="all, delete-orphan")
    inventory_movements = relationship("InventoryMovement", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization {self.name} ({self.status})>"
    
    def is_active(self):
        """Verifica si la organización está activa"""
        return self.status == OrganizationStatus.active
    
    def can_use_module(self, module_name):
        """Verifica si puede usar un módulo específico"""
        return self.modules_enabled.get(module_name, False)
    
    def get_limits(self):
        """Retorna los límites según el plan"""
        limits = {
            "free": {"users": 1, "products": 100, "storage_mb": 100},
            "basic": {"users": 3, "products": 500, "storage_mb": 500},
            "premium": {"users": 10, "products": 2000, "storage_mb": 2000},
            "enterprise": {"users": -1, "products": -1, "storage_mb": -1}  # -1 = ilimitado
        }
        return limits.get(self.subscription_plan.value, limits["free"])


class OrganizationInvitation(Base):
    """
    Invitaciones para unirse a una organización
    """
    __tablename__ = "organization_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    role = Column(String, default="vendedor")
    
    status = Column(String, default="pending")  # pending, accepted, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    accepted_at = Column(DateTime)
    
    def is_valid(self):
        """Verifica si la invitación es válida"""
        if self.status != "pending":
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

