import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models
from database import get_db
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

router = APIRouter()

# Пути из .env
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "media")
PRODUCTS_MEDIA_DIR = os.getenv("PRODUCTS_MEDIA_DIR", os.path.join(MEDIA_ROOT, "products"))

# Убедимся, что папка существует
os.makedirs(PRODUCTS_MEDIA_DIR, exist_ok=True)

@router.post("/", response_model=schemas.ProductOut)
async def create_product(product: schemas.ProductCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_product(db, product)


@router.get("/", response_model=list[schemas.ProductOut])
async def read_products(db: AsyncSession = Depends(get_db)):
    return await crud.get_products(db)


@router.get("/{product_id}", response_model=schemas.ProductOut)
async def read_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    await crud.delete_product(db, product_id)
    return {"detail": "Product deleted"}


@router.patch("/{product_id}", response_model=schemas.ProductOut)
async def update_product(
    product_id: int,
    updates: schemas.ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    data = updates.model_dump(exclude_unset=True)
    data.pop("available", None)

    updated = await crud.update_product(db, product_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated


@router.post("/{product_id}/upload-image")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    os.makedirs(PRODUCTS_MEDIA_DIR, exist_ok=True)

    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join(PRODUCTS_MEDIA_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/{PRODUCTS_MEDIA_DIR}/{filename}".replace("\\", "/")

    image = models.ProductImage(
        product_id=product.id,
        image_url=relative_url
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return {"id": image.id, "image_url": image.image_url}


@router.delete("/images/{image_id}")
async def delete_product_image(image_id: int, db: AsyncSession = Depends(get_db)):
    image = await db.get(models.ProductImage, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = os.path.join(os.getcwd(), image.image_url.lstrip("/"))

    if os.path.exists(file_path):
        os.remove(file_path)

    await db.delete(image)
    await db.commit()

    return {"detail": "Image deleted"}


@router.get("/{product_id}/images")
async def get_product_images_route(product_id: int, db: AsyncSession = Depends(get_db)):
    images = await crud.get_product_images(db, product_id)
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this product")
    return images


@router.get("/media/products/{filename}")
async def serve_product_image(filename: str):
    file_path = os.path.join(PRODUCTS_MEDIA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)
