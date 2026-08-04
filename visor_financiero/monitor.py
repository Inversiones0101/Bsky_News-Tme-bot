"""Visor de mercados: consulta de cotizaciones y armado del mensaje diario."""
from datetime import datetime

import pytz
import yfinance as yf

from visor_financiero import config
from visor_financiero.utilidades import esta_abierto_wall_street, formatear_linea_activo


def obtener_precio_activo(ticker, nombre=""):
    """Consulta la cotización de un ticker y devuelve ``(precio, cambio %)``.

    Intenta primero con el período de 2 días y reintenta con 5 días si no
    hay suficientes datos. Devuelve ``None`` si no se pudo obtener (el
    mensaje de error ya se imprime acá).
    """
    try:
        # Intenta con 2d primero, si no hay suficientes datos prueba 5d
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) < 2:
            print(f"⚠️ {ticker}: solo {len(data)} fila(s) con 2d, reintentando con 5d...")
            data = yf.Ticker(ticker).history(period="5d")
        if len(data) < 2:
            print(f"❌ {ticker} ({nombre}): sin datos suficientes, omitiendo")
            return None

        precio = data["Close"].iloc[-1]
        precio_ant = data["Close"].iloc[-2]
        cambio = ((precio / precio_ant) - 1) * 100
        return float(precio), float(cambio)
    except Exception as e:
        print(f"❌ Error en {ticker} ({nombre}): {e}")
        return None


def formatear_precio(ticker, precio):
    """Formatea el precio de un activo (los bonos del Tesoro van en %)."""
    if ticker == "^TNX":
        return f"{precio:.2f}%"
    return f"{precio:,.2f}"


def obtener_datos_monitor(ahora=None):
    """Arma el mensaje HTML del visor de mercados.

    ``ahora`` se inyecta para las pruebas; si no se pasa se usa la hora
    actual en la zona horaria de Argentina.
    """
    if ahora is None:
        ahora = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))

    lineas = [
        "📊 <b>VISOR DE MERCADOS</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    tz_ny = pytz.timezone("America/New_York")
    abierto = esta_abierto_wall_street(ahora.astimezone(tz_ny))
    estado_ws = "🟢 MERCADO ABIERTO" if abierto else "🔴 MERCADO CERRADO"
    lineas.append(f"🇺🇸 <b>Wall Street:</b> {estado_ws}\n")

    for seccion, activos in config.MARKETS.items():
        emoji_sec = config.EMOJIS_SECCION.get(seccion, "📈")

        if seccion != "WALL_STREET":
            lineas.append(f"\n{emoji_sec} <b>{seccion.replace('_', ' ')}</b>")

        for ticker, (nombre, emoji) in activos.items():
            resultado = obtener_precio_activo(ticker, nombre)
            if resultado is None:
                continue

            precio, cambio = resultado
            precio_str = formatear_precio(ticker, precio)
            linea = formatear_linea_activo(nombre, emoji, precio_str, cambio)
            lineas.append(linea)
            print(f"✅ {ticker} ({nombre}): {precio_str} {cambio:+.2f}%")

    lineas.append("\n━━━━━━━━━━━━━━━━━━━━━━━")
    hora_ar = ahora.strftime("%H:%M")
    lineas.append(f"🕐 <i>Actualizado: {hora_ar} AR</i>")

    return "\n".join(lineas)
