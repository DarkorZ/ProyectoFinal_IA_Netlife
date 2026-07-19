"""
Validaciones de límites operativos del sistema.

Este módulo controla parámetros antes de ejecutar el orquestador.

No utiliza Gemini y no consume cuota de la API.
"""

from typing import Any

from src.config import (
    MAX_CONSULTA_CARACTERES,
    RECURSION_LIMIT_DEFAULT,
    RECURSION_LIMIT_MAX,
)


# ============================================================
# RESULTADO DE VALIDACIÓN
# ============================================================

def crear_resultado_limite(
    valido: bool,
    codigo: str,
    detalle: str,
    valor: Any = None,
) -> dict[str, Any]:
    """
    Construye un resultado uniforme de validación.
    """

    return {
        "valido": valido,
        "codigo": codigo,
        "detalle": detalle,
        "valor": valor,
    }


# ============================================================
# LONGITUD DE CONSULTA
# ============================================================

def validar_longitud_consulta(
    consulta: str,
    maximo_caracteres: int = MAX_CONSULTA_CARACTERES,
) -> dict[str, Any]:
    """
    Verifica que la consulta no supere el tamaño permitido.
    """

    if not isinstance(consulta, str):
        return crear_resultado_limite(
            valido=False,
            codigo="TIPO_CONSULTA_INVALIDO",
            detalle=(
                "La consulta debe ser una cadena de texto."
            ),
        )

    consulta_limpia = consulta.strip()

    if not consulta_limpia:
        return crear_resultado_limite(
            valido=False,
            codigo="CONSULTA_VACIA",
            detalle=(
                "La consulta no puede estar vacía."
            ),
            valor=0,
        )

    cantidad_caracteres = len(
        consulta_limpia
    )

    if cantidad_caracteres > maximo_caracteres:
        return crear_resultado_limite(
            valido=False,
            codigo="CONSULTA_DEMASIADO_EXTENSA",
            detalle=(
                "La consulta supera el máximo permitido de "
                f"{maximo_caracteres} caracteres."
            ),
            valor=cantidad_caracteres,
        )

    return crear_resultado_limite(
        valido=True,
        codigo="OK",
        detalle=(
            "La longitud de la consulta es válida."
        ),
        valor=cantidad_caracteres,
    )


# ============================================================
# LÍMITE DE RECURSIÓN
# ============================================================

def validar_recursion_limit(
    recursion_limit: int = RECURSION_LIMIT_DEFAULT,
    maximo_permitido: int = RECURSION_LIMIT_MAX,
) -> dict[str, Any]:
    """
    Verifica que el límite de pasos sea un entero válido.

    No se permiten valores demasiado altos porque podrían ocultar
    un ciclo entre agentes o tools.
    """

    if isinstance(recursion_limit, bool):
        return crear_resultado_limite(
            valido=False,
            codigo="RECURSION_LIMIT_INVALIDO",
            detalle=(
                "recursion_limit debe ser un número entero."
            ),
        )

    if not isinstance(recursion_limit, int):
        return crear_resultado_limite(
            valido=False,
            codigo="RECURSION_LIMIT_INVALIDO",
            detalle=(
                "recursion_limit debe ser un número entero."
            ),
        )

    if recursion_limit < 1:
        return crear_resultado_limite(
            valido=False,
            codigo="RECURSION_LIMIT_MUY_BAJO",
            detalle=(
                "recursion_limit debe ser mayor o igual a 1."
            ),
            valor=recursion_limit,
        )

    if recursion_limit > maximo_permitido:
        return crear_resultado_limite(
            valido=False,
            codigo="RECURSION_LIMIT_MUY_ALTO",
            detalle=(
                "recursion_limit supera el máximo operativo "
                f"permitido de {maximo_permitido}."
            ),
            valor=recursion_limit,
        )

    return crear_resultado_limite(
        valido=True,
        codigo="OK",
        detalle=(
            "El límite de recursión es válido."
        ),
        valor=recursion_limit,
    )


# ============================================================
# VALIDACIÓN COMPLETA
# ============================================================

def validar_limites_ejecucion(
    consulta: str,
    recursion_limit: int = RECURSION_LIMIT_DEFAULT,
) -> dict[str, Any]:
    """
    Ejecuta todas las validaciones operativas previas.
    """

    validacion_consulta = validar_longitud_consulta(
        consulta=consulta
    )

    if not validacion_consulta["valido"]:
        return {
            "valido": False,
            "codigo": validacion_consulta["codigo"],
            "detalle": validacion_consulta["detalle"],
            "longitud_consulta": (
                validacion_consulta["valor"]
            ),
            "recursion_limit": recursion_limit,
        }

    validacion_recursion = validar_recursion_limit(
        recursion_limit=recursion_limit
    )

    if not validacion_recursion["valido"]:
        return {
            "valido": False,
            "codigo": validacion_recursion["codigo"],
            "detalle": validacion_recursion["detalle"],
            "longitud_consulta": (
                validacion_consulta["valor"]
            ),
            "recursion_limit": (
                validacion_recursion["valor"]
            ),
        }

    return {
        "valido": True,
        "codigo": "OK",
        "detalle": (
            "Los límites operativos son válidos."
        ),
        "longitud_consulta": (
            validacion_consulta["valor"]
        ),
        "recursion_limit": (
            validacion_recursion["valor"]
        ),
    }