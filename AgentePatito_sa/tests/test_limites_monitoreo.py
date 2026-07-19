"""
Prueba de límites operativos y monitoreo.

No utiliza Gemini.

Se valida:

1. Consulta válida.
2. Consulta demasiado extensa.
3. recursion_limit válido.
4. recursion_limit demasiado alto.
5. Extracción de tokens.
6. Conteo de llamadas al modelo.
7. Conteo de tools.
8. Resumen histórico de trazabilidad.
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
    RECURSION_LIMIT_MAX,
)

from src.limites import (  # noqa: E402
    validar_limites_ejecucion,
    validar_longitud_consulta,
    validar_recursion_limit,
)

from src.monitoreo import (  # noqa: E402
    extraer_metricas_resultado,
    generar_resumen_monitoreo,
)

from src.trazabilidad import (  # noqa: E402
    registrar_interaccion,
)


# ============================================================
# RESULTADO FICTICIO
# ============================================================

def crear_resultado_ficticio() -> dict:
    """
    Construye una ejecución con tokens y una tool.
    """

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
                        "id": "tool-call-monitor-1",
                        "type": "tool_call",
                    }
                ],
                usage_metadata={
                    "input_tokens": 120,
                    "output_tokens": 20,
                    "total_tokens": 140,
                },
            ),
            ToolMessage(
                content=(
                    "FUENTE: "
                    "01_Catalogo_Productos_Precios.txt\n"
                    "CHUNK_ID: 1"
                ),
                tool_call_id="tool-call-monitor-1",
            ),
            AIMessage(
                content=(
                    "RESPUESTA_FINAL:\n"
                    "Patito Pro 2026 cuesta USD 1,299."
                ),
                usage_metadata={
                    "input_tokens": 180,
                    "output_tokens": 40,
                    "total_tokens": 220,
                },
            ),
        ]
    }


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta todas las validaciones.
    """

    print("=" * 72)
    print("PRUEBA DE LÍMITES Y MONITOREO")
    print("=" * 72)

    try:
        # ----------------------------------------------------
        # CASO 1: CONSULTA VÁLIDA
        # ----------------------------------------------------

        print("\nCASO 1: Consulta válida")

        consulta_valida = (
            "¿Cuáles son los productos disponibles?"
        )

        validacion_consulta = (
            validar_longitud_consulta(
                consulta=consulta_valida
            )
        )

        if not validacion_consulta["valido"]:
            raise ValueError(
                "Una consulta normal fue rechazada."
            )

        print(
            "Caracteres:",
            validacion_consulta["valor"],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 2: CONSULTA EXTENSA
        # ----------------------------------------------------

        print("\nCASO 2: Consulta demasiado extensa")

        consulta_extensa = (
            "A" * (
                MAX_CONSULTA_CARACTERES + 1
            )
        )

        validacion_extensa = (
            validar_longitud_consulta(
                consulta=consulta_extensa
            )
        )

        if validacion_extensa["valido"]:
            raise ValueError(
                "La consulta extensa fue aceptada."
            )

        if (
            validacion_extensa["codigo"]
            != "CONSULTA_DEMASIADO_EXTENSA"
        ):
            raise ValueError(
                "La consulta extensa recibió "
                "un código incorrecto."
            )

        print(
            "Código:",
            validacion_extensa["codigo"],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 3: RECURSIÓN VÁLIDA
        # ----------------------------------------------------

        print("\nCASO 3: recursion_limit válido")

        validacion_recursion = (
            validar_recursion_limit(
                recursion_limit=20
            )
        )

        if not validacion_recursion["valido"]:
            raise ValueError(
                "El límite 20 fue rechazado."
            )

        print(
            "Valor:",
            validacion_recursion["valor"],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 4: RECURSIÓN DEMASIADO ALTA
        # ----------------------------------------------------

        print("\nCASO 4: recursion_limit demasiado alto")

        validacion_recursion_alta = (
            validar_recursion_limit(
                recursion_limit=(
                    RECURSION_LIMIT_MAX + 1
                )
            )
        )

        if validacion_recursion_alta["valido"]:
            raise ValueError(
                "El límite excesivo fue aceptado."
            )

        if (
            validacion_recursion_alta["codigo"]
            != "RECURSION_LIMIT_MUY_ALTO"
        ):
            raise ValueError(
                "El código de recursión no coincide."
            )

        print(
            "Código:",
            validacion_recursion_alta[
                "codigo"
            ],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 5: VALIDACIÓN COMPLETA
        # ----------------------------------------------------

        print("\nCASO 5: Validación completa")

        validacion_completa = (
            validar_limites_ejecucion(
                consulta=consulta_valida,
                recursion_limit=20,
            )
        )

        if not validacion_completa["valido"]:
            raise ValueError(
                "Los límites válidos fueron rechazados."
            )

        print(
            "Longitud:",
            validacion_completa[
                "longitud_consulta"
            ],
        )

        print(
            "Recursion limit:",
            validacion_completa[
                "recursion_limit"
            ],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 6: MÉTRICAS DE RESULTADO
        # ----------------------------------------------------

        print("\nCASO 6: Extracción de métricas")

        resultado_ficticio = (
            crear_resultado_ficticio()
        )

        metricas = extraer_metricas_resultado(
            resultado=resultado_ficticio,
            latencia_segundos=4.56789,
        )

        if (
            metricas[
                "llamadas_modelo_estimadas"
            ]
            != 2
        ):
            raise ValueError(
                "No se contaron las dos llamadas "
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
                "El total de tokens no coincide."
            )

        if (
            metricas["tools"][
                "cantidad_tool_calls"
            ]
            != 1
        ):
            raise ValueError(
                "No se contó la llamada a la tool."
            )

        if (
            metricas["tools"]["tools_utilizadas"]
            != ["delegar_catalogo"]
        ):
            raise ValueError(
                "No se identificó la tool."
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
            "Tools:",
            metricas["tools"][
                "tools_utilizadas"
            ],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 7: RESUMEN HISTÓRICO
        # ----------------------------------------------------

        print("\nCASO 7: Resumen histórico")

        with TemporaryDirectory() as directorio:
            ruta_trazas = (
                Path(directorio)
                / "monitoreo.jsonl"
            )

            registrar_interaccion(
                thread_id="thread-monitor-1",
                consulta="Consulta 1",
                respuesta="Respuesta 1",
                tools_utilizadas=[
                    "delegar_catalogo",
                ],
                resultados_tools=[
                    (
                        "FUENTE: "
                        "01_Catalogo_Productos_Precios.txt\n"
                        "CHUNK_ID: 1"
                    )
                ],
                latencia_segundos=4.5,
                estado="OK",
                metadata={
                    "metricas": metricas,
                },
                ruta_archivo=ruta_trazas,
            )

            registrar_interaccion(
                thread_id="thread-monitor-2",
                consulta="Consulta 2",
                respuesta="ERROR_CONTROLADO",
                tools_utilizadas=[],
                resultados_tools=[],
                latencia_segundos=1.5,
                estado="ERROR",
                error="Error ficticio",
                metadata={
                    "codigo_error": "ERROR_PRUEBA",
                    "metricas": {
                        "tokens": {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "total_tokens": 0,
                        }
                    },
                },
                ruta_archivo=ruta_trazas,
            )

            resumen = generar_resumen_monitoreo(
                ruta_archivo=ruta_trazas
            )

            if resumen["total_interacciones"] != 2:
                raise ValueError(
                    "El resumen no contiene "
                    "dos interacciones."
                )

            if resumen["tokens_totales"] != 360:
                raise ValueError(
                    "El resumen no acumuló los tokens."
                )

            if resumen["estados"] != {
                "OK": 1,
                "ERROR": 1,
            }:
                raise ValueError(
                    "Los estados históricos "
                    "no coinciden."
                )

            if (
                resumen["codigos_error"]
                != {"ERROR_PRUEBA": 1}
            ):
                raise ValueError(
                    "No se contabilizó el código "
                    "de error."
                )

            print(
                "Interacciones:",
                resumen["total_interacciones"],
            )

            print(
                "Latencia promedio:",
                resumen[
                    "latencia_promedio_segundos"
                ],
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
        "LOS LÍMITES Y EL MONITOREO "
        "FUNCIONARON CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()