from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Category Schemas
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
    created_at: datetime
    
    class Config:
        from_attributes = True


# Supplier Schemas
class SupplierBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class Supplier(SupplierBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    price: float = Field(gt=0)
    cost: Optional[float] = Field(default=None, gt=0)
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=10, ge=0)
    max_stock: int = Field(default=100, ge=0)
    location: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    price: Optional[float] = Field(default=None, gt=0)
    cost: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    min_stock: Optional[int] = Field(default=None, ge=0)
    max_stock: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = None
    is_active: Optional[bool] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None
    supplier: Optional[Supplier] = None
    
    class Config:
        from_attributes = True


# Inventory Movement Schemas
class InventoryMovementBase(BaseModel):
    product_id: int
    movement_type: str  # 'entrada', 'salida', 'ajuste'
    quantity: int
    reason: Optional[str] = None


class InventoryMovementCreate(InventoryMovementBase):
    pass


class InventoryMovement(InventoryMovementBase):
    id: int
    user_id: int
    previous_stock: int
    new_stock: int
    created_at: datetime
    product: Optional[Product] = None
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_products: int
    total_value: float
    low_stock_products: int
    total_categories: int
    total_suppliers: int
    recent_movements: int


class LowStockAlert(BaseModel):
    product_id: int
    sku: str
    name: str
    current_stock: int
    min_stock: int
    category: Optional[str] = None
