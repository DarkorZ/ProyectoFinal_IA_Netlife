"""
Prueba de consulta combinada del Agente Orquestador.

La consulta incluye información perteneciente a:

1. Catálogo.
2. Políticas Comerciales.
3. Proceso de Ventas y CRM.

El orquestador debe detectar los tres dominios, ejecutar los
tres agentes especializados y consolidar sus respuestas.
"""

import sys
from pathlib import Path
from time import perf_counter


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.agents.orchestrator import (  # noqa: E402
    crear_orquestador,
)

from src.agents.utils import (  # noqa: E402
    extraer_respuesta_final,
    obtener_resultados_tools,
    obtener_tools_utilizadas,
)


# ============================================================
# CASO DE PRUEBA
# ============================================================

CONSULTA_MIXTA = """
Un cliente desea adquirir productos de Patito S.A.

Primero, necesito conocer los productos disponibles, sus precios
y sus características principales.

También necesito saber qué descuentos pueden aplicarse, qué
autorizaciones se requieren y cuáles son las condiciones de crédito.

Finalmente, indica cuáles son las etapas del proceso de ventas
y qué datos deben registrarse en el CRM.
""".strip()


TOOLS_ESPERADAS = {
    "delegar_catalogo",
    "delegar_politicas",
    "delegar_crm",
}


AGENTES_ESPERADOS = {
    "catalogo",
    "politicas",
    "crm",
}


FUENTES_ESPERADAS = {
    "01_Catalogo_Productos_Precios.txt",
    "02_Politicas_Comerciales_Descuentos_Credito.txt",
    "03_Proceso_Ventas_CRM.txt",
}


# ============================================================
# VALIDACIONES
# ============================================================

def validar_tools(
    tools_utilizadas: list[str],
) -> None:
    """
    Verifica que el orquestador haya invocado los tres
    agentes especializados.
    """

    conjunto_tools = set(tools_utilizadas)

    tools_faltantes = (
        TOOLS_ESPERADAS - conjunto_tools
    )

    if tools_faltantes:
        raise ValueError(
            "El orquestador no utilizó todas las tools "
            f"necesarias. Faltaron: "
            f"{sorted(tools_faltantes)}"
        )


def validar_resultados_especialistas(
    resultados_tools: list[str],
) -> None:
    """
    Verifica que las tools de delegación hayan ejecutado
    correctamente los especialistas y conservado sus fuentes.
    """

    if not resultados_tools:
        raise ValueError(
            "El orquestador no recibió resultados "
            "de los agentes especializados."
        )

    resultados_completos = "\n".join(
        resultados_tools
    )

    for agente in AGENTES_ESPERADOS:
        identificador = (
            f"AGENTE_ESPECIALISTA: {agente}"
        )

        if identificador not in resultados_completos:
            raise ValueError(
                "No se encontró la ejecución del agente: "
                f"{agente}"
            )

    for fuente in FUENTES_ESPERADAS:
        if fuente not in resultados_completos:
            raise ValueError(
                "La evidencia de los especialistas no contiene "
                f"la fuente esperada: {fuente}"
            )

    if "EVIDENCIA_RAG:" not in resultados_completos:
        raise ValueError(
            "Las tools de delegación no conservaron "
            "la evidencia RAG."
        )

    if "CHUNK_ID:" not in resultados_completos:
        raise ValueError(
            "Los resultados no contienen identificadores "
            "de fragmentos."
        )


def validar_respuesta_final(
    respuesta: str,
) -> None:
    """
    Verifica la estructura y trazabilidad de la respuesta
    consolidada.
    """

    campos_obligatorios = [
        "RESPUESTA_FINAL:",
        "AGENTES_UTILIZADOS:",
        "FUENTES:",
        "ADVERTENCIAS:",
    ]

    for campo in campos_obligatorios:
        if campo not in respuesta:
            raise ValueError(
                f"La respuesta final no contiene: {campo}"
            )

    agentes_visibles = [
        "Catálogo",
        "Políticas",
        "CRM",
    ]

    for agente in agentes_visibles:
        if agente.lower() not in respuesta.lower():
            raise ValueError(
                "La respuesta final no identifica al agente: "
                f"{agente}"
            )

    for fuente in FUENTES_ESPERADAS:
        if fuente not in respuesta:
            raise ValueError(
                "La respuesta consolidada no muestra "
                f"la fuente: {fuente}"
            )


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta y valida una consulta combinada.
    """

    print("=" * 72)
    print("PRUEBA DE ORQUESTADOR — CONSULTA COMBINADA")
    print("=" * 72)

    print("\nConsulta:")
    print(CONSULTA_MIXTA)

    try:
        orquestador = crear_orquestador()

        inicio = perf_counter()

        resultado = orquestador.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": CONSULTA_MIXTA,
                    }
                ]
            },
            config={
                "recursion_limit": 18,
            },
        )

        latencia = (
            perf_counter() - inicio
        )

        respuesta = extraer_respuesta_final(
            resultado_agente=resultado
        )

        tools_utilizadas = obtener_tools_utilizadas(
            resultado_agente=resultado
        )

        resultados_tools = obtener_resultados_tools(
            resultado_agente=resultado
        )

        validar_tools(
            tools_utilizadas=tools_utilizadas
        )

        validar_resultados_especialistas(
            resultados_tools=resultados_tools
        )

        validar_respuesta_final(
            respuesta=respuesta
        )

        print(
            f"\nTools utilizadas: "
            f"{tools_utilizadas}"
        )

        print("\nRespuesta consolidada:")
        print(respuesta)

        print(
            f"\nLatencia total: "
            f"{latencia:.2f} segundos"
        )

    except Exception as error:
        print("\nERROR DURANTE LA PRUEBA:")
        print(
            f"{type(error).__name__}: {error}"
        )
        raise SystemExit(1) from error

    print("\n" + "=" * 72)
    print(
        "LA CONSULTA COMBINADA SE ORQUESTÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()