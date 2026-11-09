import glob, json, os, collections
per = {}; tot = 0; bad = 0; nonhttp = 0; dups = 0; seen = set()
exts = collections.Counter()
for f in sorted(glob.glob("device/catalog_es/*.jsonl")):
    sysn = os.path.basename(f)[: -6]
    n = 0
    for ln in open(f, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln: continue
        try: o = json.loads(ln)
        except Exception: bad += 1; continue
        n += 1; tot += 1
        if o.get("type") != "file": print("NOFILE", sysn, o.get("p"))
        exts[(sysn, (o.get("ext") or "").lower())] += 1
        for u in (o.get("urls") or []):
            uu = u.get("u") or ""
            if not uu.startswith("http"):
                nonhttp += 1; print("NONHTTP", sysn, repr(uu[:50]))
        k = (sysn, o.get("p"))
        if k in seen: dups += 1; print("DUP", k)
        seen.add(k)
    per[sysn] = n
print("jsonl", len(per), "fichas", tot, "bad", bad, "nonhttp", nonhttp, "dups", dups)
print("dreamcast torrent", exts[("dreamcast", ".torrent")], "chd", exts[("dreamcast", ".chd")], "zip", exts[("dreamcast", ".zip")])
c = 0
for ln in open("device/catalog_es/ps2.jsonl", encoding="utf-8"):
    o = json.loads(ln)
    if any("PS2-EU-part" in (u.get("u") or "") for u in (o.get("urls") or [])): c += 1
print("ps2_con_PS2-EU-part", c)
m = json.load(open("device/map_full.json", encoding="utf-8"))
keys = list(m); sysk = [k for k in keys if not k.startswith("#")]
print("map claves", len(keys), "sistemas", len(sysk))
print("sistemas_sin_entrada", [s for s in per if s not in m])
txt = json.dumps(m)
print("extra_libretro", txt.count("%EXTRA_LIBRETRO%"), "android_data", txt.count("Android/data"))
noex = [k for k in sysk if "%EXTRA_LIBRETRO%" not in json.dumps(m[k])]
print("sin_EXTRA_LIBRETRO", len(noex), noex)

def rows(n):
    return [json.loads(l) for l in open("device/catalog_es/" + n, encoding="utf-8") if l.strip()]
sw = rows("switch.jsonl")
print("switch_fichas", len(sw), "hosts", sorted({u["u"].split("/")[2] for o in sw for u in o["urls"]}), "ext", sorted({o["ext"] for o in sw}))
dcr = rows("dreamcast.jsonl")
t = [o for o in dcr if (o["ext"] or "").lower() == ".torrent"]
print("dc_torrent", len(t), "url_acaba_en_.torrent", sum(1 for o in t if any((u["u"] or "").lower().endswith(".torrent") for u in (o["urls"] or []))))
sdb = {}
for ln in open("device/audit_sd_raw/files.tsv", encoding="utf-8", errors="replace"):
    p = ln.rstrip("\n").split("\t")
    if len(p) >= 2 and p[0].isdigit(): sdb[p[1]] = int(p[0])
sws = [(k, v) for k, v in sdb.items() if "/ROMs/switch/" in k]
print("sd_snapshot_1059_switch_n", len(sws), "tamanos", sorted({v for _, v in sws}))
