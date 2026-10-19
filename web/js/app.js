

"use strict";

// ==================================================
// 1. CONFIGURACIÓN DE LAS API
// ==================================================

const API_EMERGENCIAS =
    "https://coordinacion-emergencia.vercel.app";

const API_UBICACION =
    "https://api-ubicacion-kappa.vercel.app";

// Configura una clave restringida de Google Maps Embed API.
// No publiques claves sin las restricciones correspondientes.
const GOOGLE_MAPS_API_KEY =
    "AIzaSyDWU4P59uQdl3lKPcTYod7g3eWapAdxx5w";


// ==================================================
// 2. CONSULTAR EMERGENCIAS
// ==================================================

async function consultarEmergencias() {
    const tabla = document.getElementById("tabla-emergencias");
    const mensaje = document.getElementById("mensaje");
    const boton = document.getElementById("btn-actualizar");

    if (!tabla || !mensaje || !boton) {
        console.error("No se encontraron los elementos de la tabla.");
        return;
    }

    boton.disabled = true;
    mensaje.textContent = "Consultando emergencias...";
    mensaje.className = "";

    try {
        const respuesta = await fetch(
            `${API_EMERGENCIAS}/emergencias`
        );

        if (!respuesta.ok) {
            throw new Error(
                `Error HTTP ${respuesta.status} al consultar emergencias.`
            );
        }

        const emergencias = await respuesta.json();

        if (!Array.isArray(emergencias)) {
            throw new Error(
                "La respuesta de emergencias no tiene el formato esperado."
            );
        }

        tabla.replaceChildren();

        if (emergencias.length === 0) {
            const fila = document.createElement("tr");
            const celda = document.createElement("td");

            celda.colSpan = 5;
            celda.textContent = "No hay emergencias registradas.";

            fila.appendChild(celda);
            tabla.appendChild(fila);

            mensaje.textContent =
                "Consulta completada. No hay reportes.";
            mensaje.className = "exito";
            return;
        }

        emergencias.forEach(emergencia => {
            const fila = document.createElement("tr");

            // ID de emergencia, persona y tipo.
            const valores = [
                emergencia.id_emergencia,
                emergencia.id_persona,
                emergencia.tipo
            ];

            valores.forEach(valor => {
                const celda = document.createElement("td");
                celda.textContent = valor ?? "";
                fila.appendChild(celda);
            });

            // Estado de la emergencia.
            const celdaEstado = document.createElement("td");
            const etiquetaEstado = document.createElement("span");

            etiquetaEstado.className = "estado";
            etiquetaEstado.textContent =
                emergencia.estado ?? "Sin estado";

            celdaEstado.appendChild(etiquetaEstado);
            fila.appendChild(celdaEstado);

            // Botón para consultar ubicación.
            const celdaAccion = document.createElement("td");
            const botonUbicacion = document.createElement("button");

            botonUbicacion.type = "button";
            botonUbicacion.textContent = "Ver ubicación";

            botonUbicacion.addEventListener("click", () => {
                consultarUbicacion(emergencia.id_emergencia);
            });

            celdaAccion.appendChild(botonUbicacion);
            fila.appendChild(celdaAccion);

            tabla.appendChild(fila);
        });

        mensaje.textContent =
            `Se encontraron ${emergencias.length} emergencia(s).`;
        mensaje.className = "exito";

    } catch (error) {
        console.error("Error al consultar emergencias:", error);

        tabla.replaceChildren();

        const fila = document.createElement("tr");
        const celda = document.createElement("td");

        celda.colSpan = 5;
        celda.textContent = "No fue posible cargar las emergencias.";

        fila.appendChild(celda);
        tabla.appendChild(fila);

        mensaje.textContent =
            "No fue posible consultar la API de Emergencias. " +
            "Verifica la conexión e inténtalo nuevamente.";
        mensaje.className = "error";

    } finally {
        boton.disabled = false;
    }
}


// ==================================================
// 3. CONSULTAR UBICACIÓN DE UNA EMERGENCIA
// ==================================================

