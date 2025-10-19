import os
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from app.models import Order, OrderStatus
from sqlalchemy import select
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter()

@router.post("/callback")
async def payment_callback(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.form()
    order_id = data.get("orderid")
    status = data.get("status")

    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID missing")

    stmt = select(Order).where(Order.id == int(order_id))
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if status == "success":
        order.status = OrderStatus.paid
        redirect_url = f"{FRONTEND_URL}/payment/success?order_id={order.id}"
    else:
        order.status = OrderStatus.cancelled
        redirect_url = f"{FRONTEND_URL}/payment/fail?order_id={order.id}"

    await db.commit()
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/success")
async def payment_success(order_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return JSONResponse({
        "order_id": order.id,
        "email": order.user.email if order.user else None,
        "status": order.status,
        "message": "Оплата прошла успешно. Чек отправлен на указанную почту."
    })


@router.get("/fail")
async def payment_fail(order_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    return JSONResponse({
        "order_id": order.id if order else order_id,
        "status": "cancelled",
        "message": "Оплата не прошла. Попробуйте еще раз."
    })
