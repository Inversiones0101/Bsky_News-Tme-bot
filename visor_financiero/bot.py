"""Punto de entrada del bot: secciones, CLI y orquestación.

El bot se divide en cinco secciones independientes (alertas de streams,
visor de mercados, feeds de Bluesky, Ambito Dolar y Spotify) que se pueden
ejecutar todas juntas o por separado con ``--seccion``.

Ejemplos:
    python bot.py                        # ejecución normal
    python bot.py --dry-run              # simula sin enviar nada
    python bot.py --seccion mercados     # solo el visor de mercados
    python bot.py --dry-run --seccion bsky
"""
import argparse
import re
import sys
import time
from datetime import datetime

import feedparser
import pytz
import requests

from visor_financiero import __version__, config
from visor_financiero.historial import GestorHistorial, GestorHistorialBsky
from visor_financiero.monitor import obtener_datos_monitor
from visor_financiero.telegram import TelegramBot, TelegramBotSimulacion
from visor_financiero.utilidades import (
    extraer_imagen_de_bsky,
    limpiar_html,
    traducir_texto,
)

SECCIONES = ("alertas", "mercados", "bsky", "especial", "spotify")


def obtener_link_stream_youtube():
    return "https://www.youtube.com/@Ahora_Play/streams"


def obtener_link_stream_mundo_dinero():
    return "https://www.youtube.com/@MundoDinerovideos/streams"


# ============= SECCIONES =============

def ejecutar_alertas(bot, ahora_ar, fecha_hoy, solo_lectura=False):
    """1. Alertas de streams en vivo (AHORAPLAY y Mercado Sin Filtro)."""
    # 1. ALERTA AHORAPLAY!
    gestor_maxi = GestorHistorial(config.ARCHIVO_MAXI, solo_lectura=solo_lectura)
    if ahora_ar.weekday() < 5 and ahora_ar.hour == 12:
        if not gestor_maxi.existe(fecha_hoy):
            link_stream = obtener_link_stream_youtube()
            imagen_mmd = "https://img.youtube.com/vi/live/maxresdefault.jpg"
            if bot.enviar_alerta_mmd(link_stream, imagen_mmd):
                gestor_maxi.agregar(fecha_hoy)
                gestor_maxi.guardar()
                print(f"✅ Alerta AHORAPLAY enviada: {fecha_hoy}")

    # 1b. ALERTA MERCADO SIN FILTRO (Mundo Dinero) - 9:30 AR lunes a viernes
    gestor_msf = GestorHistorial(config.ARCHIVO_MSF, solo_lectura=solo_lectura)
    if ahora_ar.weekday() < 5 and ahora_ar.hour == 9 and ahora_ar.minute >= 30:
        if not gestor_msf.existe(fecha_hoy):
            link_msf = obtener_link_stream_mundo_dinero()
            if bot.enviar_alerta_mundo_dinero(link_msf):
                gestor_msf.agregar(fecha_hoy)
                gestor_msf.guardar()
                print(f"✅ Alerta MERCADO SIN FILTRO enviada: {fecha_hoy}")


def ejecutar_visor_mercados(bot, ahora_ar, fecha_hoy, solo_lectura=False):
    """2. VISOR DE MERCADOS (10:00-19:00 AR, lunes a viernes)."""
    if ahora_ar.weekday() < 5 and 10 <= ahora_ar.hour <= 19:
        datos = obtener_datos_monitor(ahora_ar)
        if bot.enviar_texto(datos, disable_preview=True):
            print("✅ Visor de mercados enviado")


