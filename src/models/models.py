import datetime
from enum import Enum
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import BigInteger
from sqlmodel import Column, Field, Relationship, SQLModel

from settings import settings

class UserCompanyLink(SQLModel, table=True):
    __tablename__ = "user_company_link"
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    company_id: int = Field(foreign_key="companies.id", primary_key=True)

class UserCreate(SQLModel):
    username: str = Field(description="Имя пользователя")
    salt: str = Field(description="Соль для пароля")
    password_hash: str = Field(description="Хеш пароля")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

class UserUpdate(SQLModel):
    salt: str | None = None
    password_hash: str | None = None
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

class UserRead(SQLModel):
    id: int
    username: str
    salt: str
    password_hash: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

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
    salt: str = Field(description="Соль для пароля")
    password_hash: str = Field(description="Хеш пароля")
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    tokens: List["Token"] = Relationship(back_populates="user")
    companies: List["Company"] = Relationship(
        back_populates="users",
        link_model=UserCompanyLink
    )


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

    user: "User" = Relationship(back_populates="tokens")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at: datetime.datetime = Field(
        default_factory=lambda:
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.access_token_expire_minutes)
    )


class CompanyCreate(SQLModel):
    name: str = Field(description="Название компании")
    inn: int = Field(description="ИНН компании", sa_column=Column(BigInteger))
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
    inn: int = Field(sa_column=Column(BigInteger))
    confirmed_by: Optional[str] = Field(description="Кто подтвердил компанию")
    confirmed_at: Optional[datetime.datetime] = Field(description="Когда подтвердили компанию")
    confirmer_identifier: Optional[str] = Field(description="Идентификатор (логин или имя системы)")
    json_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False)
    )


class CompanyUpdate(SQLModel):
    name: Optional[str] = Field(description="Название компании")
    inn: Optional[int] = Field(description="ИНН компании", sa_column=Column(BigInteger))
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
    inn: int = Field(description="ИНН компании", sa_column=Column(BigInteger))
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
    users: List["User"] = Relationship(
        back_populates="companies",
        link_model=UserCompanyLink
    )
