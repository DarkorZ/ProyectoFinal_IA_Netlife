"""
Interfaz Streamlit del Asistente Comercial Patito S.A.

La interfaz no contiene la lógica interna de los agentes.

Todas las solicitudes pasan por:

    ejecutar_consulta_orquestador()

De esta forma se aplican automáticamente:

- Seguridad.
- Límites operativos.
- Memoria conversacional.
- Orquestación multiagente.
- Trazabilidad.
- Métricas.
- Manejo de errores.
"""

from typing import Any

import streamlit as st

from src.config import (
    MAX_CONSULTA_CARACTERES,
    MODELO_LLM,
)
from src.ejecucion import ejecutar_consulta_orquestador
from src.interfaz import (
    acortar_identificador,
    crear_mensaje_bienvenida,
    obtener_consultas_ejemplo,
    preparar_resultado_para_ui,
)
from src.memoria import generar_thread_id
from src.monitoreo import generar_resumen_monitoreo


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Asistente Patito S.A.",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

def inicializar_estado() -> None:
    """
    Inicializa las variables utilizadas por Streamlit.

    Cada sesión del navegador recibe un thread_id independiente.
    """

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = generar_thread_id(
            "streamlit"
        )

    if "mensajes_ui" not in st.session_state:
        st.session_state.mensajes_ui = [
            {
                "role": "assistant",
                "content": crear_mensaje_bienvenida(),
                "metadata": None,
            }
        ]

    if "cantidad_consultas" not in st.session_state:
        st.session_state.cantidad_consultas = 0


def iniciar_nueva_conversacion() -> None:
    """
    Genera una conversación nueva y limpia el historial visual.

    La trazabilidad histórica guardada en outputs no se elimina.
    """

    st.session_state.thread_id = generar_thread_id(
        "streamlit"
    )

    st.session_state.mensajes_ui = [
        {
            "role": "assistant",
            "content": crear_mensaje_bienvenida(),
            "metadata": None,
        }
    ]

    st.session_state.cantidad_consultas = 0


inicializar_estado()


# ============================================================
# FUNCIONES VISUALES
# ============================================================

def mostrar_estado(
    metadata: dict[str, Any],
) -> None:
    """
    Muestra visualmente el estado de una interacción.
    """

    etiqueta = metadata.get(
        "estado_etiqueta",
        "Desconocido",
    )

    nivel = metadata.get(
        "estado_nivel",
        "info",
    )

    mensaje = (
        f"Estado de la interacción: {etiqueta}"
    )

    if nivel == "success":
        st.success(
            mensaje,
            icon="✅",
        )

    elif nivel == "warning":
        st.warning(
            mensaje,
            icon="⚠️",
        )

    elif nivel == "error":
        st.error(
            mensaje,
            icon="🚨",
        )

    else:
        st.info(
            mensaje,
            icon="ℹ️",
        )


def mostrar_detalles_ejecucion(
    metadata: dict[str, Any],
) -> None:
    """
    Presenta las métricas y la trazabilidad de una respuesta.
    """

    with st.expander(
        "Detalles de ejecución",
        expanded=False,
    ):
        mostrar_estado(
            metadata=metadata
        )

        columna_1, columna_2, columna_3 = st.columns(
            3
        )

        latencia = float(
            metadata.get(
                "latencia_segundos",
                0.0,
            )
            or 0.0
        )

        tokens = int(
            metadata.get(
                "total_tokens",
                0,
            )
            or 0
        )

        cantidad_tools = int(
            metadata.get(
                "cantidad_tool_calls",
                0,
            )
            or 0
        )

        with columna_1:
            st.metric(
                label="Latencia",
                value=f"{latencia:.2f} s",
            )

        with columna_2:
            st.metric(
                label="Tokens visibles",
                value=tokens,
            )

        with columna_3:
            st.metric(
                label="Tool calls",
                value=cantidad_tools,
            )

        st.caption(
            "Las métricas de tokens corresponden a los mensajes "
            "visibles de la ejecución principal."
        )

        tools = metadata.get(
            "tools_utilizadas",
            [],
        )

        if tools:
            st.markdown(
                "**Tools utilizadas**"
            )

            for nombre_tool in tools:
                st.code(
                    nombre_tool,
                    language=None,
                )

        else:
            st.markdown(
                "**Tools utilizadas:** ninguna"
            )

        llamadas_modelo = metadata.get(
            "llamadas_modelo_estimadas",
            0,
        )

        st.markdown(
            "**Llamadas estimadas al modelo:** "
            f"{llamadas_modelo}"
        )

        trace_id = metadata.get(
            "trace_id"
        )

        if trace_id:
            st.markdown(
                "**Trace ID**"
            )

            st.code(
                trace_id,
                language=None,
            )

        codigo_seguridad = metadata.get(
            "codigo_seguridad"
        )

        if codigo_seguridad:
            st.markdown(
                "**Código de seguridad**"
            )

            st.code(
                codigo_seguridad,
                language=None,
            )

        codigo_error = metadata.get(
            "codigo_error"
        )

        if codigo_error:
            st.markdown(
                "**Código de error**"
            )

            st.code(
                codigo_error,
                language=None,
            )

        advertencias = metadata.get(
            "advertencias",
            [],
        )

        if advertencias:
            st.markdown(
                "**Advertencias operativas**"
            )

            for advertencia in advertencias:
                st.warning(
                    advertencia
                )


