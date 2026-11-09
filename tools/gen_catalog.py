#!/usr/bin/env python3
"""gen_catalog.py — genera el catálogo corregido (gjsonl) a partir del original + auditoría.

Reglas aplicadas (mecánicas y verificables):
  R1. Fuera demos / betas / protos / samples / taikenban / kiosk / trial.
      Patrón estricto: paréntesis de No-Intro, p.ej. "(Demo)", "(Beta) (2001-05-21)".
      No toca títulos con la palabra dentro del nombre ("Test Drive Le Mans").
  R2. Fuera entradas sin URL descargable.
  R3. Deduplicado intra-sistema por nombre normalizado (quita la 2ª copia exacta).
  R4. Informe de cobertura de idioma (es/en/jp) por sistema.
  R5. Aplica la auditoría de idioma de device/audit_lang/review/*_review.json:
      - etiqueta (marcar/etiquetar/reclasificar ... es|en|jp) con confianza alta y
        nombre resoluble -> meta.lang = código (prioridad es > en > jp);
      - retirada (eliminar/excluir) con confianza alta -> fuera del catálogo;
      - NO se aplican las que exigen sustituir el fichero por otra variante, las de
        confianza media/baja ni las de nombre no resoluble: se cuentan como pendientes.
      Cada cambio aplicado queda trazado en device/catalog_audit_applied.jsonl.

Uso:
  python scripts/gen_catalog.py            # genera device/catalog_new + informe
  python scripts/gen_catalog.py --report   # solo informe, no escribe
"""
import json, os, re, sys, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "device", "catalog_orig")
DST = os.path.join(ROOT, "device", "catalog_new")
REVIEW = os.path.join(ROOT, "device", "audit_lang", "review")
AUDIT_OUT = os.path.join(ROOT, "device", "catalog_audit_applied.jsonl")

DEMO = re.compile(
    r"\((?:demo|beta|taikenban|sample|kiosk|proto|prototype|trial|preview|"
    r"location\s*test|test\s*program)\b",
    re.I,
)

# --- clasificación de las recomendaciones de la auditoría (texto -> acción) ---
A_DROP = re.compile(r"\b(eliminar|excluir|quitar del cat|no debe estar)\b", re.I)
A_REPL = re.compile(
    r"^\s*(sustituir|reemplazar|buscar|localizar|preferir|priorizar|a[nñ]adir|usar|elegir|"
    r"cambiar (el|la|este|esta) (fichero|dump|release|item|entrada)|mover a extras)", re.I)
A_TAG = re.compile(
    r"\b(marcar|marcarla|marcarlo|etiquetar|etiquetarla|asignar|re-?etiquetar|reclasificar|"
    r"poner|dejar)\b|cambiar etiqueta a", re.I)
A_NOES = re.compile(r"no marcar (es|ES)|mantener (el )?ingl[eé]s|mantener EN|mantener en ingl", re.I)


def audit_action(rec):
    """Devuelve (accion, codigo). accion: drop|lang|replace|noop|unknown."""
    if A_DROP.search(rec):
        return "drop", None
    if A_NOES.search(rec):
        return "lang", "en"
    if A_REPL.search(rec):
        return "replace", None
    if A_TAG.search(rec):
        if re.search(r"cambiar etiqueta a\s+en", rec, re.I):
            return "lang", "en"
        if re.search(r"\b(ES|castellano|espa[nñ]ol)\b", rec):
            return "lang", "es"
        if re.search(r"\b(EN|ingl[eé]s)\b", rec):
            return "lang", "en"
        if re.search(r"\b(JP|japon[eé]s)\b", rec):
            return "lang", "jp"
        if re.search(r"MULTI", rec):
            return "lang", "multi"
    if re.search(r"\bsin cambios\b", rec, re.I):
        return "noop", None
    return "unknown", None


def nkey(name):
    n = re.sub(r"\.(zip|7z|chd|iso|cso|rvz|gdi|cia|xci|nsp|vpk|torrent|bin|cue|pbp|gcm|dol|wbfs)$",
               "", name, flags=re.I)
    n = re.sub(r"[\(\[].*?[\)\]]", "", n)
    return re.sub(r"[^a-z0-9]+", "", n.lower())


def audit_load():
    """Carga las correcciones aplicables (estado != rechazada) de los *_review.json."""
    out = []
    for p in sorted(glob.glob(os.path.join(REVIEW, "*_review.json"))):
        d = json.load(open(p, encoding="utf-8"))
        for x in d.get("correcciones") or []:
            if x.get("estado") == "rechazada":
                continue
            rec = x.get("recomendacion") or ""
            acc, code = audit_action(rec)
            out.append({"sistema": x.get("sistema"), "juego": x.get("juego"),
                        "recomendacion": rec,
                        "actual": x.get("actual") or "", "accion": acc, "lang": code,
                        "confianza": (x.get("confianza") or "").lower(),
                        "fuente_json": os.path.basename(p)})
    return out


def norm(name: str) -> str:
    n = re.sub(r"\([^)]*\)", "", name)          # fuera paréntesis de región/idioma
    n = re.sub(r"[^a-z0-9]+", "", n.lower())
    return n


