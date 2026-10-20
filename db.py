
import os
import psycopg


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg.connect(database_url)

    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "stockwise_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", "5432")),
    )
