# -*- coding: utf-8 -*-
"""Recolector de ROMs/TEMP del AYN Thor.

Mueve (nunca borra) los directorios de descarga de la app que ya no tienen
proceso escribiendo en ellos a ROMs/TEMP_huerfanos_<fecha>/.

Uso:  python scripts/temp_gc.py [minutos_de_gracia] [--dry-run]
"""
import subprocess, sys, datetime, shlex

ADB = r"C:/Users/XAM-PC/AndroidTools/sdk/platform-tools/adb.exe"
TEMP = "/storage/FFF9-FF05/ROMs/TEMP"
GRACE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 30
DRY = "--dry-run" in sys.argv
DEST = "/storage/FFF9-FF05/ROMs/TEMP_huerfanos_" + datetime.date.today().strftime("%Y%m%d")


def sh(cmd):
    p = subprocess.run([ADB, "shell", cmd], capture_output=True, text=True, timeout=180)
    return p.stdout.replace("\r", "").strip()


def main():
    app_pid = sh("pidof com.arley4d.bypassarley4d")
    print(f"app pid: {app_pid or '(no corre)'}  gracia: {GRACE} min  destino: {DEST}")
    listing = sh(f'find {TEMP} -mindepth 1 -maxdepth 1 -type d -printf "%f\n" 2>/dev/null')
    dirs = [d for d in listing.splitlines() if d.strip()]
    if not dirs:
        print("TEMP vacío; nada que recoger.")
        return
    total = 0
    moved = []
    for d in dirs:
        size = sh(f'du -sk {TEMP}/{d} 2>/dev/null | cut -f1')
        size = int(size) if size.isdigit() else 0
        files = sh(f'find {TEMP}/{d} -type f | wc -l')
        recent = sh(f'find {TEMP}/{d} -type f -newermt "-{GRACE} minutes" | head -1')
        if recent:
            print(f"  SKIP  {d}  {size/1024:.1f} MB  (fichero tocado en los últimos {GRACE} min)")
            continue
        print(f"  MOVE  {d}  {size/1024:.1f} MB  ficheros={files}")
        total += size
        moved.append(d)
    print(f"candidatos: {len(moved)}  espacio a recuperar: {total/1024:.1f} MB")
    if DRY or not moved:
        return
    sh(f"mkdir -p {DEST}")
    for d in moved:
        r = sh(f"mv {TEMP}/{d} {DEST}/{d} && echo ok")
        print(f"  mv {d}: {r or 'FALLO'}")
    print("TEMP ahora:", sh(f"du -sh {TEMP} 2>/dev/null"))
    print("huerfanos ahora:", sh(f"du -sh {DEST} 2>/dev/null"))


if __name__ == "__main__":
    main()
