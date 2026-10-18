import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from con_db import obtener_conexion
from fastapi.middleware.cors import CORSMiddleware


# URL pública de la API de Ubicación.
# En Vercel se configurará mediante una variable de entorno.
API_UBICACION_URL = os.getenv(
    "API_UBICACION_URL",
    "http://127.0.0.1:8001"
).rstrip("/")


app = FastAPI(
    title="API de Emergencias",
    description="Servicio para gestionar incidentes de emergencia",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Emergencia(BaseModel):
    id_persona: int
    tipo: str
    descripcion: str


@app.get("/")
def inicio():
    return {"mensaje": "API de Emergencias funcionando"}


@app.get("/emergencias")
def consultar_emergencias():
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_emergencia,
                id_persona,
                tipo,
                descripcion,
                estado,
                fecha_reporte
            FROM emergencias
            ORDER BY fecha_reporte DESC;
        """)

        resultados = cursor.fetchall()

        return [
            {
                "id_emergencia": fila[0],
                "id_persona": fila[1],
                "tipo": fila[2],
                "descripcion": fila[3],
                "estado": fila[4],
                "fecha_reporte": fila[5]
            }
            for fila in resultados
        ]

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las emergencias"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


@app.post("/emergencias")
def registrar_emergencia(datos: Emergencia):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO emergencias
                (id_persona, tipo, descripcion)
            VALUES (%s, %s, %s)
            RETURNING id_emergencia, estado, fecha_reporte;
            """,
            (datos.id_persona, datos.tipo, datos.descripcion)
        )

        resultado = cursor.fetchone()
        conexion.commit()

        return {
            "mensaje": "Emergencia registrada correctamente",
            "id_emergencia": resultado[0],
            "id_persona": datos.id_persona,
            "tipo": datos.tipo,
            "descripcion": datos.descripcion,
            "estado": resultado[1],
            "fecha_reporte": resultado[2]
        }

    except Exception:
        if conexion:
            conexion.rollback()

        raise HTTPException(
            status_code=500,
            detail="Error al registrar la emergencia"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


@app.get("/emergencias/{id_emergencia}/ubicacion")
def consultar_ubicacion_emergencia(id_emergencia: int):
    conexion = None
    cursor = None

    try:
        # 1. Consultar la emergencia en PostgreSQL.
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT
                id_emergencia,
                id_persona,
                tipo,
                descripcion,
                estado
            FROM emergencias
            WHERE id_emergencia = %s;
            """,
            (id_emergencia,)
        )

        emergencia = cursor.fetchone()

        if emergencia is None:
            raise HTTPException(
                status_code=404,
                detail="Emergencia no encontrada"
            )

        id_persona = emergencia[1]

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la emergencia"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()

    # 2. Consultar la API de Ubicación mediante HTTP.
    try:
        respuesta = requests.get(
            f"{API_UBICACION_URL}/personas/{id_persona}/ubicacion",
            timeout=10
        )

        if respuesta.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="No hay ubicación registrada para esta persona"
            )

        respuesta.raise_for_status()
        ubicacion = respuesta.json()

    except HTTPException:
        raise

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="No fue posible consultar el servicio de Ubicación"
        )

    # 3. Devolver los datos integrados.
    return {
        "emergencia": {
            "id_emergencia": emergencia[0],
            "id_persona": emergencia[1],
            "tipo": emergencia[2],
            "descripcion": emergencia[3],
            "estado": emergencia[4]
        },
        "ubicacion": ubicacion
    }
