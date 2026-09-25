"""Pruebas de las utilidades (traducción, horarios, formato, imágenes)."""
from datetime import datetime

import pytz

from visor_financiero import utilidades


class TestLimpiarHtml:
    def test_elimina_etiquetas(self):
        assert utilidades.limpiar_html("<p>Hola <b>mundo</b></p>") == "Hola mundo"

    def test_vacio(self):
        assert utilidades.limpiar_html("") == ""
        assert utilidades.limpiar_html(None) == ""


class TestTraducirTexto:
    def test_sin_traductor_devuelve_original(self, monkeypatch):
        monkeypatch.setattr(utilidades, "TRADUCTOR_DISPONIBLE", False)
        assert utilidades.traducir_texto("Hello world") == "Hello world"

    def test_texto_vacio(self, monkeypatch):
        monkeypatch.setattr(utilidades, "TRADUCTOR_DISPONIBLE", True)
        assert utilidades.traducir_texto("") == ""
        assert utilidades.traducir_texto(None) is None

    def test_traduce_y_trunca_a_4000(self, monkeypatch):
        class FalsoTraductor:
            def __init__(self, source, target):
                self.target = target

            def translate(self, texto):
                return f"TRADUCIDO({len(texto)}):{texto}"

        monkeypatch.setattr(utilidades, "TRADUCTOR_DISPONIBLE", True)
        monkeypatch.setattr(utilidades, "GoogleTranslator", FalsoTraductor)
        resultado = utilidades.traducir_texto("x" * 5000)
        assert resultado.startswith("TRADUCIDO(4000):")

    def test_error_de_traduccion_devuelve_original(self, monkeypatch):
        class TraductorRoto:
            def __init__(self, source, target):
                pass

            def translate(self, texto):
                raise RuntimeError("red caída")

        monkeypatch.setattr(utilidades, "TRADUCTOR_DISPONIBLE", True)
        monkeypatch.setattr(utilidades, "GoogleTranslator", TraductorRoto)
        assert utilidades.traducir_texto("hola") == "hola"


class TestEstaAbiertoWallStreet:
    TZ_NY = pytz.timezone("America/New_York")

    def test_lunes_a_mediodia_abierto(self):
        ahora = self.TZ_NY.localize(datetime(2026, 8, 3, 12, 0))  # lunes
        assert utilidades.esta_abierto_wall_street(ahora) is True

    def test_fin_de_semana_cerrado(self):
        ahora = self.TZ_NY.localize(datetime(2026, 8, 8, 12, 0))  # sábado
        assert utilidades.esta_abierto_wall_street(ahora) is False

    def test_antes_de_apertura_cerrado(self):
        ahora = self.TZ_NY.localize(datetime(2026, 8, 3, 9, 29))
        assert utilidades.esta_abierto_wall_street(ahora) is False

    def test_apertura_inclusive(self):
        ahora = self.TZ_NY.localize(datetime(2026, 8, 3, 9, 30))
        assert utilidades.esta_abierto_wall_street(ahora) is True

    def test_cierre_inclusive(self):
        ahora = self.TZ_NY.localize(datetime(2026, 8, 3, 16, 0))
        assert utilidades.esta_abierto_wall_street(ahora) is True

    def test_despues_de_cierre_cerrado(self):
        ahora = self.TZ_NY.localize(datetime(2026, 8, 3, 16, 1))
        assert utilidades.esta_abierto_wall_street(ahora) is False


class TestFormatearLineaActivo:
    def test_formato_exacto_positivo(self):
        linea = utilidades.formatear_linea_activo("Bitcoin", "🟠", "61,234.50", 1.23)
        assert linea == (
            "🟠 🟢 <code>Bitcoin     </code> <b> 61,234.50</b>  <code>  +1.23%</code>"
        )

    def test_formato_exacto_negativo(self):
        linea = utilidades.formatear_linea_activo("Oro", "🥇", "2,345.67", -0.5)
        assert "🔴" in linea and "-0.50%" in linea


class TestExtraerImagenDeBsky:
    def test_patron_bsky_image(self):
        html = '<img src="https://cdn.bsky.app/img/abc.jpg" class="bsky-image">'
        assert utilidades.extraer_imagen_de_bsky(html) == "https://cdn.bsky.app/img/abc.jpg"

    def test_patron_background_image(self):
        html = 'style="background-image: url(https://cdn.bsky.app/img/x.jpg)"'
        assert utilidades.extraer_imagen_de_bsky(html) == "https://cdn.bsky.app/img/x.jpg"

    def test_patron_extension_comun(self):
        html = '<img src="https://cdn.bsky.app/img/png.png" alt="x">'
        assert utilidades.extraer_imagen_de_bsky(html) == "https://cdn.bsky.app/img/png.png"

    def test_patron_extension_webp(self):
        html = '<img src="https://cdn.bsky.app/img/foto.webp">'
        assert utilidades.extraer_imagen_de_bsky(html) == "https://cdn.bsky.app/img/foto.webp"

    def test_patron_thumb_json(self):
        html = '"thumb": "https://cdn.bsky.app/img/thumb.jpg"'
        assert utilidades.extraer_imagen_de_bsky(html) == "https://cdn.bsky.app/img/thumb.jpg"

    def test_unescape_amp(self):
        html = '<img src="https://cdn.bsky.app/img/a&amp;b.jpg" class="bsky-image">'
        assert utilidades.extraer_imagen_de_bsky(html) == "https://cdn.bsky.app/img/a&b.jpg"

    def test_url_relativa_ignorada(self):
        html = '<img src="/img/local.jpg" class="bsky-image">'
        assert utilidades.extraer_imagen_de_bsky(html) is None

    def test_sin_imagen(self):
        assert utilidades.extraer_imagen_de_bsky("<p>sin imágenes</p>") is None
