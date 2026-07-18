"""
Configuración central del proyecto Patito S.A.

Este módulo:
1. Carga las variables de entorno.
2. Define los modelos y parámetros del proyecto.
3. Centraliza las rutas de archivos y directorios.
4. Valida que exista la API key de Google.

No crea agentes ni realiza llamadas a Gemini.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# RUTAS PRINCIPALES
# ============================================================

# Ruta de la carpeta raíz del proyecto.
# __file__ corresponde a: src/config.py
# parent corresponde a: src/
# parent.parent corresponde a la raíz del proyecto.
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
VECTORSTORES_DIR = BASE_DIR / "vectorstores"
OUTPUTS_DIR = BASE_DIR / "outputs"
ASSETS_DIR = BASE_DIR / "assets"


# ============================================================
# CARGA DE VARIABLES DE ENTORNO
# ============================================================

ENV_FILE = BASE_DIR / ".env"

# Carga las variables definidas en el archivo .env.
load_dotenv(dotenv_path=ENV_FILE)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# ============================================================
# MODELOS DE GOOGLE GEMINI
# ============================================================

# Modelo utilizado para respuestas, agentes y orquestación.
MODELO_LLM = "gemini-3.5-flash"
 
# Modelo utilizado para convertir texto en vectores.
MODELO_EMBEDDING = "models/gemini-embedding-001"


# ============================================================
# PARÁMETROS DE GENERACIÓN
# ============================================================

# Una temperatura baja favorece respuestas consistentes.
TEMPERATURE = 0.0

# Tiempo máximo aproximado para una solicitud al modelo.
TIMEOUT_SEGUNDOS = 60

# Cantidad de reintentos cuando ocurre un error temporal.
MAX_RETRIES = 2


# ============================================================
# PARÁMETROS RAG
# ============================================================

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
TOP_K = 3


# ============================================================
# DOCUMENTOS DE CONOCIMIENTO
# ============================================================

ARCHIVO_CATALOGO = DATA_DIR / "01_Catalogo_Productos_Precios.txt"

ARCHIVO_POLITICAS = (
    DATA_DIR / "02_Politicas_Comerciales_Descuentos_Credito.txt"
)

ARCHIVO_CRM = DATA_DIR / "03_Proceso_Ventas_CRM.txt"


# ============================================================
# ÍNDICES VECTORIALES
# ============================================================

VECTORSTORE_CATALOGO = VECTORSTORES_DIR / "catalogo"
VECTORSTORE_POLITICAS = VECTORSTORES_DIR / "politicas"
VECTORSTORE_CRM = VECTORSTORES_DIR / "crm"


# ============================================================
# NOMBRES DE COLECCIONES CHROMA
# ============================================================

COLECCION_CATALOGO = "patito_catalogo"
COLECCION_POLITICAS = "patito_politicas"
COLECCION_CRM = "patito_crm"


# ============================================================
# VALIDACIONES
# ============================================================

def validar_configuracion() -> None:
    """
    Valida los elementos indispensables antes de ejecutar el proyecto.

    Raises:
        EnvironmentError:
            Cuando GOOGLE_API_KEY no existe o está vacía.
        FileNotFoundError:
            Cuando no se encuentra alguno de los documentos.
    """

    if not GOOGLE_API_KEY:
        raise EnvironmentError(
            "No se encontró GOOGLE_API_KEY. "
            "Verifica que exista el archivo .env en la raíz del proyecto."
        )

    archivos_requeridos = [
        ARCHIVO_CATALOGO,
        ARCHIVO_POLITICAS,
        ARCHIVO_CRM,
    ]

    archivos_faltantes = [
        archivo.name
        for archivo in archivos_requeridos
        if not archivo.exists()
    ]

    if archivos_faltantes:
        nombres = ", ".join(archivos_faltantes)

        raise FileNotFoundError(
            "No se encontraron los siguientes documentos en data/: "
            f"{nombres}"
        )


def crear_directorios_necesarios() -> None:
    """
    Crea los directorios que utilizará la aplicación.

    No elimina ni sobrescribe archivos existentes.
    """

    directorios = [
        DATA_DIR,
        VECTORSTORE_CATALOGO,
        VECTORSTORE_POLITICAS,
        VECTORSTORE_CRM,
        OUTPUTS_DIR,
        ASSETS_DIR,
    ]

    for directorio in directorios:
        directorio.mkdir(parents=True, exist_ok=True)
