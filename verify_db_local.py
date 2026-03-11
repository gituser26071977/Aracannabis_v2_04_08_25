
import os
import psycopg2
from psycopg2 import OperationalError

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5435")
DB_USER = os.getenv("DB_USER", "siap_user")
DB_PASS = os.getenv("DB_PASS", "siap_pass")
DB_NAME = os.getenv("DB_NAME", "siap_db")

def create_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection

def check_content(connection):
    cursor = connection.cursor()
    try:
        # Check Profissionais
        cursor.execute("SELECT count(*) FROM profissionais;")
        count_prof = cursor.fetchone()[0]
        print(f"\nNumber of professionals: {count_prof}")
        
        cursor.execute("SELECT nome, usuario, email, role FROM profissionais LIMIT 5;")
        profs = cursor.fetchall()
        print("Sample professionals:")
        for p in profs:
            print(f"- {p[0]} ({p[1]}, {p[2]}) - Role: {p[3]}")

        # Check Pacientes
        cursor.execute("SELECT count(*) FROM pacientes;")
        count_pac = cursor.fetchone()[0]
        print(f"\nNumber of patients: {count_pac}")
        
        cursor.execute("SELECT nome, email FROM pacientes LIMIT 5;")
        pacs = cursor.fetchall()
        print("Sample patients:")
        for p in pacs:
            print(f"- {p[0]} ({p[1]})")

    except Exception as e:
        print(f"Error checking content: {e}")

if __name__ == "__main__":
    conn = create_connection()
    if conn:
        check_content(conn)
        conn.close()
