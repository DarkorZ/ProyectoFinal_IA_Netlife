"""
Prueba directa de las Tools de recuperación.

Esta prueba valida:

1. Que las tres herramientas existan.
2. Que LangChain reconozca sus nombres y descripciones.
3. Que cada herramienta consulte su propia base.
4. Que se devuelvan fuentes, chunks y contenido.
5. Que no se mezclen los documentos.
"""

import sys
from pathlib import Path
from time import perf_counter


BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.tools.retriever_tools import (  # noqa: E402
    consultar_catalogo,
    consultar_crm,
    consultar_politicas,
)


CASOS_PRUEBA = {
    "catalogo": {
        "tool": consultar_catalogo,
        "consulta": (
            "¿Cuáles son los productos disponibles, "
            "sus precios y características?"
        ),
        "fuente_esperada": (
            "01_Catalogo_Productos_Precios.txt"
        ),
        "fuentes_prohibidas": [
            "02_Politicas_Comerciales_Descuentos_Credito.txt",
            "03_Proceso_Ventas_CRM.txt",
        ],
    },

    "politicas": {
        "tool": consultar_politicas,
        "consulta": (
            "¿Qué descuentos se pueden aplicar y cuáles "
            "son las condiciones de crédito?"
        ),
        "fuente_esperada": (
            "02_Politicas_Comerciales_Descuentos_Credito.txt"
        ),
        "fuentes_prohibidas": [
            "01_Catalogo_Productos_Precios.txt",
            "03_Proceso_Ventas_CRM.txt",
        ],
    },

    "crm": {
        "tool": consultar_crm,
        "consulta": (
            "¿Cuáles son las etapas del embudo comercial "
            "y qué información se registra en el CRM?"
        ),
        "fuente_esperada": (
            "03_Proceso_Ventas_CRM.txt"
        ),
        "fuentes_prohibidas": [
            "01_Catalogo_Productos_Precios.txt",
            "02_Politicas_Comerciales_Descuentos_Credito.txt",
        ],
    },
}


def validar_respuesta(
    nombre_base: str,
    respuesta: str,
    fuente_esperada: str,
    fuentes_prohibidas: list[str],
) -> None:
    """
    Valida el formato, la fuente y el aislamiento de una tool.
    """

    if not isinstance(respuesta, str):
        raise TypeError(
            f"La tool de {nombre_base} no devolvió texto."
        )

    if "ESTADO: OK" not in respuesta:
        raise ValueError(
            f"La tool de {nombre_base} no terminó "
            "correctamente."
        )

    base_esperada = (
        f"BASE_CONSULTADA: {nombre_base}"
    )

    if base_esperada not in respuesta:
        raise ValueError(
            f"La respuesta no identifica correctamente "
            f"la base '{nombre_base}'."
        )

    if fuente_esperada not in respuesta:
        raise ValueError(
            f"No apareció la fuente esperada para "
            f"'{nombre_base}'."
        )

    for fuente_prohibida in fuentes_prohibidas:
        if fuente_prohibida in respuesta:
            raise ValueError(
                f"La tool '{nombre_base}' mezcló información "
                f"de la fuente: {fuente_prohibida}"
            )

    if "CHUNK_ID:" not in respuesta:
        raise ValueError(
            f"La tool '{nombre_base}' no devolvió chunk_id."
        )

    if "DISTANCIA:" not in respuesta:
        raise ValueError(
            f"La tool '{nombre_base}' no devolvió distancia."
        )

    if "<fragmento>" not in respuesta:
        raise ValueError(
            f"La tool '{nombre_base}' no devolvió "
            "contenido documental."
        )


def ejecutar_prueba() -> None:
    """
    Ejecuta y valida las tres herramientas.
    """

    print("=" * 65)
    print("PRUEBA DE TOOLS DE RECUPERACIÓN — PATITO S.A.")
    print("=" * 65)

    try:
        for nombre_base, configuracion in CASOS_PRUEBA.items():
            herramienta = configuracion["tool"]
            consulta = configuracion["consulta"]

            print("\n" + "-" * 65)
            print(f"TOOL: {herramienta.name}")
            print(f"BASE: {nombre_base}")
            print(f"CONSULTA: {consulta}")
            print("-" * 65)

            if not herramienta.description:
                raise ValueError(
                    f"La tool '{herramienta.name}' "
                    "no tiene descripción."
                )

            inicio = perf_counter()

            respuesta = herramienta.invoke(
                {
                    "consulta": consulta,
                }
            )

            latencia = perf_counter() - inicio

            validar_respuesta(
                nombre_base=nombre_base,
                respuesta=respuesta,
                fuente_esperada=configuracion[
                    "fuente_esperada"
                ],
                fuentes_prohibidas=configuracion[
                    "fuentes_prohibidas"
                ],
            )

            vista_previa = (
                respuesta[:700]
                .replace("\n\n", "\n")
                .strip()
            )

            print("\nVista previa:")
            print(vista_previa)

            if len(respuesta) > 700:
                print("\n...")

            print(
                f"\nLatencia: {latencia:.2f} segundos"
            )
            print("Estado: correcta")

    except Exception as error:
        print("\nERROR DURANTE LA PRUEBA:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 65)
    print("LAS TRES TOOLS FUNCIONARON CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    ejecutar_prueba()