import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

# МОДЕЛИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
class UserBase(SQLModel):
    full_name: str = Field(description="Полное имя пользователя")
    position: Optional[str] = Field(default=None, description="Должность")
    company: Optional[str] = Field(default=None, description="Компания, в которой работает пользователь")

class User(UserBase, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    auth_data: Optional["AuthData"] = Relationship(back_populates="user")

class UserRead(UserBase):
    id: int
    created_at: datetime.datetime

class UserUpdate(SQLModel):
    full_name: str | None = None
    position: str | None = None
    company: str | None = None

# МОДЕЛИ ДЛЯ АУТЕНТИФИКАЦИИ
class AuthData(SQLModel, table=True):
    __tablename__ = "auth_data"
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    login: str = Field(unique=True, index=True)
    password_hash: str
    user: User = Relationship(back_populates="auth_data")

# МОДЕЛИ ДЛЯ ДАННЫХ КОМПАНИЙ
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

# МОДЕЛЬ ДЛЯ ТОКЕНА
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"