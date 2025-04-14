import psycopg2
import csv
import os

conn = psycopg2.connect(
    host="localhost",
    database="qbs",
    user="postgres",
    password="amina",
    port="5432"
)
cursor = conn.cursor()

def load_data_from_csv(file_path):
    print(f"\nЗагрузка из файла: {file_path}")
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        row_count = 0

        is_archive = "Тип объекта" not in reader.fieldnames

        for row in reader:
            row_count += 1

            try:
                if is_archive:
                    object_type_name = row["Вид объекта авторских прав"].strip()
                    authors_raw = row["ФИО"]
                    title = row["Название произведения"]
                    pub_date = row["Дата регистрации"]
                    app_num = row["Дата поступления"]
                    app_date = None 
                else:
                    object_type_name = row["Тип объекта"].strip()
                    authors_raw = row["Авторы"]
                    title = row["Название RU"]
                    pub_date = row["Дата публикации"]
                    app_num = row["Рег. номер заявки"]
                    app_date = row["Дата подачи заявки"]

                cursor.execute("SELECT id FROM object_types WHERE name = %s", (object_type_name,))
                result = cursor.fetchone()
                if result:
                    object_type_id = result[0]
                else:
                    cursor.execute("INSERT INTO object_types (name) VALUES (%s) RETURNING id", (object_type_name,))
                    object_type_id = cursor.fetchone()[0]
                    print(f"   + Тип объекта добавлен: {object_type_name} (ID: {object_type_id})")

                cursor.execute("""
                    INSERT INTO patent_records (
                        certificate_number,
                        publication_date,
                        application_number,
                        application_date,
                        creation_date,
                        object_type_id,
                        title_ru,
                        active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    row["Св-во №"],
                    pub_date,
                    app_num,
                    app_date,
                    row["Дата создания объекта"],
                    object_type_id,
                    title,
                    row["Статус"]
                ))
                patent_id = cursor.fetchone()[0]
                print(f"→ [#{row_count}] Патент добавлен: '{title}' (ID: {patent_id})")

                authors = [a.strip() for a in authors_raw.split(",") if a.strip()]
                for author in authors:
                    cursor.execute("SELECT id FROM authors WHERE name = %s", (author,))
                    result = cursor.fetchone()
                    if result:
                        authors_id = result[0]
                        print(f"   - Автор найден: {author} (ID: {authors_id})")
                    else:
                        cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id", (author,))
                        authors_id = cursor.fetchone()[0]
                        print(f"   + Автор добавлен: {author} (ID: {authors_id})")

                    cursor.execute("""
                        INSERT INTO patent_authors (patent_id, authors_id)
                        VALUES (%s, %s)
                    """, (patent_id, authors_id))
                    print(f"Связь добавлена: патент {patent_id} — автор {authors_id}")

            except Exception as e:
                print(f" Ошибка в строке #{row_count}: {e}")

        conn.commit()
        print(f"Загружено {row_count} записей из {file_path}")


actual_path = 'kazpatent_data.csv'
archive_path = 'kazpatentArchive_data.csv'


load_data_from_csv(actual_path)
load_data_from_csv(archive_path)

print("Все данные успешно загружены в базу данных.")
cursor.close()
conn.close()
