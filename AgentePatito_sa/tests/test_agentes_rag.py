"""
Prueba individual de los tres agentes RAG.

La prueba confirma que:

1. Cada agente responde una consulta de su dominio.
2. Cada agente llama su propia tool.
3. La respuesta final muestra fuentes.
4. No se utilizan herramientas de otros agentes.
"""

import sys
from pathlib import Path
from time import perf_counter


BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.agents.catalogo_agent import (  # noqa: E402
    crear_agente_catalogo,
)

from src.agents.crm_agent import (  # noqa: E402
    crear_agente_crm,
)

from src.agents.politicas_agent import (  # noqa: E402
    crear_agente_politicas,
)

from src.agents.utils import (  # noqa: E402
    extraer_respuesta_final,
    obtener_resultados_tools,
    obtener_tools_utilizadas,
)


CASOS_PRUEBA = {
    "catalogo": {
        "crear_agente": crear_agente_catalogo,
        "consulta": (
            "¿Cuáles son los productos disponibles, "
            "sus precios y sus principales características?"
        ),
        "tool_esperada": "consultar_catalogo",
        "fuente_esperada": (
            "01_Catalogo_Productos_Precios.txt"
        ),
        "tools_prohibidas": [
            "consultar_politicas",
            "consultar_crm",
        ],
    },

    "politicas": {
        "crear_agente": crear_agente_politicas,
        "consulta": (
            "¿Qué descuentos se pueden aplicar y qué "
            "autorización se necesita?"
        ),
        "tool_esperada": "consultar_politicas",
        "fuente_esperada": (
            "02_Politicas_Comerciales_Descuentos_Credito.txt"
        ),
        "tools_prohibidas": [
            "consultar_catalogo",
            "consultar_crm",
        ],
    },

    "crm": {
        "crear_agente": crear_agente_crm,
        "consulta": (
            "¿Cuáles son las etapas del proceso de ventas "
            "y qué información debe registrarse en el CRM?"
        ),
        "tool_esperada": "consultar_crm",
        "fuente_esperada": (
            "03_Proceso_Ventas_CRM.txt"
        ),
        "tools_prohibidas": [
            "consultar_catalogo",
            "consultar_politicas",
        ],
    },
}


def validar_caso(
    nombre_agente: str,
    respuesta: str,
    tools_utilizadas: list[str],
    resultados_tools: list[str],
    tool_esperada: str,
    fuente_esperada: str,
    tools_prohibidas: list[str],
) -> None:
    """
    Valida la respuesta y las herramientas utilizadas.
    """

    if tool_esperada not in tools_utilizadas:
        raise ValueError(
            f"El agente '{nombre_agente}' no utilizó "
            f"la tool requerida: {tool_esperada}."
        )

    for tool_prohibida in tools_prohibidas:
        if tool_prohibida in tools_utilizadas:
            raise ValueError(
                f"El agente '{nombre_agente}' utilizó una "
                f"tool no permitida: {tool_prohibida}."
            )

    if not resultados_tools:
        raise ValueError(
            f"El agente '{nombre_agente}' no recibió "
            "resultados de su herramienta."
        )

    evidencia_completa = "\n".join(
        resultados_tools
    )

    if fuente_esperada not in evidencia_completa:
        raise ValueError(
            f"La evidencia del agente '{nombre_agente}' "
            "no contiene la fuente esperada."
        )

    campos_respuesta = [
        "RESPUESTA:",
        "ADVERTENCIAS:",
        "FUENTES:",
    ]

    for campo in campos_respuesta:
        if campo not in respuesta:
            raise ValueError(
                f"La respuesta del agente '{nombre_agente}' "
                f"no contiene el campo: {campo}"
            )

    if fuente_esperada not in respuesta:
        raise ValueError(
            f"La respuesta final del agente '{nombre_agente}' "
            "no muestra la fuente consultada."
        )


def ejecutar_prueba() -> None:
    """
    Ejecuta una consulta válida sobre cada agente.
    """

    print("=" * 70)
    print("PRUEBA DE AGENTES RAG ESPECIALIZADOS — PATITO S.A.")
    print("=" * 70)

    try:
        for nombre, configuracion in CASOS_PRUEBA.items():
            print("\n" + "-" * 70)
            print(f"AGENTE: {nombre}")
            print(
                f"CONSULTA: "
                f"{configuracion['consulta']}"
            )
            print("-" * 70)

            agente = configuracion[
                "crear_agente"
            ]()

            inicio = perf_counter()

            resultado = agente.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": configuracion[
                                "consulta"
                            ],
                        }
                    ]
                },
                config={
                    "recursion_limit": 8,
                },
            )

            latencia = perf_counter() - inicio

            respuesta = extraer_respuesta_final(
                resultado
            )

            tools_utilizadas = obtener_tools_utilizadas(
                resultado
            )

            resultados_tools = obtener_resultados_tools(
                resultado
            )

            validar_caso(
                nombre_agente=nombre,
                respuesta=respuesta,
                tools_utilizadas=tools_utilizadas,
                resultados_tools=resultados_tools,
                tool_esperada=configuracion[
                    "tool_esperada"
                ],
                fuente_esperada=configuracion[
                    "fuente_esperada"
                ],
                tools_prohibidas=configuracion[
                    "tools_prohibidas"
                ],
            )

            print(
                f"\nTools utilizadas: "
                f"{tools_utilizadas}"
            )

            print("\nRespuesta final:")
            print(respuesta)

            print(
                f"\nLatencia total: "
                f"{latencia:.2f} segundos"
            )

            print("Estado: correcto")

    except Exception as error:
        print("\nERROR DURANTE LA PRUEBA:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 70)
    print("LOS TRES AGENTES RAG FUNCIONARON CORRECTAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_prueba()
    