"""
Capa de seguridad determinística de Patito S.A.

Analiza las consultas antes de enviarlas al modelo.

Permite detectar:

- Intentos de revelar prompts internos.
- Solicitudes de credenciales o variables de entorno.
- Credenciales incluidas accidentalmente.
- Intentos de desactivar reglas.
- Intentos de registrar oportunidades sin confirmación.
- Manipulación directa de tools internas.

Este módulo no utiliza Gemini y no consume cuota.
"""

import re
import unicodedata
from typing import Any

from src.trazabilidad import sanitizar_texto


# ============================================================
# MENSAJES DE CONTROL PERMITIDOS
# ============================================================

MENSAJES_CONTROL_VALIDOS = {
    "confirmo el registro",
    "cancelo el registro",
}


# ============================================================
# REGLAS DE SEGURIDAD
# ============================================================

REGLAS_SEGURIDAD = [
    # --------------------------------------------------------
    # EXTRACCIÓN DE PROMPTS O INSTRUCCIONES INTERNAS
    # --------------------------------------------------------
    {
        "codigo": "EXTRACCION_PROMPT_INTERNO",
        "categoria": "prompt_injection",
        "detalle": (
            "No se permite solicitar prompts, instrucciones "
            "internas ni mensajes del sistema."
        ),
        "patrones": [
            (
                r"\b("
                r"revel\w*|"
                r"muestr\w*|"
                r"dime|"
                r"entreg\w*|"
                r"imprim\w*|"
                r"copi\w*|"
                r"expon\w*|"
                r"escrib\w*"
                r")\b"
                r".{0,100}"
                r"\b("
                r"system\s+prompt|"
                r"prompt\s+del\s+sistema|"
                r"instrucciones\s+internas|"
                r"mensaje\s+del\s+sistema|"
                r"reglas\s+internas"
                r")\b"
            ),
            (
                r"\b(cual|cuales|que)\b"
                r".{0,50}"
                r"\b("
                r"system\s+prompt|"
                r"prompt\s+del\s+sistema|"
                r"instrucciones\s+internas|"
                r"mensaje\s+del\s+sistema"
                r")\b"
            ),
        ],
    },

    # --------------------------------------------------------
    # SOLICITUD DE CREDENCIALES
    # --------------------------------------------------------
    {
        "codigo": "EXTRACCION_CREDENCIALES",
        "categoria": "credenciales",
        "detalle": (
            "No se permite solicitar credenciales, API keys, "
            "tokens ni variables privadas."
        ),
        "patrones": [
            (
                r"\b("
                r"revel\w*|"
                r"muestr\w*|"
                r"dime|"
                r"entreg\w*|"
                r"imprim\w*|"
                r"copi\w*|"
                r"expon\w*|"
                r"compart\w*"
                r")\b"
                r".{0,100}"
                r"\b("
                r"api\s*key|"
                r"google_api_key|"
                r"token|"
                r"credencial(?:es)?|"
                r"contrasena|"
                r"clave\s+secreta|"
                r"variables?\s+de\s+entorno"
                r")\b"
            ),
            (
                r"\b(cual|cuales|que)\b"
                r".{0,50}"
                r"\b("
                r"api\s*key|"
                r"google_api_key|"
                r"token|"
                r"credencial(?:es)?|"
                r"clave\s+secreta|"
                r"variables?\s+de\s+entorno"
                r")\b"
            ),
        ],
    },

    # --------------------------------------------------------
    # CREDENCIAL INCLUIDA EN LA CONSULTA
    # --------------------------------------------------------
    {
        "codigo": "CREDENCIAL_EN_CONSULTA",
        "categoria": "credenciales",
        "detalle": (
            "La consulta contiene una cadena con apariencia "
            "de credencial y fue bloqueada para protegerla."
        ),
        "patrones": [
            r"\baiza[a-z0-9_\-]{20,}\b",
            (
                r"\bgoogle_api_key\s*[:=]\s*"
                r"[^\s,;]+"
            ),
            (
                r"\bbearer\s+"
                r"[a-z0-9._\-]{12,}"
            ),
        ],
    },

    # --------------------------------------------------------
    # INTENTO DE DESACTIVAR REGLAS
    # --------------------------------------------------------
    {
        "codigo": "DESACTIVACION_REGLAS",
        "categoria": "prompt_injection",
        "detalle": (
            "No se permite desactivar, ignorar o sustituir "
            "las reglas de seguridad del sistema."
        ),
        "patrones": [
            (
                r"\b("
                r"ignor\w*|"
                r"omit\w*|"
                r"desactiv\w*|"
                r"elimin\w*|"
                r"olvid\w*|"
                r"salt\w*"
                r")\b"
                r".{0,100}"
                r"\b("
                r"reglas|"
                r"instrucciones|"
                r"restricciones|"
                r"seguridad|"
                r"rol|"
                r"prompt"
                r")\b"
            ),
            (
                r"\bactua\s+como\b"
                r".{0,100}"
                r"\b("
                r"sin\s+reglas|"
                r"sin\s+restricciones|"
                r"administrador\s+total"
                r")\b"
            ),
        ],
    },

    # --------------------------------------------------------
    # REGISTRO SIN CONFIRMACIÓN
    # --------------------------------------------------------
    {
        "codigo": "REGISTRO_SIN_CONFIRMACION",
        "categoria": "acciones",
        "detalle": (
            "No se permite registrar oportunidades sin "
            "confirmación explícita del usuario."
        ),
        "patrones": [
            (
                r"\b("
                r"registr\w*|"
                r"guard\w*|"
                r"cre\w*|"
                r"insert\w*"
                r")\b"
                r".{0,120}"
                r"\b("
                r"sin\s+confirmar|"
                r"sin\s+confirmacion|"
                r"omite\s+la\s+confirmacion|"
                r"no\s+pidas\s+confirmacion|"
                r"sin\s+preguntar"
                r")\b"
            ),
            r"\bconfirmado\s*=\s*true\b",
            (
                r"\busa\b"
                r".{0,80}"
                r"\bregistrar_oportunidad\b"
                r".{0,100}"
                r"\b("
                r"directamente|"
                r"sin\s+confirmar|"
                r"forzado"
                r")\b"
            ),
        ],
    },

    # --------------------------------------------------------
    # MANIPULACIÓN DIRECTA DE TOOLS
    # --------------------------------------------------------
    {
        "codigo": "MANIPULACION_TOOL_INTERNA",
        "categoria": "herramientas",
        "detalle": (
            "No se permite forzar la ejecución directa de "
            "herramientas internas."
        ),
        "patrones": [
            (
                r"\b("
                r"llam\w*|"
                r"ejecut\w*|"
                r"invoc\w*|"
                r"forz\w*"
                r")\b"
                r".{0,80}"
                r"\b("
                r"delegar_catalogo|"
                r"delegar_politicas|"
                r"delegar_crm|"
                r"delegar_accion|"
                r"registrar_oportunidad"
                r")\b"
            ),
        ],
    },
]


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalizar_para_seguridad(
    texto: str,
) -> str:
    """
    Normaliza un texto para facilitar las comparaciones.

    La función:

    - Convierte el texto a minúsculas.
    - Elimina acentos.
    - Elimina espacios repetidos.
    - Conserva guiones bajos utilizados en nombres técnicos.

    Ejemplo:

        "Muéstrame la GOOGLE_API_KEY"

    se convierte en:

        "muestrame la google_api_key"
    """

    texto_normalizado = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto_sin_acentos = "".join(
        caracter
        for caracter in texto_normalizado
        if not unicodedata.combining(caracter)
    )

    return " ".join(
        texto_sin_acentos.casefold().split()
    )


