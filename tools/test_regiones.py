#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_regiones.py — Regresión del clasificador de región/idioma y del limpiador
de etiquetas Japan del pipeline de catálogo.

Ejecutar:  python3 scripts/test_regiones.py        (unittest, verbose)
           python3 -m pytest scripts/test_regiones.py -q

No modifica el catálogo ni los módulos bajo prueba: solo lee device/catalog_es
(comprobaciones de integridad, se saltan si el directorio no existe).
"""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from regiones import classify, regions          # noqa: E402
from filtro_catalogo import limpiar_jp, RANK     # noqa: E402

CAT = os.path.join(ROOT, "device", "catalog_es")

# (nombre, etiqueta esperada, etiquetas prohibidas)
CASOS_CLASIFICADOR = [
    # --- Japón suelto: JP ------------------------------------------------
    ("Akumajou Dracula X - Chi no Rondo (Japan).chd", "JP", set()),
    ("Final Fantasy IV (JP).sfc", "JP", set()),
    ("Rockman 2 - Dr. Wily no Nazo (J).nes", "JP", set()),
    ("Mother (J) [!].nes", "JP", {"ES", "EU", "US", "ASIA"}),
    ("Chrono Trigger (Jpn).sfc", "JP", set()),
    ("Biohazard (Jap).bin", "JP", set()),
    ("Sonic (Japan) (En,Ja) (Rev 1).zip", "JP", set()),
    # --- Japón mezclado: NO debe ser JP ---------------------------------
    ("Kidou Senshi Gundam (Japan, USA) (En,Ja).zip", "US", {"JP"}),
    ("Winning Eleven 6 (Japan, Europe) (En,Ja,Fr,De).zip", "EU", {"JP"}),
    ("Biohazard 2 (Japan, USA) (Rev 1).zip", "US", {"JP"}),
    ("Ridge Racer (Japan, Asia) (En,Ja).zip", "ASIA", {"JP"}),
    # --- parche fan a castellano ----------------------------------------
    ("Final Fight (USA, Japan) [T+Spa100_Sayans].zip", "ES-fan", {"JP"}),
    ("Final Fantasy IV (J) [T-Spa].smc", "ES-fan", set()),
    ("Chrono Trigger (USA) (Castellano).sfc", "ES-fan", set()),
    # --- [SGB Enhanced] no es Spain -------------------------------------
    ("Picross 2 (Japan) (SGB Enhanced).zip", "JP", {"ES"}),
    ("Wario Land 2 (USA) (SGB Enhanced) (GB Compatible).zip", "US", {"ES"}),
    ("Pokemon Yellow (Europe) (SGB Enhanced).gb", "EU", {"ES"}),
    # --- sufijos de versión no rompen el parseo --------------------------
    ("Sonic the Hedgehog (USA) (Rev 1).md", "US", set()),
    ("Sonic the Hedgehog (Europe) (Rev A).md", "EU", set()),
    ("Sonic the Hedgehog (Europe) (v1.1).md", "EU", set()),
    ("Sonic the Hedgehog (USA) (Proto).bin", "US", set()),
    ("Sonic the Hedgehog (USA) (Beta).bin", "US", set()),
    ("Sonic the Hedgehog (USA) (Demo).bin", "US", set()),
    ("Sonic the Hedgehog (Japan) (Demo).bin", "JP", set()),
    ("Juego (v1.0).bin", "N/D", set()),
    ("Juego (Proto).bin", "N/D", set()),
    # --- castellano por lista de idiomas --------------------------------
    ("Alien Resurrection (Europe) (En,Fr,De,Es,It).chd", "ES", set()),
    ("Juego (En,Fr,De,Es,It).iso", "ES", set()),
    ("Juego (Spain).zip", "ES", set()),
    ("Juego (Es).zip", "ES", set()),
    ("Juego (Spa).zip", "ES", set()),
    ("Battle Arena Toshinden (E) [S]", "ES", set()),
    # --- etiquetas simples ----------------------------------------------
    ("Super Mario World (Europe).sfc", "EU", set()),
    ("Super Mario World (USA).sfc", "US", set()),
    ("Marvel Vs. Capcom (Asia).zip", "ASIA", set()),
    ("Juego (World).zip", "EU", set()),
    # --- sin etiquetas ---------------------------------------------------
    ("1941.zip", "N/D", {"ES", "EU", "US", "ASIA", "JP"}),
    ("fotns.zip", "N/D", {"ES", "EU", "US", "ASIA", "JP"}),
    ("OpenBOR Game v3.0.1.pak", "N/D", {"ES", "EU", "US", "ASIA", "JP"}),
    # --- ruido de formato ------------------------------------------------
    ("Sonic  the  Hedgehog  (Europe)  (En,Fr).zip", "EU", set()),
    ("Final Fantasy VII (USA) - Disc-1.chd", "US", set()),
    ("Final Fantasy VII (Japan) - Disc-1.chd", "JP", set()),
    ("Final Fantasy VII (Europe)  - Disc-2.chd", "EU", set()),
    ("Metal Gear Solid (USA) (Disc 1) (Rev 1).chd", "US", set()),
]


class TestClasificador(unittest.TestCase):
    def test_tabla_de_casos(self):
        fallos = []
        for name, esperado, prohibido in CASOS_CLASIFICADOR:
            rank, lab = classify(name)
            if lab != esperado:
                fallos.append(f"{name!r}: esperado {esperado}, obtenido {lab} (rank {rank})")
            malos = prohibido & {lab}
            if malos:
                fallos.append(f"{name!r}: etiqueta prohibida {sorted(malos)} obtenida")
        self.assertFalse(fallos, "\n  " + "\n  ".join(fallos))

    def test_rank_coherente_con_label(self):
        """regiones.py y filtro_catalogo.py usan escalas distintas (0..4 vs -1..4):
        lo que debe respetarse es el ORDEN relativo entre etiquetas, no el valor."""
        muestras = {}
        for name, lab, _ in CASOS_CLASIFICADOR:
            muestras.setdefault(lab, name)
        labels = [l for l in muestras if l in RANK]
        fallos = []
        for i, a in enumerate(labels):
            for b in labels[i + 1:]:
                ra = classify(muestras[a])[0]
                rb = classify(muestras[b])[0]
                if (RANK[a] > RANK[b]) != (ra > rb):
                    fallos.append(f"orden incoherente {a}({RANK[a]}/{ra}) vs {b}({RANK[b]}/{rb})")
        self.assertFalse(fallos, "\n  " + "\n  ".join(fallos))

    def test_tokens_no_generan_regiones_espurias(self):
        """Grupos que no son región no deben producir etiquetas."""
        for name in ("Juego (SGB Enhanced).gb",
                     "Juego (GB Compatible).gb",
                     "Juego (Virtual Console).wad",
                     "Juego (En,Fr,De).bin"):
            self.assertEqual(regions(name), set(), name)


class TestLimpiarJP(unittest.TestCase):
    """limpiar_jp() debe borrar la mención a Japón de 'n' y 'p' sin tocar urls/meta."""

    @staticmethod
    def base(n, p=None):
        return {"type": "file", "p": p or n, "n": n, "ext": ".zip",
                "urls": [{"u": "https://archive.org/download/x/Japan%20(USA).zip",
                          "size": "1 MB", "size_bytes": 1048576}],
                "meta": {"path": "./" + (p or n), "name": n, "desc": "Japan"}}

    def limpio(self, n, p=None):
        return json.loads(limpiar_jp(self.base(n, p)))

    def test_usa_japan(self):
        o = self.limpio("Metroid Prime (USA, Japan) (Rev 1).zip")
        self.assertNotRegex(o["n"], r"(?i)japan")
        self.assertIn("(USA)", o["n"])

    def test_japan_usa(self):
        o = self.limpio("Sonic (Japan, USA).zip")
        self.assertNotRegex(o["n"], r"(?i)japan")
        self.assertIn("(USA)", o["n"])

    def test_jap_abreviado(self):
        o = self.limpio("Sonic (Jap) (USA).zip")
        self.assertNotRegex(o["n"], r"(?i)jap")

    def test_j_suelto_en_grupo_mixto(self):
        o = self.limpio("Sonic (J, USA).zip")
        self.assertNotRegex(o["n"], r"\(J\b")

    def test_urls_y_meta_intactos(self):
        src = self.base("Metroid Prime (USA, Japan).zip")
        o = json.loads(limpiar_jp(src))
        self.assertEqual(o["urls"], src["urls"])
        self.assertEqual(o["meta"], src["meta"])

    def test_no_toca_nombres_limpios(self):
        src = self.base("Metroid Prime (USA).zip")
        self.assertEqual(json.loads(limpiar_jp(src)), src)

    def test_idempotente(self):
        uno = limpiar_jp(self.base("Metroid Prime (USA, Japan) (Rev 1).zip"))
        dos = limpiar_jp(json.loads(uno))
        self.assertEqual(uno, dos)


class TestCatalogoDesplegado(unittest.TestCase):
    """Integridad del catálogo generado (se salta si no existe)."""

    def setUp(self):
        if not os.path.isdir(CAT):
            self.skipTest("device/catalog_es no existe")

    def fichas(self):
        for fn in sorted(os.listdir(CAT)):
            if not fn.endswith(".jsonl"):
                continue
            for line in open(os.path.join(CAT, fn), encoding="utf-8", errors="replace"):
                line = line.strip()
                if line:
                    yield fn[:-6], json.loads(line)

    def test_sin_menciones_japon_en_n_p(self):
        malos = []
        for sistema, o in self.fichas():
            for campo in ("n", "p"):
                if re.search(r"(?i)japan|\bjpn\b|\bjap\b|\((?:j|jp)\b", o.get(campo) or ""):
                    malos.append(f"{sistema}: {campo}={o.get(campo)!r}")
        self.assertFalse(malos, f"{len(malos)} fichas con mención Japón:\n  " + "\n  ".join(malos[:40]))

    def test_urls_absolutas(self):
        malas = []
        for sistema, o in self.fichas():
            urls = o.get("urls") or []
            u = urls[0].get("u") if urls else ""
            if not str(u).startswith("http"):
                malas.append(f"{sistema}: {u!r}")
        self.assertFalse(malas, f"{len(malas)} fichas sin URL http:\n  " + "\n  ".join(malas[:40]))

    def test_nada_clasificado_como_jp(self):
        malos = [f"{s}: {o.get('n')!r}" for s, o in self.fichas()
                 if classify(o.get("n") or o.get("p") or "")[1] == "JP"]
        self.assertFalse(malos, f"{len(malos)} fichas JP en el catálogo:\n  " + "\n  ".join(malos[:40]))


def main():
    if "--tabla" in sys.argv:
        # salida legible caso a caso, útil para el informe
        ok = 0
        for name, esperado, prohibido in CASOS_CLASIFICADOR:
            rank, lab = classify(name)
            bien = lab == esperado and not (prohibido & {lab})
            ok += bien
            print(f"[{'PASS' if bien else 'FAIL'}] {name:58.58} -> {lab:6} (rank {rank})"
                  + ("" if bien else f"   esperado {esperado}"))
        print(f"\n{ok}/{len(CASOS_CLASIFICADOR)} casos de la tabla OK")
        sys.argv = [a for a in sys.argv if a != "--tabla"]
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()
