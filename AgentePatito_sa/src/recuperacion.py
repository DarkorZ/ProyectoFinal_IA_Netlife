"""
Servicios de recuperación semántica de Patito S.A.

Este módulo consulta los índices Chroma existentes y devuelve
los fragmentos más cercanos a una pregunta.

Todavía no genera respuestas con Gemini y no crea agentes.
"""

from typing import Any

from langchain_chroma import Chroma

from src.config import TOP_K


def buscar_en_indice(
    vectorstore: Chroma,
    consulta: str,
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    """
    Recupera los fragmentos más cercanos a una consulta.

    Args:
        vectorstore:
            Índice Chroma que será consultado.

        consulta:
            Pregunta o texto del usuario.

        top_k:
            Número máximo de fragmentos que se recuperarán.

    Returns:
        list[dict]:
            Fragmentos recuperados junto con sus metadatos
            y distancia semántica.

    Raises:
        ValueError:
            Si la consulta está vacía o top_k no es válido.
    """

    consulta_limpia = consulta.strip()

    if not consulta_limpia:
        raise ValueError(
            "La consulta no puede estar vacía."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k debe ser mayor que cero."
        )

    resultados_chroma = (
        vectorstore.similarity_search_with_score(
            query=consulta_limpia,
            k=top_k,
        )
    )

    resultados = []

    for posicion, resultado in enumerate(
        resultados_chroma,
        start=1,
    ):
        documento, distancia = resultado

        resultados.append(
            {
                "posicion": posicion,
                "contenido": documento.page_content,
                "fuente": documento.metadata.get(
                    "source",
                    "fuente_desconocida",
                ),
                "agente": documento.metadata.get(
                    "agent",
                    "agente_desconocido",
                ),
                "chunk_id": documento.metadata.get(
                    "chunk_id",
                    "sin_id",
                ),
                "caracteres": documento.metadata.get(
                    "characters",
                    len(documento.page_content),
                ),
                "distancia": float(distancia),
            }
        )

    return resultados


def construir_contexto(
    resultados: list[dict[str, Any]],
) -> str:
    """
    Convierte los resultados recuperados en texto estructurado.

    Este formato será reutilizado posteriormente por los agentes.

    Args:
        resultados:
            Fragmentos obtenidos mediante búsqueda semántica.

    Returns:
        str:
            Contexto con fuentes y fragmentos.
    """

    if not resultados:
        return (
            "No se encontraron fragmentos en la base "
            "de conocimiento consultada."
        )

    bloques = []

    for resultado in resultados:
        bloque = (
            f"[Fuente: {resultado['fuente']} | "
            f"Agente: {resultado['agente']} | "
            f"Chunk: {resultado['chunk_id']}]\n"
            f"{resultado['contenido']}"
        )

        bloques.append(bloque)

    return "\n\n---\n\n".join(bloques)