@REM Start n instances of the fetch job
set /p num_instances=Enter the number of instances to start: 

start cmd /k  uvicorn server.main:app --reload
start cmd /k  python server/jobs/extract_pages/main.py
for /l %%x in (1, 1, %num_instances%) do (
    start cmd /k python server/jobs/fetch_questions/main.py
)
