"""
Carga y fragmentación de las bases de conocimiento de Patito S.A.

Este módulo se encarga de:

1. Leer los documentos TXT.
2. Convertirlos al formato Document de LangChain.
3. Dividir cada documento en fragmentos independientes.
4. Agregar metadatos para garantizar trazabilidad.

Este archivo todavía no crea embeddings ni índices vectoriales.
"""

from pathlib import Path
import shutil

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    ARCHIVO_CATALOGO,
    ARCHIVO_CRM,
    ARCHIVO_POLITICAS,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLECCION_CATALOGO,
    COLECCION_CRM,
    COLECCION_POLITICAS,
    VECTORSTORE_CATALOGO,
    VECTORSTORE_CRM,
    VECTORSTORE_POLITICAS,
    crear_directorios_necesarios,
    validar_configuracion,
)
from src.modelos import crear_modelo_embeddings

def leer_documento_txt(
    ruta_archivo: Path,
    nombre_agente: str,
) -> Document:
    """
    Lee un archivo TXT y lo convierte en un Document de LangChain.

    Args:
        ruta_archivo:
            Ruta completa del archivo que será leído.

        nombre_agente:
            Nombre del agente responsable de ese documento.

    Returns:
        Document:
            Documento con el contenido y sus metadatos.

    Raises:
        FileNotFoundError:
            Si el archivo no existe.

        ValueError:
            Si el documento está vacío.
    """

    if not ruta_archivo.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta_archivo}"
        )

    contenido = ruta_archivo.read_text(
        encoding="utf-8"
    ).strip()

    if not contenido:
        raise ValueError(
            f"El documento {ruta_archivo.name} está vacío."
        )

    documento = Document(
        page_content=contenido,
        metadata={
            "source": ruta_archivo.name,
            "agent": nombre_agente,
            "document_type": "base_conocimiento",
        },
    )

    return documento


def dividir_documento(
    documento: Document,
) -> list[Document]:
    """
    Divide un documento en fragmentos pequeños.

    Cada fragmento conserva los metadatos del documento original
    y recibe un identificador único dentro de ese documento.

    Args:
        documento:
            Documento que será dividido.

    Returns:
        list[Document]:
            Lista de fragmentos creados.
    """

    separador = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    fragmentos = separador.split_documents(
        [documento]
    )

    for numero, fragmento in enumerate(
        fragmentos,
        start=1,
    ):
        fragmento.metadata["chunk_id"] = numero
        fragmento.metadata["characters"] = len(
            fragmento.page_content
        )

    return fragmentos


def cargar_fragmentos_catalogo() -> list[Document]:
    """
    Carga y fragmenta el documento del agente de Catálogo.
    """

    documento = leer_documento_txt(
        ruta_archivo=ARCHIVO_CATALOGO,
        nombre_agente="catalogo",
    )

    return dividir_documento(documento)


def cargar_fragmentos_politicas() -> list[Document]:
    """
    Carga y fragmenta el documento del agente de Políticas.
    """

    documento = leer_documento_txt(
        ruta_archivo=ARCHIVO_POLITICAS,
        nombre_agente="politicas",
    )

    return dividir_documento(documento)


def cargar_fragmentos_crm() -> list[Document]:
    """
    Carga y fragmenta el documento del agente de CRM.
    """

    documento = leer_documento_txt(
        ruta_archivo=ARCHIVO_CRM,
        nombre_agente="crm",
    )

    return dividir_documento(documento)


def cargar_todas_las_bases() -> dict[str, list[Document]]:
    """
    Carga y fragmenta las tres bases de conocimiento.

    Returns:
        dict[str, list[Document]]:
            Diccionario que contiene los fragmentos de cada agente.
    """

    validar_configuracion()

    bases = {
        "catalogo": cargar_fragmentos_catalogo(),
        "politicas": cargar_fragmentos_politicas(),
        "crm": cargar_fragmentos_crm(),
    }

    return bases

def limpiar_directorio_indice(
    ruta_directorio: Path,
) -> None:
    """
    Elimina un índice anterior y crea nuevamente su directorio.

    Esta limpieza evita duplicar fragmentos cuando se ejecuta
    varias veces el script de generación de índices.

    Args:
        ruta_directorio:
            Directorio local donde se almacenará la base Chroma.
    """

    if ruta_directorio.exists():
        shutil.rmtree(ruta_directorio)

    ruta_directorio.mkdir(
        parents=True,
        exist_ok=True,
    )


def generar_ids_fragmentos(
    fragmentos: list[Document],
) -> list[str]:
    """
    Genera identificadores únicos y reproducibles para Chroma.

    Ejemplos:
        catalogo-chunk-1
        politicas-chunk-2
        crm-chunk-3

    Args:
        fragmentos:
            Fragmentos que serán almacenados.

    Returns:
        list[str]:
            Identificadores correspondientes a cada fragmento.
    """

    ids = []

    for fragmento in fragmentos:
        agente = fragmento.metadata["agent"]
        chunk_id = fragmento.metadata["chunk_id"]

        identificador = (
            f"{agente}-chunk-{chunk_id}"
        )

        ids.append(identificador)

    return ids


