"""
Prueba de funciones auxiliares de la interfaz.

No utiliza Streamlit, Gemini ni Chroma.
"""

import sys
from pathlib import Path


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.interfaz import (  # noqa: E402
    acortar_identificador,
    crear_mensaje_bienvenida,
    obtener_consultas_ejemplo,
    preparar_resultado_para_ui,
)


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta todas las validaciones de interfaz.
    """

    print("=" * 72)
    print("PRUEBA DE FUNCIONES DE INTERFAZ")
    print("=" * 72)

    try:
        # ----------------------------------------------------
        # CASO 1: MENSAJE DE BIENVENIDA
        # ----------------------------------------------------

        print("\nCASO 1: Mensaje de bienvenida")

        mensaje = crear_mensaje_bienvenida()

        dominios_esperados = [
            "Productos",
            "Descuentos",
            "proceso de ventas",
            "registro",
        ]

        for dominio in dominios_esperados:
            if (
                dominio.casefold()
                not in mensaje.casefold()
            ):
                raise ValueError(
                    "El mensaje de bienvenida no menciona: "
                    f"{dominio}"
                )

        print(
            "Caracteres:",
            len(mensaje),
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 2: RESULTADO EXITOSO
        # ----------------------------------------------------

        print("\nCASO 2: Preparar resultado exitoso")

        resultado_exitoso = {
            "exito": True,
            "estado": "OK",
            "trace_id": "TRACE-PRUEBA-001",
            "latencia_segundos": 4.56789,
            "tools_utilizadas": [
                "delegar_catalogo",
            ],
            "metricas": {
                "llamadas_modelo_estimadas": 2,
                "tokens": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                },
                "tools": {
                    "cantidad_tool_calls": 1,
                },
            },
            "advertencias": [],
            "codigo_error": None,
        }

        resumen_exitoso = (
            preparar_resultado_para_ui(
                resultado=resultado_exitoso
            )
        )

        if (
            resumen_exitoso["estado"]
            != "OK"
        ):
            raise ValueError(
                "El estado exitoso no coincide."
            )

        if (
            resumen_exitoso[
                "estado_etiqueta"
            ]
            != "Completada"
        ):
            raise ValueError(
                "La etiqueta de estado no coincide."
            )

        if (
            resumen_exitoso["total_tokens"]
            != 150
        ):
            raise ValueError(
                "Los tokens no fueron preparados."
            )

        if (
            resumen_exitoso[
                "cantidad_tool_calls"
            ]
            != 1
        ):
            raise ValueError(
                "Las tools no fueron contabilizadas."
            )

        print(
            "Estado:",
            resumen_exitoso[
                "estado_etiqueta"
            ],
        )

        print(
            "Tokens:",
            resumen_exitoso[
                "total_tokens"
            ],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 3: RESULTADO RECHAZADO
        # ----------------------------------------------------

        print("\nCASO 3: Preparar resultado rechazado")

        resultado_rechazado = {
            "exito": True,
            "estado": "RECHAZADA",
            "trace_id": "TRACE-SEGURIDAD-001",
            "latencia_segundos": 0.002,
            "tools_utilizadas": [],
            "metricas": {},
            "advertencias": [
                (
                    "La consulta fue bloqueada antes "
                    "de enviarse al modelo."
                )
            ],
            "codigo_seguridad": (
                "EXTRACCION_CREDENCIALES"
            ),
        }

        resumen_rechazado = (
            preparar_resultado_para_ui(
                resultado=resultado_rechazado
            )
        )

        if (
            resumen_rechazado["estado"]
            != "RECHAZADA"
        ):
            raise ValueError(
                "El rechazo no fue conservado."
            )

        if (
            resumen_rechazado[
                "codigo_seguridad"
            ]
            != "EXTRACCION_CREDENCIALES"
        ):
            raise ValueError(
                "No se conservó el código de seguridad."
            )

        if not resumen_rechazado[
            "advertencias"
        ]:
            raise ValueError(
                "No se conservó la advertencia."
            )

        print(
            "Estado:",
            resumen_rechazado[
                "estado_etiqueta"
            ],
        )

        print(
            "Código:",
            resumen_rechazado[
                "codigo_seguridad"
            ],
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 4: IDENTIFICADOR CORTO
        # ----------------------------------------------------

        print("\nCASO 4: Acortar thread_id")

        thread_largo = (
            "streamlit-"
            "1234567890abcdefghijklmnopqrstuv"
        )

        thread_corto = acortar_identificador(
            identificador=thread_largo,
            maximo=24,
        )

        if len(thread_corto) > 24:
            raise ValueError(
                "El identificador supera el máximo."
            )

        if "..." not in thread_corto:
            raise ValueError(
                "No se agregó el indicador de recorte."
            )

        print(
            "Thread mostrado:",
            thread_corto,
        )

        print("Resultado: correcto")

        # ----------------------------------------------------
        # CASO 5: CONSULTAS DE EJEMPLO
        # ----------------------------------------------------

        print("\nCASO 5: Consultas de ejemplo")

        ejemplos = obtener_consultas_ejemplo()

        if len(ejemplos) != 4:
            raise ValueError(
                "Deben existir cuatro consultas "
                "de ejemplo."
            )

        if (
            "Preparar oportunidad"
            not in ejemplos
        ):
            raise ValueError(
                "Falta el ejemplo de acción."
            )

        print(
            "Ejemplos:",
            len(ejemplos),
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
        "LAS FUNCIONES DE INTERFAZ "
        "FUNCIONARON CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()