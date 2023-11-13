import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
# Connect to the database
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)


cur = conn.cursor()


def fetch_all_records():
    query = "select * from pages"
    cur.execute(query)
    results = cur.fetchall()
    print(results)
    return results


def fetch_records_with_file_id(fileId: str):
    query = f"select * from pages where file_id = {fileId}"
    cur.execute(query)

    results = cur.fetchall()
    print(results)
    return results


def insert_page_to_db(pageId: str, fileId: str, pageNumber: int, totalPages: int, content: str, questions: str):
    query = f"insert into pages(page_id, file_id, page_number, total_pages, content, questions) values ('{pageId}', '{fileId}', '{pageNumber}', '{totalPages}', '{content}', '{questions}')"

    cur.execute(query)
    conn.commit()


# Close the cursor and connection
fetch_all_records()
cur.close()
conn.close()
