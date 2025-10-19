from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from fastapi import Request, HTTPException
from app.auth_crud import get_current_user
from sqlalchemy.exc import IntegrityError


from typing import Optional, List, cast

from app.models import Order, OrderItem, Product, Category
from app import schemas, models
import httpx
import os

PAYKEEPER_URL = os.getenv("PAYKEEPER_URL", "https://demo.paykeeper.ru/create/")
SUCCESS_URL = os.getenv("PAYKEEPER_SUCCESS_URL", "http://localhost:5173/checkout/success")
FAIL_URL = os.getenv("PAYKEEPER_FAIL_URL", "http://localhost:5173/checkout/fail")


async def create_payment(order_id: int, amount: float, client_email: str, client_phone: str):
    payload = {
        "clientid": f"order-{order_id}",
        "orderid": str(order_id),
        "sum": str(amount),
        "service_name": "Оплата заказа",
        "client_email": client_email,
        "client_phone": client_phone,
        "success_url": SUCCESS_URL,  # ✅ редирект после оплаты
        "fail_url": FAIL_URL         # ❌ редирект при неудаче
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(PAYKEEPER_URL, data=payload)
        response.raise_for_status()
        data = response.json()

    return data["invoice_url"]


# --- USER CRUD ---
async def get_current_user_optional(request: Request) -> Optional[models.User]:
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

# --- CATEGORY CRUD ---

async def create_category(db: AsyncSession, category: schemas.CategoryCreate):
    new_cat = Category(**category.dict())
    db.add(new_cat)
    await db.commit()
    await db.refresh(new_cat)
    return new_cat

async def get_categories(db: AsyncSession):
    result = await db.execute(select(Category))
    return list(result.scalars().all())

# --- PRODUCT CRUD ---

async def create_product(db: AsyncSession, product: schemas.ProductCreate):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    try:
        await db.commit()
        await db.refresh(new_product)
        return new_product
    except IntegrityError as e:
        await db.rollback()
        # Проверяем, что именно уникальность нарушена
        if "products_name_key" in str(e.orig):
            raise HTTPException(
                status_code=409,
                detail=f"Товар с названием '{product.name}' уже существует"
            )
        raise

async def get_products(db: AsyncSession):
    result = await db.execute(select(Product))
    return list(result.scalars().all())

async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def delete_product(db: AsyncSession, product_id: int):
    await db.execute(delete(Product).where(Product.id == product_id))
    await db.commit()

async def update_product(db: AsyncSession, product_id: int, updates: dict):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        return None

    for key, value in updates.items():
        setattr(product, key, value)

    try:
        await db.commit()
        await db.refresh(product)
        return product
    except IntegrityError as e:
        await db.rollback()
        if "products_name_key" in str(e.orig):
            raise HTTPException(
                status_code=409,
                detail=f"Товар с названием '{updates.get('name')}' уже существует"
            )
        raise



# --- ORDER CRUD ---

async def create_order(db: AsyncSession, order_data: schemas.OrderCreate):
    order = models.Order(user_id=order_data.user_id, status=order_data.status or models.OrderStatus.new)
    db.add(order)
    await db.flush()

    for item in order_data.items:
        db.add(models.OrderItem(
            order_id=order.id,
            product_name=item.product_name,
            quantity=item.quantity
        ))

    await db.commit()

    # Теперь достаём заказ с подгруженными связями
    result = await db.execute(
        select(models.Order)
        .options(
            selectinload(models.Order.items).selectinload(models.OrderItem.product),
            selectinload(models.Order.user)
        )
        .where(models.Order.id == order.id)
    )
    return result.scalar_one()


# Все заказы
async def get_all_orders(db: AsyncSession):
    result = await db.execute(
        select(models.Order)
        .options(
            selectinload(models.Order.items).selectinload(models.OrderItem.product)
        )
    )
    return result.scalars().unique().all()


# Заказы пользователя
async def get_orders_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.Order)
        .options(
            selectinload(models.Order.items).selectinload(models.OrderItem.product)
        )
        .where(models.Order.user_id == user_id)
    )
    return result.scalars().unique().all()


# Обновление заказа
async def update_order(db: AsyncSession, order_id: int, order_data: schemas.OrderUpdate):
    result = await db.execute(select(models.Order).where(models.Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return None

    for key, value in order_data.dict(exclude_unset=True).items():
        setattr(order, key, value)

    await db.commit()
    await db.refresh(order)
    return order


# Удаление заказа
async def delete_order(db: AsyncSession, order_id: int):
    result = await db.execute(select(models.Order).where(models.Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return False

    await db.delete(order)
    await db.commit()
    return True

#Заказ по id
async def get_order_by_id(db: AsyncSession, order_id: int):
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# --- PRODUCT IMAGES CRUD ---
async def get_product_images(db: AsyncSession, product_id: int):
    """
    Возвращает все изображения для конкретного товара по его ID.
    """
    result = await db.execute(
        select(models.ProductImage)
        .where(models.ProductImage.product_id == product_id)
    )
    images = result.scalars().all()
    return [
        {"id": img.id, "image_url": img.image_url}
        for img in images
    ]

