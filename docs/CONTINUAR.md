# AYN Thor + ES-DE + RetroXam — guía de continuación

Última actualización: **2026-11-09 09:30** (hora local del PC).
Este documento es el punto de entrada para cualquier IA o persona que retome el proyecto.
Los detalles cronológicos están en `ESTADO.md`; la lista de trabajo, en `TAREAS.md`.

---

## 1. Qué es el proyecto

Convertir una **AYN Thor** (Android 13, 8 GB RAM, Snapdragon) en una consola portátil completa:

- **ES-DE** como frontend (36 sistemas configurados, media en la microSD).
- **Catálogo propio** de 5.496 fichas (36 ficheros JSONL) que la app **RetroXam** usa para descargar juegos (torrent / HTTP / MediaFire / 1fichier).
- **Emuladores por sistema** mapeados en `es_systems.xml` (RetroArch con cores, AetherSX2, Eden, Dolphin, PPSSPP, DuckStation…).

El repositorio donde estás leyendo esto contiene el **catálogo publicado** (los 36 `.jsonl` en la raíz) y, desde ahora, la **documentación y las herramientas** en `docs/` y `tools/`.

---

## 2. Dónde vive cada cosa

| Cosa | Ruta |
|---|---|
| Catálogo publicado (este repo) | `servixam-max/retroxam-roms`, rama `main` |
| Proyecto local en el PC | `C:\Users\XAM-PC\Proyectos\AYN-Thor-ESDE` |
| Bitácora completa | `docs/ESTADO.md` (+ `docs/ESTADO-LOG.html`) |
| Backlog | `docs/TAREAS.md` (+ `docs/TAREAS-LOG.html`) |
| Catálogo de trabajo (local) | `device/catalog_es/*.jsonl` (36, 5.496 fichas) |
| ADB | `C:\Users\XAM-PC\AndroidTools\sdk\platform-tools\adb.exe` |
| Serial ADB (Wi-Fi) | `adb-9205e6b1-5oHeeV._adb-tls-connect._tcp` |
| SD (exFAT, 477 GB) | `/storage/FFF9-FF05` — ROMs en `/storage/FFF9-FF05/ROMs/<sistema>/` |
| ES-DE (datos) | `/storage/emulated/0/ES-DE/` (gamelists, downloaded_media, settings) |
| ES-DE (config app) | `/storage/emulated/0/Android/data/org.es_de.frontend/files/` |
| `es_systems.xml` | `/storage/emulated/0/ES-DE/custom_systems/es_systems.xml` |
| Copias del XML | `es_systems.xml.bak_*` junto al original |

Espacio libre en la SD: **418 GB** de 477 GB (a fecha de este documento).

---

## 3. Acceso al dispositivo

```bash
ADB="C:/Users/XAM-PC/AndroidTools/sdk/platform-tools/adb.exe"
S="adb-9205e6b1-5oHeeV._adb-tls-connect._tcp"
"$ADB" connect "$S"          # ADB por Wi-Fi, ya emparejado
"$ADB" -s "$S" shell ...
```

El equipo tiene **Magisk** (root con `su -c`). Paquetes relevantes:

- ES-DE: `org.es_de.frontend/.MainActivity`
- RetroArch: `com.retroarch.aarch64`
- AetherSX2 (PS2): `xyz.aethersx2.android/.EmulationActivity`
- Eden (Switch): `dev.eden.eden_emulator`
- App RetroXam: instalada como APK propia (ver `device/apk/` en el proyecto local).

---

## 4. Reglas de trabajo (importantes)

1. **Idioma**: todo el trabajo y la documentación en español.
2. **No cerrar tareas sin evidencia de dispositivo**: PID vivo, línea de log, captura con contenido real. «La lista se ve bien» no es evidencia.
3. **Un solo piloto a la vez**: si hay un proceso interactivo en marcha, no se toca ADB con inputs. Antes de tomar el testigo, mira el log del frontend y las capturas recientes:
   ```bash
   adb shell 'tail -5 /storage/emulated/0/ES-DE/logs/es_log.txt'
   ls -lt scratch/*.png | head
   ```
4. **Los scripts de la app no son repo git**: el proyecto local no tiene `.git`; el único repositorio es éste.
5. **Nunca volcar credenciales** de ScreenScraper en logs o capturas (se detectó y se corrigió una fuga en `ss_probe.py`).

---

## 5. Trampas ya resueltas (no repetir estos errores)

### ES-DE

