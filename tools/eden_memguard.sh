#!/system/bin/sh
# Eden/Yuzu memguard v3: con Eden vivo, mantiene la cache a cero (drop cada 2 s).
# Es el unico metodo que ha evitado el OOM del kernel en el pico de arranque del juego.
# Instalado en /data/adb/service.d/71-eden-memguard.sh (Magisk).
LOG=/data/local/tmp/eden_memguard.log
LAST=0
while true; do
  PID=$(/system/bin/pidof dev.eden.eden_emulator 2>/dev/null)
  if [ -z "$PID" ]; then
    /system/bin/sleep 4
    continue
  fi
  echo 1 > /proc/sys/vm/drop_caches
  NOW=$(/system/bin/date +%s)
  if [ $((NOW-LAST)) -gt 300 ]; then
    LAST=$NOW
    echo "$(/system/bin/date +%F_%T) drop periodico pid=$PID free=$(/system/bin/awk '/MemFree/{print $2}' /proc/meminfo)kB" >> $LOG
  fi
  /system/bin/sleep 2
done
