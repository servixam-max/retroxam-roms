#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compara gamelists de ES-DE (dispositivo) contra el catalogo refiltrado de RetroXam.
Solo lectura: trabaja con los ficheros ya volcados en device/gl_now y los inventarios TSV.
"""
import json, os, re, unicodedata
from pathlib import Path

ROOT = Path(r"C:/Users/XAM-PC/Proyectos/AYN-Thor-ESDE")
GL = ROOT / "device" / "gl_now"
CAT = ROOT / "device" / "catalog_es"
EMU0 = "/storage/emulated/0/ROMs"
SD = "/storage/FFF9-FF05/ROMs"
QUAR = SD + "/_cuarentena"

SYS_ORDER = ["atomiswave","cps1","cps2","cps3","dreamcast","fbneo","gb","gba","gbc","gc",
             "mame","megacd","megadrive","model2","model3","n3ds","n64","naomi","naomi2",
             "nds","neogeo","nes","openbor","ps2","ps3","psp","psvita","psx","saturn",
             "sega32x","snes","switch","wii","wiiu","xbox","xbox360"]

# --- inventarios de ROMs -----------------------------------------------------
def load_inv(path):
    files = {}
    if not Path(path).exists():
        return files
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n").rstrip("\r")
            if not line:
                continue
            size, _, p = line.partition("\t")
            files[p] = int(size) if size.isdigit() else 0
    return files

INV_EMU0 = load_inv(ROOT / "device" / "roms_inv_emu0.tsv")
INV_SD = load_inv(ROOT / "device" / "roms_inv_sd.tsv")
ALL_FILES = set(INV_EMU0) | set(INV_SD)

# basename -> lista de rutas completas
BY_BASE = {}
for p in ALL_FILES:
    BY_BASE.setdefault(p.rsplit("/", 1)[-1].lower(), []).append(p)

# --- mapeo sistema ES-DE -> carpeta de ROMs (segun es_systems.xml) -----------
def sysdir_map():
    m = {}
    f = ROOT / "device" / "es_systems_custom.xml"
    if f.exists():
        txt = f.read_text(encoding="utf-8", errors="replace")
        for blk in re.findall(r"<system>(.*?)</system>", txt, re.S):
            n = re.search(r"<name>([^<]+)</name>", blk)
            p = re.search(r"<path>([^<]+)</path>", blk)
            if n and p:
                m[n.group(1).strip()] = p.group(1).strip().replace("%ROMPATH%/", "").lstrip("/")
    return m

SYSDIR = sysdir_map()

# --- parseo de gamelists ----------------------------------------------------
GAME_RE = re.compile(r"<game>(.*?)</game>", re.S)
def tag(block, name):
    m = re.search(r"<%s>(.*?)</%s>" % (name, name), block, re.S)
    return m.group(1).strip() if m else ""

JP_RE = re.compile(r"(japan|jap[oó]n|jpn|japanese|\(j\)|\[j\]|\(jp\)|\[jp\]|nihon)", re.I)

def parse_gamelist(path):
    txt = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for blk in GAME_RE.findall(txt):
        out.append({
            "path": tag(blk, "path"),
            "name": tag(blk, "name"),
            "region": tag(blk, "region"),
            "lang": tag(blk, "lang"),
            "md5": tag(blk, "md5"),
        })
    return out

def resolve(p, sysname):
    """Devuelve (estado, ruta_encontrada, raiz) para un <path> de gamelist."""
    rel = p
    for pref in ("./", ".\\"):
        if rel.startswith(pref):
            rel = rel[len(pref):]
    rel = rel.lstrip("/")
    if not rel:
        return ("vacio", None, None)
    sd_dir = SYSDIR.get(sysname, sysname)
    cands = []
    if p.startswith("/"):
        cands.append(("abs", p))
    else:
        if sd_dir != sysname:
            cands.append((EMU0, "%s/%s/%s" % (EMU0, sd_dir, rel)))
            cands.append((SD, "%s/%s/%s" % (SD, sd_dir, rel)))
        cands.append((EMU0, "%s/%s/%s" % (EMU0, sysname, rel)))
        cands.append((SD, "%s/%s/%s" % (SD, sysname, rel)))
    for _, c in cands:
        c = c.replace("//", "/")
        if c in ALL_FILES:
            root = "emu0" if c.startswith(EMU0) else ("sd" if c.startswith(SD) else "abs")
            return ("ok", c, root)
    # no existe: buscar por nombre de fichero en toda la SD
    base = rel.rsplit("/", 1)[-1].lower()
    hits = BY_BASE.get(base, [])
    if hits:
        q = [h for h in hits if "/_cuarentena/" in h]
        if q:
            return ("cuarentena", q[0], "cuarentena")
        return ("otra_ruta", hits[0], "otro")
    return ("roto", None, None)

# --- catalogo ---------------------------------------------------------------
def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()

catalog = {}
for sysname in SYS_ORDER:
    f = CAT / (sysname + ".jsonl")
    rows = []
    if f.exists():
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    catalog[sysname] = rows

# --- comparacion ------------------------------------------------------------
report = {
    "generado": None,
    "fuentes": {
        "gamelists": "/storage/emulated/0/ES-DE/gamelists/<sistema>/gamelist.xml (copia local: device/gl_now/)",
        "nota_ruta": "es_settings.xml NO define ROMDirectory -> %ROMPATH% por defecto /storage/emulated/0/ROMs",
        "catalogo": "device/catalog_es/<sistema>.jsonl",
        "inventarios": ["device/roms_inv_emu0.tsv", "device/roms_inv_sd.tsv"],
    },
    "totales": {},
    "sistemas": {},
    "menciones_japon": {},
    "solo_catalogo": [],
    "solo_gamelist": [],
}

gl_systems = sorted([d.name for d in GL.iterdir() if d.is_dir()]) if GL.exists() else []
cat_systems = sorted([p.stem for p in CAT.glob("*.jsonl")])
report["solo_catalogo"] = sorted(set(cat_systems) - set(gl_systems))
report["solo_gamelist"] = sorted(set(gl_systems) - set(cat_systems))
report["sistemas_gamelist"] = gl_systems
report["sistemas_catalogo"] = cat_systems

tot_games = 0
tot_cat = 0
tot_cat_orphan = 0
tot_gl_orphan = 0
tot_broken = 0
tot_jp = 0
all_gl_paths = 0

for sysname in gl_systems:
    f = GL / sysname / "gamelist.xml"
    games = parse_gamelist(f) if f.exists() else []
    tot_games += len(games)
    all_gl_paths += len(games)
    rows = catalog.get(sysname, [])
    tot_cat += len(rows)

    cat_by_base = {}
    cat_by_name = {}
    for r in rows:
        p = r.get("p") or ""
        b = p.rsplit("/", 1)[-1].lower()
        cat_by_base.setdefault(b, []).append(r)
        nm = norm((r.get("meta") or {}).get("name") or r.get("n") or "")
        if nm:
            cat_by_name.setdefault(nm, []).append(r)

    gl_by_base = {}
    for g in games:
        b = g["path"].rsplit("/", 1)[-1].lower()
        gl_by_base.setdefault(b, []).append(g)

    # catalogo sin gamelist (por nombre de fichero; si no, por nombre visible)
    cat_orphans, cat_orphans_nameonly = [], []
    for r in rows:
        p = (r.get("p") or "")
        b = p.rsplit("/", 1)[-1].lower()
        if b in gl_by_base:
            continue
        nm = norm((r.get("meta") or {}).get("name") or r.get("n") or "")
        if nm and nm in {norm(g["name"]) for g in games}:
            cat_orphans_nameonly.append({"p": p, "n": r.get("n"), "match_por": "name"})
            continue
        cat_orphans.append({
            "p": p,
            "n": r.get("n"),
            "name": (r.get("meta") or {}).get("name"),
            "urls": [u.get("u") for u in (r.get("urls") or [])][:2],
            "en_disco": bool(BY_BASE.get(b)),
        })

    # gamelist sin catalogo
    gl_orphans = []
    broken = []
    jp = []
    for g in games:
        b = g["path"].rsplit("/", 1)[-1].lower()
        if b not in cat_by_base:
            if norm(g["name"]) not in cat_by_name:
                gl_orphans.append({"name": g["name"], "path": g["path"], "region": g["region"]})
        est, found, root = resolve(g["path"], sysname)
        if est != "ok":
            broken.append({"name": g["name"], "path": g["path"], "estado": est,
                           "encontrado_en": found, "region": g["region"]})
        for field in ("name", "path"):
            if JP_RE.search(g[field] or ""):
                jp.append({"campo": field, "valor": g[field], "name": g["name"], "path": g["path"]})
                break

    tot_cat_orphan += len(cat_orphans)
    tot_gl_orphan += len(gl_orphans)
    tot_broken += len(broken)
    tot_jp += len(jp)

    report["sistemas"][sysname] = {
        "carpeta_roms": SYSDIR.get(sysname, sysname),
        "gamelist_games": len(games),
        "catalogo_entradas": len(rows),
        "catalogo_sin_gamelist": len(cat_orphans),
        "catalogo_sin_gamelist_solo_por_nombre": len(cat_orphans_nameonly),
        "gamelist_sin_catalogo": len(gl_orphans),
        "rutas_rotas": len(broken),
        "menciones_japon": len(jp),
        "detalle": {
            "catalogo_sin_gamelist": cat_orphans,
            "gamelist_sin_catalogo": gl_orphans,
            "rutas_rotas": broken,
            "menciones_japon": jp,
        },
    }
    if jp:
        report["menciones_japon"][sysname] = jp

report["totales"] = {
    "gamelists": len(gl_systems),
    "total_game": tot_games,
    "catalogo_entradas": tot_cat,
    "catalogo_sin_gamelist": tot_cat_orphan,
    "gamelist_sin_catalogo": tot_gl_orphan,
    "rutas_rotas": tot_broken,
    "menciones_japon": tot_jp,
    "rutas_totales_analizadas": all_gl_paths,
}

out = ROOT / "device" / "gamelist_vs_catalog.json"
with open(out, "w", encoding="utf-8") as fh:
    json.dump(report, fh, ensure_ascii=False, indent=1)
print(json.dumps(report["totales"], ensure_ascii=False, indent=1))
print("solo_catalogo:", report["solo_catalogo"], "solo_gamelist:", report["solo_gamelist"])
print("escrito:", out)
