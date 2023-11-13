import uuid
import pika
import sys
import os
import io
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage


class Page:
    def __init__(self, page_number, page_id, file_id, content):
        self.page_number = page_number
        self.page_id = page_id
        self.file_id = file_id
        self.content = content


base_path = "C:\\Users\\ashmi\\Repos\\opengrad\\parse_end\\temp_files"


def extract_text_from_pages(file_id_name: str) -> list[Page]:
    pages = []
    with open(base_path + "\\" + file_id_name, 'rb') as file:
        resource_manager = PDFResourceManager()
        output_string = io.StringIO()
        converter = TextConverter(
            resource_manager, output_string, laparams=None)
        page_interpreter = PDFPageInterpreter(resource_manager, converter)

        count = 1
        for page in PDFPage.get_pages(file, check_extractable=True):
            page_interpreter.process_page(page)
            content = output_string.getvalue()
            pages.append(
                Page(count, str(uuid.uuid4()), file_id_name, content))
            count += 1

        converter.close()
        output_string.close()

    return pages


def send_page_content_message():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    queue_name = 'pages'
    channel.queue_declare(queue=queue_name)

    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body='Hello World!')

    connection.close()


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    queue_name = 'files'
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        file_id_name = body.decode('utf-8')
        pages: list[Page] = extract_text_from_pages(file_id_name)

    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)

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
