"""
Tool para registrar oportunidades comerciales de Patito S.A.

La escritura se realiza de forma determinística y controlada.

La herramienta:

1. Valida los datos obligatorios.
2. Exige confirmación explícita.
3. Genera un identificador único.
4. Registra fecha y hora.
5. Detecta registros duplicados.
6. Guarda cada oportunidad como una línea JSON dentro de un TXT.

El agente de lenguaje no escribe directamente en el archivo.
"""

import hashlib
import json
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DIRECTORIO_OUTPUTS = BASE_DIR / "outputs"

ARCHIVO_OPORTUNIDADES = (
    DIRECTORIO_OUTPUTS
    / "registro_oportunidades.txt"
)


ETAPAS_VALIDAS = {
    "prospecto",
    "contacto",
    "calificación",
    "calificacion",
    "propuesta/cotización",
    "propuesta/cotizacion",
    "negociación",
    "negociacion",
    "cierre ganada",
    "cierre perdida",
    "posventa",
}


# Ecuador continental utiliza UTC-5.
ZONA_HORARIA_ECUADOR = timezone(
    timedelta(hours=-5)
)


# ============================================================
# ESQUEMA DE ENTRADA
# ============================================================

class EntradaRegistroOportunidad(BaseModel):
    """
    Datos necesarios para registrar una oportunidad comercial.
    """

    cliente: str = Field(
        min_length=2,
        description=(
            "Nombre completo del cliente o razón social."
        ),
    )

    contacto: str = Field(
        min_length=3,
        description=(
            "Correo electrónico, teléfono u otro medio "
            "de contacto."
        ),
    )

    productos: list[str] = Field(
        min_length=1,
        description=(
            "Lista de productos de interés del cliente."
        ),
    )

    cantidad_total: int = Field(
        ge=1,
        description=(
            "Cantidad total estimada de productos."
        ),
    )

    monto_estimado: float = Field(
        gt=0,
        description=(
            "Monto estimado de la oportunidad en USD."
        ),
    )

    etapa: str = Field(
        min_length=3,
        description=(
            "Etapa actual del proceso comercial."
        ),
    )

    proxima_accion: str = Field(
        min_length=3,
        description=(
            "Siguiente actividad que debe realizarse."
        ),
    )

    vendedor: str = Field(
        min_length=2,
        description=(
            "Nombre del vendedor responsable."
        ),
    )

    descuento: float = Field(
        default=0.0,
        ge=0,
        le=30,
        description=(
            "Porcentaje de descuento propuesto."
        ),
    )

    condicion_pago: str = Field(
        default="Por definir",
        min_length=3,
        description=(
            "Condición de pago acordada o propuesta."
        ),
    )

    confirmado: bool = Field(
        description=(
            "Debe ser True únicamente cuando el usuario haya "
            "confirmado expresamente el registro."
        ),
    )

    @field_validator(
        "cliente",
        "contacto",
        "etapa",
        "proxima_accion",
        "vendedor",
        "condicion_pago",
    )
    @classmethod
    def limpiar_campos_texto(
        cls,
        valor: str,
    ) -> str:
        """
        Elimina espacios innecesarios de los campos.
        """

        valor_limpio = " ".join(
            valor.strip().split()
        )

        if not valor_limpio:
            raise ValueError(
                "El campo no puede quedar vacío."
            )

        return valor_limpio

    @field_validator("productos")
    @classmethod
    def limpiar_productos(
        cls,
        productos: list[str],
    ) -> list[str]:
        """
        Limpia la lista y elimina productos vacíos.
        """

        productos_limpios = []

        for producto in productos:
            producto_limpio = " ".join(
                producto.strip().split()
            )

            if producto_limpio:
                productos_limpios.append(
                    producto_limpio
                )

        if not productos_limpios:
            raise ValueError(
                "Debe existir al menos un producto válido."
            )

        return productos_limpios

    @field_validator("etapa")
    @classmethod
    def validar_etapa(
        cls,
        etapa: str,
    ) -> str:
        """
        Verifica que la etapa pertenezca al proceso comercial.
        """

        etapa_limpia = " ".join(
            etapa.strip().split()
        )

        if etapa_limpia.casefold() not in ETAPAS_VALIDAS:
            etapas_mostradas = (
                "Prospecto, Contacto, Calificación, "
                "Propuesta/Cotización, Negociación, "
                "Cierre Ganada, Cierre Perdida o Posventa"
            )

            raise ValueError(
                "La etapa indicada no es válida. "
                f"Utilice: {etapas_mostradas}."
            )

        return etapa_limpia


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(
    texto: str,
) -> str:
    """
    Normaliza texto para comparar registros.

    Se eliminan:

    - Diferencias entre mayúsculas y minúsculas.
    - Acentos.
    - Espacios adicionales.
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


def obtener_fecha_actual() -> str:
    """
    Obtiene la fecha y hora de Ecuador en formato ISO 8601.
    """

    return datetime.now(
        ZONA_HORARIA_ECUADOR
    ).isoformat(
        timespec="seconds"
    )


def generar_identificador() -> str:
    """
    Genera un identificador legible para la oportunidad.

    Ejemplo:

    OP-20260718-213015-A1B2
    """

    ahora = datetime.now(
        ZONA_HORARIA_ECUADOR
    )

    componente_fecha = ahora.strftime(
        "%Y%m%d-%H%M%S"
    )

    componente_unico = hashlib.sha256(
        (
            ahora.isoformat()
            + str(ahora.timestamp())
        ).encode("utf-8")
    ).hexdigest()[:4].upper()

    return (
        f"OP-{componente_fecha}-"
        f"{componente_unico}"
    )


def generar_huella_oportunidad(
    cliente: str,
    contacto: str,
    productos: list[str],
    cantidad_total: int,
    monto_estimado: float,
    etapa: str,
    proxima_accion: str,
) -> str:
    """
    Genera una huella para detectar oportunidades duplicadas.

    El orden de los productos no afecta la comparación.
    """

    productos_normalizados = sorted(
        normalizar_texto(producto)
        for producto in productos
    )

    contenido = {
        "cliente": normalizar_texto(cliente),
        "contacto": normalizar_texto(contacto),
        "productos": productos_normalizados,
        "cantidad_total": cantidad_total,
        "monto_estimado": round(
            monto_estimado,
            2,
        ),
        "etapa": normalizar_texto(etapa),
        "proxima_accion": normalizar_texto(
            proxima_accion
        ),
    }

    contenido_json = json.dumps(
        contenido,
        ensure_ascii=False,
        sort_keys=True,
    )

    return hashlib.sha256(
        contenido_json.encode("utf-8")
    ).hexdigest()


def leer_registros(
    ruta_archivo: Path = ARCHIVO_OPORTUNIDADES,
) -> list[dict[str, Any]]:
    """
    Lee los registros válidos existentes.

    Las líneas dañadas se ignoran para evitar que un registro
    incorrecto detenga toda la aplicación.
    """

    if not ruta_archivo.exists():
        return []

    registros = []

    with ruta_archivo.open(
        mode="r",
        encoding="utf-8",
    ) as archivo:
        for numero_linea, linea in enumerate(
            archivo,
            start=1,
        ):
            linea_limpia = linea.strip()

            if not linea_limpia:
                continue

            try:
                registro = json.loads(
                    linea_limpia
                )

                if isinstance(registro, dict):
                    registros.append(registro)

            except json.JSONDecodeError:
                print(
                    "Advertencia: se ignoró la línea "
                    f"{numero_linea} del archivo de "
                    "oportunidades porque no contiene "
                    "un JSON válido."
                )

    return registros


def buscar_duplicado(
    huella: str,
    registros: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Busca una oportunidad con la misma huella.
    """

    for registro in registros:
        if registro.get("huella") == huella:
            return registro

    return None


