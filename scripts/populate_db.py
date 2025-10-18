import json
import logging
import os
from argon2 import PasswordHasher
from sqlmodel import Session, select
from dotenv import load_dotenv

load_dotenv()

from src.database import engine, init_db
from src.models import User, AuthData, ConsolidatedData
from src.repositories.user_repository import UserRepository
from src.repositories.data_repository import DataRepository

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_initial_user(session: Session):
    repo = UserRepository(session)
    logger.info("Checking for initial admin user...")
    
    admin_login = "admin"
    admin_user = repo.get_by_login(admin_login)
    
    if not admin_user:
        logger.info("Admin user not found, creating one...")
        ph = PasswordHasher()
        
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            raise ValueError("ADMIN_PASSWORD is not set in the .env file. Cannot create admin user.")
        
        new_user = User(full_name="Admin User", position="Administrator", company="System")
        new_auth_data = AuthData(
            login=admin_login,
            password_hash=ph.hash(admin_password)
        )
        repo.create(new_user, new_auth_data)
        logger.info(f"User '{admin_login}' created successfully.")
    else:
        logger.info("Admin user already exists.")

def populate_data_from_json(session: Session, json_file_path: str):
    repo = DataRepository(session)
    logger.info(f"Attempting to populate data from {json_file_path}...")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found at '{json_file_path}'. Skipping population.")
        return
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from '{json_file_path}'. Check file format.")
        return
        
    for item in data_list:
        inn = item.get('inn')
        year = item.get('year')
        if not inn or not year:
            logger.warning(f"Skipping record due to missing 'inn' or 'year': {item}")
            continue

        existing = repo.get_by_inn_and_year(inn, year)
        
        if not existing:
            model_fields = ConsolidatedData.model_fields.keys()
            filtered_item = {k: v for k, v in item.items() if k in model_fields}
            
            new_record = ConsolidatedData(**filtered_item)
            repo.create(new_record)
            logger.info(f"Added record for INN {inn} for year {year}")
        else:
            logger.warning(f"Record for INN {inn} for year {year} already exists. Skipping.")

def main():
    logger.info("--- Starting Database Initialization and Population Script ---")
    
    logger.info("Step 1: Initializing database tables...")
    init_db()
    logger.info("Tables initialized successfully.")
    
    with Session(engine) as session:
        logger.info("Step 2: Creating initial admin user...")
        create_initial_user(session)
        
        logger.info("Step 3: Populating data from JSON file...")
        populate_data_from_json(session, "data.json") 
    
    logger.info("--- Script finished successfully ---")

if __name__ == "__main__":
    main()