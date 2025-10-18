import logging
from typing import List

from sqlmodel import Session, select

from src.models.models import CompanyCreate, CompanyUpdate, CompanyRead

logger = logging.getLogger(__name__)

class CompanyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: CompanyCreate) -> CompanyCreate:
        self.session.add(data)
        self.session.commit()
        self.session.refresh(data)
        return data

    def get_by_id(self, record_id: int) -> CompanyRead | None:
        return self.session.get(CompanyRead, record_id)

    def list_all(self, skip: int = 0, limit: int = 100) -> List[CompanyRead]:
        statement = select(CompanyRead).offset(skip).limit(limit)
        results = self.session.exec(statement).all()
        return results

    def get_by_inn(self, inn: str) -> CompanyRead | None:
        statement = select(CompanyRead).where(CompanyRead.inn == inn)
        return self.session.exec(statement).first()

    def get_by_inn_and_year(self, inn: str, year: int) -> CompanyRead | None:
        statement = select(CompanyRead).where(CompanyRead.inn == inn, CompanyRead.year == year)
        return self.session.exec(statement).first()

    def get_by_industry(self, industry: str) -> CompanyRead | None:
        statement = select(CompanyRead).where(CompanyRead.industry == industry)
        return self.session.exec(statement).first()

    def update(self, db_obj: CompanyRead, obj_in: CompanyUpdate) -> CompanyRead:
        """Частично обновляет запись в БД."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, record_id: int) -> bool:
        """Удаляет запись по ID и возвращает True в случае успеха."""
        record = self.get_by_id(record_id)
        if not record:
            return False

        self.session.delete(record)
        self.session.commit()
        return True