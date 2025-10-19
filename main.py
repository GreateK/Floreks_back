from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routers import categories, products, orders, auth, PayKeeper

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory="media"), name="media")
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(PayKeeper.router, prefix="/payments", tags=["payments"])

MEDIA_DIR = os.path.join(os.getcwd(), "media")
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

# Монтируем папку /media для доступа к файлам
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")