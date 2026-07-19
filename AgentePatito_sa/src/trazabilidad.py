"""
Módulo de trazabilidad local para Patito S.A.

Registra cada interacción del sistema en formato JSONL.

La trazabilidad permite conservar:

- Identificador de la interacción.
- Fecha y hora.
- Thread de conversación.
- Consulta del usuario.
- Respuesta final.
- Agentes utilizados.
- Tools utilizadas.
- Fuentes documentales.
- Chunks recuperados.
- Latencia.
- Estado.
- Errores.

Este módulo no utiliza Gemini y no consume cuota de la API.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DIRECTORIO_TRAZABILIDAD = (
    BASE_DIR
    / "outputs"
    / "trazabilidad"
)

ARCHIVO_TRAZABILIDAD = (
    DIRECTORIO_TRAZABILIDAD
    / "interacciones.jsonl"
)


# Ecuador continental utiliza UTC-5.
ZONA_HORARIA_ECUADOR = timezone(
    timedelta(hours=-5)
)


# Relación entre tools y agentes.
MAPA_TOOLS_AGENTES = {
    "delegar_catalogo": "catalogo",
    "delegar_politicas": "politicas",
    "delegar_crm": "crm",
    "delegar_accion": "accion",
    "consultar_catalogo": "catalogo",
    "consultar_politicas": "politicas",
    "consultar_crm": "crm",
    "registrar_oportunidad": "accion",
}


# ============================================================
# FUNCIONES GENERALES
# ============================================================

def obtener_timestamp() -> str:
    """
    Obtiene la fecha y hora actual de Ecuador.

    Returns:
        str:
            Fecha en formato ISO 8601.
    """

    return datetime.now(
        ZONA_HORARIA_ECUADOR
    ).isoformat(
        timespec="seconds"
    )


def generar_trace_id() -> str:
    """
    Genera un identificador único para la interacción.

    Ejemplo:
        TRACE-20260718-223015-A1B2C3
    """

    ahora = datetime.now(
        ZONA_HORARIA_ECUADOR
    )

    componente_fecha = ahora.strftime(
        "%Y%m%d-%H%M%S"
    )

    componente_unico = (
        uuid4().hex[:6].upper()
    )

    return (
        f"TRACE-{componente_fecha}-"
        f"{componente_unico}"
    )


def lista_unica(
    elementos: list[str],
) -> list[str]:
    """
    Elimina valores repetidos conservando el orden.
    """

    vistos = set()
    resultado = []

    for elemento in elementos:
        elemento_limpio = str(
            elemento
        ).strip()

        if (
            elemento_limpio
            and elemento_limpio not in vistos
        ):
            vistos.add(
                elemento_limpio
            )

            resultado.append(
                elemento_limpio
            )

    return resultado


# ============================================================
# PROTECCIÓN DE DATOS SENSIBLES
# ============================================================

def sanitizar_texto(
    texto: str | None,
) -> str:
    """
    Oculta posibles credenciales dentro del texto.

    La función protege principalmente:

    - Claves con prefijo AIza.
    - Variables GOOGLE_API_KEY.
    - Tokens enviados mediante Bearer.

    No reemplaza una política completa de protección de datos,
    pero reduce el riesgo de guardar credenciales por accidente.
    """

    if texto is None:
        return ""

    texto_seguro = str(texto)

    patrones_reemplazos = [
        (
            r"AIza[A-Za-z0-9_\-]{20,}",
            "[GOOGLE_API_KEY_OCULTA]",
        ),
        (
            (
                r"(?i)(GOOGLE_API_KEY\s*[:=]\s*)"
                r"[^\s,;]+"
            ),
            r"\1[OCULTA]",
        ),
        (
            (
                r"(?i)(Bearer\s+)"
                r"[A-Za-z0-9._\-]+"
            ),
            r"\1[TOKEN_OCULTO]",
        ),
    ]

    for patron, reemplazo in patrones_reemplazos:
        texto_seguro = re.sub(
            patron,
            reemplazo,
            texto_seguro,
        )

    return texto_seguro


# ============================================================
# EXTRACCIÓN DE AGENTES
# ============================================================

def inferir_agentes(
    tools_utilizadas: list[str],
) -> list[str]:
    """
    Identifica los agentes involucrados a partir de las tools.
    """

    agentes = []

    for nombre_tool in tools_utilizadas:
        agente = MAPA_TOOLS_AGENTES.get(
            nombre_tool
        )

        if agente:
            agentes.append(
                agente
            )

    return lista_unica(
        agentes
    )


# ============================================================
# EXTRACCIÓN DE FUENTES Y CHUNKS
# ============================================================

def extraer_fuentes(
    resultados_tools: list[str],
) -> list[str]:
    """
    Extrae nombres de archivos TXT de los resultados
    devueltos por las tools.
    """

    contenido = "\n".join(
        str(resultado)
        for resultado in resultados_tools
    )

    patron_fuente = (
        r"[A-Za-z0-9_ÁÉÍÓÚáéíóúÑñ\-]+\.txt"
    )

    fuentes = re.findall(
        patron_fuente,
        contenido,
    )

    return lista_unica(
        fuentes
    )


def extraer_chunks(
    resultados_tools: list[str],
) -> list[str]:
    """
    Extrae identificadores de chunks escritos en diferentes
    formatos.

    Formatos reconocidos:

    CHUNK_ID: 1
    CHUNK_ID: catalogo-chunk-1
    Chunk 2
    Chunks: 1, 2, 3
    """

    contenido = "\n".join(
        str(resultado)
        for resultado in resultados_tools
    )

    chunks = []

    # Formato: CHUNK_ID: valor
    coincidencias_chunk_id = re.findall(
        r"CHUNK_ID\s*:\s*([A-Za-z0-9_\-]+)",
        contenido,
        flags=re.IGNORECASE,
    )

    chunks.extend(
        coincidencias_chunk_id
    )

    # Formato: Chunk 1
    coincidencias_chunk_simple = re.findall(
        r"\bChunk\s+([A-Za-z0-9_\-]+)",
        contenido,
        flags=re.IGNORECASE,
    )

    chunks.extend(
        coincidencias_chunk_simple
    )

    # Formato: Chunks: 1, 2, 3
    coincidencias_chunks_lista = re.findall(
        r"\bChunks?\s*:\s*([0-9,\s]+)",
        contenido,
        flags=re.IGNORECASE,
    )

    for coincidencia in coincidencias_chunks_lista:
        valores = re.findall(
            r"\d+",
            coincidencia,
        )

        chunks.extend(
            valores
        )

    return lista_unica(
        chunks
    )


# ============================================================
# CONSTRUCCIÓN DEL REGISTRO
# ============================================================

def crear_registro_trazabilidad(
    thread_id: str,
    consulta: str,
    respuesta: str,
    tools_utilizadas: list[str] | None = None,
    resultados_tools: list[str] | None = None,
    latencia_segundos: float = 0.0,
    estado: str = "OK",
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Construye el registro completo de una interacción.

    Args:
        thread_id:
            Identificador de la conversación.

        consulta:
            Mensaje recibido del usuario.

        respuesta:
            Respuesta final del sistema.

        tools_utilizadas:
            Tools llamadas durante la interacción.

        resultados_tools:
            Contenido devuelto por las tools.

        latencia_segundos:
            Tiempo total de ejecución.

        estado:
            Resultado general. Ejemplos:
            OK, ERROR, RECHAZADA o PENDIENTE.

        error:
            Mensaje de error, cuando exista.

        metadata:
            Información adicional opcional.

    Returns:
        dict:
            Registro listo para guardarse como JSON.
    """

    tools = lista_unica(
        tools_utilizadas or []
    )

    resultados = [
        str(resultado)
        for resultado in (
            resultados_tools or []
        )
    ]

    agentes = inferir_agentes(
        tools
    )

    fuentes = extraer_fuentes(
        resultados
    )

    chunks = extraer_chunks(
        resultados
    )

    estado_normalizado = (
        str(estado).strip().upper()
        or "DESCONOCIDO"
    )

    registro = {
        "schema_version": "1.0",
        "trace_id": generar_trace_id(),
        "timestamp": obtener_timestamp(),
        "thread_id": sanitizar_texto(
            thread_id
        ),
        "consulta": sanitizar_texto(
            consulta
        ),
        "respuesta": sanitizar_texto(
            respuesta
        ),
        "agentes_utilizados": agentes,
        "tools_utilizadas": tools,
        "fuentes": fuentes,
        "chunks": chunks,
        "latencia_segundos": round(
            max(
                float(latencia_segundos),
                0.0,
            ),
            4,
        ),
        "estado": estado_normalizado,
        "error": (
            sanitizar_texto(error)
            if error
            else None
        ),
        "metadata": metadata or {},
    }

    return registro


