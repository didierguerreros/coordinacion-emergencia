from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from con_db import obtener_conexion

app = FastAPI(
    title="API de Ubicación",
    description="Servicio para gestionar ubicaciones reportadas",
    version="1.0.0"
)


class Ubicacion(BaseModel):
    id_persona: int
    latitud: float
    longitud: float


@app.get("/")
def inicio():
    return {"mensaje": "API de Ubicación funcionando"}


@app.post("/ubicaciones")
def registrar_ubicacion(datos: Ubicacion):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO ubicaciones
                (id_persona, latitud, longitud)
            VALUES (%s, %s, %s)
            RETURNING id_ubicacion, fecha_reporte;
            """,
            (datos.id_persona, datos.latitud, datos.longitud)
        )

        resultado = cursor.fetchone()
        conexion.commit()

        return {
            "mensaje": "Ubicación registrada correctamente",
            "id_ubicacion": resultado[0],
            "id_persona": datos.id_persona,
            "latitud": datos.latitud,
            "longitud": datos.longitud,
            "fecha_reporte": resultado[1]
        }

    except Exception as error:
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

@app.get("/ubicaciones")
def consultar_ubicaciones():
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_ubicacion,
                id_persona,
                latitud,
                longitud,
                fecha_reporte
            FROM ubicaciones
            ORDER BY fecha_reporte DESC;
        """)

        resultados = cursor.fetchall()

        ubicaciones = []

        for fila in resultados:
            ubicaciones.append({
                "id_ubicacion": fila[0],
                "id_persona": fila[1],
                "latitud": float(fila[2]),
                "longitud": float(fila[3]),
                "fecha_reporte": fila[4]
            })

        return ubicaciones

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar las ubicaciones"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()

@app.get("/personas/{id_persona}/ubicacion")
def consultar_ubicacion_persona(id_persona: int):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_ubicacion,
                id_persona,
                latitud,
                longitud,
                fecha_reporte
            FROM ubicaciones
            WHERE id_persona = %s
            ORDER BY fecha_reporte DESC;
        """, (id_persona,))

        resultados = cursor.fetchall()

        if not resultados:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron ubicaciones para esta persona"
            )

        ubicaciones = []

        for fila in resultados:
            ubicaciones.append({
                "id_ubicacion": fila[0],
                "id_persona": fila[1],
                "latitud": float(fila[2]),
                "longitud": float(fila[3]),
                "fecha_reporte": fila[4]
            })

        return {
            "id_persona": id_persona,
            "cantidad": len(ubicaciones),
            "ubicaciones": ubicaciones
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