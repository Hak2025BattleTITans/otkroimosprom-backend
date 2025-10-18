import csv
import json
import logging
from logging.config import dictConfig
from pathlib import Path
from typing import List, Dict, Any, Optional

import aiofiles

try:
    from logging_config import LOGGING_CONFIG, ColoredFormatter

    dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if type(handler) is logging.StreamHandler:
            handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))
except ImportError:
    logger = logging.getLogger(__name__)

class AsyncCSVReader:
    def __init__(self, path: str, delimiter: str = ","):
        logger.debug(f"Initialized AsyncCSVReader with path: {path} and delimiter: '{delimiter}'")
        self.path = path
        self.delimiter = delimiter

    def _clean_value(self, value: str) -> Any:
        """Очищает и конвертирует значения из CSV"""
        if not value or value.strip() == "":
            return None

        # Заменяем запятые на точки для числовых значений
        cleaned = value.replace(",", ".").strip()

        # Пытаемся конвертировать в число
        try:
            if "." in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
        except ValueError:
            return cleaned

    def _extract_key_fields(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает ключевые поля для базы данных"""
        return {
            "inn": row.get("ИНН"),
            "name": row.get("Наименование организации"),
            "full_name": row.get("Полное наименование организации"),
            "spark_status": row.get("Статус СПАРК"),
            "main_industry": row.get("Основная отрасль"),
            "company_size_final": row.get("Размер предприятия (итог)"),
            "organization_type": row.get("Тип организации"),
            "support_measures": row.get("Данные о мерах поддержки"),
            "special_status": row.get("Наличие особого статуса"),
        }

    async def read_companies(self) -> List[Dict[str, Any]]:
        """
        Читает CSV файл с данными предприятий и возвращает список словарей с JSON данными
        """
        companies = []

        async with aiofiles.open(self.path, mode="r", encoding="utf-8") as f:
            logger.debug(f"Reading CSV file from path: {self.path}")
            content = await f.read()

        reader = csv.DictReader(content.splitlines(), delimiter=self.delimiter)

        for row_num, row in enumerate(reader, start=1):
            # Очищаем значения
            cleaned_row = {k: self._clean_value(v) for k, v in row.items()}

            # Добавляем номер записи
            cleaned_row["number"] = row_num

            companies.append(cleaned_row)

        logger.debug(f"Read {len(companies)} companies from CSV file")
        return companies

    async def read_companies_with_key_fields(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Читает CSV файл и возвращает:
        1. Полные JSON данные всех компаний
        2. Только ключевые поля для базы данных
        """
        companies = await self.read_companies()

        # Извлекаем ключевые поля для базы данных
        key_fields = [self._extract_key_fields(company) for company in companies]

        logger.debug(f"Extracted {len(key_fields)} key fields for database")
        return companies, key_fields

    async def write_companies(self, companies: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Записывает данные компаний в CSV файл
        """
        if output_path is None:
            original_path = Path(self.path)
            output_path = str(original_path.with_name(original_path.stem + "_processed.csv"))

        if not companies:
            logger.warning("No companies to write")
            return output_path

        # Получаем все возможные поля из первой записи
        fieldnames = list(companies[0].keys())

        async with aiofiles.open(output_path, mode="w", encoding="utf-8", newline="") as f:
            # Записываем заголовки
            await f.write(self.delimiter.join(fieldnames) + "\n")

            # Записываем данные
            for company in companies:
                row_values = []
                for field in fieldnames:
                    value = company.get(field, "")
                    # Конвертируем в строку и экранируем если нужно
                    if value is None:
                        row_values.append("")
                    else:
                        row_values.append(str(value))

                await f.write(self.delimiter.join(row_values) + "\n")

        logger.debug(f"Wrote {len(companies)} companies to CSV file: {output_path}")
        return output_path

    async def get_company_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Находит компанию по ИНН
        """
        companies = await self.read_companies()

        for company in companies:
            if company.get("ИНН") == inn:
                return company

        return None

    async def get_companies_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """
        Находит компании по отрасли
        """
        companies = await self.read_companies()

        return [company for company in companies
                if company.get("Основная отрасль") == industry]

    async def get_companies_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Находит компании по статусу
        """
        companies = await self.read_companies()

        return [company for company in companies
                if company.get("Статус ИТОГ") == status]


if __name__ == "__main__":
    import asyncio

    async def main():
        # Пример использования AsyncCSVReader
        reader = AsyncCSVReader("raw_schedule.csv")

        print("=== Пример 1: Чтение всех компаний ===")
        companies = await reader.read_companies()
        print(f"Загружено {len(companies)} компаний")

        if companies:
            print(f"Первая компания: {companies[0]['Наименование организации']}")
            print(f"ИНН первой компании: {companies[0]['ИНН']}")

        print("\n=== Пример 2: Чтение с ключевыми полями ===")
        all_data, key_fields = await reader.read_companies_with_key_fields()
        print(f"Полных записей: {len(all_data)}")
        print(f"Ключевых полей: {len(key_fields)}")

        if key_fields:
            print(f"Пример ключевых полей: {key_fields[0]}")

        print("\n=== Пример 3: Поиск компании по ИНН ===")
        if companies:
            first_inn = companies[0]['ИНН']
            company = await reader.get_company_by_inn(first_inn)
            if company:
                print(f"Найдена компания: {company['Наименование организации']}")

        print("\n=== Пример 4: Фильтрация по отрасли ===")
        it_companies = await reader.get_companies_by_industry("IT")
        print(f"IT компаний: {len(it_companies)}")

        print("\n=== Пример 5: Фильтрация по статусу ===")
        active_companies = await reader.get_companies_by_status("Включено")
        print(f"Активных компаний: {len(active_companies)}")

        print("\n=== Пример 6: Анализ ключевых метрик ===")
        # Анализируем новые ключевые поля
        industries = {}
        company_sizes = {}
        support_measures = {}
        special_statuses = {}

        for company in companies:
            industry = company.get("Основная отрасль", "Не указана")
            company_size = company.get("Размер предприятия (итог)", "Не указан")
            support = company.get("Данные о мерах поддержки", "Не указано")
            special_status = company.get("Наличие особого статуса", "Не указан")

            industries[industry] = industries.get(industry, 0) + 1
            company_sizes[company_size] = company_sizes.get(company_size, 0) + 1
            support_measures[support] = support_measures.get(support, 0) + 1
            special_statuses[special_status] = special_statuses.get(special_status, 0) + 1

        print("Распределение по отраслям:")
        for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True):
            print(f"  {industry}: {count}")

        print("\nРаспределение по размерам предприятий:")
        for size, count in sorted(company_sizes.items(), key=lambda x: x[1], reverse=True):
            print(f"  {size}: {count}")

        print("\nРаспределение по мерам поддержки:")
        for support, count in sorted(support_measures.items(), key=lambda x: x[1], reverse=True):
            print(f"  {support}: {count}")

        print("\nРаспределение по особым статусам:")
        for status, count in sorted(special_statuses.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")

        print("\n=== Пример 7: Анализ компаний с поддержкой ===")
        companies_with_support = [c for c in companies if c.get("Данные о мерах поддержки") == "Получены"]
        print(f"Компаний с мерами поддержки: {len(companies_with_support)}")

        if companies_with_support:
            print("Примеры компаний с поддержкой:")
            for i, company in enumerate(companies_with_support[:3], 1):
                print(f"  {i}. {company.get('Наименование организации')} (ИНН: {company.get('ИНН')})")

        print("\n=== Пример 8: Анализ особых статусов ===")
        companies_with_special_status = [c for c in companies if c.get("Наличие особого статуса") == "Есть"]
        print(f"Компаний с особым статусом: {len(companies_with_special_status)}")

        if companies_with_special_status:
            print("Компании с особым статусом:")
            for i, company in enumerate(companies_with_special_status[:3], 1):
                print(f"  {i}. {company.get('Наименование организации')} (ИНН: {company.get('ИНН')})")

        print("\n=== Пример 9: Сохранение обработанных данных ===")
        # Фильтруем компании с поддержкой
        companies_with_support = [c for c in companies if c.get("Данные о мерах поддержки") == "Получены"]

        if companies_with_support:
            output_path = await reader.write_companies(companies_with_support)
            print(f"Сохранено {len(companies_with_support)} компаний с поддержкой в файл: {output_path}")

        print("\n=== Пример 10: Анализ по типам организаций ===")
        # Анализируем типы организаций
        org_types = {}
        for company in companies:
            org_type = company.get("Тип организации", "Не указан")
            org_types[org_type] = org_types.get(org_type, 0) + 1

        print("Распределение по типам организаций:")
        for org_type, count in sorted(org_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {org_type}: {count}")

        print("\n=== Пример 11: Комплексный анализ ключевых метрик ===")
        # Анализируем комбинации ключевых полей
        key_metrics_analysis = {
            "total_companies": len(companies),
            "companies_with_support": len([c for c in companies if c.get("Данные о мерах поддержки") == "Получены"]),
            "companies_with_special_status": len([c for c in companies if c.get("Наличие особого статуса") == "Есть"]),
            "large_companies": len([c for c in companies if c.get("Размер предприятия (итог)") == "Крупное"]),
            "medium_companies": len([c for c in companies if c.get("Размер предприятия (итог)") == "Среднее"]),
            "small_companies": len([c for c in companies if c.get("Размер предприятия (итог)") == "Малое"]),
        }

        print("Ключевые метрики:")
        for metric, value in key_metrics_analysis.items():
            print(f"  {metric}: {value}")

        # Процентное соотношение
        if key_metrics_analysis["total_companies"] > 0:
            support_percentage = (key_metrics_analysis["companies_with_support"] / key_metrics_analysis["total_companies"]) * 100
            special_percentage = (key_metrics_analysis["companies_with_special_status"] / key_metrics_analysis["total_companies"]) * 100

            print(f"\nПроцентное соотношение:")
            print(f"  Компаний с поддержкой: {support_percentage:.1f}%")
            print(f"  Компаний с особым статусом: {special_percentage:.1f}%")

    # Запуск примеров
    asyncio.run(main())
