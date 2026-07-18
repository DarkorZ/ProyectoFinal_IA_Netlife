"""
Prueba inicial de conexión con Google Gemini.

Este archivo comprueba:
1. La configuración del proyecto.
2. La disponibilidad del modelo de chat.
3. La disponibilidad del modelo de embeddings.

No crea índices ni agentes.
"""

import sys
from pathlib import Path
from time import perf_counter


# Permite ejecutar el archivo directamente desde la carpeta raíz.
BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.config import (  # noqa: E402
    MODELO_EMBEDDING,
    MODELO_LLM,
    crear_directorios_necesarios,
    validar_configuracion,
)

from src.modelos import (  # noqa: E402
    crear_modelo_chat,
    crear_modelo_embeddings,
)


def probar_configuracion() -> None:
    """
    Verifica variables de entorno, documentos y directorios.
    """

    print("\n1. Validando configuración...")

    crear_directorios_necesarios()
    validar_configuracion()

    print("   Configuración válida.")
    print(f"   Modelo LLM: {MODELO_LLM}")
    print(f"   Modelo de embeddings: {MODELO_EMBEDDING}")


def probar_modelo_chat() -> None:
    """
    Envía una instrucción mínima al modelo de chat.
    """

    print("\n2. Probando modelo de chat...")

    modelo = crear_modelo_chat()

    inicio = perf_counter()

    respuesta = modelo.invoke(
        "Responde únicamente con el texto: Conexión Gemini correcta."
    )

    latencia = perf_counter() - inicio

    contenido = respuesta.content

    if isinstance(contenido, list):
        texto = " ".join(
            bloque.get("text", "")
            for bloque in contenido
            if isinstance(bloque, dict)
        ).strip()
    else:
        texto = str(contenido).strip()

    if not texto:
        raise RuntimeError(
            "Gemini respondió, pero no se obtuvo contenido de texto."
        )

    print(f"   Respuesta: {texto}")
    print(f"   Latencia: {latencia:.2f} segundos")


def probar_embeddings() -> None:
    """
    Genera un vector a partir de una frase pequeña.
    """

    print("\n3. Probando modelo de embeddings...")

    embeddings = crear_modelo_embeddings()

    inicio = perf_counter()

    vector = embeddings.embed_query(
        "Consulta de prueba sobre el catálogo de Patito S.A."
    )

    latencia = perf_counter() - inicio

    if not vector:
        raise RuntimeError(
            "El modelo de embeddings devolvió un vector vacío."
        )

    if not all(isinstance(valor, float) for valor in vector):
        raise TypeError(
            "El embedding contiene valores que no son numéricos."
        )

    print("   Embedding generado correctamente.")
    print(f"   Dimensiones del vector: {len(vector)}")
    print(f"   Latencia: {latencia:.2f} segundos")

    # No mostramos el vector completo porque es extenso
    # y no aporta valor a la demostración.


def ejecutar_pruebas() -> None:
    """
    Ejecuta todas las pruebas y presenta errores controlados.
    """

    print("=" * 60)
    print("PRUEBA DE CONEXIÓN — PATITO S.A.")
    print("=" * 60)

    try:
        probar_configuracion()
        probar_modelo_chat()
        probar_embeddings()

    except EnvironmentError as error:
        print("\nERROR DE CONFIGURACIÓN:")
        print(error)
        raise SystemExit(1) from error

    except FileNotFoundError as error:
        print("\nERROR DE ARCHIVOS:")
        print(error)
        raise SystemExit(1) from error

    except Exception as error:
        print("\nERROR DURANTE LA CONEXIÓN:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 60)
    print("TODAS LAS PRUEBAS FINALIZARON CORRECTAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    ejecutar_pruebas()