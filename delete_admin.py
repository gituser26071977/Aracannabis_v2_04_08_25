
import os
import psycopg2
from psycopg2 import OperationalError

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5435")
DB_USER = os.getenv("DB_USER", "siap_user")
DB_PASS = os.getenv("DB_PASS", "siap_pass")
DB_NAME = os.getenv("DB_NAME", "siap_db")

def create_connection():
    try:
        connection = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return connection
    except OperationalError as e:
        print(f"The error '{e}' occurred")
        return None

def delete_admin(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM profissionais WHERE usuario = 'admin';")
        connection.commit()
        print(f"Deleted user 'admin'. Rows affected: {cursor.rowcount}")
    except Exception as e:
        print(f"Error deleting user: {e}")
        connection.rollback()

if __name__ == "__main__":
    conn = create_connection()
    if conn:
        delete_admin(conn)
        conn.close()
