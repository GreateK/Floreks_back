from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
import jwt

from app import schemas, models
from app.auth_crud import (
    get_user_by_email,
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db

router = APIRouter()
security_scheme = HTTPBearer(auto_error=False)


class AuthCheckResponse(BaseModel):
    email: Optional[str]


@router.post("/register", response_model=schemas.UserOut)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    existing = await get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email уже используется")

    hashed_pw = get_password_hash(user.password)
    new_user = models.User(email=user.email, password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.UserOut)
async def login(user: schemas.UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    """Авторизация пользователя"""
    db_user = await get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Неверные email или пароль")

    token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,  # 1 день
        samesite="lax",
    )

    return db_user


@router.get("/me")
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Проверка текущего авторизованного пользователя"""
    return {"email": current_user.email}


@router.post("/logout")
def logout(response: Response):
    """Выход — удалить токен"""
    response.delete_cookie("access_token")
    return {"detail": "Выход выполнен успешно"}


@router.get("/check", response_model=AuthCheckResponse)
async def check_auth(request: Request):
    """Проверить авторизацию через cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return {"email": None}

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return {"email": None}
        return {"email": email}
    except jwt.ExpiredSignatureError:
        return {"email": None}
    except jwt.InvalidTokenError:
        return {"email": None}
