import uuid
from fastapi import FastAPI, File, UploadFile
import pika
app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}

save_path = "C:\\Users\\ashmi\\Repos\\opengrad\\parse_end\\temp_files"


def send_message_to_file_queue(file_id_name: str):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    queue_name = 'files'
    channel.queue_declare(queue=queue_name)

    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=file_id_name)

    connection.close()


@app.post("/file/")
async def receive_file(file: UploadFile):
    file_id = uuid.uuid4()
    filename_split = list(file.filename.split('.'))
    file_id_name = str(file_id) + '.' + filename_split[-1]

    with open(f"{save_path}\\{file_id_name}", "wb") as f:
        f.write(await file.read())

    send_message_to_file_queue(file_id_name)
    return {"filename": file.filename}
