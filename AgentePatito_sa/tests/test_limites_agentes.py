"""
Prueba de límites entre los agentes especializados.

Cada agente recibe una pregunta que pertenece al dominio
de otro agente y debe:

1. No llamar herramientas.
2. No inventar una respuesta.
3. Indicar que la consulta está fuera de su alcance.
4. Recomendar el agente especializado correcto.
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
    obtener_tools_utilizadas,
)


CASOS_FUERA_DE_ALCANCE = [
    {
        "nombre": "catalogo_recibe_politicas",
        "crear_agente": crear_agente_catalogo,
        "consulta": (
            "¿Qué porcentaje de descuento puede aprobar "
            "directamente un vendedor?"
        ),
        "agente_recomendado": "Políticas",
    },
    {
        "nombre": "catalogo_recibe_crm",
        "crear_agente": crear_agente_catalogo,
        "consulta": (
            "¿Cuáles son las etapas del embudo comercial "
            "que deben registrarse en el CRM?"
        ),
        "agente_recomendado": "CRM",
    },
    {
        "nombre": "politicas_recibe_catalogo",
        "crear_agente": crear_agente_politicas,
        "consulta": (
            "¿Cuál es el producto más económico y cuál "
            "es su precio?"
        ),
        "agente_recomendado": "Catálogo",
    },
    {
        "nombre": "politicas_recibe_crm",
        "crear_agente": crear_agente_politicas,
        "consulta": (
            "¿Qué campos debo completar para registrar "
            "una oportunidad en el CRM?"
        ),
        "agente_recomendado": "CRM",
    },
    {
        "nombre": "crm_recibe_catalogo",
        "crear_agente": crear_agente_crm,
        "consulta": (
            "¿Qué productos están disponibles y cuáles "
            "son sus precios?"
        ),
        "agente_recomendado": "Catálogo",
    },
    {
        "nombre": "crm_recibe_politicas",
        "crear_agente": crear_agente_crm,
        "consulta": (
            "¿Qué descuento se puede ofrecer sin aprobación "
            "del gerente comercial?"
        ),
        "agente_recomendado": "Políticas",
    },
]


def validar_fuera_de_alcance(
    nombre_caso: str,
    respuesta: str,
    tools_utilizadas: list[str],
    agente_recomendado: str,
) -> None:
    """
    Valida la respuesta de un agente ante una consulta
    que no pertenece a su especialidad.
    """

    if tools_utilizadas:
        raise ValueError(
            f"El caso '{nombre_caso}' llamó herramientas "
            f"aunque estaba fuera de alcance: "
            f"{tools_utilizadas}"
        )

    if "FUERA_DE_ALCANCE:" not in respuesta:
        raise ValueError(
            f"El caso '{nombre_caso}' no indicó "
            "FUERA_DE_ALCANCE."
        )

    if "AGENTE_RECOMENDADO:" not in respuesta:
        raise ValueError(
            f"El caso '{nombre_caso}' no incluyó "
            "AGENTE_RECOMENDADO."
        )

    if agente_recomendado.lower() not in respuesta.lower():
        raise ValueError(
            f"El caso '{nombre_caso}' no recomendó "
            f"el agente esperado: {agente_recomendado}."
        )


def ejecutar_prueba() -> None:
    """
    Ejecuta todos los casos fuera de alcance.
    """

    print("=" * 72)
    print("PRUEBA DE LÍMITES ENTRE AGENTES — PATITO S.A.")
    print("=" * 72)

    try:
        for caso in CASOS_FUERA_DE_ALCANCE:
            print("\n" + "-" * 72)
            print(f"CASO: {caso['nombre']}")
            print(f"CONSULTA: {caso['consulta']}")
            print("-" * 72)

            agente = caso["crear_agente"]()

            inicio = perf_counter()

            resultado = agente.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": caso["consulta"],
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

            validar_fuera_de_alcance(
                nombre_caso=caso["nombre"],
                respuesta=respuesta,
                tools_utilizadas=tools_utilizadas,
                agente_recomendado=caso[
                    "agente_recomendado"
                ],
            )

            print("\nRespuesta:")
            print(respuesta)

            print(
                f"\nTools utilizadas: "
                f"{tools_utilizadas or 'ninguna'}"
            )

            print(
                f"Latencia: {latencia:.2f} segundos"
            )

            print("Estado: correcto")

    except Exception as error:
        print("\nERROR DURANTE LA PRUEBA:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 72)
    print("LOS LÍMITES DE LOS AGENTES FUNCIONARON CORRECTAMENTE")
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()