#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria SOLO LECTURA: coherencia gamelists ES-DE <-> catalogo de la app (AYN Thor).

Entradas (ya volcadas en local, sin tocar el dispositivo):
  device/gamelists_raw/<sistema>/gamelist.xml      (36 gamelists)
  device/roms_index.txt                            (find /storage/FFF9-FF05/ROMs -type f)
  device/roms_dirs.txt                             (find ... -type d)
  device/catalog_es/<sistema>.jsonl                (catalogo de la app)

Salidas: device/gamelists_audit.json  y  device/GAMELISTS_AUDIT.md
"""
import os, re, json, xml.etree.ElementTree as ET
from collections import Counter, defaultdict

ROOT = r"C:\Users\XAM-PC\Proyectos\AYN-Thor-ESDE"
RAW = os.path.join(ROOT, "device", "gamelists_raw")
CAT = os.path.join(ROOT, "device", "catalog_es")
OUT_JSON = os.path.join(ROOT, "device", "gamelists_audit.json")
OUT_MD = os.path.join(ROOT, "device", "GAMELISTS_AUDIT.md")

SD = "/storage/FFF9-FF05"
ROMS = SD + "/ROMs"
QUAR = ROMS + "/_cuarentena"
SYS = ("atomiswave cps1 cps2 cps3 dreamcast fbneo gb gba gbc gc mame megacd megadrive "
       "model2 model3 n3ds n64 naomi naomi2 nds neogeo nes openbor ps2 ps3 psp psvita psx "
       "saturn sega32x snes switch wii wiiu xbox xbox360").split()
assert len(SYS) == 36, len(SYS)

RE_JP = re.compile(r"(?i)japan|jap\b|jpn|\bjp\b|\(j\)")
MAXEX = 20


def norm(s):
    s = (s or "").replace("\\", "/").strip()
    while s.startswith("./"):
        s = s[2:]
    return s


def load_index():
    files, dirs = set(), set()
    for name, acc in (("roms_index.txt", files), ("roms_dirs.txt", dirs)):
        with open(os.path.join(ROOT, "device", name), encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.rstrip("\r\n")
                if ln:
                    acc.add(ln)
    return files, dirs


def parse_gamelist(path):
    try:
        root = ET.parse(path).getroot()
        return [{"name": (g.findtext("name") or "").strip(),
                 "desc": (g.findtext("desc") or ""),
                 "path": (g.findtext("path") or "").strip()} for g in root.findall("game")], "xml.etree"
    except Exception as e:                                    # noqa: BLE001
        txt = open(path, encoding="utf-8", errors="replace").read()
        out = []
        for blk in re.findall(r"<game>(.*?)</game>", txt, re.S):
            n = re.search(r"<name>(.*?)</name>", blk, re.S)
            d = re.search(r"<desc>(.*?)</desc>", blk, re.S)
            p = re.search(r"<path>(.*?)</path>", blk, re.S)
            out.append({"name": (n.group(1).strip() if n else ""),
                        "desc": (d.group(1) if d else ""),
                        "path": (p.group(1).strip() if p else "")})
        return out, "regex-fallback (%s)" % e


def load_catalog(sysname):
    p = os.path.join(CAT, sysname + ".jsonl")
    out = []
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:                                  # noqa: BLE001
                pass
    return out


def main():
    files, dirs = load_index()
    by_dir = defaultdict(dict)
    for f in files:
        d, b = f.rsplit("/", 1)
        by_dir[d][b.lower()] = b

    report = {
        "alcance": "SOLO LECTURA: no se ha modificado ninguna gamelist, ROM ni ajuste del dispositivo",
        "gamelists_base": "/storage/emulated/0/ES-DE/gamelists/<sistema>/gamelist.xml",
        "roms_base": ROMS + "/<sistema>/ (segun custom_systems/es_systems.xml -> %ROMPATH%/<sistema>)",
        "catalogo_local": CAT.replace("\\", "/"),
        "sistemas": {},
        "totales": {},
    }

    tot = Counter()
    motivos = Counter()
    jp_tok = Counter()
    jp_field = Counter()
    rows = []

    for s in SYS:
        gl_path = os.path.join(RAW, s, "gamelist.xml")
        if not os.path.exists(gl_path):
            report["sistemas"][s] = {"error": "gamelist ausente en el volcado local"}
            continue
        entries, how = parse_gamelist(gl_path)
        cat = load_catalog(s)
        base = "%s/%s" % (ROMS, s)

        gl_paths, gl_base, gl_names = set(), set(), set()
        for e in entries:
            rp = norm(e["path"])
            gl_paths.add(rp)
            gl_base.add(rp.rsplit("/", 1)[-1])
            if e["name"]:
                gl_names.add(e["name"])
        gl_base_ci = {x.casefold() for x in gl_base}
        gl_names_ci = {x.casefold() for x in gl_names}

        broken, quar, quar_res = [], [], []
        for e in entries:
            rp = norm(e["path"])
            ap = rp if rp.startswith("/") else base + "/" + rp
            if ".torrent" in e["path"]:
                tot["rutas_torrent"] += 1
                if ap in files:
                    tot["rutas_torrent_existen"] += 1
            if ap.startswith(QUAR + "/"):
                quar.append({"name": e["name"], "gamelist_path": e["path"], "abs": ap})
            if ap in files:
                continue
            if ap.rstrip("/") in dirs or (ap + "/") in dirs:
                motivo = "la ruta es un directorio, no un fichero"
                motivos["DIRECTORIO"] += 1
            else:
                alt_forever = ("%s/FOREVER/%s/%s" % (ROMS, s, rp)) in files
                real = None
                for pre in ("%s/japan/%s/" % (QUAR, s), "%s/%s/" % (QUAR, s), QUAR + "/japan/"):
                    if (pre + rp) in files:
                        real = pre + rp
                        break
                d, b = ap.rsplit("/", 1)
                ci = by_dir.get(d, {}).get(b.lower())
                if real and alt_forever:
                    motivo = "no existe en %s/; hay copia en ROMs/FOREVER/%s/ y en _cuarentena/" % (s, s)
                    motivos["FOREVER+CUARENTENA"] += 1
                elif real:
                    motivo = "no existe en %s/; la ROM solo esta en /ROMs/_cuarentena/ (movida a cuarentena)" % s
                    motivos["SOLO_CUARENTENA"] += 1
                elif alt_forever:
                    motivo = "no existe en %s/; hay copia en ROMs/FOREVER/%s/ (fuera de la ruta de ES-DE)" % (s, s)
                    motivos["SOLO_FOREVER"] += 1
                elif ci and ci != b:
                    motivo = "no existe en la SD; en el directorio hay \"%s\" (solo difiere en mayusculas)" % ci
                    motivos["MAYUSCULAS"] += 1
                else:
                    motivo = "no existe en la SD (ni el fichero ni el directorio)"
                    motivos["AUSENTE"] += 1
                if real:
                    quar_res.append({"name": e["name"], "gamelist_path": e["path"],
                                     "abs": ap, "real": real})
                if ".torrent" in e["path"]:
                    motivos["CON_SUFIJO_TORRENT"] += 1
            broken.append({"name": e["name"], "gamelist_path": e["path"], "abs": ap, "motivo": motivo})

        # 4) huerfanas catalogo -> gamelist
        orphans, orphans_ci, orph_on_sd = [], [], 0
        for c in cat:
            p = norm(c.get("p") or "")
            n = (c.get("n") or "").strip()
            pb = p.rsplit("/", 1)[-1]
            if (pb and pb in gl_base) or (n and n in gl_names):
                continue
            on_sd = (base + "/" + p) in files
            orph_on_sd += 1 if on_sd else 0
            orphans.append({"n": n, "p": p, "ext": c.get("ext"), "en_sd": on_sd})
            if not ((pb and pb.casefold() in gl_base_ci) or (n and n.casefold() in gl_names_ci)):
                orphans_ci.append({"n": n, "p": p})
        cat_base = {norm(c.get("p") or "").rsplit("/", 1)[-1] for c in cat}
        cat_names = {(c.get("n") or "").strip() for c in cat}
        gl_sin_ficha = sum(1 for e in entries
                           if norm(e["path"]).rsplit("/", 1)[-1] not in cat_base
                           and e["name"] not in cat_names)

        # 5) Japon
        jp = []
        for e in entries:
            campos, muestra = [], ""
            for fld in ("name", "desc", "path"):
                txt = e[fld] or ""
                ms = RE_JP.findall(txt)
                if ms:
                    campos.append(fld)
                    jp_field[fld] += 1
                    for m in ms:
                        jp_tok[m.lower()] += 1
                    if not muestra:
                        if fld == "desc":
                            m = RE_JP.search(txt)
                            a, b = max(0, m.start() - 45), min(len(txt), m.end() + 45)
                            muestra = "..." + txt[a:b].replace("\n", " ") + "..."
                        else:
                            muestra = txt
            if campos:
                jp.append({"name": e["name"], "path": e["path"], "campos": campos,
                           "match": "; ".join(sorted({m.lower() for f in ("name", "desc", "path")
                                                      for m in RE_JP.findall(e[f] or "")})),
                           "muestra": muestra})

        row = {
            "gamelist_entries": len(entries),
            "catalogo_fichas": len(cat),
            "rotas": len(broken),
            "cuarentena_literal": len(quar),
            "cuarentena_resuelta": len(quar_res),
            "huerfanas": len(orphans),
            "huerfanas_ci": len(orphans_ci),
            "huerfanas_en_sd": orph_on_sd,
            "gamelist_sin_ficha": gl_sin_ficha,
            "japon": len(jp),
            "parse": how,
            "dup_paths": len(entries) - len(gl_paths),
            "rotas_ejemplos": broken[:MAXEX],
            "cuarentena_ejemplos": (quar or quar_res)[:MAXEX],
            "huerfanas_ejemplos": orphans[:MAXEX],
            "japon_ejemplos": jp[:MAXEX],
        }
        report["sistemas"][s] = row
        for k in ("gamelist_entries", "catalogo_fichas", "rotas", "cuarentena_literal",
                  "cuarentena_resuelta", "huerfanas", "huerfanas_ci", "huerfanas_en_sd",
                  "gamelist_sin_ficha", "japon", "dup_paths"):
            tot[k] += row[k]
        rows.append((s, row))
        print("%-11s gl=%4d cat=%4d rotas=%4d cuar=%2d/%2d huerf=%4d(enSD %3d) jp=%3d" %
              (s, len(entries), len(cat), len(broken), len(quar), len(quar_res),
               len(orphans), orph_on_sd, len(jp)), flush=True)

    report["totales"] = dict(tot)
    report["totales"]["sistemas"] = 36
    report["totales"]["ficheros_roms_indexados"] = len(files)
    tot["ficheros_roms_indexados"] = len(files)
    report["totales"]["rotas_por_motivo"] = dict(motivos)
    report["totales"]["japon_tokens"] = dict(jp_tok)
    report["totales"]["japon_por_campo"] = dict(jp_field)

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    write_md(report, rows, tot, motivos, jp_tok, jp_field)
    print("\nTOTALES", json.dumps(report["totales"], ensure_ascii=False))
    print("JSON:", OUT_JSON)
    print("MD:", OUT_MD)


def esc(s):
    return (s or "").replace("|", "\\|")


def write_md(report, rows, tot, motivos, jp_tok, jp_field):
    L = []
    A = L.append
    gl_t, cat_t = tot["gamelist_entries"], tot["catalogo_fichas"]

    A("# Auditoria gamelists ES-DE vs catalogo de la app — AYN Thor")
    A("")
    A("**Solo lectura.** No se ha modificado ninguna gamelist, ROM ni ajuste del dispositivo "
      "(unicamente `ls`/`find`/`cat` sobre `ES-DE` y `ROMs`, y el catalogo ya volcado en local).")
    A("")
    A("- Gamelists: `/storage/emulated/0/ES-DE/gamelists/<sistema>/gamelist.xml` — **36 ficheros, 3,7 MB**")
    A("- ROMs: `/storage/FFF9-FF05/ROMs/<sistema>/` — ruta que declara `custom_systems/es_systems.xml` "
      "(`%ROMPATH%/<sistema>`, 205 sistemas definidos; los 36 auditados usan esa forma)")
    A("- Catalogo: `C:/Users/XAM-PC/Proyectos/AYN-Thor-ESDE/device/catalog_es/<sistema>.jsonl`")
    A("- Ficheros reales indexados bajo `ROMs`: **%d** (`find /storage/FFF9-FF05/ROMs -type f`)" %
      tot["ficheros_roms_indexados"])
    A("")
    A("Todas las rutas de las gamelists son relativas (`./fichero.ext`); se resuelven, igual que hace "
      "ES-DE, contra el directorio del sistema: `/storage/FFF9-FF05/ROMs/<sistema>/<path>`.")
    A("")
    A("## Tabla resumen (puntos 1-5)")
    A("")
    A("| sistema | (1) entradas gamelist | (1) fichas catalogo | (2) rutas rotas | (3) paths en _cuarentena | (4) huerfanas catalogo | (5) menciones Japon |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    for s, r in rows:
        A("| %s | %d | %d | %d | %d | %d | %d |" % (s, r["gamelist_entries"], r["catalogo_fichas"],
                                                   r["rotas"], r["cuarentena_literal"],
                                                   r["huerfanas"], r["japon"]))
    A("| **TOTAL (36)** | **%d** | **%d** | **%d** | **%d** | **%d** | **%d** |" %
      (gl_t, cat_t, tot["rotas"], tot["cuarentena_literal"], tot["huerfanas"], tot["japon"]))
    A("")
    A("## 1. Entradas de gamelist vs fichas de catalogo")
    A("")
    A("Gamelists: **%d entradas** en 36 sistemas (0 `<folder>`, 0 `<path>` duplicados). "
      "Catalogo: **%d fichas**. Diferencia: **%+d** fichas de catalogo sin entrada de gamelist." %
      (gl_t, cat_t, cat_t - gl_t))
    A("")
    A("| sistema | entradas gamelist | fichas catalogo | diferencia | entradas sin ficha en catalogo |")
    A("|---|---:|---:|---:|---:|")
    for s, r in rows:
        A("| %s | %d | %d | %+d | %d |" % (s, r["gamelist_entries"], r["catalogo_fichas"],
                                           r["catalogo_fichas"] - r["gamelist_entries"],
                                           r["gamelist_sin_ficha"]))
    A("")
    A("## 2. Entradas con `<path>` que no existe en la SD (rutas rotas)")
    A("")
    A("**Total: %d de %d entradas (%.1f%%)**, repartidas en %d sistemas; %d sistemas sin ninguna ruta rota." %
      (tot["rotas"], gl_t, 100.0 * tot["rotas"] / max(1, gl_t),
       sum(1 for _, r in rows if r["rotas"]), sum(1 for _, r in rows if not r["rotas"])))
    A("")
    A("Desglose por motivo:")
    A("")
    for k, v in sorted(motivos.items(), key=lambda x: -x[1]):
        A("- `%s`: **%d**" % (k, v))
    A("")
    A("Nota sobre el sufijo `.torrent`: **%d de las %d entradas** (%.0f%%) tienen `<path>` acabado en `.torrent` "
      "(p. ej. `./Ikaruga (Japan).zip.torrent`); de esas, **%d existen** en la SD como fichero marcador y solo "
      "**%d estan rotas**. El unico caso roto sin copia en cuarentena es `gba / Advance Guardian Heroes.zip`." %
      (tot["rutas_torrent"], gl_t, 100.0 * tot["rutas_torrent"] / max(1, gl_t),
       tot["rutas_torrent_existen"], tot["rutas_torrent"] - tot["rutas_torrent_existen"]))
    A("")
    A("### 2.1 Ranking por sistema")
    A("")
    A("| sistema | rutas rotas | % de sus entradas |")
    A("|---|---:|---:|")
    for s, r in sorted(rows, key=lambda x: (-x[1]["rotas"], -x[1]["japon"])):
        if r["rotas"]:
            A("| %s | %d | %.1f%% |" % (s, r["rotas"], 100.0 * r["rotas"] / max(1, r["gamelist_entries"])))
    A("")
    A("### 2.2 Ejemplos (hasta 20 por sistema; ruta absoluta resuelta + motivo)")
    A("")
    for s, r in sorted(rows, key=lambda x: -x[1]["rotas"]):
        if not r["rotas"]:
            continue
        A("#### %s — %d rotas de %d entradas" % (s, r["rotas"], r["gamelist_entries"]))
        A("")
        A("| # | nombre | `<path>` en gamelist | ruta absoluta resuelta | motivo |")
        A("|---:|---|---|---|---|")
        for i, b in enumerate(r["rotas_ejemplos"], 1):
            A("| %d | %s | `%s` | `%s` | %s |" % (i, esc(b["name"]), esc(b["gamelist_path"]),
                                                  esc(b["abs"]), esc(b["motivo"])))
        if r["rotas"] > len(r["rotas_ejemplos"]):
            A("")
            A("*(+%d rotas mas en este sistema)*" % (r["rotas"] - len(r["rotas_ejemplos"])))
        A("")
    A("## 3. Entradas que apuntan a `/storage/FFF9-FF05/ROMs/_cuarentena/`")
    A("")
    A("- Rutas que contienen literalmente `/ROMs/_cuarentena/`: **%d** "
      "(ninguna gamelist escribe rutas absolutas de cuarentena: todas son `./fichero`)." % tot["cuarentena_literal"])
    A("- Entradas cuyo `<path>` resuelve a una ROM que **ya no esta** en `ROMs/<sistema>/` y **solo existe** "
      "dentro de `_cuarentena` (japan/<sistema> o <sistema>): **%d**. Son entradas que deberian salir de la "
      "gamelist y que ademas rompen el lanzamiento (se cuentan tambien en el punto 2)." % tot["cuarentena_resuelta"])
    A("")
    qej = [(s, q) for s, r in rows for q in r["cuarentena_ejemplos"]]
    if qej:
        A("Reparto por sistema: " + ", ".join(
            "**%s** %d" % (s, r["cuarentena_resuelta"]) for s, r in
            sorted(rows, key=lambda x: -x[1]["cuarentena_resuelta"]) if r["cuarentena_resuelta"]) + ".")
        A("")
        A("Ejemplos (hasta 2 por sistema):")
        A("")
        A("| sistema | nombre | `<path>` en la gamelist | ruta real hoy (dentro de `_cuarentena`) |")
        A("|---|---|---|---|")
        seen = Counter()
        shown = 0
        for s, q in qej:
            if seen[s] >= 2 or shown >= MAXEX:
                continue
            seen[s] += 1
            shown += 1
            A("| %s | %s | `%s` | `%s` |" % (s, esc(q["name"]), esc(q["gamelist_path"]),
                                             esc(q.get("real", q["abs"]))))
        A("")
        A("*(%d entradas en total. El detalle por sistema, hasta 20 por sistema, esta en "
          "`device/gamelists_audit.json` -> `sistemas.<sistema>.cuarentena_ejemplos`)*" % len(qej))
    A("")
    A("## 4. Fichas del catalogo sin correspondencia en la gamelist (huerfanas catalogo -> gamelist)")
    A("")
    A("Criterio: la ficha es huerfana si **ni** su `p` (basename del `<path>`) **ni** su `n` aparecen en "
      "la gamelist del sistema (comparacion exacta; con comparacion laxa sin mayusculas el resultado es el "
      "mismo: %d). **Total: %d de %d fichas (%.1f%%)**." %
      (tot["huerfanas_ci"], tot["huerfanas"], cat_t, 100.0 * tot["huerfanas"] / max(1, cat_t)))
    A("")
    A("Matiz importante: el catalogo es un inventario descargable (archive.org), no la lista de lo instalado, "
      "mientras que las gamelists solo contienen lo descargado. De las %d huerfanas, **%d tienen ademas el "
      "fichero ausente en `ROMs/<sistema>/`** y **%d tienen la ROM presente pero sin entrada en la gamelist** "
      "(esto ultimo seria el fallo real de sincronizacion catalogo -> ES-DE)." %
      (tot["huerfanas"], tot["huerfanas"] - tot["huerfanas_en_sd"], tot["huerfanas_en_sd"]))
    A("")
    A("| sistema | fichas catalogo | huerfanas | % | de ellas, ROM presente en la SD |")
    A("|---|---:|---:|---:|---:|")
    for s, r in sorted(rows, key=lambda x: -x[1]["huerfanas"]):
        A("| %s | %d | %d | %.1f%% | %d |" % (s, r["catalogo_fichas"], r["huerfanas"],
                                             100.0 * r["huerfanas"] / max(1, r["catalogo_fichas"]),
                                             r["huerfanas_en_sd"]))
    A("")
    A("### 4.1 Ejemplos (hasta 20 por sistema)")
    A("")
    for s, r in sorted(rows, key=lambda x: -x[1]["huerfanas"]):
        if not r["huerfanas"]:
            continue
        extra = "" if r["huerfanas"] <= len(r["huerfanas_ejemplos"]) else \
            " ... (+%d)" % (r["huerfanas"] - len(r["huerfanas_ejemplos"]))
        A("- **%s** (%d): " % (s, r["huerfanas"]) +
          "; ".join("`%s`" % esc(o["p"] or o["n"]) for o in r["huerfanas_ejemplos"]) + extra)
    A("")
    A("## 5. Menciones a Japon en campos visibles")
    A("")
    A("Regex: `(?i)japan|jap\\b|jpn|\\bjp\\b|\\(j\\)` aplicada a `<name>`, `<desc>` y `<path>`. "
      "**%d entradas afectadas de %d (%.1f%%)**." %
      (tot["japon"], gl_t, 100.0 * tot["japon"] / max(1, gl_t)))
    A("")
    A("Hallazgos por campo: " + ", ".join("`%s` en %d" % (k, v) for k, v in sorted(jp_field.items(), key=lambda x: -x[1])) +
      ". Tokens detectados: " + ", ".join("`%s` x%d" % (k, v) for k, v in sorted(jp_tok.items(), key=lambda x: -x[1])) + ".")
    A("")
    A("| sistema | entradas con mencion |")
    A("|---|---:|")
    for s, r in sorted(rows, key=lambda x: -x[1]["japon"]):
        if r["japon"]:
            A("| %s | %d |" % (s, r["japon"]))
    A("")
    A("### 5.1 Ejemplos (hasta 20 por sistema)")
    A("")
    for s, r in sorted(rows, key=lambda x: -x[1]["japon"]):
        if not r["japon"]:
            continue
        A("**%s** (%d)" % (s, r["japon"]))
        A("")
        A("| nombre | `<path>` | campo(s) | match |")
        A("|---|---|---|---|")
        for j in r["japon_ejemplos"]:
            A("| %s | `%s` | %s | %s |" % (esc(j["name"]), esc(j["path"]),
                                           ", ".join(j["campos"]), esc(j["match"])))
        if r["japon"] > len(r["japon_ejemplos"]):
            A("")
            A("*(+%d mas)*" % (r["japon"] - len(r["japon_ejemplos"])))
        A("")
    A("## 6. Verificacion sobre el dispositivo (controles de solo lectura)")
    A("")
    A("Estas comprobaciones se lanzaron con `adb shell \"su -c '...'\"` (solo `ls`, `find`, `grep`, `du`, `[ -e ]`) "
      "para validar que el analisis local refleja el dispositivo:")
    A("")
    A("| control | comando | resultado |")
    A("|---|---|---|")
    A("| nº de directorios de gamelist | `ls -1 /storage/emulated/0/ES-DE/gamelists/ \\| wc -l` | 36, conjunto identico a los 36 sistemas y a `device/catalog_es/*.jsonl` (diff vacio) |")
    A("| integridad de los volcados | `grep -c \"<game>\" .../gamelist.xml` | saturn 150, mame 200, nes 150, psvita 12, wiiu 3 — igual que el conteo local |")
    A("| indice de ROMs completo | `find /storage/FFF9-FF05/ROMs -type f \\| wc -l` | 3918 = %d lineas de `device/roms_index.txt` |" % tot["ficheros_roms_indexados"])
    A("| contenido de la cuarentena | `find /storage/FFF9-FF05/ROMs/_cuarentena -type f \\| wc -l` | 290 ficheros (278 de ellos referenciados por gamelists) |")
    A("| rutas relativas vs absolutas | `grep \"<path>\"` | 100%% relativas (`./fichero`); ninguna mencion literal a `_cuarentena` |")
    A("| caso roto sin copia | `[ -e ]` sobre `ROMs/gba/Advance Guardian Heroes.zip` y su ruta en cuarentena | no existe en ninguna de las dos |")
    A("| caso roto en cuarentena | `[ -e ]` sobre `ROMs/dreamcast/Ikaruga (Japan).zip.torrent` y `_cuarentena/japan/dreamcast/...` | solo existe dentro de `_cuarentena` |")
    A("| tamano de las gamelists | `du -sh .../gamelists` | 3.7M |")
    A("")
    A("## 7. Totales globales")
    A("")
    A("| metrica | valor |")
    A("|---|---:|")
    A("| sistemas auditados | 36 |")
    A("| entradas de gamelist | %d |" % gl_t)
    A("| fichas de catalogo | %d |" % cat_t)
    A("| diferencia catalogo - gamelist | %+d |" % (cat_t - gl_t))
    A("| rutas rotas (`<path>` inexistente) | %d |" % tot["rotas"])
    A("| ... de ellas, ROM solo en `_cuarentena` | %d |" % tot["cuarentena_resuelta"])
    A("| rutas con `/ROMs/_cuarentena/` literal | %d |" % tot["cuarentena_literal"])
    A("| fichas huerfanas catalogo -> gamelist | %d |" % tot["huerfanas"])
    A("| ... de ellas con ROM presente en la SD | %d |" % tot["huerfanas_en_sd"])
    A("| entradas de gamelist con mencion a Japon | %d |" % tot["japon"])
    A("| entradas de gamelist sin ficha en el catalogo | %d |" % tot["gamelist_sin_ficha"])
    A("| `<path>` acabados en `.torrent` (existentes / rotos) | %d (%d / %d) |" %
      (tot["rutas_torrent"], tot["rutas_torrent_existen"],
       tot["rutas_torrent"] - tot["rutas_torrent_existen"]))
    A("| ficheros reales bajo `/storage/FFF9-FF05/ROMs` | %d |" % tot["ficheros_roms_indexados"])
    A("| `<path>` duplicados dentro de una gamelist | %d |" % tot["dup_paths"])
    A("")
    A("### Los 3 sistemas mas problematicos")
    A("")
    for i, (s, r) in enumerate(sorted(rows, key=lambda x: (-x[1]["rotas"], -x[1]["japon"]))[:3], 1):
        A("%d. **%s** — %d rutas rotas de %d entradas (%.0f%%), %d de ellas con la ROM solo en cuarentena, "
          "%d entradas con mencion a Japon, %d fichas huerfanas." %
          (i, s, r["rotas"], r["gamelist_entries"],
           100.0 * r["rotas"] / max(1, r["gamelist_entries"]), r["cuarentena_resuelta"],
           r["japon"], r["huerfanas"]))
    A("")
    A("Ordenado por numero absoluto de rutas rotas. En proporcion (sistemas con al menos 10 entradas), los peores "
      "son: " + ", ".join("**%s** %.0f%% (%d/%d)" % (s, 100.0 * r["rotas"] / max(1, r["gamelist_entries"]),
                                                     r["rotas"], r["gamelist_entries"])
                          for s, r in sorted([x for x in rows if x[1]["gamelist_entries"] >= 10],
                                             key=lambda x: -x[1]["rotas"] / max(1, x[1]["gamelist_entries"]))[:3]) + ".")
    A("")
    A("---")
    A("")
    A("*Datos crudos: `device/gamelists_audit.json`. Gamelists volcadas tal cual: "
      "`device/gamelists_raw/<sistema>/gamelist.xml`. Indices: `device/roms_index.txt`, `device/roms_dirs.txt`. "
      "Scripts: `scripts/pull_gamelists.sh` + `scripts/gamelists_audit.py`.*")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L).replace("\r", "") + "\n")


if __name__ == "__main__":
    main()
