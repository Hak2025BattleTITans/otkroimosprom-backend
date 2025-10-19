import requests
import pandas as pd
import json
import time
import os

def get_company_data_from_deepseek():
    """
    Получение данных о компаниях через API DeepSeek
    """
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    API_KEY =  "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"

    prompt = """
    Ты - эксперт по российским компаниям и экономической статистике. Сгенерируй реалистичные финансовые и операционные данные в формате CSV для следующих московских компаний за 2022-2024 годы.

    ТРЕБОВАНИЯ К ФОРМАТУ ДАННЫХ:
    - Разделитель: точка с запятой (;)
    - Кодировка: UTF-8
    - Заголовки столбцов должны быть точно как в примере ниже
    - Данные должны быть реалистичными для каждой отрасли


    ТРЕБОВАНИЯ К ДАННЫМ:
    - Для каждой компании данные за 2022, 2023, 2024 годы (всего 36 строк)
    - Средняя зарплата должна быть разной по годам: 65, 75, 82 тыс. руб.
    - Данные об оказанных мерах поддержки: "Да"/"Нет"/"Нет сведений" (случайно распределить)
    - Особые статусы: "Промышленный комплекс" для промышленных компаний, "Технопарк" для IT, "Сведения отсутствуют" для остальных
    - Реалистичные финансовые показатели, соответствующие отраслевым нормам
    - Уровень загрузки мощностей от 70% до 96%
    - Наличие экспорта в зависимости от отрасли
    - Все числовые показатели должны коррелировать между собой

    ФОРМАТ CSV ДОЛЖЕН СООТВЕТСТВОВАТЬ ЭТОМУ ПРИМЕРУ:
    ИНН;Наименование организации;Основная отрасль;Подотрасль (Основная);Данные об оказанных мерах поддержки;Наличие особого статуса;Выручка предприятия, тыс. руб;Чистая прибыль (убыток),тыс. руб.;Среднесписочная численность персонала, работающего в Москве, чел;Фонд оплаты труда сотрудников, работающего в Москве, тыс. руб.;Средняя з.п. сотрудников, работающего в Москве, тыс.руб.;Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб.;Налог на прибыль, тыс.руб.;Налог на имущество, тыс.руб.;Налог на землю, тыс.руб.;НДФЛ, тыс.руб.;Транспортный налог, тыс.руб.;Прочие налоги;Акцизы, тыс. руб.;Инвестиции в Мск тыс. руб.;Объем экспорта, тыс. руб.;Уровень загрузки производственных мощностей;Наличие поставок продукции на экспорт;Объем экспорта (млн руб.) за предыдущий календарный год;Координаты адреса производства;Округ;Район;Год;Подтвержден;Кем подтвержден;Вид организации;Дата последнего изменения

    ВЕРНИ ТОЛЬКО CSV ДАННЫЕ БЕЗ ЛЮБЫХ ДОПОЛНИТЕЛЬНЫХ КОММЕНТАРИЕВ, ОБЪЯСНЕНИЙ ИЛИ ФОРМАТИРОВАНИЯ MARKDOWN. ЗАГОЛОВКи CSV ПРОПУСТИ.
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    try:
        print("Отправка запроса к DeepSeek API...")
        start_time = time.time()
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()

        result = response.json()
        generated_content = result['choices'][0]['message']['content']

        print("Данные успешно получены от DeepSeek!")
        processing_time = time.time() - start_time

        print(f"⏱️  Время обработки: {processing_time:.2f} секунд")
        return generated_content

    except Exception as e:
        print(f"Ошибка при обращении к DeepSeek API: {e}")


def save_to_csv_and_display(csv_data, DATA_FILEPATH='test_data_3.csv'):
    """
    Сохранение данных в CSV файл и вывод в терминал
    """
    # Чтение существующего файла для определения стартового номера
    try:
        with open(DATA_FILEPATH, 'r', encoding='utf-8') as f:
            existing_lines = f.readlines()
        start_number = len(existing_lines)  # Нумерация с количества существующих строк
    except FileNotFoundError:
        start_number = 1

    # Обработка и добавление номеров к новым данным
    lines = csv_data.strip().split('\n')
    headers = lines[0] if lines else ""
    data_lines = lines[1:] if len(lines) > 1 else []

    # Добавляем номера к данным
    numbered_data_lines = []
    for i, line in enumerate(data_lines):
        numbered_line = f"{start_number + i};{line}"
        numbered_data_lines.append(numbered_line)

    # Формируем полные данные с заголовком
    full_data = f"{headers}\n" + "\n".join(numbered_data_lines)

    # Сохранение в файл csv
    with open(DATA_FILEPATH, 'a', encoding='utf-8') as f:
        if start_number == 1:  # Если файл новый, пишем заголовок
            f.write(headers + '\n')
        f.write("\n".join(numbered_data_lines) + '\n')


def convert_csv_to_json(csv_filename, json_filename=None):
    """
    Конвертирует CSV файл в JSON формат

    Args:
        csv_filename (str): путь к CSV файлу
        json_filename (str): путь для сохранения JSON файла (если None, будет создан автоматически)
    """
    if json_filename is None:
        json_filename = csv_filename.replace('.csv', '.json')

    try:
        # Чтение CSV файла
        df = pd.read_csv(csv_filename, delimiter=';', encoding='utf-8')

        # Конвертация в JSON
        json_data = df.to_json(json_filename, orient='records', indent=2, force_ascii=False)

        print(f" Данные успешно конвертированы в JSON")
        print(f"📊 Количество записей: {len(df)}")

        return json_data

    except Exception as e:
        print(f" Ошибка при конвертации CSV в JSON: {e}")
        return None

def main_function(DATA_FILEPATH='test_data_3.csv'):
    """
    Основная функция
    """
    print(" Получение данных о компаниях через DeepSeek API...")

    # Получение данных от DeepSeek
    csv_data = get_company_data_from_deepseek()

    # Сохранение и отображение данных
    save_to_csv_and_display(csv_data, DATA_FILEPATH)
    result_df = pd.read_csv(DATA_FILEPATH, encoding='utf-8', delimiter=";")
    #convert_csv_to_json(DATA_FILEPATH)
    return result_df

if __name__ == "__main__":
    main_function()