- **Lista de PSX con «carpetas»**: si dentro de `ROMs/psx/` existen directorios como `SwanStation/` o `Beetle PSX HW/` (datos del core), ES-DE los muestra como entradas. Los datos de RetroArch van fuera de la carpeta de ROMs. *(T-55)*
- **Añadir sistemas propios**: sólo por `custom_systems/es_systems.xml`; `es_find_rules.xml` define cómo se localizan los emuladores.
- **Lanzar con parámetros**: para PS2 el sistema usa `%EXTRA_bootPath%`; con `%ROM%` a secas AetherSX2 volvía al menú. *(T-57)*
- **Rutas de media**: `downloaded_media` está en la SD y se enlaza/bindea a la ruta que espera ES-DE (`/storage/emulated/0/ES-DE/downloaded_media`).
- **Arranque**: `settings/es_settings.xml` controla `StartupSystem` / `StartupView`. Para volver limpio: `am force-stop org.es_de.frontend && am start -n org.es_de.frontend/.MainActivity`.

### Emuladores

- **Switch / Eden**: con **Turnip** (v25, v27) Eden aborta en `Vulkan::vk::Device::CreateGraphicsPipeline` (`libyuzu-android.so`, SIGABRT). Con el **driver Vulkan del sistema** (`Qualcomm Adreno 512.676.53`) arranca. Criterio fiable de driver en log: `logcat -d | grep 'Report: Driver'` — la línea `loading default driver: vulkan.adreno.so` aparece siempre y no dice nada. *(T-56, T-58)*
- **Memoria (8 GB)**: Eden con un `.xci` consume 4–5 GB. Medidas aplicadas:
  - `71-eden-memguard.sh`: limpieza previa (force-stop de apps + `am kill-all` + `drop_caches`), sube el arranque de ~3,1 GB a ~4,67 GB libres.
  - `72-eden-oomguard.sh`: fija `oom_score_adj=-800` mientras `VmRSS > 2 GB`, lo devuelve a 200 al quedar idle.
  - Resultado medido: sesión de 30XX **47 min** sin kill de lmkd. Aun así, en sesiones largas el guest sigue siendo el límite. *(T-59)*
  - Diagnóstico: `dumpsys activity exit-info dev.eden.eden_emulator` distingue `APP CRASH(NATIVE)` de `LOW_MEMORY`.
- **Turnip manual**: copiar el `.zip`/`.so` a `gpu_drivers`, `chown u0_a173:ext_data_rw`, `chmod 660`, `chcon u:object_r:media_rw_data_file:s0:c173,c256,c512,c768`, seleccionar en el gestor. Volver al driver del sistema = radio «Sistema» con `driver_path=` vacío.

### Scripts de arranque (Magisk)

- `/data/adb/service.d/` ejecuta **todo** fichero ejecutable al arrancar, sin importar el nombre. Los desactivados se renombran a `*.DISABLED`.
- Ahí viven: `10-esde-media-sd.sh` (bind de media), `50-psvita-guard.sh`, `60-ps3-guard.sh`, `70-switch-guard.sh`, `71-eden-memguard.sh`, `72-eden-oomguard.sh`, `72-temp-gc.sh`, `73-ra-watch.sh`, `82-tico-import.sh`, `98-coveroverlay-watchdog.sh`.
- Un script de arranque no puede usar `du` ni nada que dependa de `/storage` montado; se ejecuta demasiado pronto.

### Catálogo y descargas

- El catálogo son **36 JSONL**, uno por sistema, 5.496 líneas. Validación local:
  ```bash
  python scripts/cat_count.py          # 5.496 fichas / 36 ficheros
  python scripts/verify_catalog.py     # bad 0 nonhttp 0 dups 0, dc_torrent 105/105
  python scripts/test_regiones.py      # 13 tests de etiquetado de región
  ```
- **Stubs `.torrent`**: muchas fichas apuntan a `.torrent` que en realidad son texto con una URL (MediaFire/1fichier). `tools/torrent_stub_fix.py --dry-run` audita la contradicción. *(T-52/T-40)*
- **Fichas restringidas**: ~885 fichas exigen login (577) o pasan por MediaFire (909); hay que decidir entre login en el descargador o marcarlas `meta.restringido` para no ofrecerlas. *(T-40)*
- **Torrent real verificado**: Debian, 792.723.456 B, sha256 oficial, 2 MB/s, 37 conexiones; la descarga **sobrevive a `am force-stop`** y reanuda con el parcial. *(T-33)*
- **ScreenScraper**: el scraping funciona desde la UI de ES-DE (ESCRAPEAR → ScreenScraper). Cupo medido `requeststoday 2058/20000`, `requestskotoday 1070/2000`; el cupo KO agotado **no** bloquea. El scrapeo de PSX procesó 16/16 y dejó la gamelist en 196 `<game>` / 195 `<desc>`. *(T-49)*

---

## 6. Estado real (2026-11-09)

Funciona y está verificado en dispositivo:

- ADB por Wi-Fi, root, scripts de arranque activos.
- ES-DE con 36 sistemas, media en la SD, scraping operativo.
- **PS1**: lista limpia y arranque real desde el frontend (varios títulos).
- **PS2**: arreglado con `%EXTRA_bootPath%`; 007 arranca desde ES-DE.
- **Switch**: 30XX arranca con el driver del sistema; sesión de 47 min sin kills.
- **Descargas**: torrent real completo y verificado por hash; flujo de la app y reanudación tras force-stop.

