from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func, Computed, Enum as PgEnum
from sqlalchemy.orm import relationship
from database import Base
import enum

class Category(Base):
    __tablename__ = "catigories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tittle = Column(String, nullable=False)

    products = relationship("Product", back_populates="category")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    image_url = Column(String, nullable=False)

    product = relationship("Product", back_populates="images")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    catigory = Column(Integer, ForeignKey("catigories.id"))
    name = Column(String, nullable=False)
    price = Column(Integer, default=0)
    amount = Column(Integer, default=0)
    available = Column(Boolean, Computed("amount > 0", persisted=True), nullable=False)
    description = Column(String, server_default="Описание отсутсвует")
    image_url = Column(String, nullable=True)

    category = relationship("Category", back_populates="products")
    images = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )




class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    orders = relationship("Order", back_populates="user")


class OrderStatus(str, enum.Enum):
    new = "new"
    pending = "pending"
    paid = "paid"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(PgEnum(OrderStatus, name="orders_statuses", create_type=False), nullable=False, server_default=OrderStatus.new.value)

    user = relationship(
        "User",
        back_populates="orders",
        lazy="joined"
    )
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete",
        lazy="selectin"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_name = Column(String, ForeignKey("products.name"))
    quantity = Column(Integer, nullable=False)

    product = relationship("Product", lazy="selectin")
    order = relationship("Order", back_populates="items")
