import uuid
from fastapi import FastAPI, File, UploadFile
import pika
app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}

save_path = "C:\\Users\\ashmi\\Repos\\opengrad\\parse_end\\temp_files"


def send_message_to_file_queue(file_id: str):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    queue_name = 'files'
    channel.queue_declare(queue=queue_name)

    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=file_id)

    connection.close()


@app.post("/file/")
async def receive_file(file: UploadFile):
    file_id = str(uuid.uuid4())

    with open(f"{save_path}\\{file_id}", "wb") as f:
        f.write(await file.read())

    send_message_to_file_queue(file_id)
    return {"filename": file.filename}
