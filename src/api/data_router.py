import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel

from src.database import get_session
from src.models import ConsolidatedDataRead, ConsolidatedData, User
from src.repositories.data_repository import DataRepository
from src.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data"])


# --- Pydantic модель для частичного обновления ---
# Включает все поля, которые можно изменять
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


# --- Эндпоинты ---

@router.post("/", response_model=ConsolidatedDataRead, status_code=status.HTTP_201_CREATED)
def create_data(data_in: ConsolidatedData, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Добавление новой записи о компании."""
    repo = DataRepository(db)
    existing = repo.get_by_inn_and_year(data_in.inn, data_in.year)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Data for this INN and year already exists",
        )
    return repo.create(data_in)


@router.get("/", response_model=List[ConsolidatedDataRead])
def get_all_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Получение списка записей о компаниях."""
    repo = DataRepository(db)
    return repo.list_all(skip=skip, limit=limit)


@router.get("/{record_id}", response_model=ConsolidatedDataRead)
def get_data_by_id(record_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Получение одной записи по ID."""
    repo = DataRepository(db)
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.patch("/{record_id}", response_model=ConsolidatedDataRead)
def update_data(record_id: int, data_update: ConsolidatedDataUpdate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Частичное обновление записи. 
    Можно передать в теле запроса только те поля, которые нужно изменить.
    """
    repo = DataRepository(db)
    record_to_update = repo.get_by_id(record_id)
    if not record_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    
    updated_record = repo.update(record_to_update, data_update)
    return updated_record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data(record_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Удаление записи о компании."""
    repo = DataRepository(db)
    if not repo.delete(record_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return None # При успехе возвращаем пустой ответ со статусом 204