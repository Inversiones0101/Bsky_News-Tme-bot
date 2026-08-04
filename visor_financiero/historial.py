"""Gestores de historial: memoria de URLs/ítems ya enviados.

Dos gestores:

- ``GestorHistorialBsky``: historial en JSON organizado por cuenta de
  Bluesky (archivo ``last_id_bsky.json``), con un límite de URLs por cuenta.
- ``GestorHistorial``: historial simple de líneas de texto (``.txt``),
  usado para los feeds especiales, Spotify y las alertas de streams.

Ambos soportan el modo ``solo_lectura`` (útil para ``--dry-run``): en ese
modo ``guardar()`` no escribe nada y no se toca el sistema de archivos.
"""
import json
import os

from visor_financiero import config


class GestorHistorialBsky:
    """
    Historial de Bluesky organizado por cuenta.

    Archivo: last_id_bsky.json
    Estructura:
    {
        "TRENDSPIDER_BSKY": [
            "https://bsky.app/.../post/abc123",
            "https://bsky.app/.../post/def456",
            ...  (ultimas 15 URLs de esta cuenta)
        ],
        "BARCHART_BSKY": [
            "https://bsky.app/.../post/xyz789",
            ...
        ]
    }
    - Guarda las ultimas 15 URLs por cuenta
    - Al agregar la 16ta, descarta la mas vieja (la primera de la lista)
    - Identifica naturalmente cada post por su URL unica de Bluesky
    """

    def __init__(self, archivo=None, solo_lectura=False):
        self.ARCHIVO = archivo or config.ARCHIVO_BSKY
        self.LIMITE_POR_CUENTA = config.LIMITE_POR_CUENTA
        self.solo_lectura = solo_lectura
        self.data = self._cargar()

    def _cargar(self):
        if not os.path.exists(self.ARCHIVO):
            print("📄 Creando nuevo last_id_bsky.json")
            return {}
        try:
            with open(self.ARCHIVO, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
                if not contenido:
                    print("📄 last_id_bsky.json vacío, iniciando nuevo")
                    return {}
                return json.loads(contenido)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON corrupto en last_id_bsky.json: {e} — iniciando nuevo")
            # Backup del archivo corrupto (no en modo solo lectura)
            if not self.solo_lectura:
                try:
                    os.rename(self.ARCHIVO, f"{self.ARCHIVO}.backup")
                except OSError:
                    pass
            return {}
        except Exception as e:
            print(f"⚠️ Error cargando last_id_bsky.json: {e}")
            return {}

    def existe(self, nombre_feed, url):
        """Devuelve True si la URL ya fue enviada para esta cuenta"""
        lista = self.data.get(nombre_feed, [])
        return url in lista

    def agregar(self, nombre_feed, url):
        """
        Agrega la URL a la lista de esta cuenta.
        Si supera LIMITE_POR_CUENTA, descarta la mas vieja.
        """
        if nombre_feed not in self.data:
            self.data[nombre_feed] = []

        lista = self.data[nombre_feed]

        # No agregar duplicados
        if url in lista:
            return

        lista.append(url)  # agrega al final (mas reciente)

        # Si supera el limite, elimina el mas viejo (el primero)
        if len(lista) > self.LIMITE_POR_CUENTA:
            lista.pop(0)
            print(f"🗑️ [{nombre_feed}] URL vieja eliminada del historial")

        self.data[nombre_feed] = lista

    def guardar(self):
        if self.solo_lectura:
            return
        try:
            with open(self.ARCHIVO, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=1, ensure_ascii=False)
            total = sum(len(v) for v in self.data.values())
            print(f"✅ last_id_bsky.json guardado ({total} URLs en {len(self.data)} cuentas)")
        except Exception as e:
            print(f"❌ Error guardando last_id_bsky.json: {e}")

    def mostrar_estado(self):
        """Muestra un resumen del historial para los logs"""
        for cuenta, urls in self.data.items():
            print(f"   📋 {cuenta}: {len(urls)}/{self.LIMITE_POR_CUENTA} URLs guardadas")


class GestorHistorial:
    """
    Gestor simple de historial para archivos .txt
    Usado por: last_id_especial.txt, last_id_spotify.txt, ultimo_maxi.txt
    """

    def __init__(self, archivo, solo_lectura=False):
        self.archivo = archivo
        self.solo_lectura = solo_lectura
        self.limite = config.LIMITE_HISTORIAL_SIMPLE
        self.datos = self._cargar()

    def _cargar(self):
        if os.path.exists(self.archivo):
            with open(self.archivo, "r", encoding="utf-8") as f:
                items = [line.strip() for line in f if line.strip()]
                # Deduplicar manteniendo orden
                vistos = set()
                resultado = []
                for item in items:
                    if item not in vistos:
                        vistos.add(item)
                        resultado.append(item)
                return resultado
        return []

    def existe(self, item):
        return item in self.datos

    def agregar(self, item):
        if item not in self.datos:
            self.datos.append(item)

    def guardar(self):
        if self.solo_lectura:
            return
        items_a_guardar = self.datos[-self.limite:]
        with open(self.archivo, "w", encoding="utf-8") as f:
            f.write("\n".join(items_a_guardar))
