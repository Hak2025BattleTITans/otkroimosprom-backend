import logging
import os
from logging.config import dictConfig
from pathlib import Path
from emul_data import main_function
# from dotenv import find_dotenv, load_dotenv
import numpy as np
import pandas as pd

#from logging_config import LOGGING_CONFIG, ColoredFormatter

# ===== Paths setup ======
# env_path = find_dotenv(".env", usecwd=True)
# load_dotenv(env_path, override=True, encoding="utf-8-sig")

OPTIMIZED_DIR = Path("optimized") #Path(os.environ.get("OPTIMIZED_DIR", "optimized"))
OPTIMIZED_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = Path("uploads") #Path(os.environ.get("OPTIMIZED_DIR", "optimized"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Доп Csvшки, любые нужные вам
CONFIG_FILE = "/app/src/optimizer/configurators/configs.csv"

# ===== Logging setup ======
# dictConfig(LOGGING_CONFIG)
# logger = logging.getLogger(__name__)

# root_logger = logging.getLogger()
# for handler in root_logger.handlers:
#     if type(handler) is logging.StreamHandler:
#         handler.setFormatter(ColoredFormatter('%(levelname)s:     %(asctime)s %(name)s - %(message)s'))


logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(asctime)s %(name)s - %(message)s'))
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

def check_files_exist(filenames):
    """Проверяет, существуют ли все файлы в списке."""
    for filename in filenames:
        if not os.path.exists(filename):
            logger.error(f"\nОШИБКА: Не найден необходимый файл '{filename}'.")
            logger.error("Пожалуйста, сначала запустите соответствующий сценарий оптимизации.")
            return False
    return True

class Optimizer:
    @staticmethod
    def _ensure_dataframe(data, *, nrows=None):
        """Ensure that incoming data is represented as a pandas DataFrame."""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, (str, os.PathLike)):
            df = pd.read_csv(data, delimiter=',', nrows=nrows)
            if df.shape[1] == 1:
                df = pd.read_csv(data, delimiter=';', nrows=nrows)
        else:
            raise TypeError(f"Unsupported data type: {type(data)!r}")
        df.columns = df.columns.str.strip()
        return df

    def universal_data_preparator(self, raw_data):
        """
        (НОВАЯ ЛОГИКА) Полный цикл подготовки данных путем поиска в эталонном файле.

        Example:
            >>> optimizer = Optimizer()
            >>> raw_df = pd.read_csv('raw_schedule.csv', delimiter=';')
            >>> prepared_df = optimizer.universal_data_preparator(raw_df)
        """
        logger.info("\n--- Проверка и подготовка исходных данных ---")

        try:
            raw_df = self._ensure_dataframe(raw_data)
        except FileNotFoundError:
            logger.error(f"Не удалось прочитать файл'{raw_data}'.")
            return None
        except Exception as exc:
            logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: Ошибка: {exc}"); return None
            raise

        # ===========================
        # Твой код здесь


        # ===========================


        # ===========================
        # Верни потом обработанный DataFrame
        # ===========================

        processed_df = main_function() #принимает путь к файлу csv. Не проверяет, есть ли он в пути. Сам файл - test_data_3.csv


        return processed_df

if __name__ == "__main__":
    optimizer = Optimizer()
    raw_df = pd.read_csv("raw_schedule.csv", delimiter=";")
    prepared_df = optimizer.universal_data_preparator(raw_df)
    print(prepared_df)
