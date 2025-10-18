import logging
from typing import Optional

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from src.models import User, AuthData, UserUpdate

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_login(self, login: str) -> Optional[User]:
        logger.info(f"Getting user by login {login}")
        statement = (
            select(User)
            .join(AuthData)
            .where(AuthData.login == login)
            .options(selectinload(User.auth_data))
        )
        return self.session.exec(statement).first()

    def create(self, user_data: User, auth_data: AuthData) -> User:
        logger.info(f"Creating user {user_data.full_name} with login {auth_data.login}")
        user_data.auth_data = auth_data
        
        self.session.add(user_data)
        self.session.commit()
        self.session.refresh(user_data)
        return user_data

    def update(self, user: User, update_data: UserUpdate) -> User:
        """Частично обновляет данные пользователя."""
        logger.info(f"Updating user id {user.id}")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(user, key, value)
            
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user