"""
Configuración de memoria conversacional del sistema.

La memoria se utiliza para conservar el estado de una conversación
entre diferentes invocaciones del orquestador.

Cada conversación debe utilizar un thread_id diferente.

Durante el desarrollo se utiliza InMemorySaver. Su contenido existe
únicamente mientras el proceso de Python permanece activo.
"""

from functools import lru_cache
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver


@lru_cache(maxsize=1)
def obtener_memoria_corta() -> InMemorySaver:
    """
    Crea una única instancia de memoria en proceso.

    El uso de lru_cache evita generar un checkpointer diferente
    cada vez que se construye el orquestador.

    Returns:
        InMemorySaver:
            Almacén de estado temporal utilizado por LangGraph.
    """

    return InMemorySaver()


def generar_thread_id(
    prefijo: str = "patito",
) -> str:
    """
    Genera un identificador único para una conversación.

    Ejemplo:
        patito-a34c92256bb34a67a51605de458fa204

    Args:
        prefijo:
            Texto que permite identificar el origen del hilo.

    Returns:
        str:
            Identificador único de conversación.
    """

    prefijo_limpio = (
        prefijo.strip().lower().replace(" ", "-")
    )

    if not prefijo_limpio:
        prefijo_limpio = "patito"

    return (
        f"{prefijo_limpio}-"
        f"{uuid4().hex}"
    )