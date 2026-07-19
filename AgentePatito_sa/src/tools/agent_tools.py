"""
Tools para delegar consultas a los agentes especializados.

Estas herramientas representan el segundo nivel de la arquitectura:

Orquestador
    ↓
Tool de delegación
    ↓
Agente especializado
    ↓
Tool interna
    ↓
Base Chroma o archivo de salida

El orquestador no consulta directamente las bases vectoriales
ni escribe directamente en archivos.
"""

from typing import Any, Callable

from langchain.tools import tool

from src.agents.accion_agent import crear_agente_accion
from src.agents.catalogo_agent import crear_agente_catalogo
from src.agents.crm_agent import crear_agente_crm
from src.agents.politicas_agent import crear_agente_politicas
from src.agents.utils import (
    extraer_respuesta_final,
    obtener_resultados_tools,
    obtener_tools_utilizadas,
)


# ============================================================
# EJECUCIÓN DE AGENTES RAG
# ============================================================

def ejecutar_agente_especializado(
    nombre_agente: str,
    crear_agente: Callable[[], Any],
    consulta: str,
) -> str:
    """
    Ejecuta un agente RAG especializado.

    Esta función se utiliza para:

    - Catálogo.
    - Políticas Comerciales.
    - CRM.

    Conserva tanto la respuesta redactada por el agente como
    la evidencia original recuperada desde la tool RAG.
    """

    consulta_limpia = consulta.strip()

    if not consulta_limpia:
        return (
            "ESTADO: ERROR_VALIDACION\n"
            f"AGENTE_ESPECIALISTA: {nombre_agente}\n"
            "DETALLE: La consulta delegada no puede estar vacía."
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

        respuesta = extraer_respuesta_final(
            resultado_agente=resultado
        )

        tools_internas = obtener_tools_utilizadas(
            resultado_agente=resultado
        )

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


# ============================================================
# EJECUCIÓN DEL AGENTE DE ACCIÓN
# ============================================================

def ejecutar_agente_accion(
    consulta_actual: str,
    contexto_previo: str = "",
) -> str:
    """
    Ejecuta el Agente de Acción.

    El contexto previo permite conservar el resumen presentado
    antes de que el usuario confirme o cancele el registro.

    Args:
        consulta_actual:
            Mensaje actual del usuario.

        contexto_previo:
            Respuesta previa del sistema relacionada con el
            registro. Normalmente contiene RESUMEN_PENDIENTE y
            CONFIRMACION_REQUERIDA.

    Returns:
        Resultado estructurado del Agente de Acción.
    """

    consulta_limpia = consulta_actual.strip()
    contexto_limpio = contexto_previo.strip()

    if not consulta_limpia:
        return (
            "ESTADO: ERROR_VALIDACION\n"
            "AGENTE_ESPECIALISTA: accion\n"
            "DETALLE: La consulta actual no puede estar vacía."
        )

    try:
        agente = crear_agente_accion()

        mensajes = []

        # Cuando existe un resumen previo, se envía como un
        # mensaje anterior del asistente. De esta forma el
        # Agente de Acción puede comprobar que la confirmación
        # ocurrió después de presentar los datos.
        if contexto_limpio:
            mensajes.append(
                {
                    "role": "assistant",
                    "content": contexto_limpio,
                }
            )

        mensajes.append(
            {
                "role": "user",
                "content": consulta_limpia,
            }
        )

        resultado = agente.invoke(
            {
                "messages": mensajes,
            },
            config={
                "recursion_limit": 12,
            },
        )

        respuesta = extraer_respuesta_final(
            resultado_agente=resultado
        )

        tools_internas = obtener_tools_utilizadas(
            resultado_agente=resultado
        )

        resultados_internos = obtener_resultados_tools(
            resultado_agente=resultado
        )

        tools_texto = (
            ", ".join(tools_internas)
            if tools_internas
            else "ninguna"
        )

        resultados_texto = (
            "\n\n".join(resultados_internos)
            if resultados_internos
            else "No se ejecutaron tools internas."
        )

        return (
            "ESTADO: OK\n"
            "AGENTE_ESPECIALISTA: accion\n"
            f"CONSULTA_ACTUAL: {consulta_limpia}\n"
            f"CONTEXTO_PREVIO_RECIBIDO: "
            f"{'sí' if contexto_limpio else 'no'}\n"
            f"TOOLS_ACCION_UTILIZADAS: {tools_texto}\n"
            "\n"
            "RESPUESTA_ESPECIALISTA:\n"
            f"{respuesta}\n"
            "\n"
            "RESULTADOS_ACCION:\n"
            f"{resultados_texto}"
        )

    except Exception as error:
        return (
            "ESTADO: ERROR_AGENTE\n"
            "AGENTE_ESPECIALISTA: accion\n"
            f"TIPO_ERROR: {type(error).__name__}\n"
            f"DETALLE: {error}"
        )


# ============================================================
# TOOLS RAG PARA EL ORQUESTADOR
# ============================================================

@tool
def delegar_catalogo(consulta: str) -> str:
    """
    Delega una consulta al Agente de Catálogo de Patito S.A.

    Utiliza esta herramienta para consultar productos, precios,
    stock, disponibilidad, especificaciones o características.

    No la utilices para descuentos, crédito, CRM ni registros.
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

    Utiliza esta herramienta para consultar descuentos,
    autorizaciones, crédito, pagos, devoluciones, garantías
    o reglas comerciales.

    No la utilices para precios, CRM ni registros.
    """

    return ejecutar_agente_especializado(
        nombre_agente="politicas",
        crear_agente=crear_agente_politicas,
        consulta=consulta,
    )


@tool
def delegar_crm(consulta: str) -> str:
    """
    Delega una consulta informativa al Agente de CRM.

    Utiliza esta herramienta para consultar etapas del embudo,
    campos obligatorios, procedimientos y requisitos del CRM.

    No la utilices para registrar o guardar una oportunidad.
    Para ejecutar un registro utiliza delegar_accion.
    """

    return ejecutar_agente_especializado(
        nombre_agente="crm",
        crear_agente=crear_agente_crm,
        consulta=consulta,
    )


# ============================================================
# TOOL DE ACCIÓN PARA EL ORQUESTADOR
# ============================================================

@tool
def delegar_accion(
    consulta_actual: str,
    contexto_previo: str = "",
) -> str:
    """
    Delega una solicitud al Agente de Acción.

    Utiliza esta herramienta cuando el usuario quiera preparar,
    confirmar, cancelar o registrar una oportunidad comercial.

    Para una solicitud inicial:

    - Coloca el mensaje actual en consulta_actual.
    - Utiliza una cadena vacía en contexto_previo.

    Para una confirmación o cancelación posterior:

    - Coloca la confirmación actual en consulta_actual.
    - Copia en contexto_previo el resumen de registro presentado
      anteriormente al usuario.

    No utilices esta herramienta para consultar información
    documental sobre catálogo, políticas o CRM.
    """

    return ejecutar_agente_accion(
        consulta_actual=consulta_actual,
        contexto_previo=contexto_previo,
    )


TOOLS_AGENTES = [
    delegar_catalogo,
    delegar_politicas,
    delegar_crm,
    delegar_accion,
]