# Setup logger
import logging
import re
import uuid
from logging.config import dictConfig
from pathlib import Path

from typing import Any, Dict, List, Optional

import aiofiles
from fastapi import (APIRouter, Depends, File, HTTPException, Query,
                     UploadFile)

from api.auth import get_current_user
from csv_reader.reader import AsyncCSVReader
from database.database import db
from logging_config import LOGGING_CONFIG, ColoredFormatter
from models import Company, UserCompanyLink, User, UserCreate
from settings import settings


dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if type(handler) is logging.StreamHandler:
        handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))


router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(get_current_user)]
    )

UPLOAD_DIR = Path(settings.upload_dir)
OPTIMIZED_DIR = Path(settings.optimized_dir)

MAX_FILE_SIZE_BYTES = settings.max_file_size_bytes
CSV_CONTENT_TYPES = settings.csv_content_types  # browsers often use the latter

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def _resolve_csv_path(file_key: str, path: Optional[Path] = UPLOAD_DIR) -> Path:
    """
    Безопасно резолвит путь к CSV на основе file_key из сессии.
    Поддерживает как абсолютный путь, так и просто имя файла.
    """
    logger.debug(f"Resolving CSV path for file_key: {file_key}")

    # Если в Redis лежит абсолютный путь – используем его.
    candidate = Path(file_key)
    if not candidate.is_absolute():
        logger.debug(f"File_key is not absolute: {file_key}")
        candidate = (path / file_key).resolve()

    # Блокируем выход из UPLOAD_DIR, если путь не абсолютный в file_key
    try:
        candidate.relative_to(path)
    except ValueError:
        error_log = (
            f"\nCandidate: {candidate}"
            f"\nUpload dir: {path}"
            f"\nParents: {list(candidate.parents)}"
            f"\nIs absolute: {candidate.is_absolute()}"
        )
        logger.error(f"Attempt to access file outside of upload directory: {error_log}")
        raise HTTPException(status_code=400, detail="Invalid CSV path")

    if not candidate.exists():
        logger.error(f"CSV not found: {candidate}")
        raise HTTPException(status_code=404, detail="CSV not found")

    if candidate.suffix.lower() != ".csv":
        logger.error(f"Not a CSV file: {candidate.name}")
        raise HTTPException(status_code=400, detail="Only .csv files are allowed")

    return candidate


def _make_outfile(stem: str) -> Path:
    """Create a unique output file path under OPTIMIZED_DIR."""
    # Example: stem='sess_xxx__overbooking' -> 'sess_xxx__overbooking__1738139123.csv'
    from time import time

    outfile = OPTIMIZED_DIR / f"{stem}__{int(time())}.csv"
    # Defensive: ensure parent exists
    outfile.parent.mkdir(parents=True, exist_ok=True)
    return outfile

def _sanitize_filename(name: str) -> str:
    """
    Keep only safe chars and collapse spaces. Keep extension if present.
    """

    logger.debug(f"Sanitizing filename: {name}")
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    # disallow hidden files or empty names
    if not name or name.startswith("."):
        name = f"file.csv"
    # force .csv extension
    if not name.lower().endswith(".csv"):
        name += ".csv"

    logger.debug(f"Sanitized filename: {name}")
    return name


@router.post("/upload")
async def upload_csv_file(
    file: UploadFile = File(..., description="CSV file to upload"),
    as_name: Optional[str] = Query(default=None, description="Name to save the file as"),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"Uploading file: {file.filename}, user: {current_user.username}")

    # 1) Validate file
    if file.content_type not in CSV_CONTENT_TYPES and not file.filename.lower().endswith(".csv"):
        logger.warning(f"Unsupported file type: {file.content_type}")
        raise HTTPException(status_code=415, detail="Only CSV files are allowed")

    original_name = file.filename or "upload.csv"
    safe_original = _sanitize_filename(original_name)
    target_display_name = _sanitize_filename(as_name) if as_name else safe_original

    # 2) Unique stored name + path
    stored_name = f"{uuid.uuid4().hex}_{target_display_name}"
    stored_path = UPLOAD_DIR / stored_name

    # 3) Stream upload with size cap
    total = 0
    try:
        async with aiofiles.open(stored_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    logger.debug("File upload complete")
                    break
                total += len(chunk)
                if total > MAX_FILE_SIZE_BYTES:
                    logger.warning("File too large")
                    raise HTTPException(status_code=413, detail="File too large (limit 50 MB)")
                await out.write(chunk)
    except HTTPException:
        if stored_path.exists():
            try:
                stored_path.unlink()
            except Exception:
                logger.error("Failed to delete oversized file", exc_info=True)
                pass
        raise
    finally:
        logger.debug("Closing uploaded file")
        await file.close()

    # 4) Process CSV with AsyncCSVReader
    logger.debug(f"Processing CSV with AsyncCSVReader: {stored_path}")
    try:
        reader = AsyncCSVReader(str(stored_path))
        companies_data, key_fields = await reader.read_companies_with_key_fields()

        logger.info(f"Read {len(companies_data)} companies from CSV")

        # 5) Save to database
        session = db.getSession()
        try:
            saved_companies = []

            for i, (company_data, key_field) in enumerate(zip(companies_data, key_fields)):
                # Create Company record with key fields
                company = Company(
                    inn=int(key_field["inn"]) if key_field["inn"] else 0,
                    name=key_field["name"] or "",
                    full_name=key_field["full_name"] or "",
                    spark_status=key_field["spark_status"] or "",
                    main_industry=key_field["main_industry"] or "",
                    company_size_final=key_field["company_size_final"] or "",
                    organization_type=key_field["organization_type"],
                    support_measures=key_field["support_measures"] == "Получены",
                    special_status=key_field["special_status"],
                    json_data=company_data  # Store full data as JSONB
                )

                session.add(company)
                session.flush()  # Get the ID

                # Create UserBase relationship
                user_base = UserCompanyLink(
                    user_id=current_user.id,
                    company_id=company.id
                )
                session.add(user_base)

                saved_companies.append({
                    "id": company.id,
                    "name": company.name,
                    "inn": company.inn
                })

            session.commit()
            logger.info(f"Saved {len(saved_companies)} companies to database")

        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error processing CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CSV processing error: {e}")

    logger.info(f"File uploaded and processed successfully: {stored_name} ({total} bytes)")

    return {
        "file_name": safe_original,
        "stored_name": stored_name,
        "size_bytes": total,
        "companies_processed": len(saved_companies),
        "companies_saved": saved_companies[:5],  # Show first 5 companies
    }
