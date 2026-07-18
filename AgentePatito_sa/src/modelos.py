"""
Creación centralizada de los modelos de Google Gemini.

Este módulo ofrece funciones para construir:
- El modelo de lenguaje utilizado por los agentes.
- El modelo de embeddings utilizado por los índices RAG.

Centralizar estos objetos permite cambiar un modelo o parámetro
sin modificar todos los agentes del proyecto.
"""

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)

from src.config import (
    GOOGLE_API_KEY,
    MAX_RETRIES,
    MODELO_EMBEDDING,
    MODELO_LLM,
    TEMPERATURE,
    TIMEOUT_SEGUNDOS,
    validar_configuracion,
)


def crear_modelo_chat() -> ChatGoogleGenerativeAI:
    """
    Construye el modelo de chat de Google Gemini.

    Returns:
        ChatGoogleGenerativeAI:
            Cliente que utilizarán los agentes y el orquestador.

    Raises:
        EnvironmentError:
            Si no está configurada GOOGLE_API_KEY.
    """

    validar_configuracion()

    modelo = ChatGoogleGenerativeAI(
        model=MODELO_LLM,
        google_api_key=GOOGLE_API_KEY,
        temperature=TEMPERATURE,
        timeout=TIMEOUT_SEGUNDOS,
        max_retries=MAX_RETRIES,
    )

    return modelo


def crear_modelo_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    Construye el modelo de embeddings de Google Gemini.

    Returns:
        GoogleGenerativeAIEmbeddings:
            Cliente para convertir documentos y consultas en vectores.

    Raises:
        EnvironmentError:
            Si no está configurada GOOGLE_API_KEY.
    """

    validar_configuracion()

    embeddings = GoogleGenerativeAIEmbeddings(
        model=MODELO_EMBEDDING,
        google_api_key=GOOGLE_API_KEY,
    )

    return embeddings