start cmd /k  uvicorn server.main:app --reload
start cmd /k  python server/jobs/extract_pages/main.py

@REM Start maximum of 3 instances of the api call for openai
start cmd /k  python server/jobs/fetch_questions/main.py
start cmd /k  python server/jobs/fetch_questions/main.py
start cmd /k  python server/jobs/fetch_questions/main.py
