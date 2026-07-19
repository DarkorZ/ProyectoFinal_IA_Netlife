"""
Ejecución central y controlada del orquestador.

Toda interacción de la aplicación debe pasar por este módulo.

Responsabilidades:

1. Validar la consulta y el thread_id.
2. Validar límites operativos.
3. Ejecutar el orquestador.
4. Utilizar memoria mediante thread_id.
5. Medir la latencia.
6. Extraer respuesta, tools y resultados.
7. Extraer tokens y métricas.
8. Generar advertencias operativas.
9. Clasificar el estado de la respuesta.
10. Registrar la trazabilidad.
11. Transformar excepciones técnicas en errores controlados.

Los reintentos de llamadas al modelo se configuran en
crear_modelo_chat().

Este módulo no reintenta automáticamente todo el orquestador
porque algunas tools generan efectos reales, como escribir una
oportunidad en un archivo.
"""

from pathlib import Path
from time import perf_counter
from typing import Any

from src.agents.orchestrator import crear_orquestador
from src.agents.utils import (
    extraer_respuesta_final,
    obtener_resultados_tools,
    obtener_tools_utilizadas,
)
from src.config import (
    RECURSION_LIMIT_DEFAULT,
)
from src.limites import (
    validar_limites_ejecucion,
)
from src.monitoreo import (
    extraer_metricas_resultado,
)
from src.trazabilidad import (
    ARCHIVO_TRAZABILIDAD,
    registrar_interaccion,
)
from src.seguridad import (
    analizar_consulta_seguridad,
    construir_respuesta_seguridad,
)

# ============================================================
# ESTADOS DEL SISTEMA
# ============================================================

ESTADOS_VALIDOS = {
    "OK",
    "PENDIENTE",
    "RECHAZADA",
    "CANCELADA",
    "DUPLICADO",
    "ERROR",
    "ERROR_VALIDACION",
}


# ============================================================
# MÉTRICAS VACÍAS
# ============================================================

def crear_metricas_vacias(
    latencia_segundos: float = 0.0,
) -> dict[str, Any]:
    """
    Construye una estructura de métricas vacía.

    Se utiliza cuando la consulta no llega a ejecutarse o cuando
    ocurre un error antes de recibir mensajes del agente.
    """

    return {
        "cantidad_mensajes": 0,
        "llamadas_modelo_estimadas": 0,
        "latencia_segundos": round(
            max(
                float(latencia_segundos),
                0.0,
            ),
            4,
        ),
        "tokens": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "mensajes_con_usage_metadata": 0,
        },
        "tools": {
            "cantidad_tool_calls": 0,
            "cantidad_tool_messages": 0,
            "tools_utilizadas": [],
            "limite_esperado": 0,
            "supera_limite_esperado": False,
        },
    }


# ============================================================
# CONFIGURACIÓN DEL AGENTE
# ============================================================

def construir_configuracion_agente(
    thread_id: str,
    con_memoria: bool,
    recursion_limit: int,
) -> dict[str, Any]:
    """
    Construye la configuración de ejecución del agente.

    Cuando con_memoria es True, se incluye thread_id para
    recuperar el historial de la conversación.
    """

    configuracion: dict[str, Any] = {
        "recursion_limit": recursion_limit,
    }

    if con_memoria:
        configuracion["configurable"] = {
            "thread_id": thread_id,
        }

    return configuracion


# ============================================================
# CLASIFICACIÓN DE RESPUESTAS
# ============================================================