Abierto (ver `TAREAS.md` para el detalle y los comandos):

- **T-18**: 556 zips arcade siguen siendo stubs; sólo 12 juegos reales. Requiere descargarlos con la app.
- **T-09 / T-10 / T-11**: descargas desde la app y botón «Segundo plano» tras reinstalar.
- **T-23**: el repo no sirve semillas para Switch, sirve enlaces de MediaFire.
- **T-27**: hueco entre gamelists y catálogo (tabla en la sección 7).
- **T-28**: cuarentenar las versiones japonesas que queden en la SD.
- **T-31**: render de Dreamcast.
- **Sustitutos PS2**: 41 fichas con sustituto USA probado, pendiente de aplicar:
  ```bash
  python scripts/aplicar_sustituciones.py --sistema ps2 --aplicar
  ```
- **Relleno de la SD**: quedan ~418 GB libres.

---

## 7. Hueco gamelist ↔ catálogo (medido 2026-11-09)

ES-DE sólo lista lo que existe en la SD; el catálogo ofrece todo lo descargable. Diferencias por sistema (`gamelist − catálogo`):

| Sistema | Gamelist | Catálogo | Dif |
|---|---:|---:|---:|
| mame | 200 | 992 | −792 |
| nes | 142 | 336 | −194 |
| nds | 142 | 306 | −164 |
| fbneo | 150 | 303 | −153 |
| gba | 140 | 264 | −124 |
| ps3 | 97 | 200 | −103 |
| gc | 150 | 242 | −92 |
| snes | 125 | 213 | −88 |
| ps2 | 189 | 239 | −50 |
| psp | 144 | 194 | −50 |
| n64 | 140 | 185 | −45 |
| psx | 195 | 226 | −31 |
| gb | 133 | 164 | −31 |
| megadrive | 131 | 161 | −30 |
| gbc | 144 | 170 | −26 |
| xbox | 148 | 174 | −26 |
| saturn | 104 | 118 | −14 |
| dreamcast | 115 | 128 | −13 |
| n3ds | 141 | 153 | −12 |
| sega32x | 26 | 34 | −8 |
| openbor | 150 | 152 | −2 |
| naomi | 83 | 84 | −1 |
| **cps1** | 37 | 36 | **+1** |
| **psvita** | 12 | 9 | **+3** |
| **megacd** | 77 | 72 | **+5** |
| resto (0) | — | — | 0 |

Total: **3.456 entradas en gamelists / 5.496 fichas**. Los positivos (cps1, psvita, megacd) son entradas de gamelist sin ficha en el catálogo y hay que revisarlos uno a uno; los negativos son juegos ofrecidos pero aún no descargados.

---

## 8. Herramientas incluidas en `tools/`

| Script | Para qué |
|---|---|
| `cat_count.py` | cuenta fichas y ficheros del catálogo |
| `verify_catalog.py` | valida URLs, duplicados, coherencia torrent/DC |
| `test_regiones.py` | 13 tests del etiquetado de región (ES/JP/USA) |
| `filtro_catalogo.py` | reglas de región y limpieza de nombres |
| `gen_catalog.py` | genera los JSONL desde el inventario de la SD |
| `gamelists_audit.py` / `gl_vs_catalog.py` | comparan gamelists de ES-DE con el catálogo |
| `aplicar_sustituciones.py` | aplica sustitutos USA sobre fichas EU/JP |
| `temp_gc.py`, `temp_gc_boot.sh` | recogida de temporales y parciales huérfanos |
| `eden_memguard.sh`, `eden_oomguard.sh` | guardas de memoria para Eden (van en `service.d`) |
| `torrent_stub_fix.py` | audita/reescribe stubs `.torrent` que son URLs |
| `md2html.py` | regenera `ESTADO-LOG.html` y `TAREAS-LOG.html` con índice navegable |

Los scripts asumen que se ejecutan desde la raíz del proyecto local (`C:\Users\XAM-PC\Proyectos\AYN-Thor-ESDE`) y que `device/catalog_es/` existe.

---

## 9. Cómo retomar en 5 minutos

1. Leer `docs/TAREAS.md` → sección `## Tareas` (tabla con el estado vigente).
2. Leer las últimas 3 secciones de `docs/ESTADO.md` (al final del fichero, orden cronológico).
3. Comprobar el dispositivo:
   ```bash
   adb devices
   adb -s $S shell 'pidof dev.eden.eden_emulator; dumpsys activity activities | grep -m1 topResumedActivity'
   adb -s $S shell 'grep -E "MemFree|MemAvailable" /proc/meminfo'
   ```
4. Validar el catálogo antes de tocarlo:
   ```bash
   python scripts/verify_catalog.py && python scripts/test_regiones.py
   ```
5. Elegir la siguiente tarea abierta y **documentar el resultado en `ESTADO.md` + `TAREAS.md`**, no sólo en el chat.
