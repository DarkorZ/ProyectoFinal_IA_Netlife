"""
Prueba del ejecutor central del orquestador.

No utiliza Gemini.

Se validan:

1. Ejecución exitosa.
2. Extracción de tools y evidencia.
3. Clasificación de respuesta pendiente.
4. Validación de consultas vacías.
5. Manejo de cuota diaria agotada.
6. Registro automático de trazabilidad.
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.messages import (
    AIMessage,
    ToolMessage,
)


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.ejecucion import (  # noqa: E402
    ejecutar_consulta_orquestador,
)

from src.trazabilidad import (  # noqa: E402
    leer_trazas,
)


# ============================================================
# ORQUESTADORES FICTICIOS
# ============================================================

class OrquestadorExitoso:
    """
    Simula una ejecución correcta del orquestador.
    """

    def invoke(
        self,
        entrada,
        config=None,
    ):
        return {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "delegar_catalogo",
                            "args": {
                                "consulta": (
                                    "¿Cuánto cuesta "
                                    "Patito Pro 2026?"
                                )
                            },
                            "id": "tool-call-1",
                            "type": "tool_call",
                        }
                    ],
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
                    tool_call_id="tool-call-1",
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
                    )
                ),
            ]
        }


class OrquestadorPendiente:
    """
    Simula un registro pendiente de confirmación.
    """

    def invoke(
        self,
        entrada,
        config=None,
    ):
        return {
            "messages": [
                AIMessage(
                    content=(
                        "RESUMEN_PENDIENTE:\n"
                        "- Cliente: Empresa Demo\n"
                        "\n"
                        "CONFIRMACION_REQUERIDA:\n"
                        "Responde CONFIRMO EL REGISTRO."
                    )
                )
            ]
        }


class OrquestadorConError:
    """
    Simula una cuota diaria agotada.
    """

    def invoke(
        self,
        entrada,
        config=None,
    ):
        raise RuntimeError(
            "429 RESOURCE_EXHAUSTED "
            "GenerateRequestsPerDayPerProjectPerModel-FreeTier "
            "GOOGLE_API_KEY=AIzaClaveQueNoDebeGuardarse"
            "12345678901234567890"
        )


# ============================================================
# EJECUCIÓN DE LA PRUEBA
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta todas las validaciones.
    """

    print("=" * 72)
    print("PRUEBA DE EJECUCIÓN CONTROLADA")
    print("=" * 72)

    try:
        with TemporaryDirectory() as directorio:
            ruta_trazas = (
                Path(directorio)
                / "ejecuciones.jsonl"
            )

            # ------------------------------------------------
            # CASO 1: EJECUCIÓN EXITOSA
            # ------------------------------------------------

            print("\nCASO 1: Ejecución exitosa")

            resultado_exitoso = (
                ejecutar_consulta_orquestador(
                    consulta=(
                        "¿Cuánto cuesta Patito Pro 2026?"
                    ),
                    thread_id="thread-exitoso",
                    con_memoria=False,
                    orquestador=OrquestadorExitoso(),
                    ruta_trazabilidad=ruta_trazas,
                )
            )

            if not resultado_exitoso["exito"]:
                raise ValueError(
                    "La ejecución exitosa fue marcada "
                    "como error."
                )

            if resultado_exitoso["estado"] != "OK":
                raise ValueError(
                    "El estado exitoso no es OK."
                )

            if (
                resultado_exitoso[
                    "tools_utilizadas"
                ]
                != ["delegar_catalogo"]
            ):
                raise ValueError(
                    "No se extrajo la tool utilizada."
                )

            if not resultado_exitoso["trace_id"]:
                raise ValueError(
                    "No se generó trace_id."
                )

            print(
                "Estado:",
                resultado_exitoso["estado"],
            )

            print(
                "Tools:",
                resultado_exitoso[
                    "tools_utilizadas"
                ],
            )

            print(
                "Trace ID:",
                resultado_exitoso["trace_id"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 2: RESPUESTA PENDIENTE
            # ------------------------------------------------

            print("\nCASO 2: Respuesta pendiente")

            resultado_pendiente = (
                ejecutar_consulta_orquestador(
                    consulta=(
                        "Prepara una oportunidad comercial."
                    ),
                    thread_id="thread-pendiente",
                    con_memoria=False,
                    orquestador=OrquestadorPendiente(),
                    ruta_trazabilidad=ruta_trazas,
                )
            )

            if (
                resultado_pendiente["estado"]
                != "PENDIENTE"
            ):
                raise ValueError(
                    "La confirmación pendiente no fue "
                    "clasificada correctamente."
                )

            if not resultado_pendiente["exito"]:
                raise ValueError(
                    "Una operación pendiente no debe "
                    "considerarse un error técnico."
                )

            print(
                "Estado:",
                resultado_pendiente["estado"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 3: CONSULTA VACÍA
            # ------------------------------------------------

            print("\nCASO 3: Validación de consulta vacía")

            resultado_vacio = (
                ejecutar_consulta_orquestador(
                    consulta="   ",
                    thread_id="thread-vacio",
                    con_memoria=False,
                    orquestador=OrquestadorExitoso(),
                    ruta_trazabilidad=ruta_trazas,
                )
            )

            if (
                resultado_vacio["estado"]
                != "ERROR_VALIDACION"
            ):
                raise ValueError(
                    "La consulta vacía no fue rechazada."
                )

            if resultado_vacio["exito"]:
                raise ValueError(
                    "La consulta vacía fue marcada "
                    "como exitosa."
                )

            print(
                "Código:",
                resultado_vacio["codigo_error"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 4: CUOTA DIARIA
            # ------------------------------------------------

            print("\nCASO 4: Error de cuota diaria")

            resultado_error = (
                ejecutar_consulta_orquestador(
                    consulta=(
                        "Consulta que produce cuota agotada."
                    ),
                    thread_id="thread-error",
                    con_memoria=False,
                    orquestador=OrquestadorConError(),
                    ruta_trazabilidad=ruta_trazas,
                )
            )

            if resultado_error["exito"]:
                raise ValueError(
                    "El error fue marcado como exitoso."
                )

            if (
                resultado_error["codigo_error"]
                != "CUOTA_DIARIA_AGOTADA"
            ):
                raise ValueError(
                    "La cuota diaria no fue clasificada."
                )

            if resultado_error["reintentable"]:
                raise ValueError(
                    "Una cuota diaria agotada no debe "
                    "marcarse como reintentable."
                )

            if (
                "CUOTA_DIARIA_AGOTADA"
                not in resultado_error["respuesta"]
            ):
                raise ValueError(
                    "La respuesta no contiene el código "
                    "de error controlado."
                )

            print(
                "Código:",
                resultado_error["codigo_error"],
            )

            print(
                "Reintentable:",
                resultado_error["reintentable"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 5: TRAZABILIDAD AUTOMÁTICA
            # ------------------------------------------------

            print("\nCASO 5: Trazabilidad automática")

            trazas = leer_trazas(
                ruta_archivo=ruta_trazas
            )

            if len(trazas) != 4:
                raise ValueError(
                    "Deben existir cuatro trazas."
                )

            estados = [
                traza["estado"]
                for traza in trazas
            ]

            estados_esperados = [
                "OK",
                "PENDIENTE",
                "ERROR_VALIDACION",
                "ERROR",
            ]

            if estados != estados_esperados:
                raise ValueError(
                    "Los estados almacenados no coinciden. "
                    f"Obtenidos: {estados}"
                )

            ultima_traza = trazas[-1]

            if (
                "AIza"
                in str(ultima_traza["error"])
            ):
                raise ValueError(
                    "La credencial del error no fue "
                    "ocultada en la trazabilidad."
                )

            print(
                "Trazas encontradas:",
                len(trazas),
            )

            print(
                "Estados:",
                estados,
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
        "LA EJECUCIÓN CONTROLADA FUNCIONÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()