# ============================================================
# PERSISTENCIA
# ============================================================

def guardar_traza(
    registro: dict[str, Any],
    ruta_archivo: Path = ARCHIVO_TRAZABILIDAD,
) -> None:
    """
    Agrega una interacción al archivo JSONL.
    """

    ruta_archivo.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with ruta_archivo.open(
        mode="a",
        encoding="utf-8",
    ) as archivo:
        archivo.write(
            json.dumps(
                registro,
                ensure_ascii=False,
                sort_keys=True,
            )
        )

        archivo.write("\n")


def registrar_interaccion(
    thread_id: str,
    consulta: str,
    respuesta: str,
    tools_utilizadas: list[str] | None = None,
    resultados_tools: list[str] | None = None,
    latencia_segundos: float = 0.0,
    estado: str = "OK",
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
    ruta_archivo: Path = ARCHIVO_TRAZABILIDAD,
) -> dict[str, Any]:
    """
    Construye y guarda una interacción.

    Returns:
        dict:
            Registro que fue almacenado.
    """

    registro = crear_registro_trazabilidad(
        thread_id=thread_id,
        consulta=consulta,
        respuesta=respuesta,
        tools_utilizadas=tools_utilizadas,
        resultados_tools=resultados_tools,
        latencia_segundos=latencia_segundos,
        estado=estado,
        error=error,
        metadata=metadata,
    )

    guardar_traza(
        registro=registro,
        ruta_archivo=ruta_archivo,
    )

    return registro