def crear_indice_vectorial(
    fragmentos: list[Document],
    ruta_indice: Path,
    nombre_coleccion: str,
    embeddings: Embeddings,
) -> Chroma:
    """
    Crea y persiste una base vectorial Chroma.

    Args:
        fragmentos:
            Documentos fragmentados que serán indexados.

        ruta_indice:
            Carpeta donde se guardará físicamente Chroma.

        nombre_coleccion:
            Nombre lógico de la colección dentro de Chroma.

        embeddings:
            Modelo encargado de convertir texto en vectores.

    Returns:
        Chroma:
            Base vectorial creada y lista para consultas.

    Raises:
        ValueError:
            Si la lista de fragmentos está vacía.
    """

    if not fragmentos:
        raise ValueError(
            f"No existen fragmentos para crear "
            f"la colección {nombre_coleccion}."
        )

    limpiar_directorio_indice(
        ruta_directorio=ruta_indice,
    )

    vectorstore = Chroma(
        collection_name=nombre_coleccion,
        embedding_function=embeddings,
        persist_directory=str(ruta_indice),
    )

    ids = generar_ids_fragmentos(
        fragmentos=fragmentos,
    )

    vectorstore.add_documents(
        documents=fragmentos,
        ids=ids,
    )

    return vectorstore


def crear_todos_los_indices() -> dict[str, Chroma]:
    """
    Crea los tres índices vectoriales independientes.

    Cada agente recibe exclusivamente:
    - Su documento.
    - Sus fragmentos.
    - Su colección Chroma.
    - Su directorio de persistencia.

    Returns:
        dict[str, Chroma]:
            Bases vectoriales de catálogo, políticas y CRM.
    """

    validar_configuracion()
    crear_directorios_necesarios()

    bases_documentales = cargar_todas_las_bases()

    # Se crea una sola instancia del modelo de embeddings
    # y se reutiliza para indexar las tres bases.
    embeddings = crear_modelo_embeddings()

    indices = {
        "catalogo": crear_indice_vectorial(
            fragmentos=bases_documentales["catalogo"],
            ruta_indice=VECTORSTORE_CATALOGO,
            nombre_coleccion=COLECCION_CATALOGO,
            embeddings=embeddings,
        ),

        "politicas": crear_indice_vectorial(
            fragmentos=bases_documentales["politicas"],
            ruta_indice=VECTORSTORE_POLITICAS,
            nombre_coleccion=COLECCION_POLITICAS,
            embeddings=embeddings,
        ),

        "crm": crear_indice_vectorial(
            fragmentos=bases_documentales["crm"],
            ruta_indice=VECTORSTORE_CRM,
            nombre_coleccion=COLECCION_CRM,
            embeddings=embeddings,
        ),
    }

    return indices

def verificar_indice_existente(
    ruta_indice: Path,
    nombre_coleccion: str,
) -> None:
    """
    Verifica que un índice Chroma haya sido generado previamente.

    Args:
        ruta_indice:
            Directorio donde debería encontrarse el índice.

        nombre_coleccion:
            Nombre lógico de la colección Chroma.

    Raises:
        FileNotFoundError:
            Si el directorio o el archivo principal de Chroma
            no existen.
    """

    if not ruta_indice.exists():
        raise FileNotFoundError(
            f"No existe el directorio del índice "
            f"'{nombre_coleccion}': {ruta_indice}. "
            "Ejecuta primero: python generar_indices.py"
        )

    archivo_chroma = ruta_indice / "chroma.sqlite3"

    if not archivo_chroma.exists():
        raise FileNotFoundError(
            f"No se encontró chroma.sqlite3 para la colección "
            f"'{nombre_coleccion}'. "
            "Ejecuta nuevamente: python generar_indices.py"
        )


def abrir_indice_vectorial(
    ruta_indice: Path,
    nombre_coleccion: str,
    embeddings: Embeddings,
) -> Chroma:
    """
    Abre una colección Chroma previamente generada.

    Esta función no agrega documentos y no vuelve a generar
    embeddings.

    Args:
        ruta_indice:
            Directorio donde está persistido el índice.

        nombre_coleccion:
            Nombre de la colección Chroma.

        embeddings:
            Modelo que se utilizará para vectorizar las consultas.

    Returns:
        Chroma:
            Índice existente listo para realizar búsquedas.
    """

    verificar_indice_existente(
        ruta_indice=ruta_indice,
        nombre_coleccion=nombre_coleccion,
    )

    vectorstore = Chroma(
        collection_name=nombre_coleccion,
        embedding_function=embeddings,
        persist_directory=str(ruta_indice),
    )

    cantidad_documentos = len(
        vectorstore.get().get("ids", [])
    )

    if cantidad_documentos == 0:
        raise ValueError(
            f"La colección '{nombre_coleccion}' existe, "
            "pero no contiene documentos."
        )

    return vectorstore


def abrir_todos_los_indices() -> dict[str, Chroma]:
    """
    Abre las tres bases vectoriales de Patito S.A.

    Returns:
        dict[str, Chroma]:
            Diccionario con los índices de catálogo,
            políticas y CRM.
    """

    validar_configuracion()

    embeddings = crear_modelo_embeddings()

    indices = {
        "catalogo": abrir_indice_vectorial(
            ruta_indice=VECTORSTORE_CATALOGO,
            nombre_coleccion=COLECCION_CATALOGO,
            embeddings=embeddings,
        ),

        "politicas": abrir_indice_vectorial(
            ruta_indice=VECTORSTORE_POLITICAS,
            nombre_coleccion=COLECCION_POLITICAS,
            embeddings=embeddings,
        ),

        "crm": abrir_indice_vectorial(
            ruta_indice=VECTORSTORE_CRM,
            nombre_coleccion=COLECCION_CRM,
            embeddings=embeddings,
        ),
    }

    return indices


def contar_documentos_indice(
    vectorstore: Chroma,
) -> int:
    """
    Retorna la cantidad de documentos almacenados
    en una colección Chroma.
    """

    datos = vectorstore.get()

    return len(datos.get("ids", []))