import logging
from typing import Optional, Dict, Any

from sqlmodel import Session, select

from models import User

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по имени пользователя"""
        logger.info(f"Getting user by username {username}")
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        logger.info(f"Getting user by id {user_id}")
        statement = select(User).where(User.id == user_id)
        return self.session.exec(statement).first()

    def create(self, username: str, password_hash: str, salt: str) -> User:
        """Создать нового пользователя"""
        logger.info(f"Creating user {username}")

        user = User(
            username=username,
            password_hash=password_hash,
            salt=salt
        )

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user: User, **kwargs) -> User:
        """Частично обновляет данные пользователя"""
        logger.info(f"Updating user id {user.id}")

        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_password(self, user: User, new_password_hash: str, new_salt: str) -> User:
        """Обновить пароль пользователя"""
        logger.info(f"Updating password for user id {user.id}")

        user.password_hash = new_password_hash
        user.salt = new_salt

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user: User) -> bool:
        """Удалить пользователя"""
        logger.info(f"Deleting user id {user.id}")

        try:
            self.session.delete(user)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            self.session.rollback()
            return False

    def list_users(self, limit: int = 50, offset: int = 0) -> list[User]:
        """Получить список пользователей с пагинацией"""
        logger.info(f"Listing users with limit {limit}, offset {offset}")

        statement = select(User).limit(limit).offset(offset)
        return self.session.exec(statement).all()