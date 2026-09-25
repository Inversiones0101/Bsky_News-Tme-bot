"""Pruebas del visor de mercados (con yfinance mockeado)."""
from datetime import datetime

import pandas as pd
import pytest

from visor_financiero import monitor


class FakeTicker:
    """Reemplaza yf.Ticker con datos de prueba."""

    def __init__(self, periodos):
        # periodos: dict {"2d": DataFrame, "5d": DataFrame}
        self._periodos = periodos

    def history(self, period):
        return self._periodos[period]


def dataframe_con_cierres(cierres):
    return pd.DataFrame({"Close": cierres})


class TestObtenerPrecioActivo:
    def test_datos_suficientes(self, monkeypatch):
        ticker = FakeTicker(
            {"2d": dataframe_con_cierres([100.0, 101.0]), "5d": dataframe_con_cierres([])}
        )
        monkeypatch.setattr(monitor.yf, "Ticker", lambda t: ticker)
        precio, cambio = monitor.obtener_precio_activo("TEST")
        assert precio == 101.0
        assert cambio == pytest.approx(1.0)

    def test_reintenta_con_5d(self, monkeypatch):
        historial = []
        ticker = FakeTicker(
            {"2d": dataframe_con_cierres([100.0]), "5d": dataframe_con_cierres([98.0, 100.0])}
        )
        original_history = ticker.history

        def history_con_registro(period):
            historial.append(period)
            return original_history(period)

        ticker.history = history_con_registro
        monkeypatch.setattr(monitor.yf, "Ticker", lambda t: ticker)
        precio, cambio = monitor.obtener_precio_activo("TEST")
        assert historial == ["2d", "5d"]
        assert precio == 100.0
        assert cambio == pytest.approx(2.0408163265)

    def test_sin_datos_devuelve_none(self, monkeypatch):
        ticker = FakeTicker(
            {"2d": dataframe_con_cierres([100.0]), "5d": dataframe_con_cierres([99.0])}
        )
        monkeypatch.setattr(monitor.yf, "Ticker", lambda t: ticker)
        assert monitor.obtener_precio_activo("TEST", "Activo") is None

    def test_excepcion_devuelve_none(self, monkeypatch):
        def ticker_roto(t):
            raise RuntimeError("API caída")

        monkeypatch.setattr(monitor.yf, "Ticker", ticker_roto)
        assert monitor.obtener_precio_activo("TEST") is None


class TestFormatearPrecio:
    def test_tnx_en_porcentaje(self):
        assert monitor.formatear_precio("^TNX", 4.253) == "4.25%"

    def test_otros_con_miles(self):
        assert monitor.formatear_precio("BTC-USD", 61234.5) == "61,234.50"


class TestObtenerDatosMonitor:
    def _ahora_ar(self):
        import pytz

        tz_ar = pytz.timezone("America/Argentina/Buenos_Aires")
        return tz_ar.localize(datetime(2026, 8, 3, 12, 0))  # lunes 12:00 AR

    def test_mensaje_completo(self, monkeypatch):
        def fake_precio(ticker, nombre=""):
            if ticker == "^TNX":
                return (4.25, 0.5)
            if ticker == "ZS=F":
                return None  # activo que falla
            return (100.0, 1.0)

        monkeypatch.setattr(monitor, "obtener_precio_activo", fake_precio)
        mensaje = monitor.obtener_datos_monitor(ahora=self._ahora_ar())

        assert "VISOR DE MERCADOS" in mensaje
        assert "MERCADO ABIERTO" in mensaje  # lunes 12:00 AR = 11:00 NY
        assert "COMMODITIES" in mensaje
        assert "CRYPTOS" in mensaje
        assert "Bitcoin" in mensaje and "+1.00%" in mensaje
        assert "4.25%" in mensaje  # TNX
        # El activo que falló no aparece
        assert "Soja" not in mensaje
        # Timestamp en hora argentina
        assert "Actualizado: 12:00 AR" in mensaje

    def test_fin_de_semana_mercado_cerrado(self, monkeypatch):
        import pytz

        tz_ar = pytz.timezone("America/Argentina/Buenos_Aires")
        sabado = tz_ar.localize(datetime(2026, 8, 8, 12, 0))  # sábado
        monkeypatch.setattr(monitor, "obtener_precio_activo", lambda t, n="": (1.0, 0.0))
        mensaje = monitor.obtener_datos_monitor(ahora=sabado)
        assert "MERCADO CERRADO" in mensaje
