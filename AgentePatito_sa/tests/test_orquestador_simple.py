"""
Prueba de consultas simples del Agente Orquestador.

Se valida que:

1. Una pregunta de catálogo invoque solo Catálogo.
2. Una pregunta de políticas invoque solo Políticas.
3. Una pregunta de CRM invoque solo CRM.
4. La respuesta final incluya agentes y fuentes.
5. Se respete el límite de solicitudes de Gemini Free Tier.
"""

import sys
from pathlib import Path
from time import perf_counter, sleep


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
# CONFIGURACIÓN DE LA PRUEBA
# ============================================================

# Pausa necesaria para respetar el límite gratuito de solicitudes
# por minuto de Gemini.
PAUSA_ENTRE_CASOS = 65


CASOS_SIMPLES = {
    "catalogo": {
        "consulta": (
            "¿Cuáles son los productos disponibles, "
            "sus precios y características principales?"
        ),
        "tool_esperada": "delegar_catalogo",
        "tools_prohibidas": [
            "delegar_politicas",
            "delegar_crm",
        ],
        "agente_esperado": "catalogo",
        "fuente_esperada": (
            "01_Catalogo_Productos_Precios.txt"
        ),
    },

    "politicas": {
        "consulta": (
            "¿Qué descuentos se pueden aplicar y qué "
            "autorizaciones son necesarias?"
        ),
        "tool_esperada": "delegar_politicas",
        "tools_prohibidas": [
            "delegar_catalogo",
            "delegar_crm",
        ],
        "agente_esperado": "politicas",
        "fuente_esperada": (
            "02_Politicas_Comerciales_Descuentos_Credito.txt"
        ),
    },

    "crm": {
        "consulta": (
            "¿Cuáles son las etapas del proceso de ventas "
            "y qué datos se deben registrar en el CRM?"
        ),
        "tool_esperada": "delegar_crm",
        "tools_prohibidas": [
            "delegar_catalogo",
            "delegar_politicas",
        ],
        "agente_esperado": "crm",
        "fuente_esperada": (
            "03_Proceso_Ventas_CRM.txt"
        ),
    },
}


# ============================================================
# VALIDACIÓN
# ============================================================

def validar_respuesta_orquestador(
    nombre_caso: str,
    respuesta: str,
    tools_utilizadas: list[str],
    resultados_tools: list[str],
    configuracion: dict,
) -> None:
    """
    Valida el resultado de una consulta simple.

    Comprueba:

    - Que se invoque la tool esperada.
    - Que no se invoquen tools innecesarias.
    - Que se ejecute el agente especializado correcto.
    - Que aparezca la fuente documental esperada.
    - Que la respuesta final conserve el formato solicitado.
    """

    tool_esperada = configuracion["tool_esperada"]

    if tool_esperada not in tools_utilizadas:
        raise ValueError(
            f"El caso '{nombre_caso}' no utilizó "
            f"la tool esperada: {tool_esperada}."
        )

    for tool_prohibida in configuracion["tools_prohibidas"]:
        if tool_prohibida in tools_utilizadas:
            raise ValueError(
                f"El caso '{nombre_caso}' utilizó una "
                f"tool no necesaria: {tool_prohibida}."
            )

    if not resultados_tools:
        raise ValueError(
            f"El caso '{nombre_caso}' no recibió resultados "
            "de los agentes especializados."
        )

    resultados_completos = "\n".join(
        resultados_tools
    )

    agente_esperado = configuracion[
        "agente_esperado"
    ]

    if (
        f"AGENTE_ESPECIALISTA: {agente_esperado}"
        not in resultados_completos
    ):
        raise ValueError(
            f"No se ejecutó correctamente el agente "
            f"'{agente_esperado}'."
        )

    fuente_esperada = configuracion[
        "fuente_esperada"
    ]

    if fuente_esperada not in resultados_completos:
        raise ValueError(
            "El resultado del especialista no contiene "
            f"la fuente esperada: {fuente_esperada}."
        )

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

    if fuente_esperada not in respuesta:
        raise ValueError(
            "La respuesta final del orquestador no muestra "
            f"la fuente utilizada: {fuente_esperada}."
        )


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta las tres consultas simples.

    Entre cada caso se realiza una pausa para evitar superar
    la cuota gratuita de solicitudes por minuto de Gemini.
    """

    print("=" * 72)
    print("PRUEBA DE ORQUESTADOR — CONSULTAS SIMPLES")
    print("=" * 72)

    try:
        orquestador = crear_orquestador()

        casos = list(
            CASOS_SIMPLES.items()
        )

        for indice, (
            nombre_caso,
            configuracion,
        ) in enumerate(
            casos,
            start=1,
        ):
            print("\n" + "-" * 72)
            print(f"CASO: {nombre_caso}")
            print(
                f"CONSULTA: "
                f"{configuracion['consulta']}"
            )
            print("-" * 72)

            inicio = perf_counter()

            resultado = orquestador.invoke(
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
                    "recursion_limit": 12,
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

            validar_respuesta_orquestador(
                nombre_caso=nombre_caso,
                respuesta=respuesta,
                tools_utilizadas=tools_utilizadas,
                resultados_tools=resultados_tools,
                configuracion=configuracion,
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

            # Solo se espera cuando todavía falta otro caso.
            if indice < len(casos):
                print(
                    "\n" + "." * 72
                )
                print(
                    f"Esperando {PAUSA_ENTRE_CASOS} segundos "
                    "para respetar el límite gratuito de Gemini..."
                )
                print(
                    "." * 72
                )

                sleep(
                    PAUSA_ENTRE_CASOS
                )

    except Exception as error:
        print("\nERROR DURANTE LA PRUEBA:")
        print(
            f"{type(error).__name__}: {error}"
        )
        raise SystemExit(1) from error

    print("\n" + "=" * 72)
    print(
        "LAS CONSULTAS SIMPLES SE ORQUESTARON CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()