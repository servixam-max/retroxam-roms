import argparse, csv, json, os, shutil, sys, time

TSV = "device/logs/title_subst.tsv"

def human(n):
    if n >= 1024**3:
        return "%.2f GB" % (n / 1024**3)
    return "%.0f MB" % (n / 1024**2)

def main():
    ap = argparse.ArgumentParser(description="Aplica sustituciones de URL del catalogo desde title_subst.tsv")
    ap.add_argument("--sistema", default="ps2")
    ap.add_argument("--catalogo", default="")
    ap.add_argument("--bakdir", default="device/bak_catalog")
    ap.add_argument("--append", action="store_true", help="anade la URL nueva como alternativa en vez de sustituir urls[0]")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    ruta = args.catalogo or ("device/catalog_es/%s.jsonl" % args.sistema)
    with open(TSV, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r["sistema"] == args.sistema]
    with open(ruta, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    fichas = {}
    for i, l in enumerate(lineas):
        o = json.loads(l)
        fichas.setdefault(o["n"], []).append((i, o))
    ok, missing, dups, ya = [], [], [], []
    for r in rows:
        m = fichas.get(r["ficha"], [])
        if len(m) != 1:
            (dups if m else missing).append(r["ficha"])
            continue
        i, o = m[0]
        nueva = r["nueva_url"]
        nb = int(r["size"])
        urls = o.get("urls") or []
        if urls and urls[0].get("u") == nueva:
            ya.append(r["ficha"])
            continue
        vieja = urls[0].get("u") if urls else ""
        ok.append((i, o, r, nb, vieja))
    print("sistema=%s filas=%d aplicables=%d ya_aplicadas=%d sin_match=%d duplicadas=%d" % (args.sistema, len(rows), len(ok), len(ya), len(missing), len(dups)))
    for x in missing:
        print("  SIN MATCH:", x)
    for x in dups:
        print("  DUPLICADA:", x)
    if not args.aplicar:
        for i, o, r, nb, vieja in ok:
            print("  DRY %s -> %s (%s)" % (r["ficha"], r["fichero_nuevo"], human(nb)))
        print("dry-run: no se ha escrito nada (usa --aplicar)")
        return 0
    if not ok:
        print("nada que aplicar")
        return 0
    os.makedirs(args.bakdir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(args.bakdir, os.path.basename(ruta) + ".bak-" + ts)
    shutil.copy2(ruta, bak)
    for i, o, r, nb, vieja in ok:
        if args.append:
            o["urls"].append({"u": r["nueva_url"], "size": human(nb), "size_bytes": nb})
        else:
            o["urls"][0] = {"u": r["nueva_url"], "size": human(nb), "size_bytes": nb}
            if "size_bytes" in o: o["size_bytes"] = nb
            if "size" in o: o["size"] = human(nb)
        lineas[i] = json.dumps(o, ensure_ascii=False)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    os.replace(tmp, ruta)
    log = os.path.join("device/logs", "aplicar_sustituciones_%s_%s.tsv" % (args.sistema, ts))
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        f.write("ficha\turl_vieja\turl_nueva\n")
        for i, o, r, nb, vieja in ok:
            f.write("%s\t%s\t%s\n" % (r["ficha"], vieja, r["nueva_url"]))
    print("aplicadas=%d backup=%s log=%s" % (len(ok), bak, log))
    return 0

if __name__ == "__main__":
    sys.exit(main())