def ejecutar_feeds_bsky(bot, ahora_ar, fecha_hoy, solo_lectura=False):
    """3. FEEDS BLUESKY — sistema JSON con cabeceras por cuenta."""
    gestor_bsky = GestorHistorialBsky(solo_lectura=solo_lectura)
    enviados_bsky = 0

    for nombre_feed, url_feed in config.FEEDS_BSKY.items():
        try:
            resp = requests.get(url_feed, timeout=30)
            feed = feedparser.parse(resp.content)

            nuevos_feed = 0
            for entrada in feed.entries[:config.ENTRADAS_POR_FEED_BSKY]:
                link = entrada.get("link", "").strip()
                if not link:
                    continue

                # Consulta el historial de ESTA cuenta especificamente
                if gestor_bsky.existe(nombre_feed, link):
                    print(f"⏭️ [{nombre_feed}] Ya enviado: {link.split('/')[-1]}")
                    continue

                titulo = entrada.get("title", "")
                desc = entrada.get("description", "")
                texto_limpio = limpiar_html(desc) or titulo
                texto_traducido = traducir_texto(texto_limpio)

                imagen_url = None
                if desc and "<img" in desc:
                    imagen_url = extraer_imagen_de_bsky(desc)
                if not imagen_url:
                    try:
                        resp_html = requests.get(link, timeout=10)
                        imagen_url = extraer_imagen_de_bsky(resp_html.text)
                    except Exception:
                        pass

                if imagen_url:
                    exito = bot.enviar_foto_con_caption(imagen_url, texto_traducido, link)
                else:
                    emoji = "📊"
                    mensaje = (
                        f"{emoji} <b>{nombre_feed.replace('_', ' ')}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"{texto_traducido}\n\n"
                        f"🔗 <a href='{link}'>Ver en Bluesky</a>"
                    )
                    exito = bot.enviar_texto(mensaje, disable_preview=False)

                if exito:
                    # Registra en el historial de ESTA cuenta
                    gestor_bsky.agregar(nombre_feed, link)
                    enviados_bsky += 1
                    nuevos_feed += 1
                    time.sleep(2)

            print(f"📡 [{nombre_feed}] {nuevos_feed} nuevos enviados")

        except Exception as e:
            print(f"⚠️ Error en {nombre_feed}: {e}")
            continue

    # Guardar siempre el JSON (aunque no haya nuevos, para mantener consistencia)
    gestor_bsky.guardar()
    gestor_bsky.mostrar_estado()
    if enviados_bsky > 0:
        print(f"✅ {enviados_bsky} posts de Bluesky procesados en total")


def ejecutar_ambito_dolar(bot, ahora_ar, fecha_hoy, solo_lectura=False):
    """4. AMBITO DOLAR (apertura/cierre de jornada)."""
    gestor_especial = GestorHistorial(config.ARCHIVO_ESPECIAL, solo_lectura=solo_lectura)
    enviados_especial = 0

    for nombre, config_feed in config.FEEDS_ESPECIALES.items():
        try:
            resp = requests.get(config_feed["url"], timeout=30)
            feed = feedparser.parse(resp.content)

            for entrada in feed.entries[:config.ENTRADAS_POR_FEED_ESPECIAL]:
                link = entrada.get("link", "").strip()
                if not link or gestor_especial.existe(link):
                    continue

                titulo = entrada.get("title", "")
                desc = entrada.get("description", "")
                texto_completo = f"{titulo} {desc}"
                texto_limpio = limpiar_html(texto_completo)
                texto_inicio = texto_limpio[:100].lower()

                contiene_apertura = "apertura de jornada" in texto_inicio
                contiene_cierre = "cierre de jornada" in texto_inicio

                if not (contiene_apertura or contiene_cierre):
                    print(f"⏭️ Saltando: no es apertura/cierre ({texto_limpio[:30]}...)")
                    continue

                tipo = "APERTURA" if contiene_apertura else "CIERRE"
                emoji = config_feed.get("emoji", "💵")

                mensaje = (
                    f"{emoji} <b>Ambito Dolar - {tipo}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{texto_limpio[:500]}\n\n"
                    f"🔗 <a href='{link}'>Ver gráfico completo</a>"
                )

                if bot.enviar_texto(mensaje, disable_preview=False):
                    gestor_especial.agregar(link)
                    enviados_especial += 1
                    print(f"✅ Ambito {tipo} enviado")
                    time.sleep(1.5)

        except Exception as e:
            print(f"⚠️ Error en {nombre}: {e}")

    if enviados_especial > 0:
        gestor_especial.guardar()
        print(f"✅ {enviados_especial} posts de Ambito Dolar guardados en historial")


