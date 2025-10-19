from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List
from datetime import datetime
import enum


# Category
class CategoryBase(BaseModel):
    name: str
    tittle: str


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# Product
class ProductBase(BaseModel):
    catigory: int
    name: str
    price: Optional[int] = 0
    amount: Optional[int] = 0
    description: Optional[str] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    catigory: Optional[int] = None
    name: Optional[str] = None
    price: Optional[int] = None
    amount: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    available: Optional[bool] = None



class ProductImageOut(BaseModel):
    id: int
    image_url: str

    class Config:
        from_attributes = True


class ProductOut(ProductBase):
    id: int
    available: bool
    images: List[ProductImageOut] = []

    class Config:
        from_attributes = True

# Orders
class OrderStatus(str, enum.Enum):
    new = "new"
    pending = "pending"
    paid = "paid"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"


class OrderItemCreate(BaseModel):
    product_name: str
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    user_id: Optional[int] = None
    items: List[OrderItemCreate]
    status: Optional[OrderStatus] = OrderStatus.new


class OrderItemRead(BaseModel):
    id: int
    product_name: str
    quantity: int
    product: Optional["ProductOut"]

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    user_id: Optional[int]
    created_at: datetime
    status: OrderStatus
    items: List[OrderItemRead]

    class Config:
        from_attributes = True


class OrderItemUpdate(BaseModel):
    product_name: str
    quantity: int


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    order_items: Optional[List[OrderItemUpdate]] = None


# Auth
class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if v.isalnum():
            raise ValueError("Password must contain at least one special character")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class AuthCheckResponse(UserOut):
    pass
