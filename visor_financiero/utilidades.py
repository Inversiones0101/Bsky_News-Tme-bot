"""Utilidades del bot: traducción, horarios, formato y extracción de imágenes."""
import re
from datetime import datetime

import pytz

try:
    from deep_translator import GoogleTranslator
    TRADUCTOR_DISPONIBLE = True
except ImportError:
    TRADUCTOR_DISPONIBLE = False


def limpiar_html(texto):
    """Elimina las etiquetas HTML de un texto."""
    if not texto:
        return ""
    return re.sub(r"<[^>]+>", "", texto)


def traducir_texto(texto, destino="es"):
    """Traduce un texto al español (si deep-translator está disponible)."""
    if not TRADUCTOR_DISPONIBLE or not texto:
        return texto
    try:
        texto_truncado = texto[:4000]
        traductor = GoogleTranslator(source="auto", target=destino)
        return traductor.translate(texto_truncado)
    except Exception as e:
        print(f"⚠️ Error traduciendo: {e}")
        return texto


def esta_abierto_wall_street(ahora=None):
    """Devuelve True si Wall Street está abierto (lun-vie 9:30-16:00 NY).

    ``ahora`` se puede inyectar para facilitar las pruebas; si no se pasa,
    se usa la hora actual en la zona horaria de Nueva York.
    """
    tz_ny = pytz.timezone("America/New_York")
    ahora_ny = ahora if ahora is not None else datetime.now(tz_ny)
    if ahora_ny.weekday() >= 5:
        return False
    apertura = ahora_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    cierre = ahora_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    return apertura <= ahora_ny <= cierre


def formatear_linea_activo(nombre, emoji, precio_str, cambio):
    """Formatea la línea HTML de un activo para el visor de mercados."""
    indicador = "🟢" if cambio >= 0 else "🔴"
    cambio_str = f"{cambio:+.2f}%"
    return (
        f"{emoji} {indicador} <code>{nombre:<12}</code> "
        f"<b>{precio_str:>10}</b>  <code>{cambio_str:>8}</code>"
    )


def extraer_imagen_de_bsky(html_content):
    """Extrae la primera imagen relevante del HTML de un post de Bluesky.

    Prueba varios patrones (imágenes con clase bsky-image, CSS de fondo,
    extensiones de imagen comunes y thumbs de JSON embebido).
    """
    patrones = [
        r'<img[^>]+src="([^"]+)"[^>]*class="[^"]*bsky-image[^"]*"',
        r"background-image:\s*url\(([^)]+)\)",
        r'<img[^>]+src="([^"]+\.(?:jpg|jpeg|png|gif|webp))"',
        r'"thumb":\s*"([^"]+)"',
    ]
    for patron in patrones:
        match = re.search(patron, html_content, re.IGNORECASE)
        if match:
            url = match.group(1).replace("&amp;", "&")
            if url.startswith("http"):
                return url
    return None
