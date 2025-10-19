from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.CategoryOut)
async def create_category(category: schemas.CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_category(db, category)

@router.get("/", response_model=list[schemas.CategoryOut])
async def read_categories(db: AsyncSession = Depends(get_db)):
    return await crud.get_categories(db)