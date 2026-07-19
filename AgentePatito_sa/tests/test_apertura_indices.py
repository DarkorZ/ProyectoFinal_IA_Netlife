"""
Prueba de apertura de los índices Chroma existentes.

Esta prueba verifica que:

1. Los tres directorios existan.
2. Las tres colecciones puedan abrirse.
3. Los documentos persistidos sigan disponibles.
4. No sea necesario reconstruir los índices.
"""

import sys
from pathlib import Path
from time import perf_counter


BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.indexacion import (  # noqa: E402
    abrir_todos_los_indices,
    contar_documentos_indice,
)


CANTIDADES_ESPERADAS = {
    "catalogo": 3,
    "politicas": 4,
    "crm": 3,
}


def ejecutar_prueba() -> None:
    """
    Abre y valida los tres índices existentes.
    """

    print("=" * 65)
    print("PRUEBA DE APERTURA DE ÍNDICES — PATITO S.A.")
    print("=" * 65)

    inicio = perf_counter()

    try:
        indices = abrir_todos_los_indices()

        print("\nÍndices abiertos:\n")

        total_documentos = 0

        for nombre, vectorstore in indices.items():
            cantidad = contar_documentos_indice(
                vectorstore=vectorstore
            )

            cantidad_esperada = CANTIDADES_ESPERADAS[nombre]

            if cantidad != cantidad_esperada:
                raise ValueError(
                    f"La base '{nombre}' contiene {cantidad} "
                    f"fragmentos, pero se esperaban "
                    f"{cantidad_esperada}."
                )

            total_documentos += cantidad

            print(f"Base: {nombre}")
            print(f"  Fragmentos encontrados: {cantidad}")
            print("  Estado: correcta")
            print()

        if total_documentos != 10:
            raise ValueError(
                f"Se esperaban 10 fragmentos en total, "
                f"pero se encontraron {total_documentos}."
            )

        duracion = perf_counter() - inicio

        print(f"Total de fragmentos: {total_documentos}")
        print(f"Tiempo de apertura: {duracion:.2f} segundos")

    except Exception as error:
        print("\nERROR DURANTE LA APERTURA:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 65)
    print("LOS TRES ÍNDICES SE ABRIERON CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    ejecutar_prueba()