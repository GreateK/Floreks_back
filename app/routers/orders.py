from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from typing import List, Optional
from app import models, schemas
import app.crud as crud
from app.schemas import OrderCreate, OrderRead

router = APIRouter()

@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(crud.get_current_user_optional)
):
    user_id = current_user.id if current_user else None
    order_data.user_id = user_id
    return await crud.create_order(db, order_data)

@router.get("/", response_model=List[OrderRead])
async def read_all_orders(db: AsyncSession = Depends(get_db)):
    return await crud.get_all_orders(db)

@router.get("/user/{user_id}", response_model=List[OrderRead])
async def read_orders_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await crud.get_orders_by_user(db, user_id)

@router.get("/{order_id}", response_model=OrderRead)
async def read_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}", response_model=OrderRead)
async def update_order(order_id: int, order_data: schemas.OrderUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.update_order(db, order_id, order_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    success = await crud.delete_order(db, order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")

@router.get("/statuses")
async def get_order_statuses():
    return [
        {"id": 1, "name": "Новый"},
        {"id": 2, "name": "В обработке"},
        {"id": 3, "name": "Завершён"},
    ]