# ============================================================
# ANÁLISIS DE SEGURIDAD
# ============================================================

def analizar_consulta_seguridad(
    consulta: str,
) -> dict[str, Any]:
    """
    Analiza una consulta antes de enviarla al modelo.

    Returns:
        dict:
            Resultado de seguridad con los campos:

            - permitida;
            - codigo;
            - categoria;
            - detalle;
            - coincidencias.
    """

    if not isinstance(consulta, str):
        return {
            "permitida": False,
            "codigo": "TIPO_CONSULTA_INVALIDO",
            "categoria": "validacion",
            "detalle": (
                "La consulta debe ser una cadena de texto."
            ),
            "coincidencias": [],
        }

    consulta_limpia = consulta.strip()

    if not consulta_limpia:
        # La consulta vacía será rechazada posteriormente
        # por el módulo encargado de los límites operativos.
        return {
            "permitida": True,
            "codigo": "OK",
            "categoria": None,
            "detalle": (
                "No se detectaron riesgos de seguridad."
            ),
            "coincidencias": [],
        }

    consulta_normalizada = normalizar_para_seguridad(
        consulta_limpia
    )

    # Las expresiones utilizadas para confirmar o cancelar
    # un registro son válidas y no deben bloquearse.
    if consulta_normalizada in MENSAJES_CONTROL_VALIDOS:
        return {
            "permitida": True,
            "codigo": "OK",
            "categoria": None,
            "detalle": (
                "Mensaje de control válido."
            ),
            "coincidencias": [],
        }

    for regla in REGLAS_SEGURIDAD:
        coincidencias = []

        for patron in regla["patrones"]:
            coincidencia = re.search(
                patron,
                consulta_normalizada,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if coincidencia:
                coincidencias.append(
                    {
                        "patron": patron,
                        "texto_detectado": (
                            coincidencia.group(0)
                        ),
                    }
                )

        if coincidencias:
            return {
                "permitida": False,
                "codigo": regla["codigo"],
                "categoria": regla["categoria"],
                "detalle": regla["detalle"],
                "coincidencias": coincidencias,
            }

    return {
        "permitida": True,
        "codigo": "OK",
        "categoria": None,
        "detalle": (
            "No se detectaron riesgos de seguridad."
        ),
        "coincidencias": [],
    }


# ============================================================
# RESPUESTA CONTROLADA
# ============================================================

def construir_respuesta_seguridad(
    resultado_seguridad: dict[str, Any],
) -> str:
    """
    Construye la respuesta que se muestra cuando una solicitud
    es bloqueada por las políticas de seguridad.
    """

    return (
        "SOLICITUD_RECHAZADA:\n"
        "La solicitud fue bloqueada por las políticas "
        "de seguridad del sistema.\n"
        "\n"
        "CODIGO_SEGURIDAD:\n"
        f"{resultado_seguridad['codigo']}\n"
        "\n"
        "MOTIVO:\n"
        f"{resultado_seguridad['detalle']}\n"
        "\n"
        "ALCANCE_PERMITIDO:\n"
        "Puede consultar Catálogo, Políticas Comerciales, CRM "
        "o preparar un registro de oportunidad mediante el "
        "flujo de confirmación."
    )


# ============================================================
# SANITIZACIÓN
# ============================================================

def sanitizar_consulta_seguridad(
    consulta: str,
) -> str:
    """
    Oculta posibles credenciales antes de almacenarlas.

    Utiliza la misma sanitización aplicada por el módulo de
    trazabilidad.
    """

    return sanitizar_texto(
        consulta
    )