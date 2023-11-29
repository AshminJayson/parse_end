import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# create table pages(page_id text, file_id text, page_number int, total_pages int, content text, questions text);


def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cur = conn.cursor()
    return [cur, conn]


def drop_connection(cur, conn):
    cur.close()
    conn.close()


def fetch_all_records():
    query = "select * from pages"
    cur, conn = get_connection()
    cur.execute(query)
    results = cur.fetchall()
    # print(results)
    drop_connection(cur, conn)
    return results


def fetch_records_with_file_id(fileId: str):
    query = f"select * from pages where file_id = '{fileId}' order by page_number asc"
    cur, conn = get_connection()
    cur.execute(query)

    results = cur.fetchall()
    # print(results)
    drop_connection(cur, conn)
    return results


def insert_page_to_db(pageId: str, fileId: str, pageNumber: int, totalPages: int, content: str, questions: str):
    query = f"insert into pages(page_id, file_id, page_number, total_pages, content, questions) values ('{pageId}', '{fileId}', '{pageNumber}', '{totalPages}', '{content}', '{questions}')"
    cur, conn = get_connection()
    cur.execute(query)
    conn.commit()
    drop_connection(cur, conn)
