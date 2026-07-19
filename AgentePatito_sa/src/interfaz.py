"""
Funciones auxiliares para la interfaz de Patito S.A.

Este módulo prepara resultados para su presentación visual.

No contiene componentes Streamlit y no realiza llamadas a Gemini.
"""

from typing import Any


# ============================================================
# PRESENTACIÓN DE ESTADOS
# ============================================================

PRESENTACION_ESTADOS = {
    "OK": {
        "etiqueta": "Completada",
        "nivel": "success",
    },
    "PENDIENTE": {
        "etiqueta": "Pendiente",
        "nivel": "info",
    },
    "RECHAZADA": {
        "etiqueta": "Rechazada",
        "nivel": "warning",
    },
    "CANCELADA": {
        "etiqueta": "Cancelada",
        "nivel": "warning",
    },
    "DUPLICADO": {
        "etiqueta": "Registro duplicado",
        "nivel": "warning",
    },
    "ERROR": {
        "etiqueta": "Error",
        "nivel": "error",
    },
    "ERROR_VALIDACION": {
        "etiqueta": "Error de validación",
        "nivel": "error",
    },
}


# ============================================================
# MENSAJE INICIAL
# ============================================================

def crear_mensaje_bienvenida() -> str:
    """
    Construye el mensaje inicial del asistente.
    """

    return (
        "Bienvenido al Asistente Comercial de Patito S.A.\n\n"
        "Puedo ayudarte con:\n\n"
        "- Productos, precios, stock y características.\n"
        "- Descuentos, crédito y políticas comerciales.\n"
        "- Etapas y requisitos del proceso de ventas.\n"
        "- Preparación y registro controlado de oportunidades.\n\n"
        "Para registrar una oportunidad, primero presentaré un "
        "resumen y solicitaré confirmación explícita."
    )


# ============================================================
# IDENTIFICADORES
# ============================================================

def acortar_identificador(
    identificador: str | None,
    maximo: int = 36,
) -> str:
    """
    Acorta un identificador conservando inicio y final.

    Ejemplo:

        streamlit-1234567890abcdefghijklmnop

    puede mostrarse como:

        streamlit-123456...klmnop
    """

    if not identificador:
        return "No disponible"

    texto = str(
        identificador
    ).strip()

    if len(texto) <= maximo:
        return texto

    caracteres_finales = 8

    caracteres_iniciales = (
        maximo
        - caracteres_finales
        - 3
    )

    return (
        f"{texto[:caracteres_iniciales]}"
        f"..."
        f"{texto[-caracteres_finales:]}"
    )


# ============================================================
# RESULTADOS PARA LA INTERFAZ
# ============================================================

def preparar_resultado_para_ui(
    resultado: dict[str, Any],
) -> dict[str, Any]:
    """
    Extrae únicamente información serializable y útil para UI.

    Se evita guardar resultado_crudo en session_state porque
    puede contener objetos internos de LangChain.
    """

    metricas = resultado.get(
        "metricas",
        {},
    )

    if not isinstance(metricas, dict):
        metricas = {}

    tokens = metricas.get(
        "tokens",
        {},
    )

    if not isinstance(tokens, dict):
        tokens = {}

    metricas_tools = metricas.get(
        "tools",
        {},
    )

    if not isinstance(metricas_tools, dict):
        metricas_tools = {}

    tools_utilizadas = resultado.get(
        "tools_utilizadas",
        [],
    )

    if not isinstance(
        tools_utilizadas,
        list,
    ):
        tools_utilizadas = []

    advertencias = resultado.get(
        "advertencias",
        [],
    )

    if not isinstance(
        advertencias,
        list,
    ):
        advertencias = []

    estado = str(
        resultado.get(
            "estado",
            "DESCONOCIDO",
        )
    ).upper()

    presentacion = PRESENTACION_ESTADOS.get(
        estado,
        {
            "etiqueta": estado,
            "nivel": "info",
        },
    )

    return {
        "estado": estado,
        "estado_etiqueta": (
            presentacion["etiqueta"]
        ),
        "estado_nivel": (
            presentacion["nivel"]
        ),
        "exito": bool(
            resultado.get(
                "exito",
                False,
            )
        ),
        "trace_id": resultado.get(
            "trace_id"
        ),
        "latencia_segundos": round(
            float(
                resultado.get(
                    "latencia_segundos",
                    0.0,
                )
                or 0.0
            ),
            4,
        ),
        "tools_utilizadas": [
            str(nombre)
            for nombre in tools_utilizadas
        ],
        "cantidad_tool_calls": int(
            metricas_tools.get(
                "cantidad_tool_calls",
                len(tools_utilizadas),
            )
            or 0
        ),
        "llamadas_modelo_estimadas": int(
            metricas.get(
                "llamadas_modelo_estimadas",
                0,
            )
            or 0
        ),
        "input_tokens": int(
            tokens.get(
                "input_tokens",
                0,
            )
            or 0
        ),
        "output_tokens": int(
            tokens.get(
                "output_tokens",
                0,
            )
            or 0
        ),
        "total_tokens": int(
            tokens.get(
                "total_tokens",
                0,
            )
            or 0
        ),
        "advertencias": [
            str(advertencia)
            for advertencia in advertencias
        ],
        "codigo_error": resultado.get(
            "codigo_error"
        ),
        "codigo_seguridad": resultado.get(
            "codigo_seguridad"
        ),
        "reintentable": resultado.get(
            "reintentable"
        ),
    }


# ============================================================
# CONSULTAS DE EJEMPLO
# ============================================================

def obtener_consultas_ejemplo() -> dict[str, str]:
    """
    Devuelve consultas rápidas para la barra lateral.
    """

    return {
        "Consultar catálogo": (
            "¿Cuáles son los productos disponibles, sus precios "
            "y sus características principales?"
        ),
        "Consultar descuentos": (
            "¿Qué descuentos pueden aplicarse y qué "
            "autorizaciones se requieren?"
        ),
        "Consultar CRM": (
            "¿Cuáles son las etapas del proceso de ventas y qué "
            "datos deben registrarse en el CRM?"
        ),
        "Preparar oportunidad": (
            "Quiero registrar una oportunidad para Empresa ABC."
        ),
    }