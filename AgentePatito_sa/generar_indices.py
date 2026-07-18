"""
Script de generación de índices vectoriales de Patito S.A.

Debe ejecutarse cuando:

1. Se configura el proyecto por primera vez.
2. Se modifica alguno de los documentos TXT.
3. Se cambia la estrategia de fragmentación.
4. Se cambia el modelo de embeddings.

Uso:
    python generar_indices.py
"""

from time import perf_counter

from src.config import (
    COLECCION_CATALOGO,
    COLECCION_CRM,
    COLECCION_POLITICAS,
    VECTORSTORE_CATALOGO,
    VECTORSTORE_CRM,
    VECTORSTORE_POLITICAS,
)

from src.indexacion import crear_todos_los_indices


CONFIGURACION_INDICES = {
    "catalogo": {
        "coleccion": COLECCION_CATALOGO,
        "ruta": VECTORSTORE_CATALOGO,
    },
    "politicas": {
        "coleccion": COLECCION_POLITICAS,
        "ruta": VECTORSTORE_POLITICAS,
    },
    "crm": {
        "coleccion": COLECCION_CRM,
        "ruta": VECTORSTORE_CRM,
    },
}


def contar_documentos(vectorstore) -> int:
    """
    Cuenta los registros almacenados en una colección Chroma.
    """

    datos = vectorstore.get()

    ids = datos.get("ids", [])

    return len(ids)


def ejecutar_generacion() -> None:
    """
    Genera los tres índices y muestra un resumen verificable.
    """

    print("=" * 65)
    print("GENERACIÓN DE ÍNDICES VECTORIALES — PATITO S.A.")
    print("=" * 65)

    inicio_total = perf_counter()

    try:
        indices = crear_todos_los_indices()

        print("\nÍndices creados:\n")

        total_fragmentos = 0

        for nombre, vectorstore in indices.items():
            configuracion = CONFIGURACION_INDICES[nombre]

            cantidad = contar_documentos(
                vectorstore=vectorstore
            )

            total_fragmentos += cantidad

            print(f"Base: {nombre}")
            print(
                f"  Colección: "
                f"{configuracion['coleccion']}"
            )
            print(
                f"  Ruta: "
                f"{configuracion['ruta']}"
            )
            print(
                f"  Fragmentos almacenados: "
                f"{cantidad}"
            )
            print()

        duracion_total = (
            perf_counter() - inicio_total
        )

        if total_fragmentos != 10:
            print(
                "ADVERTENCIA: se esperaban 10 fragmentos "
                f"en total, pero se almacenaron "
                f"{total_fragmentos}."
            )

        print(f"Total de fragmentos: {total_fragmentos}")
        print(
            f"Tiempo total: "
            f"{duracion_total:.2f} segundos"
        )

    except Exception as error:
        print("\nERROR DURANTE LA GENERACIÓN:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 65)
    print("LOS TRES ÍNDICES SE GENERARON CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    ejecutar_generacion()