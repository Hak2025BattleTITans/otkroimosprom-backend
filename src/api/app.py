import logging
import os
from logging.config import dictConfig
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api import auth_router
from api.data_router import router as data_router
from api.user_router import router as user_router
from logging_config import LOGGING_CONFIG, ColoredFormatter
from src.database import init_db 

# Setup logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if type(handler) is logging.StreamHandler:
        handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))

app = FastAPI()

# Set up API routers
api_v1 = APIRouter(prefix="/v1", tags=["v1"])
api_v1.include_router(auth_router)

app.include_router(api_v1, prefix="/api")

# CORS settings
origins = [
    "https://ruzserver.ru",
    "https://okto.ruzserver.ru",
    "https://www.ruzserver.ru",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # можно поставить ["*"] для теста
    allow_credentials=True,
    allow_methods=["*"],            # разрешить все методы (GET, POST и т.д.)
    allow_headers=["*"],            # разрешить все заголовки
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполнится при старте приложения
    logger.info("Application startup...")
    logger.info("Initializing database...")
    init_db() # Создаем таблицы в БД при старте
    yield
    # Код, который выполнится при завершении работы
    logger.info("Application shutdown.")

app = FastAPI(
    title="OtkroiMosprom API",
    description="API для проекта 'Откроймоспром'",
    version="1.0.0",
    lifespan=lifespan 
)

# Настройка API роутеров
api_v1 = APIRouter(prefix="/v1")
api_v1.include_router(auth_router)
api_v1.include_router(data_router) 
api_v1.include_router(user_router)
app.include_router(api_v1, prefix="/api")

# Настройка CORS
origins = [
    "https://ruzserver.ru",
    "https://okto.ruzserver.ru",
    "https://www.ruzserver.ru",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root(request: Request):
    logger.info(f"Request from {request.client.host}")
    return {"message": "Welcome to OtkroiMosprom API"}
