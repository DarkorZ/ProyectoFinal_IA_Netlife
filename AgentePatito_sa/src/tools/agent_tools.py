"""
Tools para delegar consultas a los agentes especializados.

Estas herramientas representan el segundo nivel de la arquitectura:

Orquestador
    ↓
Tool de delegación
    ↓
Agente especializado
    ↓
Tool RAG
    ↓
Base Chroma

El orquestador no consulta directamente las bases vectoriales.
"""

from typing import Any, Callable

from langchain.tools import tool

from src.agents.catalogo_agent import crear_agente_catalogo
from src.agents.crm_agent import crear_agente_crm
from src.agents.politicas_agent import crear_agente_politicas
from src.agents.utils import (
    extraer_respuesta_final,
    obtener_resultados_tools,
    obtener_tools_utilizadas,
)


def ejecutar_agente_especializado(
    nombre_agente: str,
    crear_agente: Callable[[], Any],
    consulta: str,
) -> str:
    """
    Ejecuta un agente especializado y devuelve un resultado
    estructurado para el orquestador.

    Args:
        nombre_agente:
            Nombre lógico del especialista.

        crear_agente:
            Función encargada de construir o recuperar el agente.

        consulta:
            Tarea delegada por el orquestador.

    Returns:
        str:
            Respuesta especializada junto con información
            de trazabilidad y evidencia RAG.
    """

    consulta_limpia = consulta.strip()

    if not consulta_limpia:
        return (
            "ESTADO: ERROR_VALIDACION\n"
            f"AGENTE_ESPECIALISTA: {nombre_agente}\n"
            "La consulta delegada no puede estar vacía."
        )

    try:
        agente = crear_agente()

        resultado = agente.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": consulta_limpia,
                    }
                ]
            },
            config={
                "recursion_limit": 8,
            },
        )

        # Respuesta final redactada por el agente especializado.
        respuesta = extraer_respuesta_final(
            resultado_agente=resultado
        )

        # Nombres de las tools RAG utilizadas internamente.
        tools_internas = obtener_tools_utilizadas(
            resultado_agente=resultado
        )

        # Resultados originales devueltos por las tools RAG.
        # Aquí se conservan las fuentes, chunks, distancias
        # y fragmentos recuperados.
        resultados_rag = obtener_resultados_tools(
            resultado_agente=resultado
        )

        tools_texto = (
            ", ".join(tools_internas)
            if tools_internas
            else "ninguna"
        )

        evidencia_rag = (
            "\n\n".join(resultados_rag)
            if resultados_rag
            else "No se obtuvo evidencia documental."
        )

        return (
            "ESTADO: OK\n"
            f"AGENTE_ESPECIALISTA: {nombre_agente}\n"
            f"CONSULTA_DELEGADA: {consulta_limpia}\n"
            f"TOOLS_RAG_UTILIZADAS: {tools_texto}\n"
            "\n"
            "RESPUESTA_ESPECIALISTA:\n"
            f"{respuesta}\n"
            "\n"
            "EVIDENCIA_RAG:\n"
            f"{evidencia_rag}"
        )

    except Exception as error:
        return (
            "ESTADO: ERROR_AGENTE\n"
            f"AGENTE_ESPECIALISTA: {nombre_agente}\n"
            f"TIPO_ERROR: {type(error).__name__}\n"
            f"DETALLE: {error}"
        )


@tool
def delegar_catalogo(consulta: str) -> str:
    """
    Delega una consulta al Agente de Catálogo de Patito S.A.

    Usa esta herramienta cuando la consulta necesite información
    sobre productos, precios, stock, disponibilidad,
    especificaciones o características técnicas.

    No la utilices para descuentos, crédito ni procesos de CRM.

    Args:
        consulta:
            Pregunta específica que debe resolver el especialista
            de catálogo.
    """

    return ejecutar_agente_especializado(
        nombre_agente="catalogo",
        crear_agente=crear_agente_catalogo,
        consulta=consulta,
    )


@tool
def delegar_politicas(consulta: str) -> str:
    """
    Delega una consulta al Agente de Políticas Comerciales.

    Usa esta herramienta cuando la consulta necesite información
    sobre descuentos, niveles de autorización, crédito, pagos,
    devoluciones, garantías o reglas comerciales.

    No la utilices para consultar precios ni procesos de CRM.

    Args:
        consulta:
            Pregunta específica que debe resolver el especialista
            de políticas comerciales.
    """

    return ejecutar_agente_especializado(
        nombre_agente="politicas",
        crear_agente=crear_agente_politicas,
        consulta=consulta,
    )


@tool
def delegar_crm(consulta: str) -> str:
    """
    Delega una consulta al Agente de Proceso de Ventas y CRM.

    Usa esta herramienta cuando la consulta necesite información
    sobre el embudo comercial, etapas de ventas, campos
    obligatorios, registro de oportunidades o procedimientos CRM.

    No la utilices para precios, stock, descuentos o crédito.

    Args:
        consulta:
            Pregunta específica que debe resolver el especialista
            de CRM.
    """

    return ejecutar_agente_especializado(
        nombre_agente="crm",
        crear_agente=crear_agente_crm,
        consulta=consulta,
    )


TOOLS_AGENTES = [
    delegar_catalogo,
    delegar_politicas,
    delegar_crm,
]