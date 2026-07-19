"""
Prueba de consulta fuera del alcance comercial.

El orquestador debe rechazar una pregunta que no corresponde
al catálogo, las políticas comerciales ni el proceso CRM.

No debe llamar ninguna tool de delegación.
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
    obtener_tools_utilizadas,
)


# ============================================================
# CASO DE PRUEBA
# ============================================================

CONSULTA_FUERA_DEL_SISTEMA = (
    "¿Cuál es la capital de Francia?"
)


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Comprueba que una consulta externa no sea delegada
    a ningún agente comercial.
    """

    print("=" * 72)
    print("PRUEBA DE ORQUESTADOR — FUERA DEL SISTEMA")
    print("=" * 72)

    print(
        f"\nConsulta: "
        f"{CONSULTA_FUERA_DEL_SISTEMA}"
    )

    try:
        orquestador = crear_orquestador()

        inicio = perf_counter()

        resultado = orquestador.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            CONSULTA_FUERA_DEL_SISTEMA
                        ),
                    }
                ]
            },
            config={
                "recursion_limit": 8,
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

        if tools_utilizadas:
            raise ValueError(
                "El orquestador utilizó agentes comerciales "
                "para una consulta fuera del sistema: "
                f"{tools_utilizadas}"
            )

        if "FUERA_DEL_SISTEMA:" not in respuesta:
            raise ValueError(
                "El orquestador no indicó que la consulta "
                "estaba fuera del sistema."
            )

        if "DOMINIOS_DISPONIBLES:" not in respuesta:
            raise ValueError(
                "El orquestador no mostró los dominios "
                "disponibles."
            )

        dominios_esperados = [
            "Catálogo",
            "Políticas",
            "CRM",
        ]

        for dominio in dominios_esperados:
            if dominio.lower() not in respuesta.lower():
                raise ValueError(
                    "La respuesta no muestra el dominio: "
                    f"{dominio}"
                )

        print("\nRespuesta:")
        print(respuesta)

        print(
            f"\nTools utilizadas: "
            f"{tools_utilizadas or 'ninguna'}"
        )

        print(
            f"Latencia: "
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
        "EL CONTROL FUERA DEL SISTEMA FUNCIONÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()