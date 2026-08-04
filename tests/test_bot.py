"""Pruebas del CLI y de la orquestación de secciones."""
import pytest

from visor_financiero import bot as bot_modulo


class TestArgumentParser:
    def test_valores_por_defecto(self):
        args = bot_modulo.crear_argument_parser().parse_args([])
        assert args.dry_run is False
        assert args.seccion is None

    def test_dry_run(self):
        args = bot_modulo.crear_argument_parser().parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_seccion(self):
        args = bot_modulo.crear_argument_parser().parse_args(["--seccion", "bsky"])
        assert args.seccion == "bsky"

    def test_seccion_invalida(self):
        with pytest.raises(SystemExit):
            bot_modulo.crear_argument_parser().parse_args(["--seccion", "inexistente"])

    def test_version(self):
        with pytest.raises(SystemExit) as excinfo:
            bot_modulo.crear_argument_parser().parse_args(["--version"])
        assert excinfo.value.code == 0


class TestMain:
    def _monkeypatch_secciones(self, monkeypatch):
        llamadas = {}
        funciones = {
            "alertas": "ejecutar_alertas",
            "mercados": "ejecutar_visor_mercados",
            "bsky": "ejecutar_feeds_bsky",
            "especial": "ejecutar_ambito_dolar",
            "spotify": "ejecutar_spotify",
        }

        def fabricar(nombre):
            def funcion(bot, ahora_ar, fecha_hoy, solo_lectura=False):
                llamadas[nombre] = solo_lectura

            return funcion

        for nombre, attr in funciones.items():
            monkeypatch.setattr(bot_modulo, attr, fabricar(nombre))
        return llamadas

    def test_main_dry_run_ejecuta_todas_solo_lectura(self, monkeypatch):
        llamadas = self._monkeypatch_secciones(monkeypatch)

        # En dry-run jamás debe instanciarse el bot real
        def bot_real_prohibido(*args, **kwargs):
            raise AssertionError("TelegramBot no debe instanciarse en --dry-run")

        monkeypatch.setattr(bot_modulo, "TelegramBot", bot_real_prohibido)
        bot_modulo.main(["--dry-run"])

        assert llamadas == {
            "alertas": True,
            "mercados": True,
            "bsky": True,
            "especial": True,
            "spotify": True,
        }

    def test_main_seccion_filtra(self, monkeypatch):
        llamadas = self._monkeypatch_secciones(monkeypatch)
        monkeypatch.setattr(
            bot_modulo, "TelegramBot", lambda *a, **k: object()
        )
        bot_modulo.main(["--seccion", "bsky"])
        assert list(llamadas) == ["bsky"]

    def test_main_modo_real_no_solo_lectura(self, monkeypatch):
        llamadas = self._monkeypatch_secciones(monkeypatch)
        monkeypatch.setattr(
            bot_modulo, "TelegramBot", lambda *a, **k: object()
        )
        bot_modulo.main([])
        assert all(v is False for v in llamadas.values())