def mostrar_mensaje(
    mensaje: dict[str, Any],
) -> None:
    """
    Dibuja un mensaje almacenado en el historial visual.
    """

    role = mensaje.get(
        "role",
        "assistant",
    )

    content = mensaje.get(
        "content",
        "",
    )

    metadata = mensaje.get(
        "metadata"
    )

    with st.chat_message(
        role
    ):
        st.markdown(
            content
        )

        if (
            role == "assistant"
            and isinstance(
                metadata,
                dict,
            )
        ):
            mostrar_detalles_ejecucion(
                metadata=metadata
            )


# ============================================================
# BARRA LATERAL
# ============================================================

consulta_ejemplo = None

with st.sidebar:
    st.title(
        "Panel del sistema"
    )

    st.markdown(
        "**Modelo configurado**"
    )

    st.code(
        MODELO_LLM,
        language=None,
    )

    st.markdown(
        "**Conversación actual**"
    )

    st.code(
        acortar_identificador(
            st.session_state.thread_id
        ),
        language=None,
    )

    st.caption(
        "Cada conversación utiliza un thread_id "
        "independiente para conservar la memoria."
    )

    st.metric(
        label="Consultas en esta sesión",
        value=st.session_state.cantidad_consultas,
    )

    if st.button(
        "Nueva conversación",
        use_container_width=True,
        type="primary",
    ):
        iniciar_nueva_conversacion()
        st.rerun()

    st.divider()

    st.subheader(
        "Consultas de ejemplo"
    )

    consultas_ejemplo = obtener_consultas_ejemplo()

    for etiqueta, consulta in consultas_ejemplo.items():
        if st.button(
            etiqueta,
            key=f"ejemplo_{etiqueta}",
            use_container_width=True,
        ):
            consulta_ejemplo = consulta

    st.divider()

    st.subheader(
        "Monitoreo acumulado"
    )

    try:
        resumen_monitoreo = generar_resumen_monitoreo()

        total_interacciones = resumen_monitoreo.get(
            "total_interacciones",
            0,
        )

        latencia_promedio = float(
            resumen_monitoreo.get(
                "latencia_promedio_segundos",
                0.0,
            )
            or 0.0
        )

        tokens_acumulados = resumen_monitoreo.get(
            "tokens_totales",
            0,
        )

        st.metric(
            label="Interacciones registradas",
            value=total_interacciones,
        )

        st.metric(
            label="Latencia promedio",
            value=f"{latencia_promedio:.2f} s",
        )

        st.metric(
            label="Tokens visibles acumulados",
            value=tokens_acumulados,
        )

        estados_historicos = resumen_monitoreo.get(
            "estados",
            {},
        )

        if estados_historicos:
            st.markdown(
                "**Estados históricos**"
            )

            st.json(
                estados_historicos
            )

        agentes_historicos = resumen_monitoreo.get(
            "agentes",
            {},
        )

        if agentes_historicos:
            st.markdown(
                "**Agentes utilizados**"
            )

            st.json(
                agentes_historicos
            )

    except Exception as error:
        st.warning(
            "No fue posible cargar el resumen "
            "de monitoreo."
        )

        st.caption(
            "Detalle local: "
            f"{type(error).__name__}"
        )

    st.divider()

    st.caption(
        "Los archivos generados dentro de outputs contienen "
        "registros y trazabilidad local. No deben incluirse "
        "en GitHub."
    )


# ============================================================
# ENCABEZADO PRINCIPAL
# ============================================================

st.title(
    "Asistente Comercial Patito S.A."
)

st.markdown(
    """
Sistema multiagente para consultas comerciales y registro
controlado de oportunidades.
"""
)

st.caption(
    "Dominios disponibles: Catálogo, Políticas Comerciales, "
    "Proceso de Ventas, CRM y Registro de Oportunidades."
)

st.divider()


# ============================================================
# HISTORIAL VISUAL
# ============================================================

for mensaje_guardado in st.session_state.mensajes_ui:
    mostrar_mensaje(
        mensaje=mensaje_guardado
    )


# ============================================================
# ENTRADA DEL USUARIO
# ============================================================

consulta_chat = st.chat_input(
    placeholder=(
        "Escribe una consulta comercial..."
    ),
    max_chars=MAX_CONSULTA_CARACTERES,
)

consulta_usuario = (
    consulta_ejemplo
    if consulta_ejemplo
    else consulta_chat
)


# ============================================================
# EJECUCIÓN DE LA CONSULTA
# ============================================================

if consulta_usuario:
    consulta_limpia = str(
        consulta_usuario
    ).strip()

    if consulta_limpia:
        mensaje_usuario = {
            "role": "user",
            "content": consulta_limpia,
            "metadata": None,
        }

        st.session_state.mensajes_ui.append(
            mensaje_usuario
        )

        with st.chat_message(
            "user"
        ):
            st.markdown(
                consulta_limpia
            )

        with st.chat_message(
            "assistant"
        ):
            with st.spinner(
                "Analizando la solicitud..."
            ):
                resultado = ejecutar_consulta_orquestador(
                    consulta=consulta_limpia,
                    thread_id=(
                        st.session_state.thread_id
                    ),
                    con_memoria=True,
                )

            respuesta = resultado.get(
                "respuesta",
                (
                    "ERROR_CONTROLADO:\n"
                    "No se obtuvo una respuesta del sistema."
                ),
            )

            metadata_ui = preparar_resultado_para_ui(
                resultado=resultado
            )

            st.markdown(
                respuesta
            )

            mostrar_detalles_ejecucion(
                metadata=metadata_ui
            )

        mensaje_asistente = {
            "role": "assistant",
            "content": respuesta,
            "metadata": metadata_ui,
        }

        st.session_state.mensajes_ui.append(
            mensaje_asistente
        )

        st.session_state.cantidad_consultas += 1