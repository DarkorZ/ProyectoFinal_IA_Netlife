"""
Módulo de métricas y monitoreo del sistema multiagente.

Permite analizar:

- Cantidad de mensajes.
- Llamadas al modelo.
- Llamadas a tools.
- Nombres de tools utilizadas.
- Tokens de entrada.
- Tokens de salida.
- Tokens totales.
- Latencia.
- Estados históricos.
- Errores registrados.

Este módulo no realiza llamadas a Gemini.
"""

from collections import Counter
from pathlib import Path
from typing import Any

from langchain_core.messages import (
    AIMessage,
    ToolMessage,
)

from src.config import (
    MAX_TOOL_CALLS_ESPERADAS,
)
from src.trazabilidad import (
    ARCHIVO_TRAZABILIDAD,
    leer_trazas,
)


# ============================================================
# UTILIDADES
# ============================================================

def lista_unica(
    elementos: list[str],
) -> list[str]:
    """
    Elimina duplicados conservando el orden.
    """

    resultado = []
    vistos = set()

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


def obtener_mensajes_resultado(
    resultado: Any,
) -> list[Any]:
    """
    Obtiene los mensajes de una ejecución LangChain.

    Acepta resultados representados como diccionario o como
    objetos que exponen un atributo values.
    """

    if resultado is None:
        return []

    if isinstance(resultado, dict):
        mensajes = resultado.get(
            "messages",
            [],
        )

        return (
            mensajes
            if isinstance(mensajes, list)
            else []
        )

    valores = getattr(
        resultado,
        "values",
        None,
    )

    if isinstance(valores, dict):
        mensajes = valores.get(
            "messages",
            [],
        )

        return (
            mensajes
            if isinstance(mensajes, list)
            else []
        )

    return []


# ============================================================
# TOKENS
# ============================================================

def obtener_usage_metadata(
    mensaje: AIMessage,
) -> dict[str, Any]:
    """
    Obtiene usage_metadata cuando el proveedor lo reporta.

    Se revisa primero el atributo estándar de AIMessage y,
    como respaldo, response_metadata.
    """

    usage_metadata = getattr(
        mensaje,
        "usage_metadata",
        None,
    )

    if isinstance(usage_metadata, dict):
        return usage_metadata

    response_metadata = getattr(
        mensaje,
        "response_metadata",
        None,
    )

    if isinstance(response_metadata, dict):
        uso_respuesta = response_metadata.get(
            "usage_metadata"
        )

        if isinstance(uso_respuesta, dict):
            return uso_respuesta

    return {}


def obtener_entero_seguro(
    valor: Any,
) -> int:
    """
    Convierte un valor numérico a entero de forma segura.
    """

    if isinstance(valor, bool):
        return 0

    if isinstance(valor, int):
        return max(valor, 0)

    if isinstance(valor, float):
        return max(int(valor), 0)

    return 0


def extraer_tokens_resultado(
    resultado: Any,
) -> dict[str, int]:
    """
    Suma los tokens reportados por todos los AIMessage.

    Si el proveedor no devuelve usage_metadata, los valores
    permanecen en cero.
    """

    tokens_entrada = 0
    tokens_salida = 0
    tokens_totales = 0
    mensajes_con_uso = 0

    mensajes = obtener_mensajes_resultado(
        resultado
    )

    for mensaje in mensajes:
        if not isinstance(
            mensaje,
            AIMessage,
        ):
            continue

        uso = obtener_usage_metadata(
            mensaje
        )

        if not uso:
            continue

        mensajes_con_uso += 1

        entrada = obtener_entero_seguro(
            uso.get(
                "input_tokens",
                uso.get("prompt_token_count", 0),
            )
        )

        salida = obtener_entero_seguro(
            uso.get(
                "output_tokens",
                uso.get(
                    "candidates_token_count",
                    0,
                ),
            )
        )

        total_reportado = obtener_entero_seguro(
            uso.get(
                "total_tokens",
                uso.get(
                    "total_token_count",
                    0,
                ),
            )
        )

        if total_reportado == 0:
            total_reportado = (
                entrada + salida
            )

        tokens_entrada += entrada
        tokens_salida += salida
        tokens_totales += total_reportado

    return {
        "input_tokens": tokens_entrada,
        "output_tokens": tokens_salida,
        "total_tokens": tokens_totales,
        "mensajes_con_usage_metadata": (
            mensajes_con_uso
        ),
    }


# ============================================================
# MENSAJES Y TOOLS
# ============================================================

