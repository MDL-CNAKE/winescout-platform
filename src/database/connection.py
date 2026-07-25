"""Connessione centralizzata al database MySQL.

Tutti i moduli che devono leggere/scrivere dati (training, raccomandazione,
app Streamlit) usano questa unica classe invece di aprire connessioni sparse
nel codice: un solo punto da aggiornare se cambiano credenziali, host o si
vuole aggiungere retry/logging piu sofisticato in futuro.
"""
import os
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Context manager per la connessione MySQL.

    Le credenziali sono lette da variabili d'ambiente (file .env in locale,
    variabili iniettate da docker-compose in container) cosi lo stesso codice
    funziona sia in sviluppo locale sia dentro Docker senza modifiche:
    in locale DB_HOST=127.0.0.1, in container DB_HOST=mysql (nome del
    servizio nella rete Docker).

    Esempio d'uso:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM wines")
    """

    def __init__(self) -> None:
        self.config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "winescout_user"),
            "password": os.getenv("DB_PASSWORD", "winescout_password"),
            "database": os.getenv("DB_NAME", "winescout"),
        }
        self.connection = None

    def __enter__(self):
        """Apre la connessione all'ingresso del blocco `with`."""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info("Connessione al database MySQL stabilita con successo.")
            return self.connection
        except Error as e:
            # Errore critico e bloccante: senza DB l'app non puo funzionare,
            # quindi rilanciamo invece di fallire silenziosamente.
            logger.error(f"Errore critico durante la connessione al database: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Chiude sempre la connessione all'uscita dal blocco, anche in caso di eccezione."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Connessione al database chiusa correttamente.")
