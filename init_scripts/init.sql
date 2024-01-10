SELECT 'CREATE DATABASE test' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test')\gexec

\c test;

create table pages(page_id text, file_id text, page_number int, total_pages int, content text, questions text);
