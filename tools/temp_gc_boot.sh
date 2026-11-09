#!/system/bin/sh
# GC de restos de descarga al arrancar. Versionado: scripts/temp_gc_boot.sh (v3).
# Instalado como /data/adb/service.d/72-temp-gc.sh (Magisk lo ejecuta en cada boot).
# OJO: no dejar backups ejecutables dentro de service.d (Magisk los ejecuta tambien).
# - ROMs/TEMP: mueve a TEMP_huerfanos_<fecha> los dirs sin ficheros tocados en 30 min.
# - Download/libtorrent_download: mueve a libtorrent_huerfanos_<fecha> los ficheros sin tocar en 7 dias.
# Nunca borra: siempre mv. Idempotente. Log: /data/local/tmp/temp_gc.log
SD=/storage/FFF9-FF05
TEMP=$SD/ROMs/TEMP
LT=$SD/Download/libtorrent_download
DAY=$(date +%Y%m%d)
DEST_T=$SD/ROMs/TEMP_huerfanos_$DAY
DEST_L=$SD/Download/libtorrent_huerfanos_$DAY
LOG=/data/local/tmp/temp_gc.log

echo "$(date +%F_%T) inicio" >> "$LOG"

# La SD puede tardar en montar tras el arranque: esperar hasta 120 s a que el
# listado de ROMs no este vacio.
i=0
while [ -z "$(ls -A "$SD/ROMs" 2>/dev/null | head -1)" ] && [ "$i" -lt 60 ]; do
  sleep 2
  i=$((i+1))
done
if [ ! -d "$SD/ROMs" ]; then
  echo "$(date +%F_%T) SD no montada tras 120 s; nada que hacer" >> "$LOG"
  exit 0
fi

n=0
if [ -d "$TEMP" ]; then
  for d in "$TEMP"/*; do
    [ -d "$d" ] || continue
    if [ -z "$(find "$d" -type f -mmin -30 2>/dev/null | head -1)" ]; then
      mkdir -p "$DEST_T"
      mv "$d" "$DEST_T"/ 2>/dev/null && n=$((n+1))
    fi
  done
fi
echo "$(date +%F_%T) TEMP: movidos $n dir(es); quedan $(ls -A "$TEMP" 2>/dev/null | wc -l) entrada(s)" >> "$LOG"

m=0
if [ -d "$LT" ]; then
  mkdir -p "$DEST_L"
  find "$LT" -maxdepth 1 -type f -mmin +10080 -exec mv {} "$DEST_L"/ \; 2>/dev/null
  m=$(find "$DEST_L" -maxdepth 1 -type f 2>/dev/null | wc -l)
fi
echo "$(date +%F_%T) torrents: $m fichero(s) en $DEST_L" >> "$LOG"