def clasificar_estado_respuesta(
    respuesta: str,
) -> str:
    """
    Determina el estado funcional de una respuesta.

    Se utilizan los encabezados estructurados definidos en los
    prompts de los agentes.
    """

    respuesta_normalizada = respuesta.upper()

    if (
        "ERROR_REGISTRO:" in respuesta_normalizada
        or "ERROR_CONTROLADO:" in respuesta_normalizada
    ):
        return "ERROR"

    if "REGISTRO_DUPLICADO:" in respuesta_normalizada:
        return "DUPLICADO"

    if "REGISTRO_CANCELADO:" in respuesta_normalizada:
        return "CANCELADA"

    if "FUERA_DEL_SISTEMA:" in respuesta_normalizada:
        return "RECHAZADA"

    if "FUERA_DE_ALCANCE:" in respuesta_normalizada:
        return "RECHAZADA"

    indicadores_pendientes = [
        "DATOS_FALTANTES:",
        "RESUMEN_PENDIENTE:",
        "CONFIRMACION_REQUERIDA:",
        "SIN_REGISTRO_PENDIENTE:",
    ]

    if any(
        indicador in respuesta_normalizada
        for indicador in indicadores_pendientes
    ):
        return "PENDIENTE"

    return "OK"


# ============================================================
# CLASIFICACIÓN DE ERRORES
# ============================================================

def clasificar_error(
    error: Exception,
) -> dict[str, Any]:
    """
    Clasifica excepciones frecuentes sin exponer información
    técnica innecesaria al usuario.
    """

    mensaje_original = str(error)
    mensaje_minusculas = mensaje_original.casefold()

    if (
        "generaterequestsperday" in mensaje_minusculas
        or "requestsperday" in mensaje_minusculas
    ):
        return {
            "codigo": "CUOTA_DIARIA_AGOTADA",
            "mensaje_usuario": (
                "Se agotó la cuota diaria disponible del "
                "modelo de inteligencia artificial."
            ),
            "accion_recomendada": (
                "Utilice una API key perteneciente a un proyecto "
                "con cuota disponible o espere la renovación."
            ),
            "reintentable": False,
        }

    if (
        "generaterequestsperminute" in mensaje_minusculas
        or "requestsperminute" in mensaje_minusculas
    ):
        return {
            "codigo": "LIMITE_POR_MINUTO",
            "mensaje_usuario": (
                "Se alcanzó temporalmente el límite de "
                "solicitudes por minuto."
            ),
            "accion_recomendada": (
                "Espere el tiempo indicado por el proveedor "
                "antes de volver a intentarlo."
            ),
            "reintentable": True,
        }

    if (
        "429" in mensaje_minusculas
        or "resource_exhausted" in mensaje_minusculas
    ):
        return {
            "codigo": "LIMITE_DE_CUOTA",
            "mensaje_usuario": (
                "El proveedor rechazó temporalmente la solicitud "
                "por límites de cuota."
            ),
            "accion_recomendada": (
                "Revise la cuota disponible y vuelva a intentarlo "
                "cuando el límite se haya restablecido."
            ),
            "reintentable": True,
        }

    if (
        "401" in mensaje_minusculas
        or "unauthenticated" in mensaje_minusculas
        or "invalid api key" in mensaje_minusculas
        or "api key not valid" in mensaje_minusculas
    ):
        return {
            "codigo": "CREDENCIALES_INVALIDAS",
            "mensaje_usuario": (
                "No fue posible autenticar la solicitud con "
                "el proveedor del modelo."
            ),
            "accion_recomendada": (
                "Verifique la variable GOOGLE_API_KEY del archivo "
                ".env."
            ),
            "reintentable": False,
        }

    if (
        "404" in mensaje_minusculas
        or "not_found" in mensaje_minusculas
        or "not found" in mensaje_minusculas
    ):
        return {
            "codigo": "MODELO_NO_DISPONIBLE",
            "mensaje_usuario": (
                "El modelo configurado no está disponible."
            ),
            "accion_recomendada": (
                "Revise MODELO_LLM en src/config.py y utilice "
                "un modelo habilitado para la cuenta."
            ),
            "reintentable": False,
        }

    if (
        "timeout" in mensaje_minusculas
        or "timed out" in mensaje_minusculas
        or "deadline_exceeded" in mensaje_minusculas
    ):
        return {
            "codigo": "TIEMPO_AGOTADO",
            "mensaje_usuario": (
                "La solicitud superó el tiempo máximo de espera."
            ),
            "accion_recomendada": (
                "Vuelva a intentarlo o revise la conexión "
                "a Internet."
            ),
            "reintentable": True,
        }

    if (
        "503" in mensaje_minusculas
        or "service unavailable" in mensaje_minusculas
        or "unavailable" in mensaje_minusculas
    ):
        return {
            "codigo": "SERVICIO_NO_DISPONIBLE",
            "mensaje_usuario": (
                "El servicio del modelo no se encuentra "
                "disponible temporalmente."
            ),
            "accion_recomendada": (
                "Vuelva a intentarlo después de unos momentos."
            ),
            "reintentable": True,
        }

    if (
        "connection" in mensaje_minusculas
        or "network" in mensaje_minusculas
        or "ssl" in mensaje_minusculas
    ):
        return {
            "codigo": "ERROR_CONEXION",
            "mensaje_usuario": (
                "No fue posible establecer una conexión segura "
                "con el proveedor."
            ),
            "accion_recomendada": (
                "Revise la conexión, el proxy, los certificados "
                "y la configuración de red."
            ),
            "reintentable": True,
        }

    if (
        "recursion_limit" in mensaje_minusculas
        or "recursion limit" in mensaje_minusculas
    ):
        return {
            "codigo": "LIMITE_RECURSION",
            "mensaje_usuario": (
                "El agente alcanzó el límite máximo de pasos "
                "permitidos."
            ),
            "accion_recomendada": (
                "Revise si existe un ciclo de llamadas entre "
                "agentes o tools."
            ),
            "reintentable": False,
        }

    return {
        "codigo": "ERROR_NO_CLASIFICADO",
        "mensaje_usuario": (
            "Ocurrió un error inesperado al procesar la consulta."
        ),
        "accion_recomendada": (
            "Revise la trazabilidad técnica para conocer "
            "el detalle."
        ),
        "reintentable": False,
    }


