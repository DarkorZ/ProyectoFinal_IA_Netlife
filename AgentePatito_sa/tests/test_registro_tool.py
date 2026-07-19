"""
Prueba de la herramienta determinística de registro.

No utiliza Gemini ni consume cuota de la API.

Se valida:

1. Que no se escriba sin confirmación.
2. Que se registre una oportunidad confirmada.
3. Que se genere un identificador.
4. Que se registre fecha y hora.
5. Que el archivo tenga contenido válido.
6. Que se detecten duplicados.
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


from src.tools.registro_tool import (  # noqa: E402
    EntradaRegistroOportunidad,
    registrar_oportunidad_en_archivo,
)


# ============================================================
# DATOS DE PRUEBA
# ============================================================

def crear_datos_prueba(
    confirmado: bool,
) -> EntradaRegistroOportunidad:
    """
    Construye una oportunidad ficticia para las pruebas.
    """

    return EntradaRegistroOportunidad(
        cliente="Empresa Demo S.A.",
        contacto="ventas@empresademo.com",
        productos=[
            "Patito Pro 2026",
        ],
        cantidad_total=2,
        monto_estimado=2598.00,
        etapa="Propuesta/Cotización",
        proxima_accion=(
            "Enviar la cotización formal al cliente"
        ),
        vendedor="Vendedor de Prueba",
        descuento=10.0,
        condicion_pago="Contado",
        confirmado=confirmado,
    )


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta todas las validaciones sobre un archivo temporal.
    """

    print("=" * 72)
    print("PRUEBA DE TOOL — REGISTRO DE OPORTUNIDADES")
    print("=" * 72)

    try:
        with TemporaryDirectory() as directorio_temporal:
            ruta_temporal = (
                Path(directorio_temporal)
                / "oportunidades_prueba.txt"
            )

            # ------------------------------------------------
            # CASO 1: SIN CONFIRMACIÓN
            # ------------------------------------------------

            print("\nCASO 1: Registro sin confirmación")

            datos_sin_confirmacion = crear_datos_prueba(
                confirmado=False
            )

            resultado_sin_confirmacion = (
                registrar_oportunidad_en_archivo(
                    datos=datos_sin_confirmacion,
                    ruta_archivo=ruta_temporal,
                )
            )

            if (
                resultado_sin_confirmacion["estado"]
                != "CONFIRMACION_REQUERIDA"
            ):
                raise ValueError(
                    "La herramienta permitió registrar "
                    "sin confirmación."
                )

            if ruta_temporal.exists():
                raise ValueError(
                    "Se creó un archivo aunque el usuario "
                    "no confirmó el registro."
                )

            print(
                "Estado:",
                resultado_sin_confirmacion["estado"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 2: REGISTRO CONFIRMADO
            # ------------------------------------------------

            print("\nCASO 2: Registro confirmado")

            datos_confirmados = crear_datos_prueba(
                confirmado=True
            )

            resultado_registro = (
                registrar_oportunidad_en_archivo(
                    datos=datos_confirmados,
                    ruta_archivo=ruta_temporal,
                )
            )

            if (
                resultado_registro["estado"]
                != "REGISTRADA"
            ):
                raise ValueError(
                    "La oportunidad confirmada no fue "
                    "registrada."
                )

            if not ruta_temporal.exists():
                raise FileNotFoundError(
                    "No se creó el archivo esperado."
                )

            if not resultado_registro.get(
                "oportunidad_id"
            ):
                raise ValueError(
                    "No se generó un identificador."
                )

            if not resultado_registro.get(
                "fecha_registro"
            ):
                raise ValueError(
                    "No se registró fecha y hora."
                )

            print(
                "ID:",
                resultado_registro["oportunidad_id"],
            )

            print(
                "Fecha:",
                resultado_registro["fecha_registro"],
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 3: CONTENIDO DEL ARCHIVO
            # ------------------------------------------------

            print("\nCASO 3: Validación del archivo")

            lineas = ruta_temporal.read_text(
                encoding="utf-8"
            ).splitlines()

            if len(lineas) != 1:
                raise ValueError(
                    "El archivo debe contener exactamente "
                    "un registro."
                )

            registro_guardado = json.loads(
                lineas[0]
            )

            campos_obligatorios = [
                "oportunidad_id",
                "fecha_registro",
                "cliente",
                "contacto",
                "productos",
                "cantidad_total",
                "monto_estimado",
                "etapa",
                "proxima_accion",
                "vendedor",
                "descuento",
                "condicion_pago",
                "huella",
            ]

            for campo in campos_obligatorios:
                if campo not in registro_guardado:
                    raise ValueError(
                        "El registro no contiene el campo: "
                        f"{campo}"
                    )

            print(
                "Campos encontrados:",
                len(registro_guardado),
            )

            print("Resultado: correcto")

            # ------------------------------------------------
            # CASO 4: DUPLICADO
            # ------------------------------------------------

            print("\nCASO 4: Prevención de duplicados")

            resultado_duplicado = (
                registrar_oportunidad_en_archivo(
                    datos=datos_confirmados,
                    ruta_archivo=ruta_temporal,
                )
            )

            if (
                resultado_duplicado["estado"]
                != "DUPLICADO"
            ):
                raise ValueError(
                    "La herramienta no detectó el "
                    "registro duplicado."
                )

            lineas_despues_duplicado = (
                ruta_temporal.read_text(
                    encoding="utf-8"
                ).splitlines()
            )

            if len(lineas_despues_duplicado) != 1:
                raise ValueError(
                    "El duplicado fue escrito en el archivo."
                )

            if (
                resultado_duplicado[
                    "oportunidad_id"
                ]
                != resultado_registro[
                    "oportunidad_id"
                ]
            ):
                raise ValueError(
                    "El duplicado no referencia el registro "
                    "original."
                )

            print(
                "Registro existente:",
                resultado_duplicado[
                    "oportunidad_id"
                ],
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
        "LA TOOL DE REGISTRO FUNCIONÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()