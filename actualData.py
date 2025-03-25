import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

url = "https://copyright.kazpatent.kz/"
driver.get(url)

try:
    scrollable_div = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//div[@id='Br']"))
    )
    print("Найден контейнер с таблицей.")
except Exception as e:
    print("Ошибка: контейнер с таблицей не найден.", e)
    driver.quit()
    exit()

last_height = 0
retries = 0
data = []

while retries < 10:
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scrollable_div)
    time.sleep(2)  

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//tbody[@id='Bh']/tr"))
    )

    rows = driver.find_elements(By.XPATH, "//tbody[@id='Bh']/tr")
    row_count = len(rows)

    if row_count > last_height:
        retries = 0
    else:
        retries += 1

    last_height = row_count
    print(f"Загружено строк: {row_count}")


def get_text_safe(element, xpath):
    """Функция безопасного извлечения текста, с JS-поддержкой."""
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        elem = element.find_elements(By.XPATH, xpath)

        if elem and elem[0].text.strip():
            return elem[0].text.strip()

        return driver.execute_script("return arguments[0].textContent.trim();", elem[0]) if elem else "НЕ НАЙДЕНО"

    except Exception as e:
        print(f"Ошибка при извлечении {xpath}: {e}")
        return "ОШИБКА"


rows = driver.find_elements(By.XPATH, "//tbody[@id='Bh']/tr")

for index, row in enumerate(rows, start=1):
    cells = row.find_elements(By.TAG_NAME, "td")

    if len(cells) < 9:
        print(f"Пропущена строка {index}: мало колонок ({len(cells)})")
        continue

    row_data = [
        get_text_safe(row, ".//td[2]//span"),
        get_text_safe(row, ".//td[3]//span"),
        get_text_safe(row, ".//td[4]//span"),
        get_text_safe(row, ".//td[5]//span"),
        get_text_safe(row, ".//td[6]//span"),
        get_text_safe(row, ".//td[7]//span"),
        get_text_safe(row, ".//td[8]//span"),
        get_text_safe(row, ".//td[9]//span")
    ]

    print(f"Строка {index}: {row_data}")

    if any(val != "НЕ НАЙДЕНО" and val != "ОШИБКА" for val in row_data):
        data.append(row_data)
    else:
        print(f"Строка {index} полностью пустая, не добавлена.")


csv_file = "kazpatent_data.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Св-во №", "Дата публикации", "Рег. номер заявки", "Дата подачи заявки", "Дата создания объекта", "Тип объекта", "Название RU", "Авторы", "Статус"])
    writer.writerows(data)

print(f"Данные сохранены в {csv_file} ({len(data)} записей)")

driver.quit()