async function consultarUbicacion(idEmergencia) {
    const detalle = document.getElementById("detalle-ubicacion");
    const mapa = document.getElementById("google-map");
    const enlace = document.getElementById("enlace-mapa");

    if (!detalle || !mapa || !enlace) {
        console.error("No se encontraron los elementos de ubicación.");
        return;
    }

    detalle.textContent = "Consultando ubicación de la emergencia...";
    enlace.hidden = true;
    mapa.removeAttribute("src");

    try {
        // La API de Emergencias consulta internamente a la API de Ubicación.
        const respuesta = await fetch(
            `${API_EMERGENCIAS}/emergencias/${encodeURIComponent(idEmergencia)}/ubicacion`
        );

        if (!respuesta.ok) {
            if (respuesta.status === 404) {
                throw new Error(
                    "No se encontró la emergencia o no tiene ubicación registrada."
                );
            }

            throw new Error(
                `Error HTTP ${respuesta.status} al consultar la ubicación.`
            );
        }

        const datos = await respuesta.json();

        const emergencia = datos.emergencia;
        const ubicacion = datos.ubicacion;

        if (!emergencia || !ubicacion) {
            throw new Error(
                "La respuesta no contiene los datos esperados de emergencia y ubicación."
            );
        }

        // La API devuelve un objeto de ubicación, no una lista.
        const ultimaUbicacion = ubicacion;

        if (
            ultimaUbicacion.latitud == null ||
            ultimaUbicacion.longitud == null
        ) {
            throw new Error(
                "La respuesta no contiene las coordenadas de la ubicación."
            );
        }

        const latitud = Number(ultimaUbicacion.latitud);
        const longitud = Number(ultimaUbicacion.longitud);

        // Validar las coordenadas.
        if (
            !Number.isFinite(latitud) ||
            !Number.isFinite(longitud) ||
            latitud < -90 ||
            latitud > 90 ||
            longitud < -180 ||
            longitud > 180
        ) {
            throw new Error(
                "Las coordenadas recibidas no son válidas."
            );
        }

        // Mostrar los datos de la emergencia y su ubicación.
        detalle.replaceChildren();

        const lineas = [
            ["Emergencia:", `#${emergencia.id_emergencia}`],
            ["Tipo:", emergencia.tipo],
            [
                "Descripción:",
                emergencia.descripcion || "Sin descripción"
            ],
            ["Estado:", emergencia.estado || "Sin estado"],
            ["Persona:", emergencia.id_persona],
            ["Latitud:", latitud],
            ["Longitud:", longitud],
            [
                "Fecha de ubicación:",
                ultimaUbicacion.fecha_reporte || "No disponible"
            ]
        ];

        lineas.forEach(([etiqueta, valor]) => {
            const linea = document.createElement("div");
            const textoEtiqueta = document.createElement("strong");

            textoEtiqueta.textContent = `${etiqueta} `;
            linea.appendChild(textoEtiqueta);

            linea.appendChild(
                document.createTextNode(String(valor ?? ""))
            );

            detalle.appendChild(linea);
        });

        // Enlace externo a Google Maps.
        const coordenadas = `${latitud},${longitud}`;

        enlace.href =
            `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(coordenadas)}`;

        enlace.hidden = false;

        // Mapa integrado, si hay una clave configurada.
        if (
            GOOGLE_MAPS_API_KEY &&
            GOOGLE_MAPS_API_KEY !==
                "REEMPLAZA_CON_TU_CLAVE_DE_GOOGLE_MAPS"
        ) {
            mapa.src =
                "https://www.google.com/maps/embed/v1/place" +
                `?key=${encodeURIComponent(GOOGLE_MAPS_API_KEY)}` +
                `&q=${encodeURIComponent(coordenadas)}` +
                "&zoom=16";
        } else {
            const aviso = document.createElement("p");

            aviso.textContent =
                "El mapa integrado requiere configurar Google Maps Embed API. " +
                "Puedes abrir las coordenadas mediante el enlace de Google Maps.";

            detalle.appendChild(aviso);
        }

    } catch (error) {
        console.error("Error al consultar ubicación:", error);

        const mensajeError = document.createElement("p");

        mensajeError.className = "error";
        mensajeError.textContent = error.message;

        detalle.replaceChildren(mensajeError);
        enlace.hidden = true;
        mapa.removeAttribute("src");
    }
}


// ==================================================
// 4. INICIALIZAR LA APLICACIÓN
// ==================================================

document.addEventListener("DOMContentLoaded", () => {
    const botonActualizar = document.getElementById("btn-actualizar");

    if (botonActualizar) {
        botonActualizar.addEventListener(
            "click",
            consultarEmergencias
        );
    }

    // Consultar los reportes al abrir la página.
    consultarEmergencias();
});