def load():
    per = {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".jsonl"):
            continue
        s = f[:-6]
        rows = []
        with open(os.path.join(SRC, f), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        per[s] = rows
    return per


def apply_audit(rows, overrides, stats, trace):
    """Aplica overrides (ya filtrados por sistema) sobre `rows` en memoria."""
    by_name = {o.get("n", ""): o for o in rows}
    by_key = collections.defaultdict(list)
    for o in rows:
        by_key[nkey(o.get("n", ""))].append(o)

    def resolve(x):
        n, a = x["juego"], x["actual"]
        if n in by_name:
            return by_name[n], "nombre_exacto"
        if a and a in by_name:
            return by_name[a], "actual_exacto"
        k = nkey(n)
        if len(by_key.get(k, [])) == 1:
            return by_key[k][0], "norm_unico"
        return None, ("norm_ambiguo" if by_key.get(k) else "sin_match")

    for x in overrides:
        if x["accion"] in ("replace", "noop", "unknown"):
            stats["_" + x["accion"]] += 1
            continue
        o, how = resolve(x)
        if o is None:
            stats["sin_match"] += 1
            trace.append({**x, "resultado": how})
            continue
        if x["confianza"] != "alta":
            stats["omitida_confianza"] += 1
            trace.append({**x, "resultado": "confianza_" + (x["confianza"] or "vacia")})
            continue
        if x["accion"] == "drop":
            o["_drop_audit"] = True
            stats["drop"] += 1
            trace.append({**x, "resultado": "drop", "match": how, "nombre": o.get("n")})
        else:
            before = str((o.get("meta") or {}).get("lang") or "")
            have = [t for t in before.split(",") if t]
            if x["lang"] in ("en", "jp") and "es" in have:
                stats["omitida_conflicto"] += 1
                trace.append({**x, "resultado": "conflicto_es", "nombre": o.get("n"),
                              "lang_antes": before})
                continue
            o.setdefault("meta", {})["lang"] = x["lang"]
            stats["lang"] += 1
            trace.append({**x, "resultado": "lang", "match": how, "nombre": o.get("n"),
                          "lang_antes": before, "lang_despues": x["lang"]})


def main():
    only_report = "--report" in sys.argv
    per = load()
    overrides = audit_load()
    by_sys = collections.defaultdict(list)
    for x in overrides:
        by_sys[x["sistema"]].append(x)
    os.makedirs(DST, exist_ok=True)
    report = {"sistemas": {}, "total_antes": 0, "total_despues": 0,
              "quitados_demo": 0, "quitados_sin_url": 0, "quitados_duplicado": 0,
              "quitados_auditoria": 0,
              "es": 0, "en": 0, "jp": 0, "multi": 0, "sin_idioma": 0,
              "auditoria": {"correcciones": len(overrides)}}
    trace = []
    for s, rows in per.items():
        stats = collections.Counter({"lang": 0, "drop": 0, "omitida_confianza": 0,
                                     "omitida_conflicto": 0,
                                     "sin_match": 0, "_replace": 0, "_noop": 0,
                                     "_unknown": 0})
        apply_audit(rows, by_sys.get(s, []), stats, trace)
        keep, seen = [], set()
        st = collections.Counter()
        for o in rows:
            n = o.get("n", "")
            if o.get("_drop_audit"):
                st["auditoria"] += 1
                o.pop("_drop_audit", None)
                continue
            if DEMO.search(n):
                st["demo"] += 1
                continue
            urls = o.get("urls") or []
            if not urls or not any(u.get("u") for u in urls):
                st["sin_url"] += 1
                continue
            k = norm(n)
            if k in seen:
                st["dup"] += 1
                continue
            seen.add(k)
            keep.append(o)
            lang = str((o.get("meta") or {}).get("lang") or "")
            ls = [x for x in lang.split(",") if x]
            if "es" in ls:
                st["es"] += 1
            elif "en" in ls:
                st["en"] += 1
            elif "jp" in ls:
                st["jp"] += 1
            elif "multi" in ls:
                st["multi"] += 1
            else:
                st["sin_idioma"] += 1
        report["sistemas"][s] = {"antes": len(rows), "despues": len(keep),
                                 "demo": st["demo"], "sin_url": st["sin_url"],
                                 "dup": st["dup"], "auditoria": st["auditoria"],
                                 "es": st["es"], "en": st["en"],
                                 "jp": st["jp"], "multi": st["multi"]}
        report["total_antes"] += len(rows)
        report["total_despues"] += len(keep)
        report["quitados_auditoria"] += st["auditoria"]
        for kk, rk in (("demo", "quitados_demo"), ("sin_url", "quitados_sin_url"),
                       ("dup", "quitados_duplicado"), ("es", "es"), ("en", "en"),
                       ("jp", "jp"), ("multi", "multi"), ("sin_idioma", "sin_idioma")):
            report[rk] += st[kk]
        if not only_report:
            with open(os.path.join(DST, s + ".jsonl"), "w", encoding="utf-8") as fh:
                for o in keep:
                    fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    aud = report["auditoria"]
    aud["aplicadas_lang"] = sum(1 for t in trace if t.get("resultado") == "lang")
    aud["aplicadas_drop"] = sum(1 for t in trace if t.get("resultado") == "drop")
    aud["omitidas_confianza"] = sum(1 for t in trace
                                    if str(t.get("resultado", "")).startswith("confianza_"))
    aud["requieren_sustitucion"] = sum(1 for x in overrides if x["accion"] == "replace")
    aud["noop"] = sum(1 for x in overrides if x["accion"] == "noop")
    aud["desconocidas"] = sum(1 for x in overrides if x["accion"] == "unknown")
    aud["omitidas_conflicto_es"] = sum(1 for t in trace if t.get("resultado") == "conflicto_es")
    aud["sin_match_aplicables"] = sum(1 for t in trace
                                      if t.get("resultado") in ("sin_match", "norm_ambiguo"))
    with open(os.path.join(ROOT, "device", "catalog_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    if not only_report:
        with open(AUDIT_OUT, "w", encoding="utf-8") as fh:
            for t in trace:
                fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "sistemas"}, ensure_ascii=False, indent=1))
    if not only_report:
        print("escrito en", DST)


if __name__ == "__main__":
    main()
