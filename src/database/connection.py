"""
Modulo per la connessione al database MySQL.
Issue #4: Connessione Python a MySQL con gestione errori e OOP.
Utilizza un Context Manager per garantire la chiusura sicura della connessione.
"""
import os
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione base del logging (requisito "gestione errori")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Classe per gestire la connessione al database MySQL.
    Implementa il pattern Context Manager (__enter__ e __exit__) 
    per un uso sicuro con la parola chiave 'with'.
    """
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'winescout_user'),
            'password': os.getenv('DB_PASSWORD', 'winescout_password'),
            'database': os.getenv('DB_NAME', 'winescout')
        }
        self.connection = None

    def __enter__(self):
        """Apre la connessione quando si entra nel blocco 'with'."""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info("Connessione al database MySQL stabilita con successo.")
            return self.connection
        except Error as e:
            logger.error(f"Errore critico durante la connessione al database: {e}")
            raise  # Rilancia l'eccezione per bloccare l'esecuzione se il DB non c'è

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Chiude la connessione quando si esce dal blocco 'with', anche in caso di errore."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Connessione al database chiusa correttamente.")
