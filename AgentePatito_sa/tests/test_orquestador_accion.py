"""
Prueba de integración entre:

- Orquestador.
- Tool delegar_accion.
- Agente de Acción.
- Tool registrar_oportunidad.
- Archivo local de oportunidades.

Se valida un flujo de dos interacciones:

1. El usuario proporciona todos los datos.
2. El sistema presenta el resumen y solicita confirmación.
3. El usuario confirma.
4. La oportunidad se registra.
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


from src.agents.orchestrator import (  # noqa: E402
    crear_orquestador,
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
# DATOS DE PRUEBA
# ============================================================

PAUSA_ENTRE_INTERACCIONES = 65

MARCA_PRUEBA = datetime.now().strftime(
    "%Y%m%d%H%M%S"
)

CLIENTE_PRUEBA = (
    f"Empresa Orquestador {MARCA_PRUEBA}"
)

CONSULTA_REGISTRO = f"""
Quiero registrar una oportunidad comercial con estos datos:

Cliente: {CLIENTE_PRUEBA}
Contacto: comercial-{MARCA_PRUEBA}@empresa-demo.com
Productos: Patito Pro 2026
Cantidad total: 2
Monto estimado: 2598 dólares
Etapa: Propuesta/Cotización
Próxima acción: Enviar la cotización formal al cliente
Vendedor: Vendedor Orquestador
Descuento: 10 por ciento
Condición de pago: Contado

