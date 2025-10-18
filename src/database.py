import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан в .env")

# echo=True выводит все SQL-запросы в консоль
engine = create_engine(DATABASE_URL, echo=True) 

def init_db():
    # Создает все таблицы в базе данных
    SQLModel.metadata.create_all(engine)

def get_session():
    # Зависимость FastAPI для получения сессии БД в эндпоинтах
    with Session(engine) as session:
        yield session