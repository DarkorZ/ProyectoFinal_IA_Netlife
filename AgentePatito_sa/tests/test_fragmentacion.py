"""
Prueba de carga y fragmentación de documentos.

Esta prueba no llama a Gemini y no consume embeddings.
Solamente verifica que los tres documentos puedan:

1. Leerse correctamente.
2. Convertirse en objetos Document.
3. Dividirse en fragmentos.
4. Conservar metadatos de trazabilidad.
"""

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.config import (  # noqa: E402
    CHUNK_OVERLAP,
    CHUNK_SIZE,
)

from src.indexacion import (  # noqa: E402
    cargar_todas_las_bases,
)


def mostrar_resumen_base(
    nombre_base: str,
    fragmentos: list,
) -> None:
    """
    Muestra un resumen de los fragmentos generados.
    """

    if not fragmentos:
        raise ValueError(
            f"La base {nombre_base} no generó fragmentos."
        )

    primer_fragmento = fragmentos[0]

    campos_requeridos = [
        "source",
        "agent",
        "document_type",
        "chunk_id",
        "characters",
    ]

    campos_faltantes = [
        campo
        for campo in campos_requeridos
        if campo not in primer_fragmento.metadata
    ]

    if campos_faltantes:
        raise ValueError(
            f"Faltan metadatos en {nombre_base}: "
            f"{campos_faltantes}"
        )

    vista_previa = (
        primer_fragmento.page_content[:200]
        .replace("\n", " ")
        .strip()
    )

    print(f"\nBase: {nombre_base}")
    print(f"Documento: {primer_fragmento.metadata['source']}")
    print(f"Agente: {primer_fragmento.metadata['agent']}")
    print(f"Cantidad de fragmentos: {len(fragmentos)}")
    print(
        "Tamaño del primer fragmento: "
        f"{len(primer_fragmento.page_content)} caracteres"
    )
    print(
        "Vista previa del primer fragmento:"
    )
    print(f"  {vista_previa}...")


def ejecutar_prueba() -> None:
    """
    Ejecuta la prueba de las tres bases documentales.
    """

    print("=" * 65)
    print("PRUEBA DE CARGA Y FRAGMENTACIÓN — PATITO S.A.")
    print("=" * 65)

    print(f"\nChunk size configurado: {CHUNK_SIZE}")
    print(f"Chunk overlap configurado: {CHUNK_OVERLAP}")

    try:
        bases = cargar_todas_las_bases()

        if len(bases) != 3:
            raise ValueError(
                "Se esperaban exactamente tres bases "
                "de conocimiento."
            )

        for nombre_base, fragmentos in bases.items():
            mostrar_resumen_base(
                nombre_base=nombre_base,
                fragmentos=fragmentos,
            )

    except UnicodeDecodeError as error:
        print("\nERROR DE CODIFICACIÓN:")
        print(
            "Uno de los documentos no se encuentra "
            "guardado en UTF-8."
        )
        print(error)
        raise SystemExit(1) from error

    except Exception as error:
        print("\nERROR DURANTE LA FRAGMENTACIÓN:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 65)
    print("LOS TRES DOCUMENTOS SE FRAGMENTARON CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    ejecutar_prueba()