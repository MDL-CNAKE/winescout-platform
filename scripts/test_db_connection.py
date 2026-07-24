"""
Script di test per verificare la connessione al database MySQL.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection


def test_connection():
    print("Test connessione al database in corso...")
    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM wines;")
            count = cursor.fetchone()[0]
            print(f"Test superato! Trovati {count} vini nel database.")
            cursor.close()
    except Exception as e:
        print(f"Test fallito: {e}")
        print("Assicurati che il container MySQL sia attivo (docker-compose up -d mysql)")


if __name__ == "__main__":
    test_connection()
