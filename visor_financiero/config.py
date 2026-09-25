"""Configuración central del bot: feeds, mercados y rutas de datos.

Toda la configuración vive acá para que el resto del paquete sea
fácil de leer y de probar. Los valores pueden sobrescribirse con
variables de entorno cuando tiene sentido (por ejemplo DIR_DATOS).
"""
import os

# ============= RUTAS DE DATOS =============

# Directorio donde se guardan los archivos de historial (last_id_*.json/txt).
# Por defecto: la raíz del repositorio, para que el bot funcione igual que
# antes sin importar desde qué directorio se invoque.
DIR_DATOS = os.environ.get(
    "DIR_DATOS",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

ARCHIVO_BSKY = os.path.join(DIR_DATOS, "last_id_bsky.json")
ARCHIVO_ESPECIAL = os.path.join(DIR_DATOS, "last_id_especial.txt")
ARCHIVO_SPOTIFY = os.path.join(DIR_DATOS, "last_id_spotify.txt")
ARCHIVO_MAXI = os.path.join(DIR_DATOS, "ultimo_maxi.txt")
ARCHIVO_MSF = os.path.join(DIR_DATOS, "ultimo_msf.txt")

# ============= BLUESKY =============

FEEDS_BSKY = {
    "TRENDSPIDER_BSKY": "https://bsky.app/profile/trendspider.com/rss",
    "BARCHART_BSKY": "https://bsky.app/profile/barchart.com/rss",
    "QUANTHUSTLE": "https://bsky.app/profile/quanthustle.bsky.social/rss",
    "EARNINGS_FORESIGHT": "https://bsky.app/profile/earningsforesight.bsky.social/rss",
    "GITHUB_TRENDING": "https://bsky.app/profile/github-trending.bsky.social/rss",
}

FEEDS_ESPECIALES = {
    "AMBITO_DOLAR": {
        "url": "https://bsky.app/profile/ambitodolar.bsky.social/rss",
        "filtros_exactos": ["Apertura de jornada", "Cierre de jornada"],
        "emoji": "💵",
    }
}

FEEDS_SPOTIFY = {
    "BLOOMBERG_LINEA": {
        "nombre": "🎧 Bloomberg Línea Argentina",
        "url_rss": "https://anchor.fm/s/7ce84050/podcast/rss",
        "url_base": "https://podcasters.spotify.com/pod/show/bloomberg-linea-argentina",
        "imagen_default": "https://is1-ssl.mzstatic.com/image/thumb/Podcasts116/v4/b6/26/1b/b6261b6d-74f2-b8af-fece-58d41c2e712e/mza_15124749693889878680.jpg/600x600bb.jpg",
        "emoji": "🎙️",
    }
}

# Cuántas entradas revisar por feed de Bluesky (las más recientes).
ENTRADAS_POR_FEED_BSKY = int(os.environ.get("ENTRADAS_POR_FEED_BSKY", "3"))
ENTRADAS_POR_FEED_ESPECIAL = int(os.environ.get("ENTRADAS_POR_FEED_ESPECIAL", "5"))

# ============= MERCADOS =============

MARKETS = {
    "WALL_STREET": {
        "^SPX": ("S&P 500", "🇺🇸"),
        "^DJI": ("Dow Jones", "🏭"),
        "^IXIC": ("NASDAQ", "💻"),
        "^VIX": ("VIX", "⚡"),
        "^TNX": ("Tasa 10Y", "📜"),
    },
    "COMMODITIES": {
        "GC=F": ("Oro", "🥇"),
        "ZS=F": ("Soja", "🌱"),
        "CL=F": ("Petróleo", "🛢️"),
        "SI=F": ("Plata", "🥈"),
    },
    "CRYPTOS": {
        "BTC-USD": ("Bitcoin", "🟠"),
        "ETH-USD": ("Ethereum", "💎"),
        "SOL-USD": ("Solana", "🟣"),
    },
}

EMOJIS_SECCION = {
    "WALL_STREET": "🏦",
    "COMMODITIES": "🌾",
    "CRYPTOS": "₿",
}

# ============= HISTORIAL =============

# Límite de URLs guardadas por cuenta de Bluesky.
LIMITE_POR_CUENTA = int(os.environ.get("BSKY_LIMITE_POR_CUENTA", "15"))
# Límite de ítems en los historiales simples (.txt).
LIMITE_HISTORIAL_SIMPLE = int(os.environ.get("LIMITE_HISTORIAL_SIMPLE", "200"))

# ============= TELEGRAM =============

TELEGRAM_TIMEOUT = int(os.environ.get("TELEGRAM_TIMEOUT", "25"))