def ejecutar_spotify(bot, ahora_ar, fecha_hoy, solo_lectura=False):
    """5. SPOTIFY (episodio más reciente de Bloomberg Línea Argentina)."""
    gestor_spotify = GestorHistorial(config.ARCHIVO_SPOTIFY, solo_lectura=solo_lectura)
    enviados_spotify = 0

    for nombre, config_feed in config.FEEDS_SPOTIFY.items():
        try:
            resp = requests.get(config_feed["url_rss"], timeout=30)
            feed = feedparser.parse(resp.content)
            print(f"📦 Spotify feed: {len(feed.entries)} episodios encontrados")

            for entrada in feed.entries[:1]:
                ep_id = entrada.get("id", "") or entrada.get("link", "")
                if not ep_id or gestor_spotify.existe(ep_id):
                    print(f"⏭️ Spotify: episodio ya enviado anteriormente")
                    continue

                titulo = entrada.get("title", "Sin título")
                link = entrada.get("link", config_feed["url_base"])
                descripcion = limpiar_html(entrada.get("description", ""))

                imagen = None
                if "image" in entrada:
                    imagen = (
                        entrada["image"].get("href")
                        if isinstance(entrada["image"], dict)
                        else entrada["image"]
                    )
                elif "itunes_image" in entrada:
                    imagen = entrada["itunes_image"]
                if not imagen:
                    imagen = config_feed.get("imagen_default")

                link_spotify = (
                    link if ("spotify.com" in link or "podcasters" in link) else config_feed["url_base"]
                )

                print(f"📤 Enviando Spotify: {titulo[:60]}...")
                if bot.enviar_spotify(titulo, link_spotify, imagen, descripcion):
                    gestor_spotify.agregar(ep_id)
                    enviados_spotify += 1
                    print(f"✅ Spotify enviado: {titulo[:50]}...")
                    time.sleep(2)

        except Exception as e:
            print(f"⚠️ Error Spotify: {e}")

    if enviados_spotify > 0:
        gestor_spotify.guardar()
        print(f"✅ {enviados_spotify} episodios de Spotify guardados en historial")


# ============= CLI =============

def crear_argument_parser():
    parser = argparse.ArgumentParser(
        prog="bot",
        description=f"VISOR FINANCIERO v{__version__} — bot de Telegram "
        "para mercados, Bluesky y podcasts.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula la ejecución: no envía mensajes ni modifica el historial.",
    )
    parser.add_argument(
        "--seccion",
        choices=SECCIONES,
        default=None,
        help="Ejecuta solo una sección (por defecto: todas).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv=None):
    args = crear_argument_parser().parse_args(argv)

    print(f"🚀 Iniciando VISOR v{__version__} - {datetime.now().strftime('%H:%M:%S')}")

    bot = TelegramBotSimulacion() if args.dry_run else TelegramBot()

    tz_ar = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora_ar = datetime.now(tz_ar)
    fecha_hoy = ahora_ar.strftime("%Y-%m-%d")

    secciones = {
        "alertas": ejecutar_alertas,
        "mercados": ejecutar_visor_mercados,
        "bsky": ejecutar_feeds_bsky,
        "especial": ejecutar_ambito_dolar,
        "spotify": ejecutar_spotify,
    }

    for nombre, funcion in secciones.items():
        if args.seccion and nombre != args.seccion:
            continue
        funcion(bot, ahora_ar, fecha_hoy, solo_lectura=args.dry_run)

    print(f"🏁 Finalizado - {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    sys.exit(main())
