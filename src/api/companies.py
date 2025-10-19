# /src/api/companies.py

import logging
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from api.auth import get_current_user
from database.database import db
from logging_config import LOGGING_CONFIG, ColoredFormatter
from models import Company, User, UserCompanyLink

# Setup logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if type(handler) is logging.StreamHandler:
        handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))

router = APIRouter(prefix="/companies", tags=["companies"])

# =========================
# Модели
# =========================

class CompanyUpdateRequest(BaseModel):
    """Модель для обновления основных полей компании"""
    name: Optional[str] = Field(None, description="Название компании")
    full_name: Optional[str] = Field(None, description="Полное наименование компании")
    spark_status: Optional[str] = Field(None, description="Статус СПАРК")
    main_industry: Optional[str] = Field(None, description="Основная отрасль")
    company_size_final: Optional[str] = Field(None, description="Размер предприятия (итог)")
    organization_type: Optional[str] = Field(None, description="Тип организации")
    support_measures: Optional[bool] = Field(None, description="Меры поддержки")
    special_status: Optional[str] = Field(None, description="Особый статус")

class CompanyKeyMetricsUpdate(BaseModel):
    """Модель для обновления ключевых метрик"""
    main_industry: Optional[str] = Field(None, description="Основная отрасль")
    company_size_final: Optional[str] = Field(None, description="Размер предприятия (итог)")
    organization_type: Optional[str] = Field(None, description="Тип организации")
    support_measures: Optional[bool] = Field(None, description="Меры поддержки")
    special_status: Optional[str] = Field(None, description="Особый статус")

class CompanyJsonDataUpdate(BaseModel):
    """Модель для обновления JSON данных"""
    json_data: Dict[str, Any] = Field(..., description="Полные JSON данные компании")

class CompanyResponse(BaseModel):
    """Модель ответа с информацией о компании"""
    id: int
    inn: int
    name: str
    full_name: str
    spark_status: str
    main_industry: str
    company_size_final: str
    organization_type: Optional[str] = None
    support_measures: Optional[bool] = None
    special_status: Optional[str] = None
    confirmation_status: str
    confirmed_at: Optional[datetime] = None
    confirmer_identifier: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CompanyListResponse(BaseModel):
    """Модель ответа со списком компаний"""
    companies: List[CompanyResponse]
    total: int
    limit: int
    offset: int

# =========================
# Утилиты
# =========================

def get_session() -> Session:
    """Получает сессию базы данных"""
    return db.getSession()

def check_company_ownership(company_id: int, user_id: int, session: Session) -> Company:
    """Проверяет, что компания принадлежит пользователю"""
    statement = (
        select(Company)
        .join(UserCompanyLink)
        .where(
            Company.id == company_id,
            UserCompanyLink.user_id == user_id
        )
    )

    company = session.exec(statement).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found or access denied"
        )
    return company

# =========================
# Эндпоинты
# =========================

@router.get("/", response_model=CompanyListResponse)
async def get_user_companies(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, description="Количество записей"),
    offset: int = Query(default=0, description="Смещение"),
):
    """Получить список компаний пользователя"""
    logger.info(f"Getting companies for user: {current_user.username}")

    session = get_session()
    try:
        statement = (
            select(Company)
            .join(UserCompanyLink)
            .where(UserCompanyLink.user_id == current_user.id)
            .limit(limit)
            .offset(offset)
        )

        companies = session.exec(statement).all()

        company_responses = [
            CompanyResponse(
                id=company.id,
                inn=company.inn,
                name=company.name,
                full_name=company.full_name,
                spark_status=company.spark_status,
                main_industry=company.main_industry,
                company_size_final=company.company_size_final,
                organization_type=company.organization_type,
                support_measures=company.support_measures,
                special_status=company.special_status,
                confirmation_status=company.confirmation_status.value,
                confirmed_at=company.confirmed_at,
                confirmer_identifier=company.confirmer_identifier,
                created_at=company.created_at,
                updated_at=company.updated_at
            )
            for company in companies
        ]

        return CompanyListResponse(
            companies=company_responses,
            total=len(company_responses),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error getting companies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get companies"
        )
    finally:
        session.close()

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
):
    """Получить детальную информацию о компании"""
    logger.info(f"Getting company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        return CompanyResponse(
            id=company.id,
            inn=company.inn,
            name=company.name,
            full_name=company.full_name,
            spark_status=company.spark_status,
            main_industry=company.main_industry,
            company_size_final=company.company_size_final,
            organization_type=company.organization_type,
            support_measures=company.support_measures,
            special_status=company.special_status,
            confirmation_status=company.confirmation_status.value,
            confirmed_at=company.confirmed_at,
            confirmer_identifier=company.confirmer_identifier,
            created_at=company.created_at,
            updated_at=company.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get company"
        )
    finally:
        session.close()

