"""Pruebas de los gestores de historial (JSON de Bluesky y .txt simple)."""
import json

import pytest

from visor_financiero import config
from visor_financiero.historial import GestorHistorial, GestorHistorialBsky


class TestGestorHistorialBsky:
    def test_archivo_inexistente_inicia_vacio(self, tmp_path):
        gestor = GestorHistorialBsky(archivo=str(tmp_path / "no_existe.json"))
        assert gestor.data == {}

    def test_agregar_y_existe(self, tmp_path):
        gestor = GestorHistorialBsky(archivo=str(tmp_path / "hist.json"))
        gestor.agregar("FEED_A", "https://bsky.app/post/1")
        assert gestor.existe("FEED_A", "https://bsky.app/post/1")
        assert not gestor.existe("FEED_A", "https://bsky.app/post/2")
        assert not gestor.existe("FEED_B", "https://bsky.app/post/1")

    def test_no_agrega_duplicados(self, tmp_path):
        gestor = GestorHistorialBsky(archivo=str(tmp_path / "hist.json"))
        gestor.agregar("FEED_A", "https://bsky.app/post/1")
        gestor.agregar("FEED_A", "https://bsky.app/post/1")
        assert gestor.data["FEED_A"] == ["https://bsky.app/post/1"]

    def test_respeta_limite_por_cuenta(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "LIMITE_POR_CUENTA", 3)
        gestor = GestorHistorialBsky(archivo=str(tmp_path / "hist.json"))
        for i in range(5):
            gestor.agregar("FEED_A", f"https://bsky.app/post/{i}")
        assert len(gestor.data["FEED_A"]) == 3
        # Se descartan las más viejas (las primeras)
        assert gestor.data["FEED_A"] == [
            "https://bsky.app/post/2",
            "https://bsky.app/post/3",
            "https://bsky.app/post/4",
        ]

    def test_guardar_y_recargar(self, tmp_path):
        archivo = tmp_path / "hist.json"
        gestor = GestorHistorialBsky(archivo=str(archivo))
        gestor.agregar("FEED_A", "https://bsky.app/post/1")
        gestor.guardar()

        # El archivo se escribe como JSON
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = json.load(f)
        assert contenido["FEED_A"] == ["https://bsky.app/post/1"]

        # Un gestor nuevo lo recarga
        gestor2 = GestorHistorialBsky(archivo=str(archivo))
        assert gestor2.existe("FEED_A", "https://bsky.app/post/1")

    def test_json_corrupto_hace_backup(self, tmp_path):
        archivo = tmp_path / "hist.json"
        archivo.write_text("{json roto", encoding="utf-8")
        gestor = GestorHistorialBsky(archivo=str(archivo))
        assert gestor.data == {}
        assert (tmp_path / "hist.json.backup").exists()

    def test_json_corrupto_solo_lectura_no_hace_backup(self, tmp_path):
        archivo = tmp_path / "hist.json"
        archivo.write_text("{json roto", encoding="utf-8")
        gestor = GestorHistorialBsky(archivo=str(archivo), solo_lectura=True)
        assert gestor.data == {}
        assert not (tmp_path / "hist.json.backup").exists()

    def test_archivo_vacio(self, tmp_path):
        archivo = tmp_path / "hist.json"
        archivo.write_text("", encoding="utf-8")
        gestor = GestorHistorialBsky(archivo=str(archivo))
        assert gestor.data == {}

    def test_solo_lectura_no_escribe(self, tmp_path):
        archivo = tmp_path / "hist.json"
        gestor = GestorHistorialBsky(archivo=str(archivo), solo_lectura=True)
        gestor.agregar("FEED_A", "https://bsky.app/post/1")
        gestor.guardar()
        assert not archivo.exists()


class TestGestorHistorial:
    def test_archivo_inexistente_inicia_vacio(self, tmp_path):
        gestor = GestorHistorial(str(tmp_path / "no.txt"))
        assert gestor.datos == []

    def test_agregar_existe_y_guardar(self, tmp_path):
        archivo = tmp_path / "hist.txt"
        gestor = GestorHistorial(str(archivo))
        gestor.agregar("item-1")
        gestor.agregar("item-2")
        assert gestor.existe("item-1")
        assert not gestor.existe("item-3")
        gestor.guardar()
        assert archivo.read_text(encoding="utf-8") == "item-1\nitem-2"

    def test_no_agrega_duplicados(self, tmp_path):
        gestor = GestorHistorial(str(tmp_path / "hist.txt"))
        gestor.agregar("item-1")
        gestor.agregar("item-1")
        assert gestor.datos == ["item-1"]

    def test_deduplica_al_cargar(self, tmp_path):
        archivo = tmp_path / "hist.txt"
        archivo.write_text("a\nb\na\nc\n", encoding="utf-8")
        gestor = GestorHistorial(str(archivo))
        assert gestor.datos == ["a", "b", "c"]

    def test_limite_al_guardar(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "LIMITE_HISTORIAL_SIMPLE", 2)
        archivo = tmp_path / "hist.txt"
        gestor = GestorHistorial(str(archivo))
        gestor.agregar("a")
        gestor.agregar("b")
        gestor.agregar("c")
        gestor.guardar()
        # Solo quedan los últimos 2 ítems
        assert archivo.read_text(encoding="utf-8") == "b\nc"

    def test_solo_lectura_no_escribe(self, tmp_path):
        archivo = tmp_path / "hist.txt"
        gestor = GestorHistorial(str(archivo), solo_lectura=True)
        gestor.agregar("a")
        gestor.guardar()
        assert not archivo.exists()

    def test_utf8_roundtrip(self, tmp_path):
        archivo = tmp_path / "hist.txt"
        gestor = GestorHistorial(str(archivo))
        gestor.agregar("https://bsky.app/post/árbol-ñandú")
        gestor.guardar()
        gestor2 = GestorHistorial(str(archivo))
        assert gestor2.existe("https://bsky.app/post/árbol-ñandú")