def construir_respuesta_error(
    clasificacion: dict[str, Any],
) -> str:
    """
    Construye una respuesta segura para mostrar al usuario.
    """

    reintentable = (
        "Sí"
        if clasificacion["reintentable"]
        else "No"
    )

    return (
        "ERROR_CONTROLADO:\n"
        f"{clasificacion['mensaje_usuario']}\n"
        "\n"
        "CODIGO_ERROR:\n"
        f"{clasificacion['codigo']}\n"
        "\n"
        "ACCION_RECOMENDADA:\n"
        f"{clasificacion['accion_recomendada']}\n"
        "\n"
        "REINTENTABLE:\n"
        f"{reintentable}"
    )


def construir_respuesta_validacion(
    codigo: str,
    detalle: str,
) -> str:
    """
    Construye una respuesta de validación uniforme.
    """

    return (
        "ERROR_CONTROLADO:\n"
        f"{detalle}\n"
        "\n"
        "CODIGO_ERROR:\n"
        f"{codigo}\n"
        "\n"
        "ACCION_RECOMENDADA:\n"
        "Corrija los datos de entrada antes de volver a ejecutar.\n"
        "\n"
        "REINTENTABLE:\n"
        "No"
    )


# ============================================================
# VALIDACIÓN BÁSICA DEL THREAD
# ============================================================

def validar_thread_id(
    thread_id: str,
) -> tuple[bool, str, str]:
    """
    Verifica que thread_id sea una cadena no vacía.

    Returns:
        tuple:
            valido, codigo_error, detalle.
    """

    if not isinstance(thread_id, str):
        return (
            False,
            "THREAD_ID_INVALIDO",
            "El thread_id debe ser una cadena de texto.",
        )

    if not thread_id.strip():
        return (
            False,
            "THREAD_ID_VACIO",
            "El thread_id no puede estar vacío.",
        )

    return True, "OK", ""


# ============================================================
# ADVERTENCIAS OPERATIVAS
# ============================================================

