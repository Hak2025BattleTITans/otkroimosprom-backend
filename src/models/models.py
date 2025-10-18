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
    organization_type: Optional[str] = None
    main_industry: Optional[str] = None
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


class ConsolidatedDataBase(SQLModel):
    inn: str = Field(index=True)
    name: str
    organization_type: Optional[str] = None
    main_industry: Optional[str] = None
    sub_industry: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None
    coordinates: Optional[str] = None
    year: int = Field(index=True)
    revenue_thous_rub: Optional[float] = None
    net_profit_thous_rub: Optional[float] = None
    taxes_to_moscow_thous_rub: Optional[float] = None
    profit_tax_thous_rub: Optional[float] = None
    property_tax_thous_rub: Optional[float] = None
    land_tax_thous_rub: Optional[float] = None
    personal_income_tax_thous_rub: Optional[float] = None
    transport_tax_thous_rub: Optional[float] = None
    other_taxes_thous_rub: Optional[float] = None
    excise_taxes_thous_rub: Optional[float] = None
    investments_in_moscow_thous_rub: Optional[float] = None
    avg_personnel_moscow: Optional[int] = None
    payroll_moscow_thous_rub: Optional[float] = None
    avg_salary_moscow_thous_rub: Optional[float] = None
    export_volume_thous_rub: Optional[float] = None
    prev_year_export_volume_mln_rub: Optional[float] = None
    capacity_utilization_percent: Optional[int] = None
    has_exports: Optional[bool] = None
    support_measures: Optional[str] = None
    special_status: Optional[str] = None
    is_confirmed: bool = Field(default=False)
    last_modified_date: Optional[datetime.date] = None

class ConsolidatedData(ConsolidatedDataBase, table=True):
    __tablename__ = "consolidated_data"
    id: Optional[int] = Field(default=None, primary_key=True)
    confirmer_type: Optional[str] = Field(default=None, description="Тип подтвердившего (USER, SYSTEM)")
    confirmer_identifier: Optional[str] = Field(default=None, description="Идентификатор (логин или имя системы)")

class ConsolidatedDataRead(ConsolidatedDataBase):
    id: int
    confirmer_type: Optional[str] = None
    confirmer_identifier: Optional[str] = None

class ConsolidatedDataUpdate(SQLModel):
    name: str | None = None
    organization_type: str | None = None
    main_industry: str | None = None
    sub_industry: str | None = None
    district: str | None = None
    region: str | None = None
    coordinates: str | None = None
    revenue_thous_rub: float | None = None
    net_profit_thous_rub: float | None = None
    taxes_to_moscow_thous_rub: float | None = None
    profit_tax_thous_rub: float | None = None
    property_tax_thous_rub: float | None = None
    land_tax_thous_rub: float | None = None
    personal_income_tax_thous_rub: float | None = None
    transport_tax_thous_rub: float | None = None
    other_taxes_thous_rub: float | None = None
    excise_taxes_thous_rub: float | None = None
    investments_in_moscow_thous_rub: float | None = None
    avg_personnel_moscow: int | None = None
    payroll_moscow_thous_rub: float | None = None
    avg_salary_moscow_thous_rub: float | None = None
    export_volume_thous_rub: float | None = None
    prev_year_export_volume_mln_rub: float | None = None
    capacity_utilization_percent: int | None = None
    has_exports: bool | None = None
    support_measures: str | None = None
    special_status: str | None = None