def extraer_tools_resultado(
    resultado: Any,
) -> dict[str, Any]:
    """
    Cuenta las llamadas a tools realizadas durante la ejecución.
    """

    mensajes = obtener_mensajes_resultado(
        resultado
    )

    nombres_tools = []
    cantidad_tool_calls = 0
    cantidad_tool_messages = 0

    for mensaje in mensajes:
        if isinstance(
            mensaje,
            AIMessage,
        ):
            tool_calls = getattr(
                mensaje,
                "tool_calls",
                None,
            )

            if isinstance(tool_calls, list):
                for tool_call in tool_calls:
                    if not isinstance(
                        tool_call,
                        dict,
                    ):
                        continue

                    nombre = tool_call.get(
                        "name"
                    )

                    if nombre:
                        nombres_tools.append(
                            str(nombre)
                        )

                        cantidad_tool_calls += 1

        if isinstance(
            mensaje,
            ToolMessage,
        ):
            cantidad_tool_messages += 1

    return {
        "cantidad_tool_calls": (
            cantidad_tool_calls
        ),
        "cantidad_tool_messages": (
            cantidad_tool_messages
        ),
        "tools_utilizadas": lista_unica(
            nombres_tools
        ),
        "limite_esperado": (
            MAX_TOOL_CALLS_ESPERADAS
        ),
        "supera_limite_esperado": (
            cantidad_tool_calls
            > MAX_TOOL_CALLS_ESPERADAS
        ),
    }


def extraer_metricas_resultado(
    resultado: Any,
    latencia_segundos: float,
) -> dict[str, Any]:
    """
    Construye las métricas completas de una ejecución.
    """

    mensajes = obtener_mensajes_resultado(
        resultado
    )

    cantidad_ai_messages = sum(
        isinstance(mensaje, AIMessage)
        for mensaje in mensajes
    )

    tokens = extraer_tokens_resultado(
        resultado=resultado
    )

    tools = extraer_tools_resultado(
        resultado=resultado
    )

    return {
        "cantidad_mensajes": len(mensajes),
        "llamadas_modelo_estimadas": (
            cantidad_ai_messages
        ),
        "latencia_segundos": round(
            max(
                float(latencia_segundos),
                0.0,
            ),
            4,
        ),
        "tokens": tokens,
        "tools": tools,
    }


# ============================================================
# RESUMEN HISTÓRICO
# ============================================================

def incrementar_contador(
    contador: Counter,
    valores: list[str],
) -> None:
    """
    Incrementa un contador para una lista de valores.
    """

    for valor in valores:
        contador[str(valor)] += 1


def generar_resumen_monitoreo(
    ruta_archivo: Path = ARCHIVO_TRAZABILIDAD,
) -> dict[str, Any]:
    """
    Resume todas las interacciones registradas en trazabilidad.
    """

    trazas = leer_trazas(
        ruta_archivo=ruta_archivo
    )

    if not trazas:
        return {
            "total_interacciones": 0,
            "latencia_promedio_segundos": 0.0,
            "latencia_maxima_segundos": 0.0,
            "tokens_totales": 0,
            "tokens_entrada": 0,
            "tokens_salida": 0,
            "estados": {},
            "agentes": {},
            "tools": {},
            "fuentes": {},
            "codigos_error": {},
        }

    estados = Counter()
    agentes = Counter()
    tools = Counter()
    fuentes = Counter()
    codigos_error = Counter()

    latencias = []

    tokens_entrada = 0
    tokens_salida = 0
    tokens_totales = 0

    for traza in trazas:
        estado = str(
            traza.get(
                "estado",
                "DESCONOCIDO",
            )
        )

        estados[estado] += 1

        incrementar_contador(
            agentes,
            traza.get(
                "agentes_utilizados",
                [],
            ),
        )

        incrementar_contador(
            tools,
            traza.get(
                "tools_utilizadas",
                [],
            ),
        )

        incrementar_contador(
            fuentes,
            traza.get(
                "fuentes",
                [],
            ),
        )

        latencia = traza.get(
            "latencia_segundos",
            0.0,
        )

        if isinstance(
            latencia,
            (int, float),
        ):
            latencias.append(
                max(float(latencia), 0.0)
            )

        metadata = traza.get(
            "metadata",
            {},
        )

        if not isinstance(metadata, dict):
            metadata = {}

        metricas = metadata.get(
            "metricas",
            {},
        )

        if not isinstance(metricas, dict):
            metricas = {}

        tokens = metricas.get(
            "tokens",
            {},
        )

        if isinstance(tokens, dict):
            tokens_entrada += obtener_entero_seguro(
                tokens.get("input_tokens", 0)
            )

            tokens_salida += obtener_entero_seguro(
                tokens.get("output_tokens", 0)
            )

            tokens_totales += obtener_entero_seguro(
                tokens.get("total_tokens", 0)
            )

        codigo_error = metadata.get(
            "codigo_error"
        )

        if codigo_error:
            codigos_error[
                str(codigo_error)
            ] += 1

    latencia_promedio = (
        sum(latencias) / len(latencias)
        if latencias
        else 0.0
    )

    latencia_maxima = (
        max(latencias)
        if latencias
        else 0.0
    )

    return {
        "total_interacciones": len(trazas),
        "latencia_promedio_segundos": round(
            latencia_promedio,
            4,
        ),
        "latencia_maxima_segundos": round(
            latencia_maxima,
            4,
        ),
        "tokens_totales": tokens_totales,
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "estados": dict(estados),
        "agentes": dict(agentes),
        "tools": dict(tools),
        "fuentes": dict(fuentes),
        "codigos_error": dict(
            codigos_error
        ),
    }