"""
Utilidades compartidas por los agentes de Patito S.A.
"""

from typing import Any

from langchain_core.messages import AIMessage, ToolMessage


def convertir_contenido_a_texto(
    contenido: Any,
) -> str:
    """
    Convierte el contenido de un mensaje de Gemini en texto.

    Gemini puede devolver un string o una lista de bloques.
    """

    if isinstance(contenido, str):
        return contenido.strip()

    if isinstance(contenido, list):
        partes = []

        for bloque in contenido:
            if isinstance(bloque, str):
                partes.append(bloque)

            elif isinstance(bloque, dict):
                texto = bloque.get("text", "")

                if texto:
                    partes.append(str(texto))

        return "\n".join(partes).strip()

    return str(contenido).strip()


def extraer_respuesta_final(
    resultado_agente: dict,
) -> str:
    """
    Obtiene el último mensaje generado por el modelo.
    """

    mensajes = resultado_agente.get("messages", [])

    for mensaje in reversed(mensajes):
        if isinstance(mensaje, AIMessage):
            texto = convertir_contenido_a_texto(
                mensaje.content
            )

            if texto:
                return texto

    raise ValueError(
        "El agente no devolvió una respuesta final de texto."
    )


def obtener_tools_utilizadas(
    resultado_agente: dict,
) -> list[str]:
    """
    Obtiene los nombres de las tools llamadas por el agente.
    """

    tools = []

    mensajes = resultado_agente.get("messages", [])

    for mensaje in mensajes:
        if isinstance(mensaje, AIMessage):
            llamadas = getattr(
                mensaje,
                "tool_calls",
                [],
            ) or []

            for llamada in llamadas:
                nombre = llamada.get("name")

                if nombre and nombre not in tools:
                    tools.append(nombre)

    return tools


def obtener_resultados_tools(
    resultado_agente: dict,
) -> list[str]:
    """
    Extrae el contenido devuelto por las herramientas.
    """

    resultados = []

    mensajes = resultado_agente.get("messages", [])

    for mensaje in mensajes:
        if isinstance(mensaje, ToolMessage):
            texto = convertir_contenido_a_texto(
                mensaje.content
            )

            resultados.append(texto)

    return resultados