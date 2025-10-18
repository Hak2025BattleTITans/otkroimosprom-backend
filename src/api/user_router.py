import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel
from argon2 import PasswordHasher

from src.database import get_session
from src.models import User, UserRead, AuthData
from src.repositories.user_repository import UserRepository
from src.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])
ph = PasswordHasher()

# --- Pydantic модели для API ---

# Модель для создания пользователя (включает логин и пароль)
class UserCreate(UserRead):
    login: str
    password: str

# Модель для частичного обновления профиля
class UserUpdate(SQLModel):
    full_name: str | None = None
    position: str | None = None
    company: str | None = None


# --- Эндпоинты ---

@router.post("/register", response_model=UserRead, status_code=status.HTTP_21_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_session)):
    """
    Регистрация нового пользователя. Этот эндпоинт доступен всем.
    """
    repo = UserRepository(db)
    # 1. Проверяем, не занят ли логин
    if repo.get_by_login(user_in.login):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login already registered",
        )
    
    # 2. Создаем объекты для БД
    # .model_validate() создает экземпляр User из данных UserCreate, игнорируя лишние поля (login, password)
    user_data = User.model_validate(user_in) 
    auth_data = AuthData(
        login=user_in.login,
        password_hash=ph.hash(user_in.password)
    )

    # 3. Сохраняем в БД через репозиторий
    created_user = repo.create(user_data, auth_data)
    return created_user


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Получение данных о текущем аутентифицированном пользователе.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Частичное обновление данных текущего пользователя.
    Можно передать только те поля, которые нужно изменить.
    """
    repo = UserRepository(db)
    updated_user = repo.update(current_user, user_update)
    return updated_user