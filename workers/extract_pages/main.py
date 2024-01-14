import json
import uuid
from dotenv import load_dotenv
import pika
import sys
import os
import io
import requests
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdf2image import convert_from_path
from google.cloud import vision
from docx import Document
from google.cloud.vision_v1 import types

load_dotenv()


class Page:
    def __init__(self, page_number, page_id, file_id, content, total_pages):
        self.page_number = page_number
        self.total_pages = total_pages
        self.page_id = page_id
        self.file_id = file_id
        self.content = content


temp_files_path = "/app/shared"

rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", 5672))
rabbitmq_user = os.environ.get("RABBITMQ_USER", "guest")
rabbitmq_pass = os.environ.get("RABBITMQ_PASS", "guest")


# def save_pdf_as_image(path):
#     # Set up PDF to image conversion
#     images = convert_from_path(path, 500)
#     images_path = []
#     for i in range(len(images)):
#         # Save pages as images in the pdf
#         images_path.append(temp_files_path + "/" + 'page' + str(i) + '.jpg')
#         images[i].save(temp_files_path + "/" +
#                        'page' + str(i) + '.jpg', 'JPEG')

#     return images_path


# def fetch_image_details(images_paths):
#     client = vision.ImageAnnotatorClient()
#     page_contents = []
#     for ind, path in enumerate(images_paths):
#         with open(path, "rb") as image_file:
#             image_content = image_file.read()

#             # Set up image object
#             image = types.Image(content=image_content)

#             # Perform OCR using full text annotations
#             print(f'Performing OCR on page {ind}')
#             response = client.document_text_detection(image=image)
#             document = response.full_text_annotation

#             page_contents.append(document.text)

#     return page_contents


def extract_text_from_pages(doc_id: str) -> list[Page]:
    pages = []
    doc_path = temp_files_path + "/" + doc_id + ".docx"

    doc = Document(doc_path)
    count = 1

    for paragraph in doc.paragraphs:
        content = paragraph.text

        page_id = str(uuid.uuid4())

        pages.append(
            Page(count, page_id, doc_id, content, 0))
        count += 1

    for page in pages:
        page.total_pages = count - 1
    return pages


def fetch_file_from_queue(pdf_id: str):

    headers = {"app_key": os.getenv('MATHPIX_APP_KEY'),
               "app_id": os.getenv('MATHPIX_APP_ID')
               }

    url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".docx"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print('Successfully parsed pdf')
        with open(temp_files_path + '/' + pdf_id + ".docx", "wb") as f:
            f.write(response.content)
        return True
    elif response.status_code == 404:
        print(f'PDF {pdf_id} not parsed yet')
        print(response.json())
    return False


def send_page_content_message(page_string: str):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port,
                                      credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)))
        channel = connection.channel()
        queue_name = 'pages'
        channel.queue_declare(queue=queue_name)

        print('Publishing message')
        channel.basic_publish(exchange='',
                              routing_key=queue_name,
                              body=page_string)

        connection.close()
    except pika.exceptions.AMQPConnectionError:
        print("RabbitMQ server is not running. Please start it and try again.")


def main():

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port,
                                      credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)))
        channel = connection.channel()
        queue_name = 'files'
        channel.queue_declare(queue=queue_name)

        def callback(ch, method, properties, body):
            pdf_id = body.decode('utf-8')
            print(f"Processing file {pdf_id}...")
            if fetch_file_from_queue(pdf_id):
                print(f"File {pdf_id} found. Processing pages....")

                pages: list[Page] = extract_text_from_pages(pdf_id)
                print("Total pages: ", len(pages))
                for page in pages:
                    page_string = json.dumps(page.__dict__)
                    send_page_content_message(page_string)

                print(f"File {pdf_id} has been completely processed.")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)

        channel.basic_consume(
            queue=queue_name, on_message_callback=callback, auto_ack=False)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        print("RabbitMQ server is not running. Please start it and try again.")


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
