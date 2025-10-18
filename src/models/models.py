import datetime
from enum import Enum
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Column, Field, Relationship, SQLModel

from settings import settings

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        nullable=False,
        index=True,
        sa_column_kwargs={"autoincrement": True}
    )
    username: str = Field(description="Имя пользователя")
    salt = Field(description="Соль для пароля")
    password_hash: str = Field(description="Хеш пароля")
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class Token(SQLModel, table=True):
    __tablename__ = "tokens"
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        nullable=False,
        index=True,
        sa_column_kwargs={"autoincrement": True}
    )
    access_token: str = Field(description="Токен доступа")
    token_type: str = Field(description="Тип токена", default="bearer")
    user_id: int = Field(foreign_key="users.id")

    user: User = Relationship(back_populates="token")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at: datetime.datetime = Field(
        default_factory=lambda:
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.access_token_expire_minutes)
    )


class CompanyCreate(SQLModel):
    name: str = Field(description="Название компании")
    inn: int = Field(description="ИНН компании")
    confirmed_by: Optional[str] = Field(description="Кто подтвердил компанию")
    confirmed_at: Optional[datetime.datetime] = Field(description="Когда подтвердили компанию")
    confirmer_identifier: Optional[str] = Field(description="Идентификатор (логин или имя системы)")
    json_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False)
    )


class CompanyRead(SQLModel):
    id: int
    name: str
    inn: int
    confirmed_by: Optional[str] = Field(description="Кто подтвердил компанию")
    confirmed_at: Optional[datetime.datetime] = Field(description="Когда подтвердили компанию")
    confirmer_identifier: Optional[str] = Field(description="Идентификатор (логин или имя системы)")
    json_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False)
    )


class CompanyUpdate(SQLModel):
    name: Optional[str] = Field(description="Название компании")
    inn: Optional[int] = Field(description="ИНН компании")
    confirmed_by: Optional[str] = Field(description="Кто подтвердил компанию")
    confirmed_at: Optional[datetime.datetime] = Field(description="Когда подтвердили компанию")
    confirmer_identifier: Optional[str] = Field(description="Идентификатор (логин или имя системы)")
    json_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))


class ConfirmationStatus(str, Enum):
    confirmed = "Подтверждён"
    user_confirmed = "Подтверждён пользователем"
    not_confirmed = "Не подтверждён"


class Company(SQLModel, table=True):
    __tablename__ = "companies"
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        nullable=False,
        index=True,
        sa_column_kwargs={"autoincrement": True}
    )
    inn: int = Field(description="ИНН компании")
    name: str = Field(description="Название компании")
    full_name: str = Field(description="Полное наименование компании")
    spark_status: str = Field(description="Статус СПАРК")
    main_industry: str = Field(description="Основная отрасль")
    company_size_final: str = Field(description="Размер предприятия (итог)")
    organization_type: Optional[str] = None
    support_measures: Optional[bool] = None
    special_status: Optional[str] = None

    confirmation_status: ConfirmationStatus = Field(default=ConfirmationStatus.not_confirmed)
    confirmed_at: Optional[datetime.datetime] = Field(description="Когда подтвердили компанию")
    confirmer_identifier: Optional[str] = Field(description="Идентификатор (логин или имя системы)")

    json_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False)
    )


class UserBase(SQLModel, table=True):
    __tablename__ = "user_base"
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    company_id: int = Field(foreign_key="companies.id", primary_key=True)

    user: User = Relationship(back_populates="user_base")
    company: Company = Relationship(back_populates="user_base")
