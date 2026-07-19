"""
Prueba de recuperación semántica.

Comprueba que cada índice:

1. Reciba una consulta.
2. Devuelva fragmentos.
3. Mantenga sus fuentes y metadatos.
4. Recupere exclusivamente documentos de su agente.
"""

import sys
from pathlib import Path
from time import perf_counter


BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.config import TOP_K  # noqa: E402
from src.indexacion import abrir_todos_los_indices  # noqa: E402
from src.recuperacion import buscar_en_indice  # noqa: E402


CASOS_PRUEBA = {
    "catalogo": (
        "¿Cuáles son los productos disponibles, "
        "sus precios y características?"
    ),

    "politicas": (
        "¿Qué descuentos comerciales se pueden aplicar "
        "y cuáles son las condiciones de crédito?"
    ),

    "crm": (
        "¿Cuáles son las etapas del embudo de ventas "
        "y qué información debe registrarse en el CRM?"
    ),
}


def mostrar_resultados(
    nombre_base: str,
    consulta: str,
    resultados: list[dict],
) -> None:
    """
    Presenta los fragmentos recuperados.
    """

    if not resultados:
        raise ValueError(
            f"La base '{nombre_base}' no devolvió resultados."
        )

    print("\n" + "-" * 65)
    print(f"BASE CONSULTADA: {nombre_base}")
    print(f"CONSULTA: {consulta}")
    print("-" * 65)

    for resultado in resultados:
        if resultado["agente"] != nombre_base:
            raise ValueError(
                f"La base '{nombre_base}' recuperó un fragmento "
                f"perteneciente al agente "
                f"'{resultado['agente']}'."
            )

        vista_previa = (
            resultado["contenido"][:250]
            .replace("\n", " ")
            .strip()
        )

        print(
            f"\nResultado {resultado['posicion']}"
        )
        print(
            f"  Fuente: {resultado['fuente']}"
        )
        print(
            f"  Agente: {resultado['agente']}"
        )
        print(
            f"  Chunk: {resultado['chunk_id']}"
        )
        print(
            f"  Distancia: "
            f"{resultado['distancia']:.6f}"
        )
        print(
            f"  Vista previa: {vista_previa}..."
        )


def ejecutar_prueba() -> None:
    """
    Ejecuta una consulta sobre cada índice.
    """

    print("=" * 65)
    print("PRUEBA DE RECUPERACIÓN SEMÁNTICA — PATITO S.A.")
    print("=" * 65)

    print(f"\nTOP_K configurado: {TOP_K}")

    try:
        indices = abrir_todos_los_indices()

        for nombre_base, consulta in CASOS_PRUEBA.items():
            inicio = perf_counter()

            resultados = buscar_en_indice(
                vectorstore=indices[nombre_base],
                consulta=consulta,
                top_k=TOP_K,
            )

            latencia = perf_counter() - inicio

            mostrar_resultados(
                nombre_base=nombre_base,
                consulta=consulta,
                resultados=resultados,
            )

            print(
                f"\nLatencia de recuperación: "
                f"{latencia:.2f} segundos"
            )

    except Exception as error:
        print("\nERROR DURANTE LA RECUPERACIÓN:")
        print(f"{type(error).__name__}: {error}")
        raise SystemExit(1) from error

    print("\n" + "=" * 65)
    print("LAS TRES BASES RECUPERARON FRAGMENTOS CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    ejecutar_prueba()