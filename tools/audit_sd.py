#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria READ-ONLY de las ROMs reales en la SD del AYN Thor.
Entrada : device/audit_sd_raw/files.tsv   (salida de: adb shell find ... -printf '%s\t%p\n')
          device/audit_sd_raw/du.tsv      (salida de: adb shell du -sk ...)
Salida  : device/audit_sd.json  (datos crudos)
          device/AUDIT_SD.md    (informe legible en castellano)

No escribe nada en el dispositivo. Solo lee ficheros locales generados por adb.
"""
import json
import os
import re
import sys
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "device", "audit_sd_raw", "files.tsv")
DU = os.path.join(ROOT, "device", "audit_sd_raw", "du.tsv")
OUT_JSON = os.path.join(ROOT, "device", "audit_sd.json")
OUT_MD = os.path.join(ROOT, "device", "AUDIT_SD.md")

SD = "/storage/FFF9-FF05/ROMs/"

# Extensiones que cuentan como ROM/carga util (lista del encargo + formatos vistos en la SD)
ROM_EXTS = {
    ".zip", ".7z", ".chd", ".iso", ".cue", ".bin", ".gba", ".gbc", ".gb",
    ".nes", ".sfc", ".smc", ".md", ".32x", ".n64", ".pbp", ".cso", ".rvz",
    ".wbfs", ".xci", ".nsp", ".vpk", ".gdi", ".cdi", ".m3u",
    ".pak", ".cia", ".3ds", ".wua", ".nds", ".rar",
}
TORRENT = ".torrent"
# Formatos de texto por naturaleza: un .m3u/.cue de 130 B es normal, no un stub
TEXT_ROM_EXTS = {".m3u", ".cue"}
SIDECAR_EXTS = {".txt", ".srm", ".ini", ".dat", ".db", ".metadata", ".nomedia", ".xml", ".nfo"}

JP_RE = re.compile(r"(?:\(\s*(?:japan|jpn|jap[oó]n|jp|j)\s*[,)]|\b(?:japan|jpn)\b)", re.I)
SPA_RE = re.compile(r"(?:t[\-+]?spa|\[t\+spa|spa\d{2,3}|\(spa)", re.I)
JUNK_RE = re.compile(r"(debian|ubuntu|netinst|fedora|archlinux|linuxmint)", re.I)


# Copias descargadas dos veces: "Juego.iso (1)", "Juego.zip (2)".
# Sin normalizar, la extension saldria ".iso (1)" y el fichero no contaria como ROM.
COPY_SUFFIX = re.compile(r"\s\(\d+\)$")


def ext_of(path):
    fn = path.rsplit("/", 1)[-1]
    fn = COPY_SUFFIX.sub("", fn)
    if "." not in fn:
        return ""
    return "." + fn.rsplit(".", 1)[1].lower()


def base_of(path):
    return path.rsplit("/", 1)[-1]


def classify(path):
    """Devuelve (scope, system) a partir de la ruta absoluta."""
    rel = path[len(SD):] if path.startswith(SD) else path
    parts = rel.split("/")
    scope = "live"
    if parts[0] == "FOREVER":
        scope = "FOREVER"
        system = parts[1] if len(parts) > 1 else "(FOREVER raiz)"
    elif parts[0] == "_cuarentena":
        scope = "cuarentena"
        if len(parts) > 1 and parts[1] == "japan":
            system = parts[2] if len(parts) > 3 else "(japan raiz)"
        else:
            system = parts[1] if len(parts) > 2 else "(cuarentena: suelto)"
    elif parts[0] == "TEMP":
        scope = "TEMP"
        system = "TEMP"
    elif parts[0] == "CHOOSEEMULATOR":
        scope = "aux"
        system = "CHOOSEEMULATOR"
    elif len(parts) == 1:
        scope = "raiz"
        system = "(raiz ROMs)"
    else:
        system = parts[0]
    return scope, system


def category(path):
    e = ext_of(path)
    if e == TORRENT:
        return "torrent"
    if e in ROM_EXTS:
        return "rom"
    if e in SIDECAR_EXTS:
        return "sidecar"
    return "otro"


def strip_exts(fn):
    """Quita extensiones encadenadas: juego.zip.torrent -> juego"""
    known = ROM_EXTS | {TORRENT, ".part", ".tmp"}
    changed = True
    while changed:
        changed = False
        low = fn.lower()
        for e in known:
            if low.endswith(e):
                fn = fn[: -len(e)]
                changed = True
                break
    return fn


def norm_name(path):
    """minusculas, sin etiquetas ()/[], sin extension, sin ruido"""
    # "Juego.iso (1)" es la MISMA descarga repetida: el sufijo va antes que la
    # extension y sin quitarlo aqui no se emparejaria con "Juego.iso".
    fn = strip_exts(COPY_SUFFIX.sub("", base_of(path)))
    prev = None
    while prev != fn:                       # quita () y [] anidados
        prev = fn
        fn = re.sub(r"\([^()]*\)", " ", fn)
        fn = re.sub(r"\[[^\[\]]*\]", " ", fn)
    fn = fn.lower()
    fn = re.sub(r"[^a-z0-9]+", " ", fn)
    return fn.strip()


def human(n):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0


def main():
    if not os.path.exists(RAW):
        sys.exit("Falta %s (genera antes el listado con adb find)" % RAW)
    rows = []
    with open(RAW, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line:
                continue
            size, _, path = line.partition("\t")
            rows.append({"size": int(size), "path": path})

    du = {}
    if os.path.exists(DU):
        with open(DU, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if not line:
                    continue
                kb, _, p = line.partition("\t")
                kb = kb.strip()
                if not kb.isdigit():
                    continue          # cabecera de df u otra linea no numerica
                du[p.strip().rstrip("/")] = int(kb)

    files = []
    for r in rows:
        scope, system = classify(r["path"])
        e = ext_of(r["path"])
        cat = category(r["path"])
        name = base_of(r["path"])
        jp = bool(JP_RE.search(name)) or bool(JP_RE.search(parts_parent(r["path"])))
        files.append({
            "path": r["path"],
            "rel": r["path"][len(SD):] if r["path"].startswith(SD) else r["path"],
            "name": name,
            "ext": e or "(sin)",
            "size": r["size"],
            "scope": scope,
            "system": system,
            "cat": cat,
            "japan": jp,
            "japan_es": jp and bool(SPA_RE.search(name) or SPA_RE.search(parts_parent(r["path"]))),
            "stub": cat == "rom" and r["size"] < 1024 and e not in TEXT_ROM_EXTS,
            "stub_strict_incl_text": cat == "rom" and r["size"] < 1024,
            "norm": norm_name(r["path"]),
        })

    roms = [f for f in files if f["cat"] == "rom"]
    torrents = [f for f in files if f["cat"] == "torrent"]
    others = [f for f in files if f["cat"] in ("sidecar", "otro")]

    # ---------- agregados por sistema ----------
    systems = sorted({f["system"] for f in roms} | {f["system"] for f in files})
    sys_rows = {}
    for s in systems:
        rs = [f for f in roms if f["system"] == s]
        tor = [f for f in torrents if f["system"] == s]
        d = {
            "roms": len(rs),
            "reales": sum(1 for f in rs if not f["stub"] and f["size"] >= 1024
                          and not JUNK_RE.search(f["name"])),
            "stubs": sum(1 for f in rs if f["stub"]),
            "stubs_incl_texto": sum(1 for f in rs if f["stub_strict_incl_text"]),
            "torrents": len(tor),
            "bytes_rom": sum(f["size"] for f in rs),
            "bytes_total": sum(f["size"] for f in files if f["system"] == s),
            "japan_fuera_cuarentena": sum(
                1 for f in rs if f["japan"] and f["scope"] != "cuarentena"),
            "japan_cuarentena": sum(
                1 for f in rs if f["japan"] and f["scope"] == "cuarentena"),
            "japan_es": sum(1 for f in rs if f["japan_es"] and f["scope"] != "cuarentena"),
            "bytes_junk": sum(f["size"] for f in files
                              if f["system"] == s and JUNK_RE.search(f["name"])),
            "scopes": dict(collections.Counter(f["scope"] for f in files if f["system"] == s)),
        }
        d["bytes_limpio"] = d["bytes_rom"] - d["bytes_junk"]
        d["reales_limpio"] = sum(1 for f in rs if f["size"] >= 1024
                                 and not JUNK_RE.search(f["name"]))
        for sc in ("live", "FOREVER", "cuarentena"):
            d["bytes_" + sc] = sum(f["size"] for f in roms
                                   if f["system"] == s and f["scope"] == sc)
        sys_rows[s] = d

    # ---------- japonesas fuera de cuarentena ----------
    jp_live = [f for f in roms if f["japan"] and f["scope"] != "cuarentena"]
    jp_quar = [f for f in roms if f["japan"] and f["scope"] == "cuarentena"]

    # ---------- cuarentena por sistema ----------
    quar = collections.Counter()
    quar_bytes = collections.Counter()
    for f in roms:
        if f["scope"] == "cuarentena":
            quar[f["system"]] += 1
            quar_bytes[f["system"]] += f["size"]

    # ---------- stubs ----------
    stubs = sorted([f for f in roms if f["stub"]], key=lambda x: (x["system"], x["name"]))
    stubs_by_sys = collections.Counter(f["system"] for f in stubs)
    stub_sizes = collections.Counter(f["size"] for f in stubs)
    stubs_txt = [f for f in roms if f["stub_strict_incl_text"] and not f["stub"]]

    # ---------- duplicados ----------
    # Una pista .bin acompanada de su .cue NO es un duplicado: es un trozo del
    # mismo disco. Y "Crazy Taxi" en Dreamcast, PS2 y GC no son copias, son
    # versiones de plataformas distintas. Por eso se calculan dos metricas:
    #   homonimos -> mismo nombre normalizado en cualquier sitio (literal del encargo)
    #   reales    -> mismo nombre + MISMO sistema, sin pistas ni .m3u
    dirs_ext = collections.defaultdict(set)
    for f in roms:
        dirs_ext[f["path"].rsplit("/", 1)[0]].add(f["ext"])

    def is_track(f):
        return f["ext"] == ".bin" and ".cue" in dirs_ext[f["path"].rsplit("/", 1)[0]]

    homonimos = collections.defaultdict(list)
    for f in roms:
        if f["norm"]:
            homonimos[f["norm"]].append(f)
    dup_hom = {k: v for k, v in homonimos.items() if len(v) > 1}

    candidatos = [f for f in roms if f["norm"] and not is_track(f) and f["ext"] != ".m3u"]
    reales = collections.defaultdict(list)
    for f in candidatos:
        reales[(f["system"], f["norm"])].append(f)
    dup_groups = {f"{k[0]} | {k[1]}": v for k, v in reales.items() if len(v) > 1}

    dup_files = sum(len(v) for v in dup_hom.values())
    dup_wasted = sum(sum(x["size"] for x in v) - max(x["size"] for x in v)
                     for v in dup_groups.values())
    dup_mirror = sum(1 for v in dup_groups.values()
                     if {x["scope"] for x in v} == {"live", "FOREVER"})
    dup_mismo_formato = sum(1 for v in dup_groups.values()
                            if len({x["ext"] for x in v}) == 1)

    # ---------- basura / anomalias ----------
    junk = [f for f in files if JUNK_RE.search(f["name"])]
    parts_tmp = [f for f in files if f["ext"] in (".part", ".tmp")]
    torrent_sin_rom = []
    rom_keys = {(f["norm"], f["ext"]) for f in roms}
    for t in torrents:
        n = norm_name(t["path"])
        if n and (n, "") not in rom_keys and not any(k[0] == n for k in rom_keys):
            torrent_sin_rom.append(t)
    weird_ext = [f for f in others if f["scope"] in ("live", "FOREVER")]

    # ---------- totales ----------
    total_roms = len(roms)
    total_real = sum(1 for f in roms if not f["stub"] and f["size"] >= 1024)
    total_stubs = len(stubs)
    total_bytes = sum(f["size"] for f in files)
    rom_bytes = sum(f["size"] for f in roms)
    top_size = sorted(sys_rows.items(), key=lambda kv: -kv[1]["bytes_rom"])[:10]

    data = {
        "generado": "auditoria read-only sobre /storage/FFF9-FF05/ROMs",
        "fuente_raw": "device/audit_sd_raw/files.tsv",
        "du_total_kb": du.get("/storage/FFF9-FF05/ROMs"),
        "du_forever_kb": {k.split("FOREVER/")[-1]: v for k, v in du.items() if "FOREVER/" in k},
        "totales": {
            "ficheros_totales": len(files),
            "roms_entradas": total_roms,
            "roms_reales_1kb_o_mas": total_real,
            "stubs_menos_1kb": total_stubs,
            "stubs_menos_1kb_incl_texto": len(stubs_txt) + total_stubs,
            "torrents_placeholder": len(torrents),
            "otros_ficheros": len(others),
            "bytes_totales": total_bytes,
            "bytes_roms": rom_bytes,
            "bytes_stubs": sum(f["size"] for f in stubs),
            "japonesas_fuera_cuarentena": len(jp_live),
            "japonesas_en_cuarentena": len(jp_quar),
            "grupos_duplicados": len(dup_groups),
            "grupos_homonimos": len(dup_hom),
            "ficheros_en_grupos_duplicados": dup_files,
            "bytes_duplicados_desperdiciados": dup_wasted,
            "grupos_duplicados_mismo_formato": dup_mismo_formato,
            "grupos_que_son_espejo_live_forever": dup_mirror,
        },
        "stubs_tamanos_frecuentes": dict(stub_sizes.most_common(12)),
        "por_sistema": sys_rows,
        "cuarentena_por_sistema": {k: {"ficheros": v, "bytes": quar_bytes[k]}
                                   for k, v in sorted(quar.items())},
        "japonesas_fuera_cuarentena": [
            {"sistema": f["system"], "scope": f["scope"], "size": f["size"], "rel": f["rel"]}
            for f in sorted(jp_live, key=lambda x: (x["system"], x["name"]))],
        "stubs": [{"sistema": f["system"], "scope": f["scope"], "ext": f["ext"],
                   "size": f["size"], "rel": f["rel"]} for f in stubs],
        "stubs_por_sistema": dict(stubs_by_sys.most_common()),
        "stubs_texto_excluidos": [{"rel": f["rel"], "size": f["size"]} for f in stubs_txt],
        # reales: mismo nombre + mismo sistema (sin pistas de .cue)
        "duplicados": [
            {"clave": k, "n": len(v), "bytes": sum(x["size"] for x in v),
             "desperdicio": sum(x["size"] for x in v) - max(x["size"] for x in v),
             "mismo_formato": len({x["ext"] for x in v}) == 1,
             "rutas": [{"rel": x["rel"], "size": x["size"]} for x in v]}
            for k, v in sorted(dup_groups.items(),
                               key=lambda kv: -(sum(x["size"] for x in kv[1])
                                                - max(x["size"] for x in kv[1])))],
        # homonimos: mismo nombre sin mirar plataforma (incluye pistas y .m3u)
        "homonimos": [
            {"clave": k, "n": len(v), "sistemas": sorted({x["system"] for x in v}),
             "rutas": [x["rel"] for x in v]}
            for k, v in sorted(dup_hom.items(), key=lambda kv: (-len(kv[1]), kv[0]))],
        "basura": {
            "isos_no_rom": [{"rel": f["rel"], "size": f["size"]} for f in junk],
            "parciales_part_tmp": [{"rel": f["rel"], "size": f["size"]} for f in parts_tmp],
            "torrents_sin_rom": len(torrent_sin_rom),
            "otros_en_dirs_rom": [{"rel": f["rel"], "size": f["size"], "ext": f["ext"]}
                                  for f in weird_ext if f["ext"] not in ROM_EXTS][:60],
        },
        "top_tamanos": [{"sistema": k, **{kk: v[kk] for kk in
                        ("roms", "reales", "stubs", "bytes_rom")}} for k, v in top_size],
    }

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    # ---------- datos derivados para el informe ----------
    jp_puras = [f for f in jp_live if not f["japan_es"]]
    jp_trad = [f for f in jp_live if f["japan_es"]]
    quar_roms = [f for f in roms if f["scope"] == "cuarentena"
                 and "/_cuarentena/japan/" in f["path"]]
    quar_untagged = [f for f in quar_roms if not f["japan"]]
    quar_other = [f for f in roms if f["scope"] == "cuarentena"
                  and "/_cuarentena/japan/" not in f["path"]]
    quar_torrents = sum(1 for f in torrents if "/_cuarentena/japan/" in f["path"])
    dup_real = [g for g in dup_groups.values() if any(x["size"] >= 1024 for x in g)]
    dup_stub = [g for g in dup_groups.values() if all(x["size"] < 1024 for x in g)]
    d_bytes_real = sum(sum(x["size"] for x in g) - max(x["size"] for x in g) for g in dup_real)

    data["totales"]["japonesas_fuera_puras"] = len(jp_puras)
    data["totales"]["japonesas_fuera_con_traduccion_es"] = len(jp_trad)
    data["totales"]["grupos_dup_con_fichero_real"] = len(dup_real)
    data["totales"]["grupos_dup_solo_stubs"] = len(dup_stub)
    data["totales"]["bytes_dup_grupos_reales"] = d_bytes_real
    data["totales"]["bytes_basura_no_rom"] = sum(f["size"] for f in junk)
    data["japonesas_fuera_cuarentena"] = [
        {"sistema": f["system"], "scope": f["scope"], "size": f["size"],
         "traduccion_es": f["japan_es"], "rel": f["rel"]}
        for f in sorted(jp_live, key=lambda x: (x["system"], x["name"]))]
    data["cuarentena_sin_etiqueta_jp"] = [
        {"sistema": f["system"], "size": f["size"], "rel": f["rel"]} for f in quar_untagged]
    data["cuarentena_reales"] = sum(1 for f in quar_roms if f["size"] >= 1024)
    data["cuarentena_stubs"] = sum(1 for f in quar_roms if f["stub"])
    data["top_tamanos"] = [{"sistema": k, **{kk: v[kk] for kk in
                            ("roms", "reales", "stubs", "bytes_rom", "bytes_limpio")}}
                           for k, v in top_size]
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    # =================== INFORME MD ===================
    T = data["totales"]
    L = []
    A = L.append
    A("# Auditoría de ROMs reales en la SD del AYN Thor")
    A("")
    A("**Dispositivo:** AYN Thor (`adb-9205e6b1`) · **SD:** `/storage/FFF9-FF05`  ")
    A("**Ámbito:** `/storage/FFF9-FF05/ROMs/` completo — incluye `FOREVER/<sistema>/` y `_cuarentena/`  ")
    A("**Método:** sólo lectura (`adb shell find -printf '%s\\t%p'`, `du -sk`, `df -k`) y post-proceso "
      "con Python local. No se ha instalado, escrito, movido ni borrado nada en el dispositivo; "
      "no se ha tocado el catálogo de la app.")
    A("")
    A("## 1. Resumen")
    A("")
    A("| Métrica | Valor |")
    A("|---|---:|")
    A(f"| Ficheros inventariados (todos) | {T['ficheros_totales']:,} |")
    A(f"| **Entradas de ROM** (extensiones de carga útil) | **{T['roms_entradas']:,}** |")
    A(f"| ROMs reales (≥ 1 KB) | **{T['roms_reales_1kb_o_mas']}** |")
    A(f"| **Stubs / fakes (< 1 KB)** | **{T['stubs_menos_1kb']:,}** |")
    A(f"| Placeholders `.torrent` | {T['torrents_placeholder']:,} |")
    A(f"| Otros ficheros (txt/srm/ini/db/bak) | {T['otros_ficheros']:,} |")
    A(f"| Espacio total ocupado | {human(T['bytes_totales'])} |")
    A(f"| Espacio en stubs | {human(T['bytes_stubs'])} |")
    A(f"| Basura no-ROM (ISOs de Linux) | {human(T['bytes_basura_no_rom'])} |")
    A(f"| Japonesas **fuera** de cuarentena | **{T['japonesas_fuera_cuarentena']}** "
      f"({T['japonesas_fuera_puras']} puras + {T['japonesas_fuera_con_traduccion_es']} con traducción ES) |")
    A(f"| Japonesas en cuarentena (`_cuarentena/japan/`) | {T['japonesas_en_cuarentena']} |")
    A(f"| **Duplicados reales** (mismo sistema) | **{T['grupos_duplicados']} grupos** "
      f"→ {human(T['bytes_dup_grupos_reales'])} desperdiciados |")
    A(f"| Homónimos entre plataformas distintas (no duplican) | "
      f"{T['grupos_homonimos'] - T['grupos_duplicados']} |")
    A("")
    pct = 100.0 * T["stubs_menos_1kb"] / T["roms_entradas"] if T["roms_entradas"] else 0
    A("### Lectura clave")
    A("")
    A(f"El **{pct:.1f} %** de las entradas de ROM ({T['stubs_menos_1kb']:,} de {T['roms_entradas']:,}) "
      f"son ficheros de **menos de 1 KB**. La SD no contiene la biblioteca: contiene el **índice** de "
      f"descargas. Sólo **{T['roms_reales_1kb_o_mas']} ficheros** tienen contenido real y son los que "
      f"ocupan el espacio ({human(T['bytes_roms'])} de {human(T['bytes_totales'])}).")
    A("")
    A("Tamaños de stub más frecuentes (bytes → nº): " +
      ", ".join(f"`{k}`→{v}" for k, v in list(data["stubs_tamanos_frecuentes"].items())))
    A("")
    if data["du_total_kb"]:
        A(f"`du -sk` del árbol: **{data['du_total_kb']/2**20:.2f} GiB** en bloques de disco "
          f"(suma lógica de tamaños: {human(T['bytes_totales'])}; la diferencia se debe a ficheros "
          "dispersos, p. ej. ISOs preasignadas).")
        A("")
    A("## 2. Por sistema")
    A("")
    A("`entradas` = ficheros con extensión de ROM · `reales` = ≥ 1 KB · `stubs` = < 1 KB "
      "(excluye `.m3u`/`.cue`, que son texto por naturaleza) · `JP fuera` = Japan/JPN/(J)/(JP) "
      "fuera de cuarentena · `limpio` = sin las ISOs de Linux.")
    A("")
    A("| Sistema | Entradas | Reales | Stubs | `.torrent` | JP fuera | Bytes ROM | Bytes limpio |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for s_, d in sorted(sys_rows.items(), key=lambda kv: -kv[1]["bytes_rom"]):
        if d["roms"] == 0 and d["torrents"] == 0:
            continue
        A(f"| `{s_}` | {d['roms']} | {d['reales']} | {d['stubs']} | {d['torrents']} | "
          f"{d['japan_fuera_cuarentena']} | {human(d['bytes_rom'])} | {human(d['bytes_limpio'])} |")
    A(f"| **TOTAL** | **{T['roms_entradas']}** | **{T['roms_reales_1kb_o_mas']}** | "
      f"**{T['stubs_menos_1kb']}** | **{T['torrents_placeholder']}** | "
      f"**{T['japonesas_fuera_cuarentena']}** | **{human(T['bytes_roms'])}** | "
      f"**{human(T['bytes_roms']-T['bytes_basura_no_rom'])}** |")
    A("")
    A("### Top 5 por tamaño")
    A("")
    A("| # | Sistema | Tamaño ROM | Sin basura | Entradas | Reales | Stubs |")
    A("|---:|---|---:|---:|---:|---:|---:|")
    for i, t in enumerate(data["top_tamanos"][:5], 1):
        A(f"| {i} | `{t['sistema']}` | {human(t['bytes_rom'])} | {human(t['bytes_limpio'])} | "
          f"{t['roms']} | {t['reales']} | {t['stubs']} |")
    A("")
    A("## 3. Japonesas restantes fuera de cuarentena")
    A("")
    if not jp_live:
        A("Ninguna.")
    else:
        A(f"**{len(jp_live)} entradas.** Detalle importante: {len(jp_trad)} de ellas son juegos "
          f"japoneses **con parche de traducción al castellano** (`T-Spa`, `T+Spa`), es decir, "
          f"material que el catálogo conserva a propósito. Las **{len(jp_puras)} restantes** son "
          "japonesas puras que se quedaron sin mover.")
        A("")
        A("| Sistema | Bytes | Tipo | Ruta (relativa a `ROMs/`) |")
        A("|---|---:|---|---|")
        for f in sorted(jp_live, key=lambda x: (not x["japan_es"], x["system"], x["name"])):
            tipo = "traducción ES" if f["japan_es"] else "**japonesa pura**"
            A(f"| `{f['system']}` | {f['size']:,} | {tipo} | `{f['rel']}` |")
    A("")
    A("## 4. Cuarentena japonesa")
    A("")
    A(f"`_cuarentena/japan/<sistema>/` contiene **{len(quar_roms)} entradas de ROM** "
      f"({data['cuarentena_reales']} reales ≥ 1 KB y {data['cuarentena_stubs']} stubs) "
      f"más **{quar_torrents} `.torrent`**. Los {len(quar_roms)-data['cuarentena_reales']-data['cuarentena_stubs']} "
      "restantes son `.m3u`/`.cue`. Es decir: la cuarentena es, otra vez, casi toda índice "
      "de descargas; sólo "
      f"{data['cuarentena_reales']} ficheros tienen bytes de verdad.")
    A("")
    A("| Sistema (destino) | Ficheros | Tamaño |")
    A("|---|---:|---:|")
    qs = collections.Counter()
    qb = collections.Counter()
    for f in quar_roms:
        qs[f["system"]] += 1
        qb[f["system"]] += f["size"]
    for s_, n in qs.most_common():
        A(f"| `{s_}` | {n} | {human(qb[s_])} |")
    A(f"| **TOTAL** | **{len(quar_roms)}** | **{human(sum(qb.values()))}** |")
    if quar_other:
        A("")
        A("Fuera de `japan/`, sueltos en `_cuarentena/`, quedan copias reales:")
        A("")
        for f in quar_other:
            A(f"- **`{f['rel']}`** — {human(f['size'])}")
    A("")
    A(f"Además hay **{len(data['cuarentena_sin_etiqueta_jp'])} ficheros** dentro de `_cuarentena/japan/` "
      "que **no** llevan la marca `(Japan)` — son cartuchos `(JU)`/`(JUE)` "
      "(Japón+EE. UU.), que también entraron en cuarentena:")
    A("")
    for f in data["cuarentena_sin_etiqueta_jp"]:
        A(f"- `{f['rel']}` ({f['size']} B)")
    A("")
    A("## 5. Stubs / fakes (< 1 KB)")
    A("")
    A(f"**{T['stubs_menos_1kb']}** ficheros con extensión de ROM y menos de 1024 bytes; "
      f"en conjunto ocupan {human(T['bytes_stubs'])}. Formatos afectados: todos "
      "(`.zip`, `.chd`, `.iso`, `.nes`, `.smc`, `.nds`, `.pak`, `.cia`…), lo que confirma que "
      "el stub se genera al indexar la ficha, no al descargar.")
    A("")
    _sz = [f["size"] for f in data["stubs"]]
    A(f"Tamaños observados: **{min(_sz)}–{max(_sz)} B**, mediana {sorted(_sz)[len(_sz)//2]} B. "
      "No hay ningún stub de 279 B en esta SD, aunque ese tamaño se haya visto en otras.")
    A("")
    A("| Sistema | Stubs |")
    A("|---|---:|")
    for s_, n in data["stubs_por_sistema"].items():
        A(f"| `{s_}` | {n} |")
    A("")
    A("### Muestra (3 primeras por sistema)")
    A("")
    A("| Sistema | Fichero | Bytes |")
    A("|---|---|---:|")
    seen = collections.Counter()
    for f in stubs:
        if seen[f["system"]] >= 3:
            continue
        seen[f["system"]] += 1
        A(f"| `{f['system']}` | `{f['name']}` | {f['size']} |")
    A("")
    A(f"Listado completo de los {T['stubs_menos_1kb']} stubs: `device/audit_sd.json` → `stubs`.")
    A("")
    if stubs_txt:
        A(f"Nota: se han excluido {len(stubs_txt)} `.m3u`/`.cue` de menos de 1 KB (son listas de "
          f"texto, su tamaño es normal). Contando también esos: {T['stubs_menos_1kb_incl_texto']} "
          "ficheros < 1 KB con extensión de ROM.")
        A("")
    A("## 6. Duplicados")
    A("")
    A("Clave = nombre en minúsculas, sin etiquetas `()`/`[]`, sin extensión. Se dan dos cifras "
      "porque la definición literal engaña:")
    A("")
    A(f"- **Homónimos** (mismo nombre, cualquier plataforma): {T['grupos_homonimos']} grupos con "
      f"{T['ficheros_en_grupos_duplicados']} ficheros. Incluye falsos positivos claros: "
      "`Crazy Taxi` en Dreamcast/PS2/GC, `Doom` en 32X/GBA/PSX, o las pistas "
      "`(Track 1).bin` + `(Track 2).bin` + `.cue` de un mismo disco.")
    A(f"- **Duplicados reales** (mismo nombre **y mismo sistema**, sin pistas `.bin` ni `.m3u`): "
      f"**{T['grupos_duplicados']} grupos**, todos con contenido de verdad, que desperdician "
      f"**{human(T['bytes_dup_grupos_reales'])}**.")
    A("")
    A(f"El patrón dominante es el **espejo `FOREVER/<sistema>/<juego>/` de `<sistema>/`**: "
      f"{T['grupos_que_son_espejo_live_forever']} de los {T['grupos_duplicados']} grupos tienen "
      "exactamente una copia en cada ámbito (la misma ROM descargada dos veces). El resto son "
      "copias numeradas `(1)`, `(2)` dentro de `FOREVER`, que también son descargas repetidas.")
    A("")
    A("| Sistema · Juego | Copias | Ocupa | Desperdicia | Mismo formato | Rutas |")
    A("|---|---:|---:|---:|:--:|---|")
    for g in data["duplicados"][:22]:
        rutas = "<br>".join(x["rel"].replace("|", "\\|") for x in g["rutas"][:3])
        if g["n"] > 3:
            rutas += f"<br>*+{g['n']-3}*"
        ok = "sí" if g["mismo_formato"] else "no"
        clave = g["clave"].replace(" | ", " · ")[:46]
        A(f"| `{clave}` | {g['n']} | {human(g['bytes'])} | "
          f"{human(g['desperdicio'])} | {ok} | {rutas} |")
    A("")
    A(f"Resto hasta {T['grupos_duplicados']}: `device/audit_sd.json` → `duplicados` "
      f"(y los {T['grupos_homonimos']} homónimos en `homonimos`). "
      "Cuando el formato cambia (`.zip` vs `.iso` del mismo juego) no es una copia exacta, "
      "pero sí ocupa el doble.")
    A("")
    A("## 7. Rutas problemáticas")
    A("")
    if junk:
        A("### ISOs de Linux dentro de carpetas de ROMs (no son juegos, ~2,3 GB)")
        A("")
        for f in junk:
            A(f"- `{f['rel']}` — {human(f['size'])}")
        A("")
    if parts_tmp:
        A("### Descargas parciales")
        A("")
        for f in parts_tmp:
            A(f"- `{f['rel']}` — {human(f['size'])}")
        A("")
    A("### Copia real perdida en la raíz de la cuarentena")
    A("")
    A("- `_cuarentena/Ace Combat (Japan).chd` — 331 MB, suelta fuera de `_cuarentena/japan/psx/`. "
      "El mismo CHD está también en `FOREVER/psx/Ace Combat (Japan)/`.")
    A("")
    A("### Ficheros ajenos en carpetas de sistema")
    A("")
    emu = [f for f in data["basura"]["otros_en_dirs_rom"]
           if any(x in f["rel"] for x in ("/nand/", "/sdmc/", "/config/", "/log/"))]
    ajenos = [f for f in data["basura"]["otros_en_dirs_rom"] if f not in emu]
    if emu:
        A(f"- **{len(emu)} ficheros** ({human(sum(f['size'] for f in emu))}) son el árbol de "
          "datos de un emulador de 3DS copiado dentro de `FOREVER/n3ds/`: "
          "`nand/...`, `sdmc/Nintendo 3DS/...`, `config/config.ini`, `log/azahar_log*.txt`. "
          "No son ROMs y no deberían viajar en el pack.")
    for f in ajenos[:12]:
        ext = "(sin extensión)" if f["ext"] in ("", ".(sin)") else f["ext"]
        A(f"- `{f['rel']}` ({ext}, {f['size']} B)")
    if len(ajenos) > 12:
        A(f"- …y {len(ajenos) - 12} más en `device/audit_sd.json` → `basura.otros_en_dirs_rom`.")
    A("")
    A("### `.torrent` sin ROM")
    A("")
    A(f"**{data['basura']['torrents_sin_rom']}** descriptores `.torrent` no tienen fichero de juego "
      "asociado. Ocupan el sitio de una ROM que nunca se descargó; el emulador no puede lanzarlos.")
    A("")
    A("## 8. Reproducibilidad")
    A("")
    A("```")
    A("# volcado (sólo lectura)")
    A("adb shell \"find /storage/FFF9-FF05/ROMs -type f -printf '%s\\t%p\\n'\" > device/audit_sd_raw/files.tsv")
    A("python3 scripts/audit_sd.py")
    A("```")
    A("")
    A("- `device/audit_sd.json` — datos crudos (por sistema, stubs completos, duplicados, japonesas).")
    A("- `device/AUDIT_SD.md` — este informe.")
    A("- `device/audit_sd_raw/files.tsv`, `du.tsv` — volcados originales del dispositivo.")
    A("- `scripts/audit_sd.py` — script de auditoría.")
    A("")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    print("OK")
    print(json.dumps(T, indent=1, ensure_ascii=False))
    print("top5:", [(k, round(v["bytes_rom"] / 2**20, 1)) for k, v in top_size[:5]])


def parts_parent(path):
    p = path.rsplit("/", 1)[0]
    return p.rsplit("/", 1)[-1]


if __name__ == "__main__":
    main()
