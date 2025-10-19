# /src/api/auth.py

import logging
import secrets
from datetime import datetime, timedelta, timezone
from logging.config import dictConfig
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlmodel import Session

from repositories.user_repository import UserRepository
from models import User, Token
from database.database import db
from logging_config import LOGGING_CONFIG, ColoredFormatter
from settings import settings

# Setup logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if type(handler) is logging.StreamHandler:
        handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))

# =========================
# Конфигурация
# =========================

SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Argon2 параметры
ph = PasswordHasher(
    time_cost=settings.argon2_time_cost,
    memory_cost=settings.argon2_memory_cost,
    parallelism=settings.argon2_parallelism
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])

# =========================
# Модели
# =========================

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=6, description="Пароль")

class UserLogin(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")

class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime
    updated_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# =========================
# Утилиты
# =========================

def generate_salt() -> str:
    """Генерирует случайную соль"""
    return secrets.token_hex(32)

def hash_password(password: str, salt: str) -> str:
    """Хеширует пароль с солью"""
    return ph.hash(password + salt)

def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Проверяет пароль"""
    logger.debug("Verifying password")
    try:
        return ph.verify(hashed_password, plain_password + salt)
    except VerifyMismatchError:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_session() -> Session:
    """Получает сессию базы данных"""
    return db.getSession()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Получает текущего пользователя по токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    session = get_session()
    try:
        user_repo = UserRepository(session)
        user = user_repo.get_by_username(username)
        if user is None:
            raise credentials_exception
        return user
    finally:
        session.close()

# =========================
# Эндпоинты
# =========================

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Регистрация нового пользователя"""
    logger.info(f"Registering new user: {user_data.username}")

    session = get_session()
    try:
        user_repo = UserRepository(session)

        # Проверяем, что пользователь не существует
        existing_user = user_repo.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Генерируем соль и хешируем пароль
        salt = generate_salt()
        password_hash = hash_password(user_data.password, salt)

        # Создаем пользователя
        user = user_repo.create(
            username=user_data.username,
            password_hash=password_hash,
            salt=salt
        )

        logger.info(f"User {user.username} registered successfully")
        return UserRead(
            id=user.id,
            username=user.username,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    finally:
        session.close()

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Вход в систему"""
    logger.info(f"Login attempt for user: {form_data.username}")

    session = get_session()
    try:
        user_repo = UserRepository(session)
        user = user_repo.get_by_username(form_data.username)

        if not user or not verify_password(form_data.password, user.password_hash, user.salt):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Создаем токен
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # Сохраняем токен в базу
        token = Token(
            access_token=access_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + access_token_expires
        )
        session.add(token)
        session.commit()

        logger.info(f"User {user.username} logged in successfully")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
    finally:
        session.close()

@router.post("/login-json", response_model=TokenResponse)
async def login_json(user_data: UserLogin):
    """Вход в систему через JSON"""
    logger.info(f"Login attempt for user: {user_data.username}")

    session = get_session()
    try:
        user_repo = UserRepository(session)
        user = user_repo.get_by_username(user_data.username)

        if not user or not verify_password(user_data.password, user.password_hash, user.salt):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Создаем токен
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # Сохраняем токен в базу
        token = Token(
            access_token=access_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + access_token_expires
        )
        session.add(token)
        session.commit()

        logger.info(f"User {user.username} logged in successfully")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
    finally:
        session.close()

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    logger.info(f"Getting user info for: {current_user.username}")

    return UserRead(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


