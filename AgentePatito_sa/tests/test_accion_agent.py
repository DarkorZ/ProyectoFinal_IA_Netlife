"""
Prueba integral del Agente de Acción.

Se valida:

1. Que solicite campos faltantes.
2. Que no escriba con datos incompletos.
3. Que presente un resumen cuando los datos estén completos.
4. Que solicite confirmación.
5. Que no escriba antes de confirmar.
6. Que utilice registrar_oportunidad después de una
   confirmación explícita.
7. Que conserve el identificador y la fecha de registro.
"""

import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter, sleep


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.agents.accion_agent import (  # noqa: E402
    crear_agente_accion,
)

from src.agents.utils import (  # noqa: E402
    extraer_respuesta_final,
    obtener_resultados_tools,
    obtener_tools_utilizadas,
)

from src.tools.registro_tool import (  # noqa: E402
    ARCHIVO_OPORTUNIDADES,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

PAUSA_ENTRE_CASOS = 65

MARCA_PRUEBA = datetime.now().strftime(
    "%Y%m%d%H%M%S"
)

CLIENTE_PRUEBA = (
    f"Empresa Integración {MARCA_PRUEBA}"
)


CONSULTA_INCOMPLETA = (
    f"Quiero registrar una oportunidad para "
    f"{CLIENTE_PRUEBA}."
)


CONSULTA_COMPLETA = f"""
Quiero preparar una oportunidad comercial con estos datos:

Cliente: {CLIENTE_PRUEBA}
Contacto: ventas-{MARCA_PRUEBA}@empresa-demo.com
Productos: Patito Pro 2026
Cantidad total: 2
Monto estimado: 2598 dólares
Etapa: Propuesta/Cotización
Próxima acción: Enviar la cotización formal al cliente
Vendedor: Vendedor de Integración
Descuento: 10 por ciento
Condición de pago: Contado

Todavía no registres la oportunidad.
""".strip()


CONFIRMACION = "CONFIRMO EL REGISTRO"


# ============================================================
# UTILIDADES
# ============================================================

def ejecutar_consulta(
    agente,
    mensajes: list[dict],
    recursion_limit: int = 10,
) -> tuple[dict, str, list[str], list[str], float]:
    """
    Ejecuta una consulta y extrae sus resultados principales.
    """

    inicio = perf_counter()

    resultado = agente.invoke(
        {
            "messages": mensajes,
        },
        config={
            "recursion_limit": recursion_limit,
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

    return (
        resultado,
        respuesta,
        tools_utilizadas,
        resultados_tools,
        latencia,
    )


def esperar_siguiente_caso() -> None:
    """
    Espera para evitar superar la cuota por minuto.
    """

    print("\n" + "." * 72)
    print(
        f"Esperando {PAUSA_ENTRE_CASOS} segundos para "
        "respetar el límite gratuito de Gemini..."
    )
    print("." * 72)

    sleep(PAUSA_ENTRE_CASOS)


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta las tres etapas del flujo de registro.
    """

    print("=" * 72)
    print("PRUEBA DEL AGENTE DE ACCIÓN")
    print("=" * 72)

    try:
        agente = crear_agente_accion()

        # ----------------------------------------------------
        # CASO 1: DATOS INCOMPLETOS
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("CASO 1: Datos incompletos")
        print("-" * 72)
        print(f"\nConsulta:\n{CONSULTA_INCOMPLETA}")

        (
            _,
            respuesta_incompleta,
            tools_incompletas,
            _,
            latencia_incompleta,
        ) = ejecutar_consulta(
            agente=agente,
            mensajes=[
                {
                    "role": "user",
                    "content": CONSULTA_INCOMPLETA,
                }
            ],
        )

        if tools_incompletas:
            raise ValueError(
                "El agente utilizó la tool con datos "
                f"incompletos: {tools_incompletas}"
            )

        if "DATOS_FALTANTES:" not in respuesta_incompleta:
            raise ValueError(
                "El agente no mostró los campos faltantes."
            )

        if "SIGUIENTE_PASO:" not in respuesta_incompleta:
            raise ValueError(
                "El agente no indicó el siguiente paso."
            )

        print("\nRespuesta:")
        print(respuesta_incompleta)
        print("\nTools utilizadas: ninguna")
        print(
            f"Latencia: {latencia_incompleta:.2f} segundos"
        )
        print("Estado: correcto")

        esperar_siguiente_caso()

        # ----------------------------------------------------
        # CASO 2: DATOS COMPLETOS SIN CONFIRMACIÓN
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("CASO 2: Datos completos sin confirmación")
        print("-" * 72)
        print(f"\nConsulta:\n{CONSULTA_COMPLETA}")

        (
            _,
            respuesta_pendiente,
            tools_pendientes,
            _,
            latencia_pendiente,
        ) = ejecutar_consulta(
            agente=agente,
            mensajes=[
                {
                    "role": "user",
                    "content": CONSULTA_COMPLETA,
                }
            ],
        )

        if tools_pendientes:
            raise ValueError(
                "El agente registró la oportunidad antes "
                f"de recibir confirmación: {tools_pendientes}"
            )

        if "RESUMEN_PENDIENTE:" not in respuesta_pendiente:
            raise ValueError(
                "El agente no presentó el resumen."
            )

        if (
            "CONFIRMACION_REQUERIDA:"
            not in respuesta_pendiente
        ):
            raise ValueError(
                "El agente no solicitó confirmación."
            )

        print("\nRespuesta:")
        print(respuesta_pendiente)
        print("\nTools utilizadas: ninguna")
        print(
            f"Latencia: {latencia_pendiente:.2f} segundos"
        )
        print("Estado: correcto")

        esperar_siguiente_caso()

        # ----------------------------------------------------
        # CASO 3: CONFIRMACIÓN EXPLÍCITA
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("CASO 3: Confirmación y registro")
        print("-" * 72)
        print(f"\nConfirmación:\n{CONFIRMACION}")

        mensajes_confirmacion = [
            {
                "role": "user",
                "content": CONSULTA_COMPLETA,
            },
            {
                "role": "assistant",
                "content": respuesta_pendiente,
            },
            {
                "role": "user",
                "content": CONFIRMACION,
            },
        ]

        (
            _,
            respuesta_confirmada,
            tools_confirmadas,
            resultados_confirmados,
            latencia_confirmada,
        ) = ejecutar_consulta(
            agente=agente,
            mensajes=mensajes_confirmacion,
            recursion_limit=12,
        )

        if (
            "registrar_oportunidad"
            not in tools_confirmadas
        ):
            raise ValueError(
                "El agente no utilizó registrar_oportunidad "
                "después de la confirmación."
            )

        if not resultados_confirmados:
            raise ValueError(
                "La tool de registro no devolvió resultados."
            )

        resultados_texto = "\n".join(
            resultados_confirmados
        )

        estados_validos = [
            "ESTADO: REGISTRADA",
            "ESTADO: DUPLICADO",
        ]

        if not any(
            estado in resultados_texto
            for estado in estados_validos
        ):
            raise ValueError(
                "La tool no devolvió un estado válido de "
                "registro o duplicado."
            )

        respuestas_validas = [
            "REGISTRO_COMPLETADO:",
            "REGISTRO_DUPLICADO:",
        ]

        if not any(
            estado in respuesta_confirmada
            for estado in respuestas_validas
        ):
            raise ValueError(
                "El agente no informó correctamente el "
                "resultado del registro."
            )

        if "OPORTUNIDAD_ID:" not in respuesta_confirmada:
            raise ValueError(
                "La respuesta no contiene el identificador."
            )

        if not ARCHIVO_OPORTUNIDADES.exists():
            raise FileNotFoundError(
                "No se creó el archivo de oportunidades."
            )

        contenido_archivo = (
            ARCHIVO_OPORTUNIDADES.read_text(
                encoding="utf-8"
            )
        )

        if CLIENTE_PRUEBA not in contenido_archivo:
            raise ValueError(
                "El archivo no contiene el cliente de prueba."
            )

        print(
            f"\nTools utilizadas: "
            f"{tools_confirmadas}"
        )

        print("\nResultado de la tool:")
        print(resultados_texto)

        print("\nRespuesta final:")
        print(respuesta_confirmada)

        print(
            f"\nLatencia: "
            f"{latencia_confirmada:.2f} segundos"
        )

        print("Estado: correcto")

    except Exception as error:
        print("\nERROR DURANTE LA PRUEBA:")
        print(
            f"{type(error).__name__}: {error}"
        )
        raise SystemExit(1) from error

    print("\n" + "=" * 72)
    print(
        "EL AGENTE DE ACCIÓN FUNCIONÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()