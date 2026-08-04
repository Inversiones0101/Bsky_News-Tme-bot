# Bsky_News-Tme-bot — VISOR FINANCIERO

Bot de automatización que captura publicaciones de **Bluesky**, noticias
financieras, cotizaciones de mercado y episodios de podcasts, y las envía
a un grupo de **Telegram**.

> VISOR FINANCIERO v2.4.0

## Características

- 📊 **Visor de mercados**: Wall Street, commodities y criptomonedas con
  cotizaciones de `yfinance` (S&P 500, Dow Jones, NASDAQ, VIX, oro, soja,
  petróleo, Bitcoin, etc.).
- 🌐 **Feeds de Bluesky**: reenvía los posts más recientes de cuentas de
  finanzas (TrendSpider, Barchart, QuantHustle, Earnings Foresight,
  GitHub Trending) con traducción automática al español y captura de
  imágenes.
- 💵 **Ambito Dolar**: detecta los posts de apertura y cierre de jornada.
- 🎙️ **Spotify**: avisa del episodio más reciente de Bloomberg Línea
  Argentina.
- 🔔 **Alertas de streams**: avisos de transmisiones en vivo
  (MaxiMedioDia y Mercado Sin Filtro).
- 🧪 **Modo simulación** (`--dry-run`): prueba el flujo completo sin
  enviar mensajes ni modificar el historial.

## Requisitos

- Python 3.9+
- Un bot de Telegram (token de [@BotFather](https://t.me/BotFather)) y el
  `chat_id` del grupo o canal de destino.

## Instalación

```bash
pip install -r requirements.txt
# o bien, para desarrollo:
pip install -e ".[dev]"
```

## Configuración

Variables de entorno:

| Variable | Descripción | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | — (obligatoria) |
| `TELEGRAM_CHAT_ID` | ID del chat/grupo destino | — (obligatoria) |
| `DIR_DATOS` | Directorio de los archivos de historial | raíz del repo |
| `BSKY_LIMITE_POR_CUENTA` | URLs recordadas por cuenta de Bluesky | `15` |
| `LIMITE_HISTORIAL_SIMPLE` | Ítems recordados en historiales `.txt` | `200` |
| `ENTRADAS_POR_FEED_BSKY` | Entradas revisadas por feed de Bluesky | `3` |
| `ENTRADAS_POR_FEED_ESPECIAL` | Entradas revisadas en el feed especial | `5` |
| `TELEGRAM_TIMEOUT` | Timeout (segundos) de las llamadas a la API | `25` |

## Uso

```bash
python bot.py                        # ejecución normal (todas las secciones)
python bot.py --dry-run              # simula sin enviar ni guardar nada
python bot.py --seccion mercados     # solo el visor de mercados
python bot.py --seccion bsky         # solo los feeds de Bluesky
python bot.py --version              # versión instalada
```

Secciones disponibles: `alertas`, `mercados`, `bsky`, `especial`, `spotify`.

### Automatización

El bot está pensado para ejecutarse cada 30 minutos (el workflow de
GitHub Actions lo hace con un cron). Cada sección decide por sí misma si
debe actuar según el horario actual en Argentina:

- Alertas de streams: lunes a viernes a las 12:00 (AHORAPLAY) y 9:30
  (Mercado Sin Filtro).
- Visor de mercados: lunes a viernes de 10:00 a 19:00.
- Bluesky / Ambito Dolar / Spotify: en cada ejecución, reenviando solo lo
  nuevo (el historial evita duplicados).

## Estructura del proyecto

```
bot.py                        # punto de entrada (compatible con el workflow)
visor_financiero/
├── __init__.py               # versión del paquete
├── bot.py                    # secciones y CLI
├── config.py                 # feeds, mercados y rutas
├── historial.py              # gestores de historial (JSON y .txt)
├── monitor.py                # visor de mercados
├── telegram.py               # cliente de Telegram (+ simulación)
└── utilidades.py             # traducción, horarios, imágenes, formato
tests/                        # pruebas (pytest)
```

## Tests

```bash
python -m pytest              # o simplemente: pytest
```

Todas las pruebas son offline: las llamadas de red (Telegram, yfinance,
RSS) están mockeadas, así que no se necesita token ni conexión.
