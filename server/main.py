import json
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
import pika

from server.utils import fetch_records_with_file_id

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
    return {"fileId": file_id}


@app.get("/file")
async def get_questions(fileId: str):
    results = fetch_records_with_file_id(fileId)
    page_by_page_results = []
    if len(results) == 0:
        return HTTPException(404, detail='Invalid fileId')

    if len(results) < results[0][3]:
        return HTTPException(100, detail='File is still being processed')

    for result in results:
        json_results = json.loads(result[5], strict=False)
        page_by_page_results.append(json_results)
    return page_by_page_results