def generar_advertencias_metricas(
    metricas: dict[str, Any],
) -> list[str]:
    """
    Genera advertencias a partir de las métricas obtenidas.

    Estas advertencias no convierten una ejecución correcta
    en un error. Solo permiten identificar comportamientos
    que deben revisarse.
    """

    advertencias = []

    tools = metricas.get(
        "tools",
        {},
    )

    if tools.get(
        "supera_limite_esperado",
        False,
    ):
        advertencias.append(
            "La ejecución superó la cantidad esperada de "
            "llamadas a tools. Revise si existe repetición "
            "innecesaria o un posible ciclo."
        )

    tokens = metricas.get(
        "tokens",
        {},
    )

    if (
        tokens.get(
            "mensajes_con_usage_metadata",
            0,
        )
        == 0
    ):
        advertencias.append(
            "El proveedor no reportó usage_metadata para esta "
            "ejecución; los tokens aparecen como cero."
        )

    return advertencias


# ============================================================
# RESPUESTA DE VALIDACIÓN
# ============================================================

def devolver_error_validacion(
    consulta: str,
    thread_id: str,
    codigo_error: str,
    detalle: str,
    con_memoria: bool,
    recursion_limit: Any,
    registrar_traza: bool,
    ruta_trazabilidad: Path,
    inicio: float,
    metadata_adicional: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Construye, registra y devuelve un error de validación.
    """

    latencia = perf_counter() - inicio

    respuesta = construir_respuesta_validacion(
        codigo=codigo_error,
        detalle=detalle,
    )

    metricas = crear_metricas_vacias(
        latencia_segundos=latencia
    )

    metadata = {
        "con_memoria": con_memoria,
        "recursion_limit": recursion_limit,
        "codigo_error": codigo_error,
        "reintentable": False,
        "metricas": metricas,
    }

    if metadata_adicional:
        metadata.update(
            metadata_adicional
        )

    registro = None

    if registrar_traza:
        registro = registrar_interaccion(
            thread_id=(
                thread_id
                if isinstance(thread_id, str)
                else str(thread_id)
            ),
            consulta=(
                consulta
                if isinstance(consulta, str)
                else str(consulta)
            ),
            respuesta=respuesta,
            tools_utilizadas=[],
            resultados_tools=[],
            latencia_segundos=latencia,
            estado="ERROR_VALIDACION",
            error=detalle,
            metadata=metadata,
            ruta_archivo=ruta_trazabilidad,
        )

    return {
        "exito": False,
        "estado": "ERROR_VALIDACION",
        "respuesta": respuesta,
        "tools_utilizadas": [],
        "resultados_tools": [],
        "latencia_segundos": round(
            latencia,
            4,
        ),
        "metricas": metricas,
        "advertencias": [],
        "trace_id": (
            registro["trace_id"]
            if registro
            else None
        ),
        "error": detalle,
        "codigo_error": codigo_error,
        "reintentable": False,
        "resultado_crudo": None,
    }

#SEGURIDAD
def devolver_rechazo_seguridad(
    consulta: str,
    thread_id: str,
    resultado_seguridad: dict[str, Any],
    con_memoria: bool,
    recursion_limit: Any,
    registrar_traza: bool,
    ruta_trazabilidad: Path,
    inicio: float,
) -> dict[str, Any]:
    """
    Registra y devuelve una solicitud rechazada por seguridad.

    Una solicitud bloqueada no representa un fallo técnico.
    El sistema funcionó correctamente al impedir la operación.
    """

    latencia = perf_counter() - inicio

    respuesta = construir_respuesta_seguridad(
        resultado_seguridad=resultado_seguridad
    )

    metricas = crear_metricas_vacias(
        latencia_segundos=latencia
    )

    advertencias = [
        (
            "La consulta fue bloqueada antes de enviarse "
            "al modelo."
        )
    ]

    registro = None

    if registrar_traza:
        registro = registrar_interaccion(
            thread_id=thread_id,
            consulta=consulta,
            respuesta=respuesta,
            tools_utilizadas=[],
            resultados_tools=[],
            latencia_segundos=latencia,
            estado="RECHAZADA",
            error=None,
            metadata={
                "con_memoria": con_memoria,
                "recursion_limit": recursion_limit,
                "codigo_seguridad": (
                    resultado_seguridad["codigo"]
                ),
                "categoria_seguridad": (
                    resultado_seguridad["categoria"]
                ),
                "metricas": metricas,
                "advertencias_operativas": advertencias,
            },
            ruta_archivo=ruta_trazabilidad,
        )

    return {
        "exito": True,
        "estado": "RECHAZADA",
        "respuesta": respuesta,
        "tools_utilizadas": [],
        "resultados_tools": [],
        "latencia_segundos": round(
            latencia,
            4,
        ),
        "metricas": metricas,
        "advertencias": advertencias,
        "trace_id": (
            registro["trace_id"]
            if registro
            else None
        ),
        "error": None,
        "codigo_error": None,
        "codigo_seguridad": (
            resultado_seguridad["codigo"]
        ),
        "reintentable": False,
        "resultado_crudo": None,
    }
# ============================================================
# EJECUCIÓN CENTRAL
# ============================================================

def ejecutar_consulta_orquestador(
    consulta: str,
    thread_id: str,
    con_memoria: bool = True,
    recursion_limit: int = RECURSION_LIMIT_DEFAULT,
    orquestador: Any | None = None,
    registrar_traza: bool = True,
    ruta_trazabilidad: Path = ARCHIVO_TRAZABILIDAD,
) -> dict[str, Any]:
    """
    Ejecuta una consulta completa de forma controlada.

    Args:
        consulta:
            Mensaje actual del usuario.

        thread_id:
            Identificador de conversación.

        con_memoria:
            Activa la recuperación de mensajes anteriores.

        recursion_limit:
            Número máximo de pasos del grafo.

        orquestador:
            Permite proporcionar un orquestador alternativo.
            Se utiliza principalmente en pruebas unitarias.

        registrar_traza:
            Indica si debe guardarse la interacción.

        ruta_trazabilidad:
            Archivo JSONL donde se almacenará la traza.

    Returns:
        dict:
            Resultado estructurado de la ejecución.
    """

    inicio = perf_counter()

    consulta_limpia = (
        consulta.strip()
        if isinstance(consulta, str)
        else str(consulta)
    )

    thread_limpio = (
        thread_id.strip()
        if isinstance(thread_id, str)
        else str(thread_id)
    )

    # --------------------------------------------------------
    # VALIDACIÓN DEL THREAD
    # --------------------------------------------------------

    (
        thread_valido,
        codigo_thread,
        detalle_thread,
    ) = validar_thread_id(
        thread_id=thread_id
    )

    if not thread_valido:
        return devolver_error_validacion(
            consulta=consulta_limpia,
            thread_id=thread_limpio,
            codigo_error=codigo_thread,
            detalle=detalle_thread,
            con_memoria=con_memoria,
            recursion_limit=recursion_limit,
            registrar_traza=registrar_traza,
            ruta_trazabilidad=ruta_trazabilidad,
            inicio=inicio,
        )
    # --------------------------------------------------------
    # VALIDACIÓN DE SEGURIDAD
    # --------------------------------------------------------

    resultado_seguridad = analizar_consulta_seguridad(
        consulta=consulta_limpia
    )

    if not resultado_seguridad["permitida"]:
        return devolver_rechazo_seguridad(
            consulta=consulta_limpia,
            thread_id=thread_limpio,
            resultado_seguridad=resultado_seguridad,
            con_memoria=con_memoria,
            recursion_limit=recursion_limit,
            registrar_traza=registrar_traza,
            ruta_trazabilidad=ruta_trazabilidad,
            inicio=inicio,
        )
    # --------------------------------------------------------
    # VALIDACIÓN DE LÍMITES
    # --------------------------------------------------------

    validacion_limites = validar_limites_ejecucion(
        consulta=consulta,
        recursion_limit=recursion_limit,
    )

    if not validacion_limites["valido"]:
        return devolver_error_validacion(
            consulta=consulta_limpia,
            thread_id=thread_limpio,
            codigo_error=validacion_limites[
                "codigo"
            ],
            detalle=validacion_limites[
                "detalle"
            ],
            con_memoria=con_memoria,
            recursion_limit=recursion_limit,
            registrar_traza=registrar_traza,
            ruta_trazabilidad=ruta_trazabilidad,
            inicio=inicio,
            metadata_adicional={
                "limites": validacion_limites,
            },
        )

    try:
        agente = (
            orquestador
            if orquestador is not None
            else crear_orquestador(
                con_memoria=con_memoria
            )
        )

        configuracion = construir_configuracion_agente(
            thread_id=thread_limpio,
            con_memoria=con_memoria,
            recursion_limit=recursion_limit,
        )

        resultado = agente.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": consulta_limpia,
                    }
                ]
            },
            config=configuracion,
        )

        latencia = perf_counter() - inicio

        respuesta = extraer_respuesta_final(
            resultado_agente=resultado
        )

        tools_utilizadas = obtener_tools_utilizadas(
            resultado_agente=resultado
        )

        resultados_tools = obtener_resultados_tools(
            resultado_agente=resultado
        )

        estado = clasificar_estado_respuesta(
            respuesta=respuesta
        )

        metricas = extraer_metricas_resultado(
            resultado=resultado,
            latencia_segundos=latencia,
        )

        advertencias = generar_advertencias_metricas(
            metricas=metricas
        )

        registro = None

        if registrar_traza:
            registro = registrar_interaccion(
                thread_id=thread_limpio,
                consulta=consulta_limpia,
                respuesta=respuesta,
                tools_utilizadas=tools_utilizadas,
                resultados_tools=resultados_tools,
                latencia_segundos=latencia,
                estado=estado,
                error=None,
                metadata={
                    "con_memoria": con_memoria,
                    "recursion_limit": recursion_limit,
                    "limites": validacion_limites,
                    "metricas": metricas,
                    "advertencias_operativas": (
                        advertencias
                    ),
                },
                ruta_archivo=ruta_trazabilidad,
            )

        return {
            "exito": estado not in {
                "ERROR",
                "ERROR_VALIDACION",
            },
            "estado": estado,
            "respuesta": respuesta,
            "tools_utilizadas": tools_utilizadas,
            "resultados_tools": resultados_tools,
            "latencia_segundos": round(
                latencia,
                4,
            ),
            "metricas": metricas,
            "advertencias": advertencias,
            "trace_id": (
                registro["trace_id"]
                if registro
                else None
            ),
            "error": None,
            "codigo_error": None,
            "reintentable": None,
            "resultado_crudo": resultado,
        }

    except Exception as error:
        latencia = perf_counter() - inicio

        clasificacion = clasificar_error(
            error=error
        )

        respuesta = construir_respuesta_error(
            clasificacion=clasificacion
        )

        metricas = crear_metricas_vacias(
            latencia_segundos=latencia
        )

        registro = None

        if registrar_traza:
            registro = registrar_interaccion(
                thread_id=thread_limpio,
                consulta=consulta_limpia,
                respuesta=respuesta,
                tools_utilizadas=[],
                resultados_tools=[],
                latencia_segundos=latencia,
                estado="ERROR",
                error=(
                    f"{type(error).__name__}: {error}"
                ),
                metadata={
                    "con_memoria": con_memoria,
                    "recursion_limit": recursion_limit,
                    "limites": validacion_limites,
                    "codigo_error": (
                        clasificacion["codigo"]
                    ),
                    "reintentable": (
                        clasificacion["reintentable"]
                    ),
                    "metricas": metricas,
                    "advertencias_operativas": [],
                },
                ruta_archivo=ruta_trazabilidad,
            )

        return {
            "exito": False,
            "estado": "ERROR",
            "respuesta": respuesta,
            "tools_utilizadas": [],
            "resultados_tools": [],
            "latencia_segundos": round(
                latencia,
                4,
            ),
            "metricas": metricas,
            "advertencias": [],
            "trace_id": (
                registro["trace_id"]
                if registro
                else None
            ),
            "error": str(error),
            "codigo_error": clasificacion["codigo"],
            "reintentable": clasificacion[
                "reintentable"
            ],
            "resultado_crudo": None,
        }