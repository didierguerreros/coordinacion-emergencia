import os
import psycopg2

def obtener_conexion():
    conexion = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv(
            "DB_NAME", "coordinacion_emergencias"
        ),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        port=os.getenv("DB_PORT", "5432")
    )
    return conexion