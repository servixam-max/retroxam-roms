#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""filtro_catalogo.py — refiltra el catálogo por región/idioma.

Criterio (usuario): castellano primero, luego Europa, luego USA; Japón fuera al 100%.
Genera device/catalog_es/<sys>.jsonl a partir de device/catalog_new/<sys>.jsonl
- Descarta toda entrada cuya región sea Japón.
- Entre variantes del mismo juego (misma identity) conserva la mejor:
  ES(3) > EU(2) > US(1) > Asia(1) > sin región(0).
- Si un juego solo existe en Japón -> desaparece del catálogo.
"""
import json, os, re, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan_sin_jp import identity  # noqa: E402
from regiones import classify  # noqa: E402

SRC = "device/catalog_new"
DST = "device/catalog_es"
RANK = {"ES": 4, "ES-fan": 4, "EU": 3, "US": 2, "ASIA": 1, "N/D": 1, "JP": -1}


def region_of(name: str) -> str:
    return classify(name)[1]


JP_TOK = re.compile(r"(?i)japan|jap|jpn|jp|j")


def limpiar_jp(obj):
    """Quita la etiqueta Japan de nombres mixtos (p.ej. \"(USA, Japan)\", \"(JAP)\",
    \"(J, USA)\") tanto del nombre visible (\"n\") como del nombre de fichero
    mostrado por la app (\"p\"). No se tocan \"urls\" ni \"meta\": la descarga sigue
    apuntando al fichero original del repo (las URLs son absolutas de archive.org)."""
    def fix(m):
        toks = [t.strip() for t in m.group(1).split(",")]
        keep = [t for t in toks if t and not JP_TOK.fullmatch(t)]
        if len(keep) == len(toks):
            return m.group(0)  # sin tokens JP: no reformatear el grupo
        return "(" + ", ".join(keep) + ")" if keep else ""

    def limpia(txt):
        out = re.sub(r"\(([^()]*)\)", fix, txt)
        # etiquetas sueltas fuera de parentesis: "Foo (Jap) Rev 1 Japan" -> "Foo Rev 1"
        out = re.sub(r"(?i)(?<![A-Za-z])(?:japan|jpn|jap)(?![A-Za-z])", "", out)
        out = re.sub(r"\(\s*\)", "", out)
        out = re.sub(r"\s{2,}", " ", out)
        out = re.sub(r"\s+([,.)\]])", r"\1", out)
        out = re.sub(r"([(\[])\s+", r"\1", out)
        return re.sub(r"\s{2,}", " ", out).strip(" -,;_")

    def tiene_jp(txt):
        if re.search(r"(?i)\b(?:japan|jap|jpn)\b", txt):
            return True
        for g in re.findall(r"\(([^()]*)\)", txt):
            if any(JP_TOK.fullmatch(t.strip()) for t in g.split(",")):
                return True
        return False

    out = dict(obj)
    for campo in ("n", "p"):
        val = out.get(campo) or ""
        if val and tiene_jp(val):
            nuevo = limpia(val)
            if nuevo:
                out[campo] = nuevo
    return json.dumps(out, ensure_ascii=False)


def main() -> None:
    os.makedirs(DST, exist_ok=True)
    stats = []
    total_in = total_out = total_jp = 0
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".jsonl"):
            continue
        sysname = fn[:-6]
        src = os.path.join(SRC, fn)
        best = {}
        order = []
        jp = 0
        n_in = 0
        for line in open(src, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            n_in += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = obj.get("n") or obj.get("p") or ""
            fname = obj.get("p") or ""
            # Japón se mira en el nombre visible Y en el nombre de fichero: hay
            # entradas gc que solo llevan "(JAP)" en "p".
            if region_of(name) == "JP" or region_of(fname) == "JP":
                jp += 1
                continue
            reg = region_of(name) if RANK.get(region_of(name), 1) >= RANK.get(region_of(fname), 1) else region_of(fname)
            key = identity(name) or name.lower()
            cur = best.get(key)
            if cur is None:
                best[key] = (RANK.get(reg, 1), obj, line)
                order.append(key)
            elif RANK.get(reg, 1) > cur[0]:
                best[key] = (RANK.get(reg, 1), obj, line)
        with open(os.path.join(DST, fn), "w", encoding="utf-8", newline="\n") as out:
            for key in order:
                out.write(limpiar_jp(best[key][1]) + "\n")
        total_in += n_in
        total_out += len(order)
        total_jp += jp
        stats.append((sysname, n_in, len(order), jp))

    print(f"{'sistema':12}{'antes':>7}{'despues':>9}{'japan':>7}")
    for s, a, b, j in sorted(stats, key=lambda x: -x[3]):
        if j or a != b:
            print(f"{s:12}{a:7}{b:9}{j:7}")
    print(f"{'TOTAL':12}{total_in:7}{total_out:9}{total_jp:7}")
    print(f"regiones descartadas por Japón: {total_jp}; sistemas: {len(stats)}")


if __name__ == "__main__":
    main()
