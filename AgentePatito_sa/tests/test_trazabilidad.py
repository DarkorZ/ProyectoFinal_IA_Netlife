"""
Prueba del módulo de trazabilidad local.

Esta prueba no utiliza Gemini.

Se valida:

1. Creación de un registro exitoso.
2. Extracción de agentes.
3. Extracción de fuentes.
4. Extracción de chunks.
5. Registro de latencia.
6. Protección de credenciales.
7. Registro de errores.
8. Escritura de varias líneas JSONL.
9. Filtrado por thread_id.
"""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.trazabilidad import (  # noqa: E402
    buscar_trazas_por_thread,
    leer_trazas,
    registrar_interaccion,
)


# ============================================================
# DATOS DE PRUEBA
# ============================================================

THREAD_PRINCIPAL = "thread-trazabilidad-001"

THREAD_SECUNDARIO = "thread-trazabilidad-002"


RESULTADO_TOOL_CATALOGO = """
ESTADO: OK
AGENTE_ESPECIALISTA: catalogo
TOOLS_RAG_UTILIZADAS: consultar_catalogo

EVIDENCIA_RAG:

<fragmento>
FUENTE: 01_Catalogo_Productos_Precios.txt
CHUNK_ID: 1
CONTENIDO:
Patito Pro 2026 tiene un precio de USD 1,299.
</fragmento>

<fragmento>
FUENTE: 01_Catalogo_Productos_Precios.txt
CHUNK_ID: 2
CONTENIDO:
Patito Lite 2026 tiene un precio de USD 649.
</fragmento>
""".strip()


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta todas las validaciones de trazabilidad.
    """

    print("=" * 72)
    print("PRUEBA DE TRAZABILIDAD LOCAL")
    print("=" * 72)

    try:
        with TemporaryDirectory() as directorio:
            ruta_temporal = (
                Path(directorio)
                / "interacciones_prueba.jsonl"
            )

            # ------------------------------------------------
            # CASO 1: INTERACCIÓN EXITOSA
            # ------------------------------------------------

            print("\nCASO 1: Registrar interacción exitosa")

            registro_exitoso = registrar_interaccion(
                thread_id=THREAD_PRINCIPAL,
                consulta=(
                    "¿Cuánto cuesta Patito Pro 2026? "
                    "GOOGLE_API_KEY=AIzaClavePrueba"
                    "12345678901234567890"
                ),
                respuesta=(
                    "RESPUESTA_FINAL: "
                    "Patito Pro 2026 cuesta USD 1,299."
                ),
                tools_utilizadas=[
                    "delegar_catalogo",
                ],
                resultados_tools=[
                    RESULTADO_TOOL_CATALOGO,
                ],
                latencia_segundos=8.25678,
                estado="OK",
                metadata={
                    "origen": "prueba",
                },
                ruta_archivo=ruta_temporal,
            )

            if not ruta_temporal.exists():
                raise FileNotFoundError(
                    "No se creó el archivo de trazabilidad."
                )

            if (
                registro_exitoso["estado"]
                != "OK"
            ):
                raise ValueError(
                    "El estado exitoso no fue registrado."
                )

            if (
                registro_exitoso[
                    "agentes_utilizados"
                ]
                != ["catalogo"]
            ):
                raise ValueError(
                    "No se identificó correctamente "
                    "el Agente de Catálogo."
                )

            if (
                registro_exitoso["fuentes"]
                != [
                    "01_Catalogo_Productos_Precios.txt"
                ]
            ):
                raise ValueError(
                    "La fuente no fue extraída "
                    "correctamente."
                )

            if set(
                registro_exitoso["chunks"]
            ) != {"1", "2"}:
                raise ValueError(
                    "Los chunks no fueron extraídos "
                    "correctamente."
                )

            if (
                registro_exitoso[
                    "latencia_segundos"
                ]
                != 8.2568
            ):
                raise ValueError(
                    "La latencia no fue redondeada "
                    "correctamente."
                )

            if (
                "AIza"
                in registro_exitoso["consulta"]
            ):
                raise ValueError(
                    "La clave de prueba no fue ocultada."
                )

            if (
                "[OCULTA]"
                not in registro_exitoso["consulta"]
                and
                "[GOOGLE_API_KEY_OCULTA]"
                not in registro_exitoso["consulta"]
            ):
                raise ValueError(
                    "No se encontró el marcador de "
                    "credencial oculta."
                )

            print(
                "Trace ID:",
                registro_exitoso["trace_id"],
            )

            print(
                "Agentes:",
                registro_exitoso[
                    "agentes_utilizados"
                ],
            )

            print(
                "Fuentes:",
                registro_exitoso["fuentes"],
            )

            print(
                "Chunks:",
                registro_exitoso["chunks"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 2: INTERACCIÓN CON ERROR
            # ------------------------------------------------

            print("\nCASO 2: Registrar interacción con error")

            registro_error = registrar_interaccion(
                thread_id=THREAD_SECUNDARIO,
                consulta=(
                    "Consulta que produjo un error."
                ),
                respuesta="",
                tools_utilizadas=[],
                resultados_tools=[],
                latencia_segundos=1.5,
                estado="ERROR",
                error=(
                    "429 RESOURCE_EXHAUSTED "
                    "GOOGLE_API_KEY=AIzaOtraClave"
                    "12345678901234567890"
                ),
                metadata={
                    "tipo": "cuota",
                },
                ruta_archivo=ruta_temporal,
            )

            if (
                registro_error["estado"]
                != "ERROR"
            ):
                raise ValueError(
                    "El error no fue registrado "
                    "con el estado correcto."
                )

            if not registro_error["error"]:
                raise ValueError(
                    "No se almacenó el detalle del error."
                )

            if (
                "AIza"
                in registro_error["error"]
            ):
                raise ValueError(
                    "La credencial del error no fue "
                    "ocultada."
                )

            print(
                "Trace ID:",
                registro_error["trace_id"],
            )

            print(
                "Estado:",
                registro_error["estado"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 3: VALIDAR ARCHIVO JSONL
            # ------------------------------------------------

            print("\nCASO 3: Validar archivo JSONL")

            lineas = ruta_temporal.read_text(
                encoding="utf-8"
            ).splitlines()

            if len(lineas) != 2:
                raise ValueError(
                    "El archivo debe contener "
                    "dos interacciones."
                )

            for linea in lineas:
                registro = json.loads(
                    linea
                )

                if not isinstance(
                    registro,
                    dict,
                ):
                    raise ValueError(
                        "Una línea no contiene "
                        "un objeto JSON."
                    )

            registros = leer_trazas(
                ruta_archivo=ruta_temporal
            )

            if len(registros) != 2:
                raise ValueError(
                    "No se leyeron los dos registros."
                )

            print(
                "Interacciones encontradas:",
                len(registros),
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 4: FILTRO POR THREAD
            # ------------------------------------------------

            print("\nCASO 4: Filtrar por thread_id")

            trazas_principales = (
                buscar_trazas_por_thread(
                    thread_id=THREAD_PRINCIPAL,
                    ruta_archivo=ruta_temporal,
                )
            )

            if len(trazas_principales) != 1:
                raise ValueError(
                    "El filtro del thread principal "
                    "no devolvió un único registro."
                )

            if (
                trazas_principales[0][
                    "thread_id"
                ]
                != THREAD_PRINCIPAL
            ):
                raise ValueError(
                    "El filtro devolvió otro thread."
                )

            print(
                "Trazas del thread principal:",
                len(trazas_principales),
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
        "LA TRAZABILIDAD LOCAL FUNCIONÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()