def guardar_registro(
    registro: dict[str, Any],
    ruta_archivo: Path = ARCHIVO_OPORTUNIDADES,
) -> None:
    """
    Guarda una oportunidad como una línea JSON.
    """

    ruta_archivo.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with ruta_archivo.open(
        mode="a",
        encoding="utf-8",
    ) as archivo:
        archivo.write(
            json.dumps(
                registro,
                ensure_ascii=False,
                sort_keys=True,
            )
        )

        archivo.write("\n")


# ============================================================
# FUNCIÓN DETERMINÍSTICA DE REGISTRO
# ============================================================

def registrar_oportunidad_en_archivo(
    datos: EntradaRegistroOportunidad,
    ruta_archivo: Path = ARCHIVO_OPORTUNIDADES,
) -> dict[str, Any]:
    """
    Valida, verifica duplicados y registra la oportunidad.

    Esta función se mantiene separada de la tool para que pueda
    probarse sin depender de una llamada a un modelo.
    """

    if not datos.confirmado:
        return {
            "estado": "CONFIRMACION_REQUERIDA",
            "mensaje": (
                "La oportunidad no fue registrada porque "
                "el usuario todavía no ha confirmado la acción."
            ),
        }

    huella = generar_huella_oportunidad(
        cliente=datos.cliente,
        contacto=datos.contacto,
        productos=datos.productos,
        cantidad_total=datos.cantidad_total,
        monto_estimado=datos.monto_estimado,
        etapa=datos.etapa,
        proxima_accion=datos.proxima_accion,
    )

    registros_existentes = leer_registros(
        ruta_archivo=ruta_archivo
    )

    registro_duplicado = buscar_duplicado(
        huella=huella,
        registros=registros_existentes,
    )

    if registro_duplicado:
        return {
            "estado": "DUPLICADO",
            "mensaje": (
                "La oportunidad no fue registrada porque "
                "ya existe un registro equivalente."
            ),
            "oportunidad_id": (
                registro_duplicado.get(
                    "oportunidad_id"
                )
            ),
            "fecha_registro": (
                registro_duplicado.get(
                    "fecha_registro"
                )
            ),
        }

    oportunidad_id = generar_identificador()
    fecha_registro = obtener_fecha_actual()

    registro = {
        "oportunidad_id": oportunidad_id,
        "fecha_registro": fecha_registro,
        "cliente": datos.cliente,
        "contacto": datos.contacto,
        "productos": datos.productos,
        "cantidad_total": datos.cantidad_total,
        "monto_estimado": round(
            datos.monto_estimado,
            2,
        ),
        "etapa": datos.etapa,
        "proxima_accion": datos.proxima_accion,
        "vendedor": datos.vendedor,
        "descuento": round(
            datos.descuento,
            2,
        ),
        "condicion_pago": datos.condicion_pago,
        "huella": huella,
    }

    guardar_registro(
        registro=registro,
        ruta_archivo=ruta_archivo,
    )

    return {
        "estado": "REGISTRADA",
        "mensaje": (
            "La oportunidad comercial fue registrada "
            "correctamente."
        ),
        "oportunidad_id": oportunidad_id,
        "fecha_registro": fecha_registro,
        "archivo": str(ruta_archivo),
    }


