
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from con_db import obtener_conexion


app = FastAPI(
    title="API de Ubicación",
    description="Servicio para registrar y consultar ubicaciones",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Ubicacion(BaseModel):
    id_persona: int
    latitud: float
    longitud: float


@app.get("/")
def inicio():
    return {
        "mensaje": "API de Ubicación funcionando"
    }


@app.post("/ubicaciones")
def registrar_ubicacion(datos: Ubicacion):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO ubicaciones (
                id_persona,
                latitud,
                longitud
            )
            VALUES (%s, %s, %s)
            RETURNING
                id_ubicacion,
                id_persona,
                latitud,
                longitud,
                fecha_reporte;
            """,
            (
                datos.id_persona,
                datos.latitud,
                datos.longitud
            )
        )

        fila = cursor.fetchone()
        conexion.commit()

        return {
            "mensaje": "Ubicación registrada correctamente",
            "id_ubicacion": fila[0],
            "id_persona": fila[1],
            "latitud": float(fila[2]),
            "longitud": float(fila[3]),
            "fecha_reporte": fila[4]
        }

    except Exception:
        if conexion:
            conexion.rollback()

        raise HTTPException(
            status_code=500,
            detail="Error al registrar la ubicación"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


@app.get("/ubicaciones/{id_persona}")
def consultar_ubicacion(id_persona: int):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT
                id_ubicacion,
                id_persona,
                latitud,
                longitud,
                fecha_reporte
            FROM ubicaciones
            WHERE id_persona = %s
            ORDER BY fecha_reporte DESC
            LIMIT 1;
            """,
            (id_persona,)
        )

        fila = cursor.fetchone()

        if fila is None:
            raise HTTPException(
                status_code=404,
                detail="No hay ubicación registrada para esta persona"
            )

        return {
            "id_ubicacion": fila[0],
            "id_persona": fila[1],
            "latitud": float(fila[2]),
            "longitud": float(fila[3]),
            "fecha_reporte": fila[4]
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la ubicación"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()


@app.get("/personas/{id_persona}/ubicacion")
def consultar_ubicacion_persona(id_persona: int):
    return consultar_ubicacion(id_persona)