@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    update_data: CompanyUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """Обновить основные данные компании"""
    logger.info(f"Updating company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Обновляем только переданные поля
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(company, key) and value is not None:
                setattr(company, key, value)

        # Обновляем время изменения
        company.updated_at = datetime.now(timezone.utc)

        session.add(company)
        session.commit()
        session.refresh(company)

        logger.info(f"Company {company_id} updated successfully")

        return CompanyResponse(
            id=company.id,
            inn=company.inn,
            name=company.name,
            full_name=company.full_name,
            spark_status=company.spark_status,
            main_industry=company.main_industry,
            company_size_final=company.company_size_final,
            organization_type=company.organization_type,
            support_measures=company.support_measures,
            special_status=company.special_status,
            confirmation_status=company.confirmation_status.value,
            confirmed_at=company.confirmed_at,
            confirmer_identifier=company.confirmer_identifier,
            created_at=company.created_at,
            updated_at=company.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )
    finally:
        session.close()

@router.patch("/{company_id}/key-metrics", response_model=CompanyResponse)
async def update_company_key_metrics(
    company_id: int,
    metrics_data: CompanyKeyMetricsUpdate,
    current_user: User = Depends(get_current_user),
):
    """Обновить ключевые метрики компании"""
    logger.info(f"Updating key metrics for company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Обновляем только переданные метрики
        update_dict = metrics_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(company, key) and value is not None:
                setattr(company, key, value)

        # Обновляем время изменения
        company.updated_at = datetime.now(timezone.utc)

        session.add(company)
        session.commit()
        session.refresh(company)

        logger.info(f"Key metrics for company {company_id} updated successfully")

        return CompanyResponse(
            id=company.id,
            inn=company.inn,
            name=company.name,
            full_name=company.full_name,
            spark_status=company.spark_status,
            main_industry=company.main_industry,
            company_size_final=company.company_size_final,
            organization_type=company.organization_type,
            support_measures=company.support_measures,
            special_status=company.special_status,
            confirmation_status=company.confirmation_status.value,
            confirmed_at=company.confirmed_at,
            confirmer_identifier=company.confirmer_identifier,
            created_at=company.created_at,
            updated_at=company.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating key metrics: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update key metrics"
        )
    finally:
        session.close()

@router.patch("/{company_id}/json-data", response_model=Dict[str, Any])
async def update_company_json_data(
    company_id: int,
    json_data: CompanyJsonDataUpdate,
    current_user: User = Depends(get_current_user),
):
    """Обновить JSON данные компании"""
    logger.info(f"Updating JSON data for company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Обновляем JSON данные
        company.json_data = json_data.json_data
        company.updated_at = datetime.now(timezone.utc)

        session.add(company)
        session.commit()
        session.refresh(company)

        logger.info(f"JSON data for company {company_id} updated successfully")

        return {
            "company_id": company.id,
            "json_data": company.json_data,
            "updated_at": company.updated_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating JSON data: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update JSON data"
        )
    finally:
        session.close()

@router.get("/{company_id}/json-data", response_model=Dict[str, Any])
async def get_company_json_data(
    company_id: int,
    current_user: User = Depends(get_current_user),
):
    """Получить JSON данные компании"""
    logger.info(f"Getting JSON data for company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        return {
            "company_id": company.id,
            "json_data": company.json_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting JSON data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get JSON data"
        )
    finally:
        session.close()

@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
):
    """Удалить компанию"""
    logger.info(f"Deleting company {company_id} for user: {current_user.username}")

    session = get_session()
    try:
        company = check_company_ownership(company_id, current_user.id, session)

        # Удаляем связь пользователя с компанией
        user_company_link_statement = select(UserCompanyLink).where(
            UserCompanyLink.user_id == current_user.id,
            UserCompanyLink.company_id == company_id
        )
        user_company_link = session.exec(user_company_link_statement).first()
        if user_company_link:
            session.delete(user_company_link)

        # Удаляем компанию
        session.delete(company)
        session.commit()

        logger.info(f"Company {company_id} deleted successfully")

        return {"message": "Company deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {e}", exc_info=True)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company"
        )
    finally:
        session.close()
