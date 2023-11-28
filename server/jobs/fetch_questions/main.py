import threading
import openai
import os
import sys
import pika
from dotenv import load_dotenv
import timeit
import json
import psycopg2


load_dotenv()


def insert_page_to_db(fileId, pageId, pageNumber, totalPages, content, questions):
    # Connect to the database
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    cur = conn.cursor()
    query = f"insert into pages values ('{pageId}', '{fileId}', '{pageNumber}', '{totalPages}', '{content}', '{questions}');"
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()


openai.api_key = os.getenv('OPENAI_API_KEY')


class Page:
    def __init__(self, page_number, page_id, file_id, content, total_pages):
        self.page_number = page_number
        self.total_pages = total_pages
        self.page_id = page_id
        self.file_id = file_id
        self.content = content


def get_structured_questions(page: Page):
    prompt = f"""
                var promptText = $@"---BEGIN INSTRUCTIONS---
                Identify and extract mcqs questions from the given text in the below mentioned format.

                TEXT : {page.content}

                ---BEGIN FORMAT TEMPLATE---
                [
                    "Question": "",
                    "QuestionNumber": "",
                    "Option1": "",
                    "Option2": "",
                    "Option3": "",
                    "Option4": "",
                    "Option5": "",
                    "CorrectOption": "",

                ]

                ---END FORMAT TEMPLATE---


                Provide your response strictly as an array of JSON object of the following format and do not write anything else :-:

                ---END INSTRUCTIONS--- 
                """

    starttime = timeit.default_timer()
    response = openai.chat.completions.create(model='gpt-3.5-turbo-16k', messages=[
        {"role": "user", "content": prompt}
    ])
    print(f"Time taken : ", timeit.default_timer() - starttime)

    print(response.usage, "\n\n")
    return response.choices[0].message.content


def thread_wrapper(ch, method, body):
    page_dict = json.loads(body.decode())
    page = Page(page_dict['page_number'], page_dict['page_id'],
                page_dict['file_id'], page_dict['content'], page_dict['total_pages'])
    print(
        f"Processing page {page.page_number} | {page.page_id} from file {page.file_id}...")

    parsed_questions = get_structured_questions(page)

    # Done to tackle postgress text input issue which does not allow single quotes in the text
    if parsed_questions[0] == "'":
        parsed_questions = parsed_questions[1:-1]
    parsed_questions = parsed_questions.replace("'", "''")

    print(parsed_questions)

    print(
        f"Updating database for page {page.page_number} of file {page.file_id}...")
    insert_page_to_db(page.file_id, page.page_id,
                      page.page_number, page.total_pages, "", parsed_questions)

    print(
        f"Page {page.page_number} from file {page.file_id} has been completely processed.")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='pages')

    def callback(ch, method, properties, body):
        t = threading.Thread(target=thread_wrapper, args=(ch, method, body))
        t.start()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue='pages', on_message_callback=callback, auto_ack=False)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
