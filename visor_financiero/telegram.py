"""Cliente de Telegram: envío de mensajes, fotos y alertas."""
import os

import requests

from visor_financiero import config


class TelegramBot:
    def __init__(self, token=None, chat_id=None, timeout=None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.timeout = timeout or config.TELEGRAM_TIMEOUT

        if not self.token or not self.chat_id:
            raise ValueError("Faltan credenciales de Telegram")

    def _base_url(self, metodo):
        return f"https://api.telegram.org/bot{self.token}/{metodo}"

    def enviar_texto(self, texto, disable_preview=True):
        url = self._base_url("sendMessage")
        payload = {
            "chat_id": self.chat_id,
            "text": texto[:4000],
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_preview,
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            return resp.status_code == 200
        except Exception as e:
            print(f"❌ Error enviando texto: {e}")
            return False

    def enviar_foto_con_caption(self, foto_url, caption, link_bsky=None):
        url = self._base_url("sendPhoto")
        header = "📊 <b>Bluesky Feed</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        footer = f"\n\n🔗 <a href='{link_bsky}'>Ver en Bluesky</a>" if link_bsky else ""
        caption_completo = f"{header}{caption}{footer}"
        if len(caption_completo) > 1024:
            caption_completo = caption_completo[:1021] + "..."
        payload = {
            "chat_id": self.chat_id,
            "photo": foto_url,
            "caption": caption_completo,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                # La respuesta puede no ser JSON (p. ej. timeouts de red);
                # en ese caso no hay descripción que analizar.
                try:
                    error_desc = resp.json().get("description", "")
                except ValueError:
                    error_desc = ""
                if "wrong" in error_desc.lower() or "failed" in error_desc.lower():
                    return self.enviar_texto(caption_completo, disable_preview=False)
                return False
            return True
        except Exception as e:
            print(f"❌ Error enviando foto: {e}")
            return False

    def enviar_alerta_mmd(self, link_stream, imagen_url=None):
        url = self._base_url("sendPhoto")
        caption = (
            "🔔 <b>¡AHORAPLAY!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📺 Transmisión en vivo MaxiMedioDia de: 13:00 - 15:00 (AR)\n\n"
            f"▶️ <a href='{link_stream}'>CLICK PARA VER AHORA</a>"
        )
        if not imagen_url:
            imagen_url = "https://img.youtube.com/vi/live/maxresdefault.jpg"
        payload = {
            "chat_id": self.chat_id,
            "photo": imagen_url,
            "caption": caption,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                return self.enviar_texto(caption, disable_preview=False)
            return True
        except Exception as e:
            return self.enviar_texto(caption, disable_preview=False)

    def enviar_alerta_mundo_dinero(self, link_stream, imagen_url=None):
        url = self._base_url("sendPhoto")
        caption = (
            "🔔 <b>¡MERCADO SIN FILTRO!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📺 Transmisión en vivo Mundo Dinero: 09:30 (AR)\n\n"
            f"▶️ <a href='{link_stream}'>CLICK PARA VER AHORA</a>"
        )
        if not imagen_url:
            imagen_url = "https://img.youtube.com/vi/live/maxresdefault.jpg"
        payload = {
            "chat_id": self.chat_id,
            "photo": imagen_url,
            "caption": caption,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                return self.enviar_texto(caption, disable_preview=False)
            return True
        except Exception as e:
            return self.enviar_texto(caption, disable_preview=False)

    def enviar_spotify(self, titulo, link_spotify, imagen_url=None, descripcion=""):
        url = self._base_url("sendPhoto")
        caption = (
            "🎙️ <b>Bloomberg Línea Argentina</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>{titulo}</b>\n\n"
            f"{descripcion[:200]}{'...' if len(descripcion) > 200 else ''}\n\n"
            f"🎧 <a href='{link_spotify}'>Escuchar en Spotify</a>"
        )
        if len(caption) > 1024:
            caption = caption[:1021] + "..."
        if not imagen_url:
            imagen_url = "https://storage.googleapis.com/spotifynewsroom/spotify-logo.png"
        payload = {
            "chat_id": self.chat_id,
            "photo": imagen_url,
            "caption": caption,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                return self.enviar_texto(caption, disable_preview=False)
            return True
        except Exception as e:
            return self.enviar_texto(caption, disable_preview=False)


class TelegramBotSimulacion:
    """Simula el envío a Telegram sin tocar la red (modo --dry-run).

    Todos los métodos registran lo que harían y devuelven True, de modo
    que el flujo del bot se puede probar de punta a punta sin credenciales.
    """

    def __init__(self):
        print("🧪 Modo simulación: no se enviarán mensajes a Telegram")

    def enviar_texto(self, texto, disable_preview=True):
        print(f"🧪 [SIMULACIÓN] sendMessage ({len(texto)} chars): {texto[:100]!r}...")
        return True

    def enviar_foto_con_caption(self, foto_url, caption, link_bsky=None):
        print(f"🧪 [SIMULACIÓN] sendPhoto: {foto_url}")
        return True

    def enviar_alerta_mmd(self, link_stream, imagen_url=None):
        print(f"🧪 [SIMULACIÓN] alerta AHORAPLAY: {link_stream}")
        return True

    def enviar_alerta_mundo_dinero(self, link_stream, imagen_url=None):
        print(f"🧪 [SIMULACIÓN] alerta MERCADO SIN FILTRO: {link_stream}")
        return True

    def enviar_spotify(self, titulo, link_spotify, imagen_url=None, descripcion=""):
        print(f"🧪 [SIMULACIÓN] Spotify: {titulo}")
        return True
