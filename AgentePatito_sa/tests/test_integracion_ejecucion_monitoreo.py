"""
Prueba de integración entre:

- Límites operativos.
- Ejecutor central.
- Extracción de métricas.
- Advertencias.
- Trazabilidad.
- Resumen histórico.

Esta prueba no utiliza Gemini.
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.config import (  # noqa: E402
    MAX_CONSULTA_CARACTERES,
    MAX_TOOL_CALLS_ESPERADAS,
    RECURSION_LIMIT_MAX,
)

from src.ejecucion import (  # noqa: E402
    ejecutar_consulta_orquestador,
)

from src.monitoreo import (  # noqa: E402
    generar_resumen_monitoreo,
)

from src.trazabilidad import (  # noqa: E402
    leer_trazas,
)


# ============================================================
# ORQUESTADOR FICTICIO CON MÉTRICAS
# ============================================================

class OrquestadorConMetricas:
    """
    Simula una ejecución correcta con tokens y una tool.
    """

    def invoke(
        self,
        entrada,
        config=None,
    ):
        return {
            "messages": [
                HumanMessage(
                    content=(
                        "¿Cuánto cuesta Patito Pro 2026?"
                    )
                ),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "delegar_catalogo",
                            "args": {
                                "consulta": (
                                    "Precio de Patito Pro 2026"
                                )
                            },
                            "id": "tool-integracion-1",
                            "type": "tool_call",
                        }
                    ],
                    usage_metadata={
                        "input_tokens": 100,
                        "output_tokens": 20,
                        "total_tokens": 120,
                    },
                ),
                ToolMessage(
                    content=(
                        "ESTADO: OK\n"
                        "AGENTE_ESPECIALISTA: catalogo\n"
                        "EVIDENCIA_RAG:\n"
                        "FUENTE: "
                        "01_Catalogo_Productos_Precios.txt\n"
                        "CHUNK_ID: 1"
                    ),
                    tool_call_id="tool-integracion-1",
                ),
                AIMessage(
                    content=(
                        "RESPUESTA_FINAL:\n"
                        "Patito Pro 2026 cuesta USD 1,299.\n"
                        "\n"
                        "AGENTES_UTILIZADOS:\n"
                        "- Agente de Catálogo\n"
                        "\n"
                        "FUENTES:\n"
                        "- 01_Catalogo_Productos_Precios.txt\n"
                        "- CHUNK_ID: 1\n"
                        "\n"
                        "ADVERTENCIAS:\n"
                        "Ninguna"
                    ),
                    usage_metadata={
                        "input_tokens": 200,
                        "output_tokens": 40,
                        "total_tokens": 240,
                    },
                ),
            ]
        }


class OrquestadorMuchasTools:
    """
    Simula una ejecución con más tool calls de las esperadas.
    """

    def invoke(
        self,
        entrada,
        config=None,
    ):
        tool_calls = []
        tool_messages = []

        cantidad_llamadas = (
            MAX_TOOL_CALLS_ESPERADAS + 1
        )

        for indice in range(
            cantidad_llamadas
        ):
            tool_id = (
                f"tool-exceso-{indice}"
            )

            tool_calls.append(
                {
                    "name": "delegar_catalogo",
                    "args": {
                        "consulta": (
                            f"Consulta repetida {indice}"
                        )
                    },
                    "id": tool_id,
                    "type": "tool_call",
                }
            )

            tool_messages.append(
                ToolMessage(
                    content=(
                        "FUENTE: "
                        "01_Catalogo_Productos_Precios.txt\n"
                        f"CHUNK_ID: {indice + 1}"
                    ),
                    tool_call_id=tool_id,
                )
            )

        return {
            "messages": [
                HumanMessage(
                    content="Consulta con exceso de tools."
                ),
                AIMessage(
                    content="",
                    tool_calls=tool_calls,
                    usage_metadata={
                        "input_tokens": 50,
                        "output_tokens": 10,
                        "total_tokens": 60,
                    },
                ),
                *tool_messages,
                AIMessage(
                    content=(
                        "RESPUESTA_FINAL:\n"
                        "Respuesta ficticia.\n"
                        "\n"
                        "AGENTES_UTILIZADOS:\n"
                        "- Agente de Catálogo\n"
                        "\n"
                        "FUENTES:\n"
                        "- 01_Catalogo_Productos_Precios.txt\n"
                        "\n"
                        "ADVERTENCIAS:\n"
                        "Ninguna"
                    ),
                    usage_metadata={
                        "input_tokens": 100,
                        "output_tokens": 20,
                        "total_tokens": 120,
                    },
                ),
            ]
        }


class OrquestadorNoDebeEjecutarse:
    """
    Produce un error si el ejecutor intenta invocarlo.

    Se utiliza para demostrar que los límites se validan antes
    de llamar al orquestador.
    """

    def invoke(
        self,
        entrada,
        config=None,
    ):
        raise AssertionError(
            "El orquestador no debía ejecutarse."
        )


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta todas las validaciones.
    """

    print("=" * 72)
    print("PRUEBA DE INTEGRACIÓN — EJECUCIÓN Y MONITOREO")
    print("=" * 72)

    try:
        with TemporaryDirectory() as directorio:
            ruta_trazas = (
                Path(directorio)
                / "integracion.jsonl"
            )

            # ------------------------------------------------
            # CASO 1: EJECUCIÓN CON MÉTRICAS
            # ------------------------------------------------

            print("\nCASO 1: Ejecución con métricas")

            resultado = ejecutar_consulta_orquestador(
                consulta=(
                    "¿Cuánto cuesta Patito Pro 2026?"
                ),
                thread_id="thread-metricas",
                con_memoria=False,
                orquestador=OrquestadorConMetricas(),
                ruta_trazabilidad=ruta_trazas,
            )

            if not resultado["exito"]:
                raise ValueError(
                    "La ejecución correcta fue marcada "
                    "como error."
                )

            if resultado["estado"] != "OK":
                raise ValueError(
                    "El estado no es OK."
                )

            metricas = resultado["metricas"]

            if (
                metricas[
                    "llamadas_modelo_estimadas"
                ]
                != 2
            ):
                raise ValueError(
                    "No se contabilizaron las llamadas "
                    "al modelo."
                )

            if (
                metricas["tokens"]["input_tokens"]
                != 300
            ):
                raise ValueError(
                    "Los tokens de entrada no coinciden."
                )

            if (
                metricas["tokens"]["output_tokens"]
                != 60
            ):
                raise ValueError(
                    "Los tokens de salida no coinciden."
                )

            if (
                metricas["tokens"]["total_tokens"]
                != 360
            ):
                raise ValueError(
                    "Los tokens totales no coinciden."
                )

            if (
                metricas["tools"][
                    "cantidad_tool_calls"
                ]
                != 1
            ):
                raise ValueError(
                    "No se contó la tool utilizada."
                )

            if resultado["advertencias"]:
                raise ValueError(
                    "No debían existir advertencias "
                    "en la ejecución normal."
                )

            print(
                "Llamadas al modelo:",
                metricas[
                    "llamadas_modelo_estimadas"
                ],
            )

            print(
                "Tokens totales:",
                metricas["tokens"]["total_tokens"],
            )

            print(
                "Tool calls:",
                metricas["tools"][
                    "cantidad_tool_calls"
                ],
            )

            print(
                "Trace ID:",
                resultado["trace_id"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 2: CONSULTA DEMASIADO EXTENSA
            # ------------------------------------------------

            print("\nCASO 2: Consulta demasiado extensa")

            resultado_extenso = (
                ejecutar_consulta_orquestador(
                    consulta=(
                        "A"
                        * (
                            MAX_CONSULTA_CARACTERES
                            + 1
                        )
                    ),
                    thread_id="thread-extenso",
                    con_memoria=False,
                    orquestador=(
                        OrquestadorNoDebeEjecutarse()
                    ),
                    ruta_trazabilidad=ruta_trazas,
                )
            )

            if (
                resultado_extenso["codigo_error"]
                != "CONSULTA_DEMASIADO_EXTENSA"
            ):
                raise ValueError(
                    "La consulta extensa no fue "
                    "clasificada correctamente."
                )

            if resultado_extenso["exito"]:
                raise ValueError(
                    "La consulta extensa fue aceptada."
                )

            print(
                "Código:",
                resultado_extenso["codigo_error"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 3: RECURSION LIMIT EXCESIVO
            # ------------------------------------------------

            print("\nCASO 3: recursion_limit excesivo")

            resultado_recursion = (
                ejecutar_consulta_orquestador(
                    consulta="Consulta válida.",
                    thread_id="thread-recursion",
                    con_memoria=False,
                    recursion_limit=(
                        RECURSION_LIMIT_MAX + 1
                    ),
                    orquestador=(
                        OrquestadorNoDebeEjecutarse()
                    ),
                    ruta_trazabilidad=ruta_trazas,
                )
            )

            if (
                resultado_recursion["codigo_error"]
                != "RECURSION_LIMIT_MUY_ALTO"
            ):
                raise ValueError(
                    "El recursion_limit excesivo no fue "
                    "clasificado correctamente."
                )

            print(
                "Código:",
                resultado_recursion[
                    "codigo_error"
                ],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 4: EXCESO DE TOOLS
            # ------------------------------------------------

            print("\nCASO 4: Advertencia por exceso de tools")

            resultado_tools = (
                ejecutar_consulta_orquestador(
                    consulta=(
                        "Consulta ficticia con muchas tools."
                    ),
                    thread_id="thread-tools",
                    con_memoria=False,
                    orquestador=OrquestadorMuchasTools(),
                    ruta_trazabilidad=ruta_trazas,
                )
            )

            cantidad_tools = (
                resultado_tools["metricas"]["tools"][
                    "cantidad_tool_calls"
                ]
            )

            if (
                cantidad_tools
                != MAX_TOOL_CALLS_ESPERADAS + 1
            ):
                raise ValueError(
                    "No se contó correctamente "
                    "el exceso de tools."
                )

            if not resultado_tools["advertencias"]:
                raise ValueError(
                    "No se generó la advertencia "
                    "por exceso de tools."
                )

            if not resultado_tools["metricas"][
                "tools"
            ]["supera_limite_esperado"]:
                raise ValueError(
                    "La métrica no identificó "
                    "el límite superado."
                )

            print(
                "Tool calls:",
                cantidad_tools,
            )

            print(
                "Advertencias:",
                resultado_tools["advertencias"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 5: TRAZABILIDAD Y RESUMEN
            # ------------------------------------------------

            print("\nCASO 5: Resumen histórico integrado")

            trazas = leer_trazas(
                ruta_archivo=ruta_trazas
            )

            if len(trazas) != 4:
                raise ValueError(
                    "Deben existir cuatro trazas."
                )

            primera_metadata = trazas[0].get(
                "metadata",
                {},
            )

            if (
                "metricas"
                not in primera_metadata
            ):
                raise ValueError(
                    "La trazabilidad no contiene "
                    "las métricas."
                )

            resumen = generar_resumen_monitoreo(
                ruta_archivo=ruta_trazas
            )

            if resumen["total_interacciones"] != 4:
                raise ValueError(
                    "El resumen no contiene "
                    "cuatro interacciones."
                )

            if resumen["tokens_totales"] != 540:
                raise ValueError(
                    "El resumen no acumuló correctamente "
                    "los tokens."
                )

            estados_esperados = {
                "OK": 2,
                "ERROR_VALIDACION": 2,
            }

            if resumen["estados"] != estados_esperados:
                raise ValueError(
                    "Los estados históricos no coinciden. "
                    f"Obtenidos: {resumen['estados']}"
                )

            print(
                "Interacciones:",
                resumen["total_interacciones"],
            )

            print(
                "Tokens acumulados:",
                resumen["tokens_totales"],
            )

            print(
                "Estados:",
                resumen["estados"],
            )

            print("Resultado: correcto")

    except Exception as error:
        print("\nERROR DURANTE LA PRUEBA:")
        print(
            f"{type(error).__name__}: {error}"
        )

        raise SystemExit(1) from error

    print("\n" + "=" * 72)
    print(
        "LA INTEGRACIÓN DE LÍMITES Y MONITOREO "
        "FUNCIONÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()