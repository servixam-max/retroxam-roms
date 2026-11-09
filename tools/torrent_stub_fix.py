#!/usr/bin/env python3
"""Resuelve los stubs .torrent de la Thor (punteros a MediaFire) a .torrent reales.

Un stub es un fichero .torrent cuyo contenido es "<URL> *Size=NN MB" + ZIP vacio.
La app (DownloadTorrentActivity) lo rechaza con "Can't decode data ... bencoded".
Este script:
  1. extrae la URL del stub,
  2. si es MediaFire, saca el enlace directo del boton de descarga,
  3. descarga el .torrent y comprueba que empieza por 'd8:' (bencode),
  4. cachea por hash de URL y, con --apply, sobrescribe los stubs que apuntaban ahi.

Uso:
  python torrent_stub_fix.py --mapa stubs.tsv --cache scratch/t52/cache --dry-run
  python torrent_stub_fix.py --mapa stubs.tsv --cache scratch/t52/cache --apply
"""
import argparse
import hashlib
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def http_get(url, timeout=60, maxbytes=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read() if maxbytes is None else r.read(maxbytes)
        return data, r.geturl(), r.headers.get("Content-Type", "")


def mediafire_direct(page_url, timeout=60):
    """Devuelve el enlace directo de descarga de una pagina /file/ de MediaFire."""
    html, _, _ = http_get(page_url, timeout=timeout)
    html = html.decode("utf-8", "ignore")
    for pat in (
        r'id="downloadButton"[^>]*href="([^"]+)"',
        r'href="(https://download[^"]+)"',
    ):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    if "File is taken down" in html or "no longer available" in html:
        raise RuntimeError("enlace muerto (taken down)")
    raise RuntimeError("sin boton de descarga (posible captcha o cambio de plantilla)")


def descargar_torrent(url, timeout=90):
    """Devuelve (bytes, url_final) de un .torrent real."""
    if "mediafire.com" in url:
        url = mediafire_direct(url, timeout=timeout)
    data, final, ctype = http_get(url, timeout=timeout)
    if not data.startswith(b"d8:") and not data.startswith(b"d4:info") and not data.startswith(b"d10:created"):
        raise RuntimeError("no es bencode (ct=%s, head=%r)" % (ctype, data[:16]))
    return data, final


def leer_mapa(path):
    """TSV con dos columnas: ruta_del_stub<TAB>url."""
    filas = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            partes = line.split("\t")
            if len(partes) >= 2:
                filas.append((partes[0], partes[1]))
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapa", required=True, help="TSV ruta_stub<TAB>url")
    ap.add_argument("--cache", required=True, help="directorio donde guardar los .torrent resueltos")
    ap.add_argument("--apply", action="store_true", help="sobrescribe los stubs (por defecto solo informa)")
    ap.add_argument("--sleep", type=float, default=1.5, help="pausa entre descargas (cortesia con el host)")
    args = ap.parse_args()

    filas = leer_mapa(args.mapa)
    os.makedirs(args.cache, exist_ok=True)

    por_url = {}
    for ruta, url in filas:
        por_url.setdefault(url, []).append(ruta)

    ok = fallo = 0
    for i, (url, rutas) in enumerate(sorted(por_url.items()), 1):
        h = hashlib.sha1(url.encode()).hexdigest()[:12]
        base = os.path.basename(urllib.parse.unquote(url)).replace("+", "_") or "bundle"
        if not base.lower().endswith(".torrent"):
            base += ".torrent"
        dest = os.path.join(args.cache, h + "-" + base)
        try:
            if os.path.exists(dest) and os.path.getsize(dest) > 100:
                print("[%02d/%d] cache %s (%d B) -> %d stubs" % (i, len(por_url), base, os.path.getsize(dest), len(rutas)))
            else:
                data, final = descargar_torrent(url)
                with open(dest, "wb") as fh:
                    fh.write(data)
                print("[%02d/%d] OK %s (%d B) -> %d stubs" % (i, len(por_url), base, len(data), len(rutas)))
                time.sleep(args.sleep)
            ok += 1
            if args.apply:
                for ruta in rutas:
                    try:
                        with open(dest, "rb") as src, open(ruta, "wb") as dst:
                            dst.write(src.read())
                    except OSError as exc:
                        print("    ! no se pudo escribir %s: %s" % (ruta, exc))
        except Exception as exc:  # noqa: BLE001
            fallo += 1
            print("[%02d/%d] FALLO %s :: %s" % (i, len(por_url), url[-60:], exc))

    print("\nbundles resueltos: %d   fallos: %d   stubs afectados: %d" % (ok, fallo, len(filas)))
    if not args.apply:
        print("dry-run: nada escrito en la SD (usa --apply con el movil conectado)")
        return 0 if fallo == 0 else 1
    return 0 if fallo == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
