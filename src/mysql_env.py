from dotenv import load_dotenv
import os

import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling


load_dotenv() 

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3307)),
    "database": os.getenv("DB_NAME", "domino_db"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456789"),
    "autocommit": False,
    "charset": "utf8mb4",

}

POOL_NAME = os.getenv("POOL_NAME", "bib_pool")
POOL_SIZE = int(os.getenv("POLL_SIZE", 5))

pool = pooling.MySQLConnectionPool(
    pool_name = POOL_NAME,
    pool_size = POOL_SIZE,
    **DB_CONFIG
)

def get_conn():
    return pool.get_connection()


def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )
        if connection.is_connected():
            print("Conexión exitosa a MySQL")
            return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()
        print("Conexión cerrada.")