def formatear_resultado_registro(
    resultado: dict[str, Any],
) -> str:
    """
    Convierte el resultado determinístico en texto estructurado
    para el agente.
    """

    lineas = [
        f"ESTADO: {resultado['estado']}",
        f"DETALLE: {resultado['mensaje']}",
    ]

    if resultado.get("oportunidad_id"):
        lineas.append(
            "OPORTUNIDAD_ID: "
            f"{resultado['oportunidad_id']}"
        )

    if resultado.get("fecha_registro"):
        lineas.append(
            "FECHA_REGISTRO: "
            f"{resultado['fecha_registro']}"
        )

    if resultado.get("archivo"):
        lineas.append(
            f"ARCHIVO: {resultado['archivo']}"
        )

    return "\n".join(lineas)


# ============================================================
# TOOL LANGCHAIN
# ============================================================

@tool(args_schema=EntradaRegistroOportunidad)
def registrar_oportunidad(
    cliente: str,
    contacto: str,
    productos: list[str],
    cantidad_total: int,
    monto_estimado: float,
    etapa: str,
    proxima_accion: str,
    vendedor: str,
    confirmado: bool,
    descuento: float = 0.0,
    condicion_pago: str = "Por definir",
) -> str:
    """
    Registra una oportunidad comercial confirmada.

    Utiliza esta herramienta únicamente cuando:

    1. Todos los campos obligatorios estén completos.
    2. Los datos hayan sido mostrados al usuario.
    3. El usuario haya confirmado expresamente el registro.

    No debe utilizarse para consultar productos, políticas o CRM.
    """

    datos = EntradaRegistroOportunidad(
        cliente=cliente,
        contacto=contacto,
        productos=productos,
        cantidad_total=cantidad_total,
        monto_estimado=monto_estimado,
        etapa=etapa,
        proxima_accion=proxima_accion,
        vendedor=vendedor,
        descuento=descuento,
        condicion_pago=condicion_pago,
        confirmado=confirmado,
    )

    resultado = registrar_oportunidad_en_archivo(
        datos=datos
    )

    return formatear_resultado_registro(
        resultado=resultado
    )