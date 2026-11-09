#!/system/bin/sh
# Eden OOM guard v1 (proyecto AYN-Thor-ESDE).
# Protege Eden del lowmemorykiller SOLO mientras emula (RSS > 2 GB) y lo
# devuelve a cached (200) cuando queda idle, para que no retenga RAM.
# Complementa a 71-eden-memguard.sh (drop_caches cada 2 s).
LOG=/data/local/tmp/eden_memguard.log
while true; do
  PID=$(/system/bin/pidof dev.eden.eden_emulator 2>/dev/null | /system/bin/awk "{print \$1}")
  if [ -n "$PID" ] && [ -r /proc/$PID/status ]; then
    RSS=$(/system/bin/awk "/VmRSS/{print \$2}" /proc/$PID/status 2>/dev/null)
    CUR=$(/system/bin/cat /proc/$PID/oom_score_adj 2>/dev/null)
    TARGET=""
    if [ -n "$RSS" ] && [ "$RSS" -gt 2000000 ] 2>/dev/null; then TARGET=-800; else TARGET=200; fi
    if [ -n "$CUR" ] && [ "$CUR" != "$TARGET" ]; then
      echo $TARGET > /proc/$PID/oom_score_adj
      NEW=$(/system/bin/cat /proc/$PID/oom_score_adj 2>/dev/null)
      echo "$(/system/bin/date +%F_%T) oom_adj pid=$PID rss=${RSS}kB $CUR->$NEW" >> $LOG
    fi
  fi
  /system/bin/sleep 15
done