Primero muéstrame el resumen. No registres todavía.
""".strip()

CONFIRMACION = "CONFIRMO EL REGISTRO"


# ============================================================
# UTILIDAD DE EJECUCIÓN
# ============================================================

def ejecutar_orquestador(
    orquestador,
    mensajes: list[dict],
    recursion_limit: int = 16,
) -> tuple[str, list[str], list[str], float]:
    """
    Ejecuta el orquestador y extrae sus resultados.
    """

    inicio = perf_counter()

    resultado = orquestador.invoke(
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
        respuesta,
        tools_utilizadas,
        resultados_tools,
        latencia,
    )


# ============================================================
# EJECUCIÓN DE LA PRUEBA
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta el flujo completo de registro desde el orquestador.
    """

    print("=" * 72)
    print("PRUEBA DE ORQUESTADOR — AGENTE DE ACCIÓN")
    print("=" * 72)

    try:
        orquestador = crear_orquestador()

        # ----------------------------------------------------
        # INTERACCIÓN 1: PREPARAR REGISTRO
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("INTERACCIÓN 1: Preparar oportunidad")
        print("-" * 72)
        print(f"\nConsulta:\n{CONSULTA_REGISTRO}")

        (
            respuesta_pendiente,
            tools_pendientes,
            resultados_pendientes,
            latencia_pendiente,
        ) = ejecutar_orquestador(
            orquestador=orquestador,
            mensajes=[
                {
                    "role": "user",
                    "content": CONSULTA_REGISTRO,
                }
            ],
        )

        if "delegar_accion" not in tools_pendientes:
            raise ValueError(
                "El orquestador no utilizó delegar_accion."
            )

        tools_no_permitidas = {
            "delegar_catalogo",
            "delegar_politicas",
            "delegar_crm",
        }

        tools_adicionales = (
            set(tools_pendientes)
            & tools_no_permitidas
        )

        if tools_adicionales:
            raise ValueError(
                "El orquestador utilizó agentes que no eran "
                f"necesarios: {sorted(tools_adicionales)}"
            )

        if not resultados_pendientes:
            raise ValueError(
                "delegar_accion no devolvió resultados."
            )

        resultados_pendientes_texto = "\n".join(
            resultados_pendientes
        )

        if (
            "AGENTE_ESPECIALISTA: accion"
            not in resultados_pendientes_texto
        ):
            raise ValueError(
                "No se ejecutó el Agente de Acción."
            )

        if (
            "TOOLS_ACCION_UTILIZADAS: ninguna"
            not in resultados_pendientes_texto
        ):
            raise ValueError(
                "El Agente de Acción utilizó la tool antes "
                "de recibir confirmación."
            )

        if (
            "RESUMEN_PENDIENTE:"
            not in respuesta_pendiente
        ):
            raise ValueError(
                "El orquestador no mostró el resumen."
            )

        if (
            "CONFIRMACION_REQUERIDA:"
            not in respuesta_pendiente
        ):
            raise ValueError(
                "El orquestador no solicitó confirmación."
            )

        # El cliente todavía no debe aparecer en el archivo.
        if ARCHIVO_OPORTUNIDADES.exists():
            contenido_previo = (
                ARCHIVO_OPORTUNIDADES.read_text(
                    encoding="utf-8"
                )
            )

            if CLIENTE_PRUEBA in contenido_previo:
                raise ValueError(
                    "La oportunidad fue escrita antes "
                    "de recibir confirmación."
                )

        print(
            f"\nTools utilizadas: "
            f"{tools_pendientes}"
        )

        print("\nRespuesta:")
        print(respuesta_pendiente)

        print(
            f"\nLatencia: "
            f"{latencia_pendiente:.2f} segundos"
        )

        print("Estado: correcto")

        # ----------------------------------------------------
        # PAUSA POR CUOTA
        # ----------------------------------------------------

        print("\n" + "." * 72)
        print(
            f"Esperando {PAUSA_ENTRE_INTERACCIONES} segundos "
            "para respetar el límite gratuito de Gemini..."
        )
        print("." * 72)

        sleep(
            PAUSA_ENTRE_INTERACCIONES
        )

        # ----------------------------------------------------
        # INTERACCIÓN 2: CONFIRMAR REGISTRO
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("INTERACCIÓN 2: Confirmar oportunidad")
        print("-" * 72)
        print(f"\nMensaje:\n{CONFIRMACION}")

        mensajes_confirmacion = [
            {
                "role": "user",
                "content": CONSULTA_REGISTRO,
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
            respuesta_confirmada,
            tools_confirmadas,
            resultados_confirmados,
            latencia_confirmada,
        ) = ejecutar_orquestador(
            orquestador=orquestador,
            mensajes=mensajes_confirmacion,
            recursion_limit=20,
        )

        if "delegar_accion" not in tools_confirmadas:
            raise ValueError(
                "El orquestador no delegó la confirmación "
                "al Agente de Acción."
            )

        if not resultados_confirmados:
            raise ValueError(
                "No se obtuvo resultado de delegar_accion."
            )

        resultados_confirmados_texto = "\n".join(
            resultados_confirmados
        )

        if (
            "TOOLS_ACCION_UTILIZADAS: "
            "registrar_oportunidad"
            not in resultados_confirmados_texto
        ):
            raise ValueError(
                "El Agente de Acción no utilizó "
                "registrar_oportunidad."
            )

        estados_validos = [
            "ESTADO: REGISTRADA",
            "ESTADO: DUPLICADO",
        ]

        if not any(
            estado in resultados_confirmados_texto
            for estado in estados_validos
        ):
            raise ValueError(
                "La tool de registro no devolvió un estado "
                "válido."
            )

        encabezados_validos = [
            "REGISTRO_COMPLETADO:",
            "REGISTRO_DUPLICADO:",
        ]

        if not any(
            encabezado in respuesta_confirmada
            for encabezado in encabezados_validos
        ):
            raise ValueError(
                "La respuesta final no informó correctamente "
                "el resultado del registro."
            )

        if "OPORTUNIDAD_ID:" not in respuesta_confirmada:
            raise ValueError(
                "La respuesta no contiene el identificador "
                "de la oportunidad."
            )

        if not ARCHIVO_OPORTUNIDADES.exists():
            raise FileNotFoundError(
                "No se creó el archivo de oportunidades."
            )

        contenido_final = (
            ARCHIVO_OPORTUNIDADES.read_text(
                encoding="utf-8"
            )
        )

        if CLIENTE_PRUEBA not in contenido_final:
            raise ValueError(
                "El archivo no contiene la oportunidad "
                "registrada."
            )

        print(
            f"\nTools utilizadas: "
            f"{tools_confirmadas}"
        )

        print("\nResultado interno:")
        print(resultados_confirmados_texto)

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
        "EL ORQUESTADOR Y EL AGENTE DE ACCIÓN "
        "FUNCIONARON CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()