# ============================================================
# LECTURA DE TRAZAS
# ============================================================

def leer_trazas(
    ruta_archivo: Path = ARCHIVO_TRAZABILIDAD,
) -> list[dict[str, Any]]:
    """
    Lee todos los registros válidos del archivo.

    Las líneas dañadas se ignoran para evitar que un registro
    incorrecto impida revisar el resto de la trazabilidad.
    """

    if not ruta_archivo.exists():
        return []

    registros = []

    with ruta_archivo.open(
        mode="r",
        encoding="utf-8",
    ) as archivo:
        for numero_linea, linea in enumerate(
            archivo,
            start=1,
        ):
            linea_limpia = linea.strip()

            if not linea_limpia:
                continue

            try:
                registro = json.loads(
                    linea_limpia
                )

                if isinstance(registro, dict):
                    registros.append(
                        registro
                    )

            except json.JSONDecodeError:
                print(
                    "Advertencia: se ignoró la línea "
                    f"{numero_linea} de trazabilidad "
                    "porque no contiene JSON válido."
                )

    return registros


def buscar_trazas_por_thread(
    thread_id: str,
    ruta_archivo: Path = ARCHIVO_TRAZABILIDAD,
) -> list[dict[str, Any]]:
    """
    Devuelve únicamente las interacciones de un thread.
    """

    thread_buscado = sanitizar_texto(
        thread_id
    )

    return [
        registro
        for registro in leer_trazas(
            ruta_archivo=ruta_archivo
        )
        if registro.get("thread_id")
        == thread_buscado
    ]