"""
Prueba de memoria conversacional del orquestador.

Se valida:

1. Que el orquestador presente un resumen pendiente.
2. Que el estado se almacene mediante thread_id.
3. Que otro thread_id no pueda acceder a ese estado.
4. Que la confirmación pueda enviarse en una invocación nueva.
5. Que no sea necesario reenviar manualmente el historial.
6. Que la oportunidad termine registrada.
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

from src.memoria import generar_thread_id  # noqa: E402

from src.tools.registro_tool import (  # noqa: E402
    ARCHIVO_OPORTUNIDADES,
)


# ============================================================
# CONFIGURACIÓN DE LA PRUEBA
# ============================================================

PAUSA_ENTRE_INTERACCIONES = 65

MARCA_PRUEBA = datetime.now().strftime(
    "%Y%m%d%H%M%S"
)

CLIENTE_PRUEBA = (
    f"Empresa Memoria {MARCA_PRUEBA}"
)

THREAD_PRINCIPAL = generar_thread_id(
    "prueba-memoria"
)

THREAD_AJENO = generar_thread_id(
    "prueba-aislamiento"
)


CONSULTA_INICIAL = f"""
Quiero registrar una oportunidad comercial con estos datos:

Cliente: {CLIENTE_PRUEBA}
Contacto: memoria-{MARCA_PRUEBA}@empresa-demo.com
Productos: Patito Pro 2026
Cantidad total: 2
Monto estimado: 2598 dólares
Etapa: Propuesta/Cotización
Próxima acción: Enviar la cotización formal al cliente
Vendedor: Vendedor Memoria
Descuento: 10 por ciento
Condición de pago: Contado

