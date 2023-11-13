import json
import timeit
from dotenv import load_dotenv
import pika
import sys
import os
import openai

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


class Page:
    def __init__(self, page_number, page_id, file_id, content):
        self.page_number = page_number
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
    print(response.choices[0].message.content)


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='pages')

    def callback(ch, method, properties, body):
        page_dict = json.loads(body.decode())
        page = Page(page_dict['page_number'], page_dict['page_id'],
                    page_dict['file_id'], page_dict['content'])
        print(
            f"Processing page {page.page_number} from file {page.file_id}...")

        get_structured_questions(page)

        print(
            f"Page {page.page_number} from file {page.file_id} has been completely processed.")

    channel.basic_consume(
        queue='pages', on_message_callback=callback, auto_ack=True)

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
