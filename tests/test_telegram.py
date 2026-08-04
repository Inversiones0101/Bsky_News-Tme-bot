"""Pruebas del cliente de Telegram (con la red mockeada)."""
import pytest

from visor_financiero import telegram


class FakeResp:
    def __init__(self, status_code=200, json_data=None, raises_json=False):
        self.status_code = status_code
        self._json = json_data
        self._raises_json = raises_json

    def json(self):
        if self._raises_json:
            raise ValueError("respuesta no JSON")
        return self._json


def hacer_bot(monkeypatch, respuestas):
    """Crea un bot y mockea requests.post devolviendo respuestas en orden."""
    llamadas = []

    def fake_post(url, json=None, timeout=None):
        llamadas.append((url, json))
        return respuestas.pop(0)

    monkeypatch.setattr(telegram.requests, "post", fake_post)
    bot = telegram.TelegramBot(token="TOKEN", chat_id="123")
    return bot, llamadas


class TestTelegramBot:
    def test_faltan_credenciales(self):
        with pytest.raises(ValueError):
            telegram.TelegramBot(token=None, chat_id=None)

    def test_enviar_texto_exitoso(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        assert bot.enviar_texto("hola") is True
        url, payload = llamadas[0]
        assert url.endswith("/sendMessage")
        assert payload["chat_id"] == "123"
        assert payload["parse_mode"] == "HTML"
        assert payload["text"] == "hola"

    def test_enviar_texto_trunca_a_4000(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        bot.enviar_texto("x" * 5000)
        assert len(llamadas[0][1]["text"]) == 4000

    def test_enviar_texto_error_red(self, monkeypatch):
        import requests as requests_mod

        def fake_post(url, json=None, timeout=None):
            raise requests_mod.ConnectionError("red caída")

        monkeypatch.setattr(telegram.requests, "post", fake_post)
        bot = telegram.TelegramBot(token="TOKEN", chat_id="123")
        assert bot.enviar_texto("hola") is False

    def test_enviar_foto_exitoso(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        assert bot.enviar_foto_con_caption("https://img.jpg", "texto") is True
        url, payload = llamadas[0]
        assert url.endswith("/sendPhoto")
        assert payload["photo"] == "https://img.jpg"
        assert "Bluesky Feed" in payload["caption"]

    def test_enviar_foto_caption_truncada_a_1024(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        bot.enviar_foto_con_caption("https://img.jpg", "x" * 2000)
        caption = llamadas[0][1]["caption"]
        assert len(caption) <= 1024
        assert caption.endswith("...")

    def test_enviar_foto_con_link_bsky(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        bot.enviar_foto_con_caption("https://img.jpg", "texto", link_bsky="https://bsky.app/post/1")
        assert "Ver en Bluesky" in llamadas[0][1]["caption"]

    def test_enviar_foto_error_descripcion_wrong_hace_fallback(self, monkeypatch):
        # sendPhoto falla con "wrong file identifier" → cae a sendMessage
        bot, llamadas = hacer_bot(
            monkeypatch,
            [
                FakeResp(400, {"description": "wrong file identifier"}),
                FakeResp(200),
            ],
        )
        assert bot.enviar_foto_con_caption("https://img.jpg", "texto") is True
        urls = [url for url, _ in llamadas]
        assert any(u.endswith("/sendMessage") for u in urls)

    def test_enviar_foto_respuesta_no_json(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(500, raises_json=True)])
        assert bot.enviar_foto_con_caption("https://img.jpg", "texto") is False

    def test_enviar_alerta_mmd_exitoso(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        assert bot.enviar_alerta_mmd("https://youtube.com/streams") is True
        assert "AHORAPLAY" in llamadas[0][1]["caption"]

    def test_enviar_alerta_mundo_dinero_exitoso(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        assert bot.enviar_alerta_mundo_dinero("https://youtube.com/streams") is True
        assert "MERCADO SIN FILTRO" in llamadas[0][1]["caption"]

    def test_enviar_spotify_exitoso(self, monkeypatch):
        bot, llamadas = hacer_bot(monkeypatch, [FakeResp(200)])
        ok = bot.enviar_spotify("Titulo", "https://spotify.com/ep", None, "descripción")
        assert ok is True
        assert "Bloomberg Línea Argentina" in llamadas[0][1]["caption"]


class TestTelegramBotSimulacion:
    def test_todos_los_metodos_devuelven_true(self):
        bot = telegram.TelegramBotSimulacion()
        assert bot.enviar_texto("hola") is True
        assert bot.enviar_foto_con_caption("https://img.jpg", "texto") is True
        assert bot.enviar_alerta_mmd("https://youtube.com") is True
        assert bot.enviar_alerta_mundo_dinero("https://youtube.com") is True
        assert bot.enviar_spotify("título", "https://spotify.com") is True

    def test_no_requiere_credenciales(self, monkeypatch):
        # La simulación no debe exigir token ni chat_id aunque no haya env vars
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        bot = telegram.TelegramBotSimulacion()
        assert bot.enviar_texto("hola") is True