Primero muestra el resumen. No registres todavía.
""".strip()


CONFIRMACION = "CONFIRMO EL REGISTRO"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def construir_configuracion(
    thread_id: str,
    recursion_limit: int = 18,
) -> dict:
    """
    Construye la configuración necesaria para una conversación.
    """

    return {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": recursion_limit,
    }


def ejecutar_mensaje(
    orquestador,
    mensaje: str,
    thread_id: str,
    recursion_limit: int = 18,
) -> tuple[
    dict,
    str,
    list[str],
    list[str],
    float,
]:
    """
    Ejecuta un único mensaje dentro de un thread.

    No reenvía manualmente el historial anterior.
    """

    inicio = perf_counter()

    resultado = orquestador.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": mensaje,
                }
            ]
        },
        config=construir_configuracion(
            thread_id=thread_id,
            recursion_limit=recursion_limit,
        ),
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


def contar_mensajes_guardados(
    orquestador,
    thread_id: str,
) -> int:
    """
    Consulta el estado almacenado de un thread.
    """

    estado = orquestador.get_state(
        construir_configuracion(
            thread_id=thread_id
        )
    )

    valores = estado.values or {}

    mensajes = valores.get(
        "messages",
        [],
    )

    return len(mensajes)


# ============================================================
# EJECUCIÓN
# ============================================================

def ejecutar_prueba() -> None:
    """
    Ejecuta el flujo completo usando memoria conversacional.
    """

    print("=" * 72)
    print("PRUEBA DE MEMORIA DEL ORQUESTADOR")
    print("=" * 72)

    print(
        f"\nThread principal: {THREAD_PRINCIPAL}"
    )

    print(
        f"Thread ajeno: {THREAD_AJENO}"
    )

    try:
        orquestador = crear_orquestador(
            con_memoria=True
        )

        # ----------------------------------------------------
        # VALIDACIÓN INICIAL
        # ----------------------------------------------------

        mensajes_iniciales = contar_mensajes_guardados(
            orquestador=orquestador,
            thread_id=THREAD_PRINCIPAL,
        )

        if mensajes_iniciales != 0:
            raise ValueError(
                "El thread principal ya contenía mensajes "
                "antes de iniciar la prueba."
            )

        # ----------------------------------------------------
        # INTERACCIÓN 1: PREPARAR REGISTRO
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("INTERACCIÓN 1: Preparar oportunidad")
        print("-" * 72)

        (
            _,
            respuesta_pendiente,
            tools_pendientes,
            resultados_pendientes,
            latencia_pendiente,
        ) = ejecutar_mensaje(
            orquestador=orquestador,
            mensaje=CONSULTA_INICIAL,
            thread_id=THREAD_PRINCIPAL,
        )

        if "delegar_accion" not in tools_pendientes:
            raise ValueError(
                "El orquestador no utilizó "
                "delegar_accion."
            )

        if (
            "RESUMEN_PENDIENTE:"
            not in respuesta_pendiente
        ):
            raise ValueError(
                "No se presentó el resumen pendiente."
            )

        if (
            "CONFIRMACION_REQUERIDA:"
            not in respuesta_pendiente
        ):
            raise ValueError(
                "No se solicitó confirmación."
            )

        if not resultados_pendientes:
            raise ValueError(
                "El Agente de Acción no devolvió resultado."
            )

        mensajes_guardados = contar_mensajes_guardados(
            orquestador=orquestador,
            thread_id=THREAD_PRINCIPAL,
        )

        if mensajes_guardados == 0:
            raise ValueError(
                "La memoria no guardó los mensajes "
                "de la primera interacción."
            )

        print(
            f"\nTools utilizadas: "
            f"{tools_pendientes}"
        )

        print("\nRespuesta:")
        print(respuesta_pendiente)

        print(
            f"\nMensajes guardados: "
            f"{mensajes_guardados}"
        )

        print(
            f"Latencia: "
            f"{latencia_pendiente:.2f} segundos"
        )

        print("Estado: correcto")

        # ----------------------------------------------------
        # AISLAMIENTO ENTRE THREADS
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("VALIDACIÓN: Aislamiento entre conversaciones")
        print("-" * 72)

        mensajes_thread_ajeno = (
            contar_mensajes_guardados(
                orquestador=orquestador,
                thread_id=THREAD_AJENO,
            )
        )

        if mensajes_thread_ajeno != 0:
            raise ValueError(
                "El thread ajeno recibió mensajes de otra "
                "conversación."
            )

        print(
            "El segundo thread no contiene mensajes "
            "del thread principal."
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
        # INTERACCIÓN 2: CONFIRMAR
        # ----------------------------------------------------

        print("\n" + "-" * 72)
        print("INTERACCIÓN 2: Confirmación con memoria")
        print("-" * 72)

        print(
            "\nEn esta ejecución se envía únicamente:"
        )

        print(CONFIRMACION)

        (
            _,
            respuesta_confirmada,
            tools_confirmadas,
            resultados_confirmados,
            latencia_confirmada,
        ) = ejecutar_mensaje(
            orquestador=orquestador,
            mensaje=CONFIRMACION,
            thread_id=THREAD_PRINCIPAL,
            recursion_limit=20,
        )

        if "delegar_accion" not in tools_confirmadas:
            raise ValueError(
                "El orquestador no recuperó el registro "
                "pendiente desde la memoria."
            )

        if not resultados_confirmados:
            raise ValueError(
                "No se obtuvo resultado del Agente de Acción."
            )

        resultados_texto = "\n".join(
            resultados_confirmados
        )

        if (
            "TOOLS_ACCION_UTILIZADAS: "
            "registrar_oportunidad"
            not in resultados_texto
        ):
            raise ValueError(
                "El Agente de Acción no utilizó "
                "registrar_oportunidad."
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
                "El orquestador no informó correctamente "
                "el resultado del registro."
            )

        if "OPORTUNIDAD_ID:" not in respuesta_confirmada:
            raise ValueError(
                "La respuesta no contiene el identificador."
            )

        if not ARCHIVO_OPORTUNIDADES.exists():
            raise FileNotFoundError(
                "No se encontró el archivo de oportunidades."
            )

        contenido = ARCHIVO_OPORTUNIDADES.read_text(
            encoding="utf-8"
        )

        if CLIENTE_PRUEBA not in contenido:
            raise ValueError(
                "El archivo no contiene la oportunidad "
                "registrada mediante memoria."
            )

        mensajes_finales = contar_mensajes_guardados(
            orquestador=orquestador,
            thread_id=THREAD_PRINCIPAL,
        )

        if mensajes_finales <= mensajes_guardados:
            raise ValueError(
                "La segunda interacción no se agregó "
                "a la memoria."
            )

        print(
            f"\nTools utilizadas: "
            f"{tools_confirmadas}"
        )

        print("\nRespuesta:")
        print(respuesta_confirmada)

        print(
            f"\nMensajes guardados al finalizar: "
            f"{mensajes_finales}"
        )

        print(
            f"Latencia: "
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
        "LA MEMORIA DEL ORQUESTADOR FUNCIONÓ CORRECTAMENTE"
    )
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_prueba()