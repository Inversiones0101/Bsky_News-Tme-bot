#!/usr/bin/env python3
"""
VISOR FINANCIERO - bot de Telegram para mercados, Bluesky y podcasts.

Este archivo es el punto de entrada histórico del bot (lo usa el workflow
de GitHub Actions: ``python bot.py``). Toda la lógica vive en el paquete
``visor_financiero``.

Uso:
    python bot.py                        # ejecución normal
    python bot.py --dry-run              # simula sin enviar nada
    python bot.py --seccion mercados     # solo una sección
    python bot.py --help                 # ayuda completa
"""
import sys

from visor_financiero.bot import main

if __name__ == "__main__":
    sys.exit(main())
