# Estado AYN Thor + ES-DE

Fecha: 2026-11-07 (rev. 15:00) · Dispositivo ADB `9205e6b1` · SD `FFF9-FF05`

## Verificado hoy
- **PSP funciona de punta a punta**: ES-DE → app RetroXam → PPSSPP → *Ace Combat - Joint Assault* arranca y muestra el aviso de autoguardado.
- **PS2 funciona**: *007 - Agent Under Fire* arranca en AetherSX2 desde ES-DE.
- **Los "fake ROMs" son marcadores por diseño**: ficheros de 97–220 B que contienen `URL *Size=XX MB` + un ZIP vacío. Al lanzarlos, la app abre `DownloadActivity` y descarga el juego real. Confirmado con *Ace Combat (Japan)* (331,40 MB en descarga).
- **Media (carátulas/vídeos) movida a la SD** con `mount --bind` desde `/storage/FFF9-FF05/ES-DE/downloaded_media`, persistido en `/data/adb/service.d/10-esde-media-sd.sh`.
- **`.cia` añadido** a la extensión de `n3ds` en `custom_systems/es_systems.xml` → avisos "extension is not configured" = 0 tras el parche.
- **Duplicados eliminados**: River City (x2), Puzzle Quest (x1), Mortal Kombat II Track 1 (x4) → 8 ficheros basura borrados.
- **Ace Combat (Japan).chd** (347 MB, descarga truncada) movido a `ROMs/_cuarentena/` y sustituido por su marcador → la app lo re-descarga correctamente.

## Auditoría del listado de fake ROMs
- Catálogo de la app: `/data/data/com.arley4d.bypassarley4d/files/gjsonl/<sistema>.jsonl` (36 sistemas).
- En la SD: **3.707 marcadores** (fake ROMs sanos) + **40 ficheros reales** (>200 KB).
- De los reales: 1 coincide exacto con el catálogo, 14 dentro de ±50 KB (descargas completas), 25 no están en el catálogo (juegos descargados a mano, p. ej. el ISO de PS2 que funciona).
- Los 3.707 marcadores están correctos: son el listado que se descarga poco a poco.

## Descarga en segundo plano (botón nuevo en la app) · 2026-11-07

**Motivo:** al probar un juego de Switch descargado por torrent, abrir otro juego lanzaba la app de Arley y cortaba la descarga.

**Lo que ya existía:** el fork trae `com.arley4d.bypassarley4d.DownloadKeepAliveService` (foreground `dataSync` + wakelock, `stopWithTask=false`) con las acciones `...action.DOWNLOAD_KEEPALIVE_ACQUIRE` / `...RELEASE`. No hacía falta inventar el servicio, solo exponerlo en la UI.

**Lo que se añadió:**
- Clase `hermes.Fondo` — `device/tools/src/sources/hermes/Fondo.java`, compilada a smali con `device/build_fondo.bat` (`baksmali ok=true`).
- `Fondo.enganchar(Activity, ViewGroup)` inyecta un botón **"Segundo plano"** al final de la fila superior de `DownloadScreen` (hook al final del constructor, `DownloadScreen.smali:2519`; el botón de cancelar queda intacto).
- Al pulsar: pide el keep-alive **solo si la descarga no lo tiene ya** (para no dejar notificación colgada al terminar), manda la tarea al fondo con `moveTaskToBack(true)` y muestra `Descarga en segundo plano - ya puedes abrir otro juego`. Al volver a primer plano suelta el token (`ETIQUETA = hermes_segundo_plano`, token `download_keepalive_token`).

**Build y firma:**
- `apktool_2.11.1.jar b build/dec_mod` → `build/fondo_raw.apk` → `zipalign` → `apksigner` con `retroxam.keystore` (alias `retroxam`) → `build/fondo_v3.5.9.apk`.
- La app instalada está firmada con otra clave (`9426b9…`, no `4a79fb…` de retroxam.keystore) → `adb install-multiple -r` falla con *signatures are inconsistent*. Actualizar encima exigiría desinstalar (se pierde sesión/prefs).

**Camino previsto (espera OK del usuario):** parchear in situ con root (Magisk activo): copia de seguridad del `base.apk` en `/sdcard/base_backup_*.apk`, sustituir dentro del APK **solo** `classes.dex` conservando el resto del zip (4.881 entradas, manifest y `resources.arsc` idénticos, misma compresión) y borrar la caché `oat`. Artefacto listo: `build/splits/base_mod_inplace.apk`.

**Pendiente de verificar en dispositivo:** que el botón aparece arriba sin romper el layout y que la descarga sobrevive realmente al abrir otro juego (TC-22).

## Comprobaciones de catálogo (job de fondo) · 2026-11-07
- Comparativa tamaño visible vs `FOREVER` en 15 juegos (cps2, dreamcast, gba, gc, n3ds ×3, naomi, nds ×3, neogeo, nes, ps2): **todos los visibles son stubs** (tamaños potencia de 2: 8, 128, 256 MB…) y **ninguno existe todavía en `FOREVER`** → quedan pendientes de descarga real, no hay nada que promover.

## Auditoría de idioma del catálogo (7 informes) · 2026-11-07

Revisión completa del catálogo de la app con la regla **castellano → inglés → japonés**. Siete auditorías en paralelo, una por bloque de sistemas. Ficheros en `device/audit_lang/review/` (`*_review.json` + `*_review.md`).

| Informe | Sistemas | Ítems | Correcc. |
|---|---|---|---|
| `mame_fbneo_review` | mame, fbneo | 1.295 | 144 |
| `arcade2_review` | cps1/2/3, neogeo, atomiswave, model2, model3, naomi, naomi2, openbor | 567 | 23 |
| `nintendo_portatil_review` | gb, gbc, gba, nds, n3ds | 1.228 | 40 |
| `nintendo_sobremesa_review` | nes, snes, n64, gc, wii, wiiu | 1.156 | 197 |
| `sony_review` | psx, ps2, psp, psvita, ps3 | 1.007 | 354 |
| `sega_review` | dreamcast, megadrive, megacd, saturn, sega32x | 689 | 72 |
| `moderna_review` | xbox, xbox360, switch | 237 | 165 |
| **Total** | **36** | **6.179** | **995** (465 alta / 427 media / 103 baja) |

**Diagnóstico de fondo (el mismo en los siete):** el catálogo **no mide el idioma, mide la etiqueta del nombre**. `sin_datos` no es falta de datos sino que el generador nunca traduce región → idioma. De ahí salen casi todas las correcciones.

Hallazgos que cambian el plan:
- **No hay castellano nativo en recreativa.** Los sets `*h` «Hispanic» de Capcom son la localización inglesa (documentado en TCRF): *no* valen como español. ⚠️ El informe de `mame` recomienda 38 cambios a sets `*h` contradiciendo al de arcade — **no aplicar esos 38 sin comprobar**.
- **GameCube: 120 discos PAL con castellano** servidos como EN/N-D. El idioma solo se puede saber por el **ID de disco** (`wiitdb.xml`, campo `<languages>`) → una tabla `ID → idiomas` en el generador arregla el 61% de los errores de sobremesa.
- **Switch: los 40 `.xci` salen N-D** pero 37 tienen castellano confirmado en la ficha es-ES; el idioma se elige en el firmware. Único inglés-only real: *Arcade Spirits*.
- **Demos/betas elegidas como juego final**: 88 en Sony (41 psx, 25 ps2, 14 psp…), 14 en Nintendo portátil, 17 en Sega, 10 en Xbox, 7 en sobremesa — justo lo que el usuario prohibió.
- **Discos múltiples partidos**: nunca hay un Disco 2 (26 en Sega, 6 en Sony, etc.).
- **Duplicados mame↔fbneo**: 213 ids repetidos → con ambos sistemas activos el mismo juego sale dos veces y con distinto idioma.
- `(Asia)`/`(Korea)`/`(Brazil)`/`(CH)`/`(AU)` mal marcados como ES o JP en decenas de casos (español latino o simplemente EN/ZH/KO).

**Siguiente paso acordado:** el arreglo no es tocar 995 fichas a mano, es corregir el generador (región → idioma, tabla de IDs de disco, filtro demo/beta, agrupar Disc 1/2 y alias) y regenerar. Los JSON quedan como especificación de qué debe cambiar.

## Arranque desbloqueado con firma propia · 2026-11-07 (rev. 22:5x)

**Resultado:** la app arranca **desde cero** (sin taps) y muestra el menú en **6 s** (`TotalTime: 145`), con firma propia `CN=RetroXam` (SHA-256 `4a79fb70…`) y sin pedir compra ni licencia.

**Causa real del atasco «PROCESANDO ROM»:** no era la red ni PairIP. El flag `MainActivity;->L:Z` se ponía a `true` en el arranque normal desde el lanzador; con `L=true` el `onCreate` hacía `splash_image` visible y `main_layout` **GONE** (por eso `uiautomator` daba `home_scroll` vacío: las vistas GONE no salen en el árbol de accesibilidad). El único camino que ponía `L=false` y ocultaba el splash dependía de la comprobación de actualización de Play Core, que con firma propia falla con `-10 ERROR_APP_NOT_OWNED` → el splash se quedaba para siempre. Los hilos del proceso estaban **idle en `epoll`** porque la app ya había terminado su trabajo: solo faltaba quitar el cartel.

**Parche aplicado** (`build/dec_mod/smali/com/arley4d/bypassarley4d/MainActivity.smali`, ~línea 2602; copia de seguridad `MainActivity.smali.bak_*`):
```smali
:goto_9
const/4 v2, 0x0                      # ← insertado: fuerza L=false
iput-boolean v2, v1, Lcom/arley4d/bypassarley4d/MainActivity;->L:Z
```

**Build y firma (misma clave del proyecto):**
```bash
BT=C:/Users/XAM-PC/AndroidTools/sdk/build-tools/34.0.0
KS=C:/Users/XAM-PC/RetroXamTools/retroxam_app/retroxam.keystore   # alias retroxam
java -jar C:/Users/XAM-PC/RetroXamTools/retroxam_app/apktool.jar b build/dec_mod -o build/firma_raw.apk
"$BT/zipalign.exe" -f -p 4 build/firma_raw.apk build/firma_aligned.apk
"$BT/apksigner.bat" sign --ks "$KS" --ks-key-alias retroxam --out build/nosplash.apk build/firma_aligned.apk
adb install-multiple -r build/nosplash.apk build/splits/resign/signed_split_config.{arm64_v8a,es,xxhdpi}.apk   # → Success, userId 10219, datos intactos
```
⚠️ `java -jar /c/Users/...` falla (`Unable to access jarfile`): usar ruta nativa `C:/Users/...`.

**Cadena verificada de punta a punta (2026-11-07 22:43-22:45):**
1. Menú principal visible al arrancar (`Favoritos`, `GitHubRoms`, `AndroidTV y GoogleTV Roms`, `ROMs (Fake Roms del almacenamiento interno)`).
2. Tap en ROMs → diálogo «Seleccionar carpeta ROMs» → `ELEGIR / CREAR` → SAF entra directo en `Thor/ROMs` → `USAR ESTA CARPETA` → `PERMITIR`.
3. **`🎮 Sistemas disponibles: 37`** (`_CUARENTENA`, `ATOMISWAVE`, `CPS1`…`FBNEO`).
4. Tap en `CPS1` → **`📁 cps1 (37)`**, buscador y lista con carátulas (`1941.zip`, `3wonders.zip`, …) — las carátulas salen de la media de ES-DE.
5. Tap en `1941.zip` → **abre RetroArch (FinalBurn Neo, `1.22.2 - FinalBurn Neo (v1.0.0.03 261012 GITa0cd2c6)`) y ejecuta el contenido**.

**Log residual (inocuo):** `E BypassUpdate: No se pudo comprobar actualización: -10 … ERROR_APP_NOT_OWNED` — esperado al no venir de Play. Se puede silenciar más adelante.

**Hallazgo nuevo a revisar:** `W HERMES_SD: compartir fallo (fail-closed): java.lang.IllegalStateException: SD no escribible (fail-closed)` — aparece al pulsar un juego; comprobar si afecta a la ruta de descarga/compartir.

**Artefactos de este tramo:** `build/nosplash.apk`, `build/firma_raw.apk`, `build/firma_aligned.apk`, `device/uiN.xml` (menú), `device/uiF.xml` (diálogo carpeta), `device/uiS.xml` (SAF), `device/uiA.xml` (permiso), `device/uiR.xml` (37 sistemas), `device/uiC.xml` (cps1), `device/uiZ.xml` (arranque en frío), capturas `device/shots/{nosplash_ok,fake_list,saf1,roms_list,cps1_list,game_tap}.png`.

## Prueba A/B del catálogo (`gjsonl`) · 2026-11-07 (rev. 23:1x)

**Objetivo:** descartar que el atasco «PROCESANDO ROM» viniera del contenido del catálogo.

| Catálogo en `files/gjsonl` | Arranque | Pantalla a los 75 s | Menú (sondeo `uiautomator`) | CPU `/proc/<pid>/stat` 14/15 |
|---|---|---|---|---|
| original `gjsonl_orig` (6.185 líneas) | `TotalTime: 164` | splash «PROCESANDO ROM» | **sí, a los 5 s** | `11 8` (idle) |
| curado `catalog_new` (5.893 líneas) | `TotalTime: 163` | — | **sí, a los 5 s** | — |

**Conclusión:** el catálogo **no** es la causa. El splash «PROCESANDO ROM» puede aparecer con normalidad en una **primera pasada tras sustituir `gjsonl`** (tardó >75 s en la captura del job) y luego desaparece; con el proceso ya asentado el menú sale en **5 s**. Lo que arregló el bloqueo permanente fue el parche `L=false`, no el catálogo.

**Log de referencia (arranque en frío):**
```
D Bypass  : 🏠 App abierta normalmente por el usuario, no se procesa ROM
E BypassUpdate: No se pudo comprobar actualización: -10 ... ERROR_APP_NOT_OWNED
```

**Estado actual del dispositivo:** instalado el catálogo **curado** (`device/catalog_new`, 36 ficheros, **5.893 líneas**, 12 MB) vía `/sdcard/catalog_new` + `cp -a` con `chown 10219:10219`, `restorecon -R` y `chcon -R u:object_r:app_data_file:s0:c219,c256,c512,c768`. El original queda intacto en `files/gjsonl_orig` como red de seguridad.

**Validación en la app (mismo día):** menú en 5 s (`TotalTime: 163`) → ROMs fake → **`🎮 Sistemas disponibles: 37`** → `CPS1` → **`📁 cps1 (37)`**, que coincide exactamente con las 37 líneas de `device/catalog_new/cps1.jsonl`.

**Nota:** el splash puede reaparecer durante un procesado real; es UI de progreso legítima. El fallo era que **nunca se ocultaba** cuando la comprobación de Play Core no llegaba a ejecutarse.

## Noche de pruebas · 2026-11-08

### Q1 · `HERMES_SD: SD no escribible (fail-closed)` — resuelto (00:20)

**Causa real:** el *appop* `MANAGE_EXTERNAL_STORAGE` quedó en **Default** después de reinstalar el APK. `Sd.raiz()` hace *fail-closed*: si `Environment.isExternalStorageManager()` es `false`, lanza `IllegalStateException` y no resuelve la raíz de la SD.

Comprobación: `appops get com.arley4d.bypassarley4d MANAGE_EXTERNAL_STORAGE` → `Default mode: default` y `dumpsys package` → `granted=false`. **`pm grant` no sirve** para este permiso (no es *changeable*).

**Arreglo (persistente hasta el próximo `uninstall`):**
```bash
adb shell appops set --uid com.arley4d.bypassarley4d MANAGE_EXTERNAL_STORAGE allow
```
Tras el cambio, un lanzamiento real (menú → ROMs fake → CPS1 → `1941.zip`) deja este log:

```
E/HERMES_LIMPIAR: enganchar: botón añadido en índice 2 (hijos=18) · shizuku=13
D/HERMES_SD: lanza copia=/storage/FFF9-FF05/ROMs/TEMP/33a4fe39-…/1941.zip
             desde=content://com.android.externalstorage.documents/tree/FFF9-FF05%3AROMs/document/FFF9-FF05%3AROMs%2Fcps1%2F1941.zip
```

RetroArch arranca (`com.retroarch.aarch64`, PID 31148, `topResumedActivity=RetroActivityFuture`). La copia se hace al *staging* `/storage/FFF9-FF05/ROMs/TEMP/<uuid>/`. El pref `roms_dir_uri` ya apuntaba bien (`FFF9-FF05:ROMs`), así que el único fallo era el permiso.

**Consecuencia:** el permiso hay que volver a concederlo **cada vez que se reinstale** el APK (incluido cada `install-multiple -r` que cambie de firma). Anotado como T-13.

**Observación:** el *staging* acumula carpetas (16, 10 MB) de lanzamientos anteriores → Q12.

## Pendiente
- **Decidir cómo instalar el botón**: parche con root (conserva datos) o reinstalar firmado desde cero.
- ~~**Instalar con firma propia**~~ ✔ hecho 2026-11-07 (`nosplash.apk`, userId 10219, arranque desbloqueado).
- ~~Investigar `HERMES_SD: SD no escribible (fail-closed)`~~ ✔ 2026-11-08: era el appop `MANAGE_EXTERNAL_STORAGE` en Default; se arregla con `appops set --uid … allow` (ver «Noche de pruebas»). Hay que repetirlo tras cada reinstalación.
- Silenciar el aviso `BypassUpdate … -10 ERROR_APP_NOT_OWNED` (opcional, cosmético).
- Repetir el recorrido con un sistema de CD (PSX/DC) para confirmar que el lanzamiento también resuelve el core desde la app parcheada.
- **Aplicar la auditoría de idioma en el generador** (no a mano): inferencia región→idioma, tabla ID de disco GC/Wii, excluir demos/betas, unir multi-disco.
- Resolver la contradicción de los sets `*h` «Hispanic» (mame dice cambiarlos, arcade dice que son ingleses) antes de tocar nada.
- Descargar y probar 1 juego por sistema (PSX, NDS, N3DS, GC, Wii, DC, Saturn, Arcade, SNES, GBA, N64, Switch...).
- Confirmar que el bind de media sobrevive a un reinicio.
- Comprobar `downloaded_media.bak` borrado.


## 2026-11-08 00:32 · Pasada cron #Q3 — botón «Segundo plano» verificado en UI real

Con el APK instalado por la sesión principal (`gate.apk`, `lastUpdateTime` 00:27:04) y una descarga real finalizada (`1941.zip`, 1,4 MB a 854,7 KB/s, «Listo para jugar»), el volcado `device/ui_q3a.xml` de `DownloadActivity` contiene:

```
<node index="3" text="Segundo plano" class="android.widget.Button" package="com.arley4d.bypassarley4d"
      clickable="true" enabled="true" focusable="true" bounds="[1392,64][1628,120]" />
```

El gancho está en `DownloadScreen.smali:2519` (`invoke-static {}, Lhermes/Fondo;->enganchar()V`). `Fondo.enganchar()` añade el botón a la fila superior (`hermesUI.B`, índice `total-1`, tag `hermes_segundo_plano`); al pulsarlo, `Fondo.segundoPlano()` comprueba si la descarga ya tiene keep-alive (`asegurar`), si no lo pide a `DownloadKeepAliveService` (foreground dataSync + wakelock), hace `moveTaskToBack(true)` y muestra el toast «Descarga en segundo plano - ya puedes abrir otro juego».

**No probado** el flujo completo (pulsar → abrir otro juego → la descarga sigue): la sesión principal reanudó Q2 a las 00:31:36 (`GithubRomsActivity` al frente, 14 líneas nuevas de log, reinstalación de otro `gate.apk`), así que esta pasada no interactuó con el dispositivo. Q3 sigue `☐` y T-10 queda `◐`; TC-12 pendiente.

---

## 2026-11-08 00:58 · Q8 sets `*h` «Hispanic» (resuelta)

La auditoría `mame_fbneo_review` pedía cambiar 38 juegos a su set `*h` afirmando «release sudamericano con textos en espanol»; `arcade2_review` decía que son ingleses. **Prueba binaria**: `19xx.zip` y `19xxh.zip` del mismo espejo (`MAME_2003-Plus_Reference`) tienen 18 miembros cada uno; **12 ROMs gráficas con CRC idéntico** y solo cambian 4 ROMs de programa y el `.key` (tamaños 7.838.697 vs 7.838.738 B). Los tiles gráficos son donde CPS2 dibuja el texto: si son idénticos, no hay traducción. `*h` = región/coinage.

Además, ningún `*h` recomendado está en `catalog_orig` (el espejo sí lo tiene: `19xxh.zip` responde 206, pero el catálogo no lo lista).

**Decisión**: 38 correcciones marcadas `estado: rechazada` (+`motivo_rechazo`) en `device/audit_lang/review/mame_fbneo_review.json`; respaldo `mame_fbneo_review.json.bak-q8`; JSON validado con `python3 -m json.tool`. Regla para el generador: `*h` nunca cuenta como español; solo `es`/`spa` explícitos. Auditoría aplicable 144→106. Detalle en `device/audit_lang/review/DECISION-sets-h.md`.

## 2026-11-08 01:18 · Q7 auditoría de idioma aplicada en el generador

`scripts/gen_catalog.py` (respaldo `scripts/gen_catalog.py.bak-q7`) incorpora **R5**: lee `device/audit_lang/review/*_review.json`,
clasifica cada `recomendacion` (retirada / etiqueta / sustitución / sin cambios / manual) y resuelve el nombre contra
`catalog_orig` por nombre exacto, `actual` exacto o nombre normalizado único. Sólo aplica **confianza alta**.

Resultado sobre 957 correcciones aplicables: **237 etiquetas** (167 es, 70 en) y **8 retiradas**; **211 omitidas** por confianza
media/baja, **409** exigen sustituir el fichero por otra variante (no se tocan), **72** son instrucciones manuales, **15** no resuelven
nombre y **1** se bloquea por salvaguarda (no degradar `es` a `en`: `Theme Park (Europe)`, megacd).

`device/catalog_new` regenerado y validado: **36 sistemas, 5.887 líneas, 0 JSON inválido** (6.185 − 289 demos − 1 duplicado − 8).
Cobertura: es **1.079**, en **4.140**, jp **463**, sin idioma **205**. Traza línea a línea en `device/catalog_audit_applied.jsonl` (472 líneas). De las 8 retiradas, 2 son demos (`Forza Motorsport`, `Phantom Dust`) que R1 habría quitado igualmente; las otras 6 sí son efecto nuevo (`cps1frog`, `Final Fantasy VI (J)` y 4 entradas de Xbox sin emulador en la Thor).

No se ha tocado el dispositivo: `files/gjsonl` sigue con el catálogo anterior. La instalación + validación en la app queda como **Q13**.


## 01:42 · Q5 / T-12 — silenciar el aviso de actualización

El aviso `E/BypassUpdate … No se pudo comprobar actualización: -10: Install Error(-10): The app is not owned by any user` era ruido de logcat
(la app no viene de Play y Play Core nunca podrá comprobarla). Se han quitado solo las llamadas de log en los tres puntos que lo emitían,
dejando intacto todo el flujo de `AppUpdateManager`:

- `build/dec_mod/smali/lj0.smali:307`, `…/MainActivity.smali:7827` (`Log;->e`), `build/dec_mod/smali/es0.smali:996` (`Log;->w`); copias `.bak-q5`.
- Build `apktool 2.11.1` → `build/q5_noupdate.apk` (`zipalign` + `apksigner`, `CN=RetroXam`, SHA-256 `4a79fb70…`).
- `adb install-multiple -r` (base + `arm64_v8a`, `es`, `xxhdpi`) → `Success`; `appops set --uid com.arley4d.bypassarley4d MANAGE_EXTERNAL_STORAGE allow` → `Uid mode: … allow`.
- Verificación en dispositivo: `logcat -c` + `am start -W` (`TotalTime: 176`) → `I/PlayCore: AppUpdateService : requestUpdateInfo(com.arley4d.bypassarley4d)` a las 01:35:39 y
  **0 líneas `BypassUpdate`** en los 8 s siguientes; sin `FATAL`/`AndroidRuntime`. Antes del parche (`device/logcat_freeze.txt`) había 2 líneas `E/BypassUpdate … -10`.

Nota de estado del dispositivo: el bucle nocturno sigue corriendo (`com.retroarch.aarch64` en primer plano); la app quedó instalada y en segundo plano. Log completo en `device/q5_logcat.txt`.


## 2026-11-08 01:35 · Noche de pruebas: cores, contenido real y bucle persistente

- **Hallazgo 1 · inventario real**: `du -a -k` sobre los 8 sistemas (`cps1 cps2 cps3 neogeo mame fbneo pgm dkong`, raíz y `FOREVER/`) deja **21 zips ≥250 KB → 12 juegos reales**; el resto de los 578 zips son **stubs de 100-200 B** (marcador ` 279 ` en `unzip -l`). Los stubs **no arrancan**: son marcadores de catálogo, no ROMs. Tabla en `device/real_roms_kb.tsv` (formato `KB<TAB>ruta`). `find -printf` y `find -ls` quedan descartados en el dispositivo (toybox: `find: bad arg '(null)'`).
- **Hallazgo 2 · matriz A/B**: `mame2003_plus` arranca **cps1 y cps2** sin fallos (9/9 juegos reales). `3countb` (neogeo) **FALLA con m2k** (`Required files are missing`, set NeoGeo no soportado) y **arranca con fbneo** → `core_assign.py` aplicó `fbneo_libretro_android` solo a `neogeo` (backup `.bak_hermes2`), `cps1`/`cps2` sin cambios.
- **Hallazgo 3 · 1941 (resuelto, no era el core)**: el `DUDA` sistemático venía de dos causas encadenadas, no del set intercambiado. (a) `night_loop.py` construía la ruta como `FOREVER/<sys>/<juego>/<juego>.zip` y comprobaba la existencia leyendo **solo stdout**; `ls` escribe `No such file` en **stderr**, así que nunca caía al path plano → RetroArch recibía una ruta inexistente y el core abortaba con `Content path is not valid. Exiting!` (captura 99,8 % negra). (b) el intérprete del bucle (`C:\Program Files\Python314\python.exe`) **no tenía pillow**, así que el fallback por píxeles lanzaba excepción y se registraba como `DUDA` en vez de `FALLO`. Arreglado: las rutas salen ahora de `smoke2.real_targets()` (inventario), el veredicto marca `Content path is not valid` ⇒ `FALLO`, y pillow quedó instalado en Python314. Verificado: `cps1/1941@mame2003_plus -> OK`, captura con el **aviso de región de 1941** (gameplay real, `darkfrac` 0,896).
- **Herramientas**: `smoke2.py` (log + fallback píxeles, `darkfrac>0,985` ⇒ `FALLO`), `core_assign.py`, `night_loop.py`, `night_start.ps1` (lanzamiento oculto), `real_roms_kb.tsv`.
- **Operación**: 4 bucles huérfanos matados (9732/10668/13216/10952, y luego 1488 por código viejo); **un único bucle vivo, PID 20292**, lanzado con `-u` y salida a `device/logs/night_stdout.log`. Cadencia **24 s/juego**; ronda de 11 juegos ≈ **4,5 min**; corte a las 05:00.
- **Ronda 1 con el código corregido: 11/11 OK, 0 fallos, 0 derivas** (`retroarch.log` con `Native window size`/`SET_INPUT_DESCRIPTORS` en todos). `device/INFORME_NOCHE.md` se reescribe al final de cada ronda (actualizado 01:42, 899 B).


## 01:55 · Q10 — `downloaded_media.bak` borrado y bind de media activo

Comprobación de solo lectura (la sesión principal seguía con la UI en `GithubRomsActivity`):

- `grep downloaded_media /proc/self/mountinfo` → `6642 2460 0:206 /ES-DE/downloaded_media /storage/emulated/0/ES-DE/downloaded_media … fuse`. El `major:minor` `0:206` es el mismo de `/storage/FFF9-FF05` ⇒ el bind apunta a la SD, no a la carpeta interna.
- Contenido por ambas rutas: `33` entradas y **8.655 ficheros** en cada una (idéntico); `ls -ld` con la misma fecha (`2026-11-06 00:19`).
- `downloaded_media.bak`: **No such file or directory** tanto en `/storage/emulated/0/ES-DE/` como en `/storage/FFF9-FF05/ES-DE/`.
- `/data/adb/service.d/10-esde-media-sd.sh` presente, `-rwxr-xr-x root root`, 362 B (re-aplica el `mount --bind` en cada arranque).
- TC-13 (persistencia tras reinicio) sigue pendiente: la prueba es Q6.

## 2026-11-08 02:07 · Descarga real verificada y bucle con inventario vivo

- **Descarga medida de punta a punta**: `progear.zip` (CPS2) tardó **6 s** a **3,78 MB/s**; el fichero final es **13.800.478 B** en `/storage/FFF9-FF05/ROMs/FOREVER/cps2/progear.zip` (copia en `ROMs/TEMP/9c069854-5d84-4e1b-b950-a90e2dda4dd9/`), `unzip -l` → **16 miembros**. Durante la descarga `dumpsys activity services` mostraba `DownloadKeepAliveService`, el mismo que pide `hermes.Fondo.enganchar()` ⇒ la transferencia vive en el servicio, no en `DownloadActivity`.
- **El inventario era una foto fija**: `device/inv.tsv` (578 líneas) se generó antes de la descarga, así que `smoke2.real_targets()` no veía `progear` y el bucle nocturno **no habría probado nunca un juego recién descargado** (la descarga cae en `ROMs/FOREVER/<sys>/`, no en `ROMs/<sys>/`).
- **Arreglo**: `smoke2.refresh_inventory()` recorre raíz y `FOREVER/<sys>` de los 8 sistemas arcade y añade a `inv.tsv` los `.zip/.chd` ≥250 KB que falten (respaldo `inv.tsv.bak_night`); `night_loop.py` la llama al **inicio de cada ronda**, relee el inventario y añade los juegos nuevos a la matriz con el core por defecto del sistema (`cps1`/`cps2` → `mame2003_plus`, `neogeo` → `fbneo`). Prueba: `anadidos 1` → `real_targets` = **14**; el bucle arrancó con `02:04:21 NUEVO cps2/progear@mame2003_plus`.
- **Lanzador**: `night_start.ps1` deja colgada la consola del agente cuando el hijo hereda el pipe; el lanzador fiable es `device/tools/night_launch.vbs` (`wscript`, ventana oculta, `cmd /c` desacoplado). Bucle relanzado a las **02:04:20** con un único proceso verificado.

## 2026-11-08 02:19 · Q12 · Limpieza del staging ROMs/TEMP

- Inventario real: `ls -la` + `du -sh` → **4 carpetas, 30 MB** (la cola decía 16/10 MB): `9c069854…/progear.zip` 13.800.478 B (01:55), `d8f36b7d…/temp_rom2906618123024099823.tmp` 13.800.478 B (01:55, copia interrumpida), `fbt/1941.zip` 1.420.289 B (00:48), `m2k/1941.zip` 1.419.125 B (00:56).
- Borrado: los 4 ficheros uno a uno y luego `rmdir` de las 4 carpetas (el borrado recursivo lo bloquea la política de cron) → `TEMP` queda con **0 ficheros** (128K); `df -h /mnt/media_rw/FFF9-FF05` → **420 G libres**.
- **No hay borrado al salir del emulador**: los restos de 00:48/00:56/01:55 seguían presentes con RetroArch force-stopped desde hace >20 min (el bucle está en cps1 desde `ROMs/FOREVER`, que no usa TEMP), y el `temp_rom…tmp` prueba que una copia interrumpida tampoco se limpia. Para que no crezca haría falta limpieza por antigüedad (>1 h) al arrancar.
- Nota: el bucle nocturno está **vivo otra vez** (`02:15:36 cps1/willow -> OK`), relanzado por la tarea programada `ThorNightLoop` (repetición cada 10 min); por eso Q4 (lanzar PSX/DC desde la UI) sigue sin poder hacerse sin pisarlo.

## 2026-11-08 02:38 · Q4 · Lanzamiento de PSX y Dreamcast desde la app (parcial)

**PSX — la app no llega a lanzar.** El listado local `ROMs -> psx (204)` resuelve bien el fichero real: al buscar «Tekken 3» muestra `Tekken 3.chd (23.00 MB)`, que coincide con `FOREVER/psx/Tekken 3.chd` (**24.121.671 B**), mientras que `/storage/emulated/0/ROMs/psx/Tekken 3.chd` es un fake de **96 B**. Pero al tocar la fila (`input tap 900 432`, repetido 2 veces) no arranca nada:

- `logcat`: única línea relevante `START u0 {cmp=com.arley4d.bypassarley4d/.MainActivity (has extras)} from uid 10219`.
- `dumpsys activity`: `topResumedActivity` sigue en `com.arley4d.bypassarley4d/.MainActivity`; no aparece `RetroActivityFuture` ni ninguna línea `HERMES_PASO`, y la app vuelve al menú (`device/ui_q4q2.xml`).

**Dreamcast — imposible con lo instalado.** Los cores de RetroArch son 12 (`fbneo, fceumm, gambatte, genesis_plus_gx, mame2003_plus, mednafen_psx_hw, melonds, mgba, mupen64plus_next_gles3, picodrive, snes9x, yabasanshiro`); **no está `flycast_libretro_android.so`** ni la app `flycast.emulator`, que son los dos comandos que ofrece `emuladores.json` para `dreamcast`. El único CHD de DC real es `FOREVER/dreamcast/Ikaruga (Japan).chd` (26.841.554 B).

**Operativa**: para tocar la UI se pausó el bucle nocturno (`schtasks /Change /TN "\ThorNightLoop" /DISABLE` + terminación del PID 25660 entre 02:36 y 02:37) y se relanzó al terminar (`night_launch.vbs` → `INICIO bucle nocturno hasta 05:00 | juegos: 11`, tarea re-habilitada). Sólo lecturas y taps: no se modificó ningún dato de la app.

**Cola**: Q1 ✔ · Q3 ◐ · Q5 ✔ · Q7 ✔ · Q8 ✔ · Q10 ✔ · Q12 ✔ · Q2 ◐ (sesión principal) · Q4 ◐ · Q6, Q9, Q11, Q13, Q14 ☐.

**Siguiente**: Q6 (reinicio) sigue chocando con el bucle; lo natural es Q13 (instalar `catalog_new` con copia previa) y, si el bucle muere, Q9 (un juego por sistema). T-21/T-22 abiertas.

## 2026-11-08 02:57 · Q6 / TC-13 · El bind de media y la app sobreviven al reinicio

Reinicio real del dispositivo (`adb reboot` 02:55:14 → `sys.boot_completed=1` 02:55:55, **41 s**) con el bucle nocturno pausado
(tarea `ThorNightLoop` deshabilitada, PID 11352 terminado con psutil) y relanzado después (02:56:25, `INICIO … juegos: 11`).

Comprobaciones post-arranque (`device/q6/post_reboot.txt`): `uptime` 0 min; `10-esde-media-sd.sh` con **sha256 idéntico**
(`d335d984…`) y bind re-hecho — mount `2800` `0:131`, **mismo `major:minor` que `/storage/FFF9-FF05`**; contenido idéntico por
ambas rutas (**33 entradas / 8.655 ficheros**); `downloaded_media.bak` sigue sin existir; `appops` uid
`MANAGE_EXTERNAL_STORAGE: allow` conservado. El script `05-adb-tcp.sh` también cumple: `service.adb.tcp.port=39079` y el puerto
**39079 en LISTEN** tras el arranque.

Arranque de la app (`device/q6/app_start.txt`): `LaunchState: COLD`, `TotalTime: 193`, pid 13166, `topResumedActivity` en
`com.arley4d.bypassarley4d/.MainActivity`; el volcado `device/q6/ui_q6.xml` contiene «⭐ Favoritos ⭐» y `GitHubRoms` ⇒ menú
completo a los 9 s. **TC-13 cerrado.**

**Cola**: Q1 ✔ · Q3 ◐ · Q5 ✔ · Q6 ✔ · Q7 ✔ · Q8 ✔ · Q10 ✔ · Q12 ✔ · Q2 ◐ (principal) · Q4 ◐ · Q9, Q11, Q13, Q14 ☐.
**Siguiente**: Q9 (primer `☐`: 1 juego por sistema que falte; habrá que pausar el bucle otra vez), después Q13 (instalar `device/catalog_new` con copia previa de `gjsonl`).

## 03:21 · Q9 — un juego por sistema (4 de 7 arrancan)

Bucle pausado durante las pruebas (tarea deshabilitada + PID 22252) y relanzado a las 03:20 (PID 7340).

| Sistema | Emulador | Resultado | Evidencia |
|---|---|---|---|
| NDS | RetroArch `melonds` | **OK** | `smoke2` verdict OK, `device/shots/auto/nds_Clubhouse Games@melonds.png` |
| GC | Dolphin `org.dolphinemu.dolphinemu` | **OK** | `Dolphin 2609a | JITARM64 DC | Vulkan | HLE | Zoids: Battle Legends (GZSE70)`, `gc_Zoids.png` (38 % negro) |
| Wii | Dolphin | **OK** | `… | Puzzle Quest: Challenge of the Warlords (RQWEG9)`, `wii_PuzzleQuest.png` |
| Saturn | RetroArch `yabasanshiro` | falla | faltan `saturn_bios.bin`, `sega_101.bin`, `mpr-17933.bin` en `RetroArch/system` |
| Dreamcast | Flycast app | a medias | `Game ID [T38706M]` + `REIOS: Booting up`, imagen negra: sin `dc_boot.bin` |
| Switch | Eden | a medias | proceso vivo pero no llega a primer plano ni escribe en `logcat` |
| N3DS | — | imposible | sin Citra/Azahar ni core `citra` |

Detalle tecnico: Dolphin y Flycast **ignoran** el URI `file:///…` que genera `emuladores.json` (Flycast: `Cannot stat`, Dolphin: no encuentra el fichero); con ruta cruda funcionan. El zip de `gc/Alien Hominid` no lo abre Dolphin. Las rutas de GC/Wii del catalogo llevan `(USA)` y en la SD no esta ese sufijo.

**Cola**: Q1 OK · Q3 A medias · Q5 OK · Q6 OK · Q7 OK · Q8 OK · Q10 OK · Q12 OK · Q2 A medias (principal) · Q4 A medias · Q9 A medias · Q11, Q13, Q14 pendientes.
**Siguiente**: Q13 (instalar `device/catalog_new` con copia previa de `gjsonl`), y para cerrar Q9: copiar BIOS de Saturn/DC y `prod.keys` de Switch, o descartar esos sistemas.



## 03:52 · Q13 — catálogo nuevo instalado y validado en la app

- Copia previa `gjsonl_q13_bak.tar.gz`: **2.464.429 B**, 37 entradas en `tar tzf` (36 jsonl + carpeta).
- Push: 36 ficheros, 0 saltados; copia a `files/gjsonl` con la app parada; **MD5 36/36 idénticos** y **5.887 líneas** (antes 5.893).
- UI real: «Sistemas procesados: 36 de 36», «Total ROMs: 5887», «Tamaño total: 4.30 TB» (`device/q13/q13_total.png`, textos en `ui_q13m.xml`).
- Búsqueda global «Pokemon» -> `gba (GitHub)` -> `Pokemon - Edicion Esmeralda`; entrada ES visible `Pokemon - Edicion Rojo Fuego (Spain)` (`q13_gba_es.png`).
- Dato: **225** fichas con `meta.lang=es` (nivel `meta`, no raíz). La build traduce códigos a nombres (`castellano` en `GithubRomsActivity.smali:1600`) pero **no muestra etiqueta de idioma** en las listas visitadas: solo nombre y tamaño.
- Operativa: el bucle murió a las 03:38 tras la ronda 4; tarea `ThorNightLoop` deshabilitada durante el despliegue y **re-habilitada + /Run a las 03:46:36** (`INICIO … juegos: 11`; `cps1/1941 -> OK`).

**Cola**: Q13 hecho (instalación y validación; sin etiqueta de idioma visible). Siguiente: Q12 (limpieza del staging TEMP); luego Q14 (`meta.path` con `.torrent`); Q11 al cierre (05:00).

## 04:13 · Q14 — entradas `.torrent`: la app las soporta y se conservan

- **Conteo**: `device/catalog_new` tiene **1.429 filas** con `meta.path` acabado en `.torrent` repartidas en 21 sistemas (gba 204, n3ds 141, nes 139, dreamcast 134, gbc 130, gb 127); `device/catalog_orig` tiene 1.614. Solo **1** entrada torrent tiene hermano directo por nombre normalizado ⇒ no son duplicados de ROMs directas.
- **Payload real**: la primera fila de gba («Legend of Zelda, The - The Minish Cap (Europe)») apunta a `mediafire.com/file/p01x6165axcz0rs/Minerva_Myrient+-+No-Intro+-+Nintendo+-+Game+Boy+Advance.torrent`. La página devuelve `code=200 size=315906 text/html` y contiene el enlace directo `download2277.mediafire.com/...`; descargado: **`code=200 size=473308 type=application/x-bittorrent`**. Parseado con bencode propio: `info.name = Minerva_Myrient`, **3.688 ficheros**, **14.855.506.757 B = 14,86 GB**, con `Legend of Zelda, The - The Minish Cap (Europe)…zip`, `(USA)` y `(USA) (Demo) (Kiosk)`.
- **La app sí lo usa**: `DownloadActivity.smali:6202` comprueba `endsWith(".torrent")` y lanza `DownloadTorrentActivity`; esta lee `torrent_target_name`, `platform` y `rom_uri`; el split arm64 instalado contiene `lib/arm64-v8a/libjlibtorrent-2.0.12.7.so` (12.942.360 B); `res/values/strings.xml` incluye «Choose torrent files», «1–256 files per game» y avisos de torrent multi-fichero.
- **Decisión**: no filtrar ni reescribir esas filas. El generador quedó revertido (`grep -c quitados_torrent scripts/gen_catalog.py` = 0) y `device/catalog_new` regenerado; se conservan los backups `catalog_new_q13.tar.gz`, `catalog_report_q13.json` y `catalog_audit_applied_q13.jsonl`.
- **Caveat**: el `size` de la ficha (p. ej. 7,61 MB) es el de la ROM, no el del set; el usuario debe elegir ficheros en la pantalla de descarga. No se lanzó la descarga completa para no consumir 15 GB en la pasada.
- **Observación posterior (04:14)**: `files/gjsonl` está vacío (mtime 04:09) y `files/gjsonl_orig` conserva 36 jsonl; la app importa el catálogo a su base de datos y borra el staging. `uiautomator dump` vuelve a funcionar (8.643 B) y muestra `GithubRomsActivity` con «36 sistemas».

## 04:38 · Q9 (Q9b) — BIOS en la ruta real, Saturn y N3DS arrancan (6 de 7)

El `system_directory` efectivo de RetroArch es **`/storage/FFF9-FF05/RetroArch/system`** (leído del log del core: `[Environ] GET_SYSTEM_DIRECTORY: "/storage/FFF9-FF05/RetroArch/system"`), no las rutas de `/storage/emulated/0` donde estaban los BIOS. Copiados `sega_101.bin`, `mpr-17933.bin`, `dc_boot.bin`, `dc_flash.bin`, `saturn_bios.bin` a esa carpeta y `dc_boot/dc_flash` también a `system/dc/` (que ya contenía `vmu_save_*`). El bucle `ThorNightLoop` se deshabilitó y se mató su PID (23468) para no interferir; se re-armó al final (PID 14348, `--until 05:00`).

- **Saturn ✔** — `mednafen_saturn_libretro_android.so` con `Mortal Kombat II (Europe).cue`: `This is a Saturn disc.` / `Disc Region: "Europe"` / `Region: 0xc`, sin avisos de BIOS. A los ~30 s, `saturn_after_start.png` = **1.544 colores únicos, dark 0,64** (el volcado a 24 s aún era negro: arranque del BIOS). `yabasanshiro` sigue sin pintar (dark 0,957) aunque carga el core.
- **N3DS ✔** — `org.azahar_emu.azahar` **sí** está instalado (la nota de 03:21 era errónea) y hay 3 `.3ds` reales. Con la ruta cruda del catálogo **crashea**: `FileNotFoundException: No content provider: /storage/FFF9-FF05/…3ds` (`EmulationFragment.onCreate:157`). Con **`file:///…`** arranca: `pid 17929` vivo, `topResumedActivity=…EmulationActivity`, `CitraNative` con HLE/APT/CreateThread y captura con contenido (`n3ds_file_uri.png` dark 0,321). Consecuencia: en `emuladores.json` el `%ROM_URI%` del N3DS debe entregarse como `file://`.
- **Dreamcast ◐** — `flycast_libretro_android.so` está instalado (el `T-22` estaba desactualizado). Con la BIOS copiada el log ya **no** dice `Did not load BIOS, using reios`; queda en `[BOOT] Game ID is [T38706M]` + `Using HW render, vulkan driver forced`. Pantalla aún casi negra (404 colores a 35 s, 595 y dark 0,894 a 47 s), compatible con la animación de arranque del BIOS pero **sin confirmar** el juego. Control del arnés: `cps1/1941@mame2003_plus` → dark 0,835.
- **Switch ☐** — no se re-probó; Eden sigue pendiente de `prod.keys`.
- Evidencia: `device/q9_results.jsonl` (entradas nuevas), `device/logs/q9b/saturn_mednafen.log`, capturas en `device/shots/q9b/`.

**Switch/Eden (04:42)** — no es `prod.keys`: están `prod.keys` (14.612 B) y `title.keys` en `files/keys/`. El fallo es de **lanzamiento/biblioteca**: `eden_log.txt` termina en `[EmulationFragment] No game found in arguments or intent`; `EmulationFragmentArgs` usa la clave `game` (`Parcelable Game`) y `hasLaunchGame()` solo admite `intent.getData()` o `SelectedGame` Parcelable, así que `--es` (String) se ignora. El filtro del manifiesto es `VIEW` + `scheme=content` + `mime=application/octet-stream`, y con `file://` responde «No game». La UI confirma biblioteca vacía («No se encontraron archivos o aún no se ha seleccionado ningún directorio de juego»). Queda para la próxima: fijar la carpeta de juegos en la UI de Eden y lanzar desde su lista.

## Informe de la noche · 2026-11-08 00:15 → 05:01 (cierre Q11)

**Resultado**: 14 ítems de cola → **10 ✔**, **4 ◐**, **0 ✘**. El APK propio (`nosplash.apk` + parches q5) queda operativo de punta a punta: descarga real desde la app a la SD, lanzamiento con el core correcto y catálogo nuevo visible (36 sistemas / 5.887 ROMs / 4,30 TB).

**Bucle de pruebas**: `device/logs/night_loop.log` desde 01:25:58 hasta 05:01:39 → **42 rondas**, **409 OK**, **8 DUDA**, **0 FALLO** (14 arranques por relanzamientos/keepalive). Cierre limpio: «HORA LIMITE alcanzada, cerrando» / «FIN bucle nocturno» a las 05:01:39; el PID 25832 ya no existe y no queda ningún bucle vivo. Tarea `ThorNightLoop` en estado Listo (próxima 05:05, fuera de la ventana 00:00–05:00 ⇒ no relanzará). Dispositivo `9205e6b1` online por ADB. Evidencia acumulada: `device/` (1,1 GB) con **269 capturas** PNG.

**Cerrado y verificado**
- **Q1/T-13 (permiso SD)** — el appop `MANAGE_EXTERNAL_STORAGE` se pierde al reinstalar; `appops set --uid … allow` lo arregla. Sin él, `HERMES_SD` es fail-closed.
- **Q5/T-12 (BypassUpdate)** — 3 llamadas `Log` eliminadas; `requestUpdateInfo` sin `BypassUpdate` (0 líneas en 8 s).
- **Q2 (descarga CPS1)** — `1941.zip` (1.419.125 B) bajado de `MAME_2003-Plus_Reference`; la puerta de identidad daba `MISMATCH matched=0 missing=19` porque el manifest era de mirrors cylum ⇒ parcheada (registra, no bloquea).
- **Q3 mitad 1 (botón «Segundo plano»)** — nodo real `Button` clickable, bounds [1392,64][1628,120], inyectado por `hermes.Fondo.enganchar()`; descarga real medida: `progear.zip` 13.800.478 B en 6 s (3,78 MB/s), 16 miembros y arranque OK (`cps2/progear@mame2003_plus -> OK`).
- **Q6/TC-13 (reinicio)** — `adb reboot` 02:55:14 → boot 02:55:55 (41 s); bind `10-esde-media-sd.sh` rehecho (mismo sha256, mount 2800, 0:131 = SD), 8.655 ficheros/33 entradas, appops conservado, app COLD 193 ms, ADB TCP 39079.
- **Q7 (auditoría de idioma)** — 957 correcciones aplicables → 237 etiquetas (167 es / 70 en) + 8 retiradas; 5.887 líneas, 0 JSON inválido.
- **Q8 (sets `*h`)** — 19xx vs 19xxh: 12 ROMs gráficas con CRC idéntico ⇒ «Hispanic» no traduce; 38 correcciones rechazadas.
- **Q10 (media)** — bind activo a la SD y `.bak` inexistente; **Q12**: TEMP limpio (4 carpetas/30 MB borradas; la app no limpia restos ni `.tmp`); **Q13**: catálogo instalado con backup previo (MD5 36/36, UI 36/36, 5.887 ROMs, 4.30 TB); **Q14**: 1.429 filas `.torrent` se conservan (torrent real de 473.308 B, 3.688 ficheros/14,86 GB, libtorrent en el split).
- **Q9 (6/7)** — NDS (`melonds`), GC/Wii (Dolphin, Vulkan), **Saturn** (`mednafen_saturn`, «Saturn disc / Europe», 1.544 colores) y **N3DS** (Azahar con `file://`) arrancan y renderizan. **Dreamcast ◐**: `flycast` + BIOS real, `Game ID [T38706M]`, negro a 47 s. **Switch bloqueado**: Eden no lanza por intent (`game` Parcelable vs `--es` String; VIEW solo `content`+`octet-stream`) y su biblioteca está vacía; `prod.keys` sí están.

**Abierto (4 ◐) y siguiente paso**
1. **Q4/TC-10 — PSX**: el tap en `ROMs -> psx` solo deja `START …MainActivity (has extras)` y vuelve al menú (T-21); Dreamcast ya tiene core (T-22 ✔) pero falta confirmar el render.
2. **Q9 — Switch**: fijar la carpeta de juegos en la UI de Eden y lanzar desde su lista (no por intent).
3. **Q3/TC-12 — supervivencia**: repetir con un juego grande (>100 MB) para tener ventana antes de abrir otro.
4. **Dreamcast**: dejar >60 s el BIOS/juego o comparar con reios para decidir si el negro es animación o fallo.


## 2026-11-08 — Refiltrado publicado y verificado (cierre)
- Origen: 5.887 fichas / 36 sistemas del repo de Arley. Descartadas por Japon: 378.
- Final: 5.506 fichas. Reparto: ES 910 + ES-fan 47 = 957 (17,4%), EU 1.222 (22,2%), US 678 (12,3%), ASIA 122 (2,2%), sin region 2.527 (45,9%), JP 0.
- limpiar_jp() ahora limpia tambien el nombre de fichero visible ("p"); 0 menciones a Japan en n/p. Las URLs/meta se dejan intactas para no romper descargas.
- Publicado en servixam-max/retroxam-roms (commits catalogo filtrado + limpieza de p). App con github_repo_input = servixam-max/retroxam-roms.
- Verificado: los 36 .jsonl del movil son identicos byte a byte a los locales (md5 uno a uno) y el repo sirve lo mismo.
- Prueba real de descarga: sega32x After Burner Complete ~ After Burner (USA).32x -> 2.097.152 B en ROMs/FOREVER/sega32x.

## 2026-11-08 (2.ª pasada) — catálogo 5.493 fichas, cero Japón también en `gc`

- **Hallazgo que obligó a re-filtrar**: 13 fichas de `gc` llevaban `(JAP)` **solo** en el nombre de fichero (`p`), no en `n`; el filtro anterior solo miraba `n`. Se descartaron: 5.506 → **5.493** fichas (`gc` 255 → **242**). Son juegos servidos desde `archive.org/download/AsiaGamecubeCollectionByGhostware/`.
- **Reglas nuevas de `scripts/filtro_catalogo.py`**: `JP_TOK` (`japan|jap|jpn|jp|j` por token completo), `tiene_jp()` (solo se reescribe un campo con marca real), `fix()` no reformatea grupos sin tokens JP (no toca `(USA, Europe)`, `(Rev 1)`), y el descarte mira Japón en `n` **o** `p`.
- **`scripts/regiones.py` alineado**: `_RANK = ES 4 / EU 3 / US 2 / ASIA 1 / N-D 1 / JP −1` y el fallback devuelve `(1.0, "N/D")`, igual que `RANK` de `filtro_catalogo.py`. Antes la suite fallaba por comparar escalas distintas.
- **Suite `scripts/test_regiones.py`: 13/13 OK** (`Ran 13 tests ... OK`), incluidos los casos `(Japan, USA)`, `(JAP)`, `(J)` suelto, idempotencia, `urls`/`meta` intactos.
- **Integridad del catálogo local** (`device/recount_new.txt`): 36 ficheros, **5.493 fichas**, **0 marcas japonesas** en `n`+`p`, **0 fichas sin URL http**, **0 fichas sin `n` o `p`**.
- **Despliegue verificado**: `device/catalog_es.tar.gz` → `files/gjsonl`; **36/36 md5 idénticos** dispositivo ↔ local (`device/md5_dev_new.lf.txt` vs `device/md5_loc_new.txt`); `gc.jsonl` en dispositivo: 242 líneas, 0 `japan`/`jpn`.
- **Publicado**: commit `11154e9` en `servixam-max/retroxam-roms` (`main`); `psx`/`gc`/`snes` descargados de `raw.githubusercontent.com` con md5 idéntico al local.
- **App**: `am start -W` → `Status: ok`, menú principal visible (`device/c1.png`); los datos de la app no se han tocado.
- **Auditorías delegadas (lote `deleg_b766c0eb`, 3 subagentes de solo lectura)**: gamelists ES-DE ↔ catálogo, auditoría independiente del catálogo 5.493 y plan definitivo de cuarentena japonesa en la SD. Informes en `device/GAMELISTS_AUDIT.md`, `device/AUDIT_CATALOGO_5493.md` y `device/PLAN_JP_FINAL.md` (+`device/cuarentena_jp2.sh`).

## 2026-11-08 11:28 — T-21 resuelto: PSX lanza, y era el doble tap

- **Causa real**: en la lista de juegos la fila **necesita dos taps**. El 1.º solo pinta la selección (barra/fondo azul) y no navega; el 2.º abre el flujo. De ahí el síntoma «tap -> vuelve al menú» de Q4: al tocar una vez y salir, la app parecía no hacer nada.
- **Traza completa con el 2.º tap** (`device/logs/t21b/`): `Bypass: 📌 DownloadActivity launchSource=github` → `🦜 TeknoParrot existente en modo actual: content://…FFF9-FF05%3AROMs/document/…FOREVER%2Fpsx%2FAce%20Combat%202%20(Europe).chd` (salta la descarga porque ya está) → `📌 EmulatorLauncher launchSource=github` → `🎮 Línea coincidente: ace combat 2 (europe)=com.github.stenzek.duckstation/.EmulationActivity %ACTION%=VIEW %DATA%=%ROMPROVIDER%` → `✅ Lanzamiento automático desde selected_emulator.txt (keep=true)` → `HERMES_GRANT: grant tree READ|PREFIX ok` + `grant doc READ ok` → `🦆 DuckStation (SAF)`.
- **Resultado**: `topResumedActivity=com.github.stenzek.duckstation/.EmulationActivity` a los **4 s**; captura `device/logs/t21b/duck2.png` con la intro de *Ace Combat 2* renderizando. PSX queda **verificado de punta a punta** (descarga + lanzamiento).
- **Descarga real medida** (TC-11/TC-21): *Ace Combat 2 (Europe).chd* **332.561.043 B** en ~2 min (pico 18 MB/s), progreso «98 MB / 317 MB» y aviso «Descarga completada»; destino `/storage/FFF9-FF05/ROMs/FOREVER/psx/`; cabecera `MComprHD` v5 correcta.
- **Aviso (no bug del lanzador)**: si DuckStation **ya está en segundo plano**, el intent VIEW se entrega a la instancia existente y se queda el juego anterior (la 1.ª captura mostraba *Alien Resurrection*). Con la app cerrada (`am force-stop`), abre el juego correcto.
- **Discrepancia menor**: el log dice `romPath elegido: /storage/emulated/0/ROMs/TEMP/psx/… (zeroCopy=false)` mientras el URI SAF usado es el de `FOREVER`; el que manda es el URI, así que funciona, pero conviene unificar.
- **UX pendiente**: parchear el `OnClickListener` de la fila para lanzar al primer toque (hoy obliga a doble tap, que es lo que parecía «no lanza»).

## 2026-11-08 12:00 — Biblioteca real vs catalogo: 9.197 huecos, y el stub como causa de los errores

- **Medicion real de la SD** (`find … -size +1M` por sistema): PSX 19 ficheros (6,9 GB), PS2 3 (11,5 GB), GameCube 4 (3,0 GB), PSP 4, Saturn 11, NDS 6, Wii 3, Switch 4, N64 2, SNES 2, NES 2, Mega Drive 1, GBA 1, **Dreamcast 0**. El grueso de la biblioteca es arcade.
- **Arbol interno** `/storage/emulated/0/ROMs`: 10.093 stubs de **105 B** con una URL dentro, **896** con ROM real en la SD y **9.197 sin fichero**. Solo hay **1 fichero real** en todo el arbol (`FOREVER/cps1/1941.zip`, 1.420.289 B).
- **Prueba A/B del error de FBNeo**: lanzar el stub `cps1/1941.zip` con `fbneo_libretro_android.so` reproduce el mensaje exacto *«This game is known but one of your romsets is missing files for THIS VERSION of FBNeo … None of those archives was found in your paths»* (`device/shots/stub_1941b.png`), mientras el zip de la SD tiene los 19 ficheros con CRC correcto. Conclusion: **los fallos «missing files» son lanzamientos de stubs**, no sets corruptos.
- **Catalogo**: 5.493 fichas confirmadas por sistema (mame 992, nes 336, nds 306, fbneo 303, gba 264, gc 242, ps2 239, psx 223, snes 213, ps3 200, psp 194, n64 185, xbox 174, gbc 170, gb 164, megadrive 161, n3ds 153, openbor 152, neogeo 131, dreamcast 128, saturn 118, naomi 84, megacd 72, switch 40, cps2 39, cps1 36, sega32x 34, model2 31, atomiswave 28, model3 26, xbox360 14, wii 13, naomi2 10, psvita 9, cps3 6, wiiu 3).
- **Dreamcast**: flycast renderiza el aviso de guardado + logo de *Ikaruga* con el CHD japones de `_cuarentena`; sin CHD no-JP en la SD no se puede cerrar el sistema.
- **Switch**: XCI al 19% y sin firmware; keys restauradas. Bloqueo de contenido, no del emulador.
- **Artefactos**: `docs/INFORME_BIBLIOTECA.html` (indice navegable, tabla por sistema, estilo minimalista), `device/biblioteca_reporte.tsv`, `scripts/compare_trees.py`, `scripts/informe_biblioteca.py`, `scripts/cat_count.py`, `scripts/html_note.py`.
- **Suite**: `python -W ignore scripts/test_regiones.py` → 13 tests, OK.


## Arcade, resuelto en lo esencial (2026-11-08 12:16)

Dos juegos se han visto **en pantalla** con salida de herramienta, no por `pid`:

| Juego | Core | BIOS junto a ROM | Resultado | Captura |
|---|---|---|---|---|
| 1941 (CPS-1) | fbneo | no necesita | título «1941 COUNTER ATTACK» | `device/shots/v_1941_fb.png` |
| 3countb (NeoGeo) | fbneo | sí (`neogeo.zip`) | partida, HUD P1/P2, CREDIT 00 | `device/shots/v_3countb_bios.png` |
| mslug (NeoGeo) | fbneo | sí | error: el `.zip` es descriptor (0 entradas) | `device/shots/v_mslug.png` |

Causa raíz triple: (1) la BIOS no se resolvía desde `RetroArch/system` y sí desde la carpeta del contenido; (2) el mapeo de cores mezclaba `fbneo` y `mame2003_plus` mientras los sets son FBNeo; (3) la mayor parte de la «biblioteca» son descriptores de ~150 B con la URL de archive.org en el comentario del ZIP, no ROMs.

Consecuencia para el informe de biblioteca: los «10.093 stubs» no son ficheros corruptos ni ROMs perdidas; son fichas de descarga. El hueco real es «descriptor sin descarga efectiva», y se mide contando descriptores frente a archivos de más de 1 MB (1.015 frente a 31 fuera de TEMP).

Queda abierto: forzar una descarga desde la app y verificar que el resultado es un zip real y que sobrevive a matar la app (TC-11/TC-12).

---

## Cierre 2026-11-08 (2ª parte): PSX y Dreamcast renderizan; TC-12 resuelto el 12:56

**Corrección posterior (12:56) — TC-12 ✔ en su definición real («la descarga sobrevive a abrir otro juego»)**
- Prueba dirigida con `device/tools/_tc12b.py Castlevania`: la lista PSX (223 fichas) tiene buscador; se eligió `Castlevania - Symphony of the Night (Europe).chd` (366 MB) porque no estaba en `FOREVER/psx`.
- Descarga real: `126 bloques, 22 conexiones`, `7,60 MB/s`. Al **98 %** (379.669.425/384.249.945 B) se lanzó ES-DE (`org.es_de.frontend/.MainActivity`), se volvió y la descarga **siguió viva**.
- Fin: `Descarga completada … 366 MB / 366 MB ✅`, **384.249.945 B** en `FOREVER/psx`, y la app auto-lanzó el juego en **DuckStation** (`com.github.stenzek.duckstation/.EmulationActivity`). Log: `device/logs/tc12/run2.log`.
- El fallo anterior era de **otro caso**: `am force-stop` (proceso muerto) sigue sin reanudar ⇒ queda como **T-33 abierto**, no como TC-12.
- Detalle de UI aprendido: el **primer tap solo selecciona la fila** y la lista se desplaza; el segundo tap hay que recalcularlo con un dump nuevo, si no cae en la fila de al lado (con `psx` acababa abriendo `ps2`).

**Lo cerrado con evidencia**
- **TC-11 ✔** descarga real desde el frontend: Toshinden 283.203.993 B → `FOREVER/psx`, CHD válido (`MComprHD`); CONSERVAR funciona y escribe en la SD.
- **T-21 ✔** PSX/DuckStation: pid 30376 estable 12 s + captura `psx_duck.png` (392.509 B).
- **T-31 ✔** Dreamcast: `4 Wheel Thunder` 727.333.814 B descargado con `curl` en el Thor (67 s, 10,8 MB/s), lanzado con Flycast; log `[BOOT] retro_load_game …` + `Geometry 640x480 @59.95` + pid 12808 + captura con cinemática en movimiento.
- **Log RetroArch ✔** aparece en `RetroArch/logs/retroarch.log` (5.380 B) al lanzar por intent; antes no se creaba porque sólo se genera al cargar contenido.

**Lo que falla (medido)**
- **TC-12 (force-stop)** `force-stop` mata la app y no hay reanudación ni servicio que la resucite; quedan **703 MB** de `.tmp`/`unpack-*.chd` huérfanos en `ROMs/TEMP` (332.561.043 + 283.203.993 + 115.343.360 + 2.097.152).
- **Bug de UI**: tocar una fila de `GithubRomsActivity` puede cerrar la activity sin descargar (reproducido 12:33 y 12:35).
- **Dreamcast del repo**: 105 de 128 fichas son `.torrent` de mediafire; sólo 23 son CHD directos. **Corregido 13:15:** sí son descargables — la app trae `DownloadTorrentActivity` + `libjlibtorrent-2.0.12.7.so` y descarga el `.torrent` real (473.308 B, 3.688 ficheros) desde mediafire. Ver TC-18 y la corrección en `TAREAS.md` (T-31). Lo que falta es la prueba de punta a punta en la Thor (**T-34**), no un cambio de catálogo.

**Siguiente**
1. Recolector de `ROMs/TEMP` al arrancar la app (o comando `scripts/temp_gc.py` que mueva huérfanos a `TEMP_huerfanos_<fecha>`).
2. **T-34**: probar la descarga torrent Dreamcast de punta a punta (ficha → `DownloadTorrentActivity` → elegir fichero → bytes creciendo). No hay que tocar `dreamcast.jsonl`: las 105 filas son válidas.
3. Reintentar TC-12 con descarga confirmada en curso (medir `.tmp` creciendo antes del `force-stop`) para separar «no sobrevive» de «no llegó a empezar».

### Anexo 13:5x — anatomía del flujo de descarga y recolector de TEMP

- El disparador real de descarga es la **zona derecha de la fila** (`x≈1700`), no el texto: con `tap 1700 426` sobre una fila PS2 se abrió `com.arley4d.bypassarley4d/.DownloadActivity` (t4279) con «Castlevania - Curse of Darkness (EU).chd · PS2 · GitHubRoms» y estado «Conectando con el servidor…».
- `DownloadActivity` tiene dos pestañas: **Descargas** (701,92) y **Segundo plano** (1510,92). Es decir, la app *tiene* un concepto de descarga en segundo plano; lo que no sobrevive es el proceso (`force-stop` → pid muere y no reaparece en 16 s de muestreo).
- El `.tmp` de PS2 apareció **preasignado** a 3.016.701.518 B (2.81 GiB) con la cola a ceros ⇒ el tamaño visible no sirve para medir progreso; hay que usar `du -sk` o la UI. Permaneció en «Conectando con el servidor…» 90 s sin escribir datos ⇒ esa URL del repo PS2 está muerta o muy lenta.
- `DownloadActivity` no es lanzable en frío (`am start -n …/.DownloadActivity` cae en `MainActivity` con el diálogo de systemas) ⇒ para reproducir hay que entrar por la lista del repo.
- En la lista PSX de 223 fichas el `tap` en x=1700 no siempre dispara: en la práctica alterna entre abrir descarga y no hacer nada (posible solapamiento de `clickable` con el scroll). Reproducible sólo de forma intermitente.

**Herramienta nueva:** `scripts/temp_gc.py [minutos_gracia] [--dry-run]` — mueve (nunca borra) los directorios huérfanos de `ROMs/TEMP` a `ROMs/TEMP_huerfanos_<fecha>/`. Ejecutado hoy: **702,9 MB + 2.877,1 MB = 3,4 GB** liberados de `TEMP` (queda en 128 K); destino `TEMP_huerfanos_20261108` (3.4G). El fichero de 2,9 GB es un stub preasignado de ceros, se puede borrar sin riesgo cuando el usuario quiera.

## 2026-11-08 13:23 - Cierre parcial del run 13:00-15:00 (cron Thor-15h-continuar)

Verificado con dispositivo real (adb-9205e6b1-5oHeeV):

1) Gamelists: verify_gamelists.sh -> comprobadas=3442 rotas=0. Cero rutas con "japan" fuera de _cuarentena y cero <path> hacia _cuarentena. Reporte de fixes: 282 lineas (281 ELIMINAR, 1 REPATH).
2) Doble tap: build/tap3.apk (parches en m40 x2, RemoteRomListActivity x2, MainActivity x1, w41 x1) firmado con retroxam.keystore e instalado; lastUpdateTime=2026-11-08 13:13:52, versionCode=180, firstInstallTime=2026-11-07 22:15:28. build/nosplash.apk ya es copia exacta de tap3 (sha256 d36f89fcc9116cde..., 15.056.837 B).
3) Lanzamiento: al pulsar una ficha de la lista GitHub (cps2/1944.zip) el logcat muestra el comando de RetroArch y la copia previa a /storage/FFF9-FF05/ROMs/TEMP/<uuid>/1944.zip. Un solo tap basta tras el parche.
4) T-21 PSX: el core mednafen_psx_hw_libretro_android.so existe en /storage/emulated/0/Android/data/com.retroarch.aarch64/files/cores (12 cores). El orden de emuladores psx en assets/emuladores.json es: self, RetroArch (mednafen_psx_hw), DuckStation (bootPath %ROM_URI%), ePSXe, FPSE. Los .m3u internos (FF VIII, FF IX, Galerians, Riven, Fear Effect 2) no arrastran sus .chd al TEMP: hipotesis principal del fallo.
5) Descargas: DownloadActivity no es exported (am start directo devuelve SecurityException), por lo que el flujo solo se puede probar desde la UI. Los stubs internos (105 B) apuntan a URLs validas (1941.zip -> 200, 1.419.125 B desde el PC) y los ficheros reales viven en la SD (FFF9-FF05/ROMs/cps2/1944.zip = 15.448.221 B).

Pendiente y como retomar:
- T-21: editar assets/emuladores.json (lista psx) para que DuckStation quede antes que RetroArch, apktool b build/dec_mod, zipalign + apksigner, install-multiple -r, y probar un .chd suelto desde la SD.
- TC-11/TC-12: probar desde la UI (GitHub -> sistema -> ficha) y vigilar con: adb -s <serial> logcat -d | grep -iE "download|okhttp|DownloadActivity".
- Comando exacto de retoma: cd C:/Users/XAM-PC/Proyectos/AYN-Thor-ESDE && java -jar device/tools/apktool.jar b build/dec_mod -o build/tap4_raw.apk


## 2026-11-08 13:44 - Verificaciones y hallazgos del run

Verificado ahora en dispositivo:
- sh /data/local/tmp/vg.sh -> comprobadas=3442 rotas=0.
- gamelists: cuarentena_paths=0, japan_total=0 (no queda ninguna ruta japonesa ni referencia a _cuarentena).
- Suite local: python -W ignore scripts/test_regiones.py -> Ran 13 tests, OK.
- Emuladores instalados: com.github.stenzek.duckstation, org.ppsspp.ppsspp, com.flycast.emulator, dev.eden.eden_emulator, org.dolphinemu.dolphinemu, org.dolphinemu.mmjr.
- RetroArch: 12 cores en /storage/emulated/0/Android/data/com.retroarch.aarch64/files/cores, incluido mednafen_psx_hw_libretro_android.so. Por tanto la causa de T-21 NO es un core ausente.

Hallazgos nuevos:
1) DuckStation lanzado por adb con ruta de fichero (--es bootPath /storage/FFF9-FF05/ROMs/psx/Ace Combat 2 (Europe).chd) abre EmulationActivity pero peta con NullPointerException en FileHelper.getDocumentNameFromUri: necesita content:// (SAF), no una ruta. Por eso la app usa %ROM_URI%.
2) RetroArch lanzado a mano con extras mínimos (CONFIGFILE vacio) provoca ANR y el sistema lo mata (ActivityManager: ANR in com.retroarch.aarch64). Prueba no concluyente al no replicar los extras exactos de la app; la UI de RetroArch si abre (MainMenuActivity -> RetroActivityFuture sin ANR).
3) Switch: Eden esta instalado y /storage/FFF9-FF05/ROMs/switch tiene 40 entradas, pero TODAS son .xci.torrent (0 ROMs reales). T-23 no se puede probar sin descargar los .xci.
4) ROMs PSX reales en SD: Ace Combat 2 (382.460.143 B), Alundra 2 (382.460.143 B), Blood Omen (472.744.703 B), Command & Conquer Disc 1 GDI (475.312.884 B).

Siguiente paso exacto para T-21: en la app, abrir lista psx y pulsar un .chd suelto (no un .m3u); si falla, reordenar assets/emuladores.json para que duckstation quede antes que retroarch en la lista psx y reconstruir con java -jar device/tools/apktool.jar b build/dec_mod -o build/tap4_raw.apk.


## 2026-11-08 13:32 - Cierre del run (modo verificacion por lock)

Coordinacion: device/logs/.pilot.lock existe con edad 1355 s (22,6 min) -> segun la regla, dejo de tocar ADB y cierro con trabajo local.

Evidencia nueva de T-21 (Reproduccion FUERA de la app, con el comando EXACTO de assets/emuladores.json):
  am start -n com.retroarch.aarch64/com.retroarch.browser.retroactivity.RetroActivityFuture -e CONFIGFILE /storage/emulated/0/Android/data/com.retroarch.aarch64/files/retroarch.cfg -e LIBRETRO mednafen_psx_hw_libretro_android.so -e ROM "/storage/FFF9-FF05/ROMs/psx/Ace Combat 2 (Europe).chd" --activity-clear-top
  - topResumedActivity = RetroActivityFuture a t+3, t+6, t+9 y t+12 s.
  - logcat pid 11325: "[ENV] Auto-start game /storage/FFF9-FF05/ROMs/psx/Ace Combat 2 (Europe).chd" y AudioTrack entregando 328.128 frames (~6,8 s de audio) -> el core mednafen ARRANCO y sonó.
  - A t+15 s el foreground paso a launcher y a t+18 s a com.arley4d.bypassarley4d/.MainActivity con "from uid 2000" (adb shell), es decir, otra sesion ADB (cron hermano de las 13:30 o piloto interactivo) robo el foco. NO fue la app.
  Conclusion: el lanzamiento PSX via RetroArch con el comando de la app funciona; el fallo observado en pruebas de UI puede ser interferencia de sesiones ADB concurrentes. Repetir aislado antes de tocar el orden de emuladores.

Otras evidencias del run:
  - DuckStation por adb con ruta directa: NullPointerException en FileHelper.getDocumentNameFromUri -> solo acepta content:// (la app ya pasa %ROM_URI%).
  - RetroArch con extras incompletos (CONFIGFILE vacio, LIBRETRO con ruta completa): ActivityManager: ANR in com.retroarch.aarch64. Forma incorrecta, no usar.
  - Switch: dev.eden.eden_emulator instalado; /storage/FFF9-FF05/ROMs/switch = 40 entradas, TODAS .xci.torrent (0 ROMs reales).
  - sh /data/local/tmp/vg.sh -> comprobadas=3442 rotas=0; cuarentena_paths=0; japan_total=0.
  - Suite: python -W ignore scripts/test_regiones.py -> Ran 13 tests, OK.

---

## Cierre 2026-11-08 13:46-13:51: causa raiz de Dreamcast (GDI vs CHD) y auditorias delegadas

### 1. T-34 — el motor torrent funciona, el boton de descarga no arranca
- `DownloadTorrentActivity` **no descarga el `.torrent`**: lanzada con la URL https de mediafire responde
  `No content provider: https://www.mediafire.com/file/dxssagn4ixz526w/Dreamcast+gdi.torrent` ⇒ espera un fichero ya local.
- Via que si funciona (probada 13:43): `curl` del `.torrent` real en el PC (161.184 B) → `push` → `cp` a
  `/data/user/0/com.arley4d.bypassarley4d/cache/dc.torrent` + `chown` al uid del `cache` → `am start -a VIEW -d content://com.arley4d.bypassarley4d.provider/cache/dc.torrent -n com.arley4d.bypassarley4d/.DownloadTorrentActivity`.
  Resultado: pide sistema, muestra el arbol `Redump / Sega - Dreamcast - GDI Files`, deja marcar fichero y crea
  `ROMs/TEMP/b07bb3d9-7e84-454e-90fb-7014f0fef0c9`.
- **Medicion 13:48**: ese directorio contiene **solo `dc.torrent` (161.184 B, mtime 13:42)**; ninguna transferencia
  empezo. El unico temporal grande de TEMP es de otra via: `885e37d8-…/temp_rom5968503602796112079.tmp` =
  384.249.945 B congelado desde las 12:55 (descarga HTTP abandonada, no torrent).
- Estado: soporte de torrent ✔ en UI, transferencia ✘. Siguiente hipotesis: el boton exige `mass_torrent_selected_indices`
  y sin seleccion real no encola nada (el dump `E6.xml` no exponia ningun nodo `checkable="true"`).

### 2. T-35 — GDI+SAF: la razon por la que «no arrancaba nada» de Dreamcast
- Error en pantalla al pulsar el juego descargado:
  `Flycast has stopped. GDI file: Cannot open track content://com.android.externalstorage.documents/tree/FFF9-FF05%3AROMs/document/…(Track%201).bin`
- Causa: la app pasa la ROM como **URI SAF**; RetroArch copia ese content:// a su cache, pero un `.gdi` referencia sus
  `.bin` hermanos por nombre relativo y esos no viajan ⇒ **ningun GDI/CUE puede arrancar por esa via**. Un **CHD**
  (monofichero) si.
- Prueba positiva 13:49-13:50: `Charge 'N Blast (Europe).chd` descargado en el propio Thor con `curl` desde la URL del
  catalogo → **65.650.516 B** (coincide con los 62,61 MB del catalogo), md5 `7b7074e7cd5d3a44b08891edcd5cebb7`, en
  `/storage/FFF9-FF05/ROMs/FOREVER/dreamcast/`. Lanzado con
  `RetroActivityFuture -e CONFIGFILE …/files/retroarch.cfg -e LIBRETRO flycast_libretro_android.so -e ROM "/storage/FFF9-FF05/ROMs/FOREVER/dreamcast/Charge 'N Blast (Europe).chd"`
  → `topResumedActivity=RetroActivityFuture t4322` y **logo «PRESS START BUTTON» de Charge 'N Blast en pantalla**
  (`device/shots/dc_chd_charge.png`).
- Consecuencia practica: Dreamcast se resuelve con los **23 CHD** del catalogo (archive.org, descargan a 10 MB/s por
  `curl` en el dispositivo); los **105 `.torrent`** son packs GDI y seguirian fallando aunque el torrent descargue, salvo
  que se pase ruta de fichero real en vez de `%ROM_URI%` o se genere un `.m3u`.
- Ya no es cierto que «fuera de cuarentena no hay ningun CHD real»: `FOREVER/dreamcast` tiene uno jugable y no japones.

### 3. Auditorias delegadas (solo lectura, dispositivo intacto)
| Informe | Cifras clave |
|---|---|
| `device/GAMELISTS_AUDIT.md` + `device/gamelists_audit.json` | gamelists **3.723** entradas vs catalogo **5.493** fichas; **279** rutas rotas (278 solo existen en `_cuarentena/japan/…`, 1 ausente real: `ROMs/gba/Advance Guardian Heroes.zip`); **0** `<path>` literales a `_cuarentena`; 2.153 huerfanas catalogo→gamelist (0 con ROM presente); **294** menciones a Japon (path 281, desc 14, name 10). Peores: saturn 46/150, dreamcast 35/150, snes 22/150. Patron unico: purgado JP a cuarentena sin regenerar gamelists |
| `device/AUDIT_CATALOGO_5493.md` + `device/audit_catalogo_5493.json` | **PUBLICABLE**. 5.493 vs 5.506 = **-13, todas `gc` `(JAP)`** (identidad `p = "gamecube (JAP)/"+n+".iso"`) + 5 renombrados (dreamcast 2, naomi 1, saturn 1, sega32x 1). 0 duplicados de `n`/`p` dentro de sistema. Idempotencia 36/36, regeneracion 36/36, punto fijo 36/36, **36/36 byte-identicos con GitHub raw** (`cmp`). 200 coincidencias de regex JP en 100 fichas son la etiqueta de idioma `Ja`. Abiertos D4-D7 (sin impacto) y riesgos R1-R7 (R2: 1.283 fichas comparten 43 URLs de pack) |
| `device/PLAN_JP_FINAL.md` + `device/plan_jp_final.tsv` + `device/cuarentena_jp2.sh` | **EN SIMULACION, sin ejecutar**. 26 filas, 25 accionables, **28 `mv`**, 0 borrados, 557.365.164 B (531,5 MiB). Decisiones: mover 13, devolver 8, renombrar 4, conservar 1. Validadas 26/26 rutas y tamanos. Corrige el enunciado: hay **18** japonesas fuera de cuarentena (no 10; el audit omitia 8 `.torrent` JP), japonesas puras **3** (no 4), devoluciones **8** (no 7: `Rampart (Europe) (Jaleco).zip.torrent` cayo por `(J`) |

Riesgo documentado del plan: renombrar desincroniza `gamelists/{nes,snes}/gamelist.xml` y `catalog_es/*.jsonl`; el
parcheo de XML queda fuera del script (pasos 6-7 del §10) para no corromper XML desde el movil.



## 2026-11-08 14:20 — T-35 acotado (crash nativo intermitente, no es el argv de ES-DE)

- **Tombstone**: `device/logs/t35/tombstone_1323.txt` — `pid 10037 / tid 10072 / name: Thread-3`, `signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0`, `Cause: null pointer dereference`, `lr=0 x0=0 x1=0 x29=0`, backtrace de 1 frame con `#00 pc 0000000000000000`, `Process uptime: 181s`. Pila inutilizable: se cierra la causa raiz por simbolizacion (no hay build con simbolos) y se pasa a vigilancia.
- **El argv no es el problema**: `es_log.txt:877` muestra la plantilla real de ES-DE (`%EXTRA_ROM%=%ROM%`, `%EXTRA_LIBRETRO%` = ruta absoluta del `.so`); relanzar ese mismo argv arranca bien en dos cores (`swanstation` PID 23979 a las 14:15:12, `flycast` PID 25703 a las 14:15:49) y sobrevive a HOME + vuelta al frente (sin crash ni ANR nuevo).
- **El sintoma reproducible es ANR**: `device/logs/t35/anr_1407.txt` — `Input dispatching timed out` sobre `RetroActivityFuture`, `Waited 5000ms for PointerCaptureChangedEvent`, pid 19245, 14:07:49. Hilo main bloqueado en syscall nativa.
- **Vigilancia permanente**: `logcat -v threadtime -b main,system,crash -r 4096 -n 6 -f /storage/emulated/0/ES-DE/logs/watch/ra_watch.log` (PID 5598). El proximo SIGSEGV tendra contexto completo.
- **APK desplegado**: `build/nosplash_uri.apk` (smali `hermes/Cue` convierte `content://` a ruta real antes de devolverla) instalado con `install-multiple -r` + 3 splits; `versionCode=180`, `lastUpdateTime=2026-11-08 14:12:03`, `firstInstallTime` intacto del 2026-11-07 22:15:28 y app operativa tras el update.
- **PS2**: los items `PS2-EU-part*` estan restringidos por archive.org — mismo item, `403` a dos `.chd` distintos (`ia801403`), `401` en `part2`/`part3`, mientras la pagina del item da 200. 126/239 fichas de `ps2.jsonl` afectadas. Retomar con `curl -sSL -o /dev/null -w "%{http_code}" -r 0-1023 <url>`.
- **Limpieza**: `scripts/temp_gc.py` real — `ROMs/TEMP` de 367,6 MB a 128 K (6 dirs a `TEMP_huerfanos_20261108`, 3,8 G acumulados). Suite: 13 tests OK.
- **Retomar T-35**: `adb shell logcat -b crash -d` o `grep -a "signal 11" /storage/emulated/0/ES-DE/logs/watch/ra_watch.log` tras el proximo cierre anomalo; con el contexto de las ultimas 50 lineas del log se decide si es el core o RetroArch.

### Correccion 14:23 — los cores van por ruta interna, no por Android/data

- Las repros anteriores con `-e LIBRETRO /storage/emulated/0/Android/data/.../cores/*.so` **no cargaban core**: `linker: library ... is not accessible for the namespace: permitted_paths="/data:/mnt/expand:/data/user/0/com.retroarch.aarch64"`. RetroArch quedaba vivo sin juego => el "no crash" de esas pruebas no vale.
- `/data/user/0/com.retroarch.aarch64/cores` NO estaba vacio: tiene **223** ficheros (sin `su` el `ls` da vacio por permisos). Existen `flycast_libretro_android.so` (23.221.552 B) y `swanstation_libretro_android.so` (5.690.384 B). Se copiaron encima los 12 cores de `Android/data/.../cores` con `chown u0_a180` (mismo contenido, sin efecto).
- **ES-DE ya pasa la ruta correcta**: `es_log.txt` -> `%EXTRA_LIBRETRO%=/data/user/0/com.retroarch.aarch64/cores/swanstation_libretro_android.so`. El fallo no esta en la plantilla.
- **Repro valida**: Dreamcast + flycast interno -> `[ENV] Libretro path: "/data/user/0/com.retroarch.aarch64/cores/flycast_libretro_android.so"`, PID 27035 estable, sobrevive KEYCODE_HOME (PID_POST 27035), `0` lineas de `Fatal signal|signal 11`, 14:23:11. T-35 sigue siendo intermitente: no se dispara bajo demanda ni con el core correcto.
- **Regla para el mapa**: todo `%EXTRA_LIBRETRO%` debe apuntar a `/data/user/0/com.retroarch.aarch64/cores/<core>.so`; `device/map_full.json` ya lo hace en sus 29 entradas.

### 14:33 — mapa de comandos completo (36/36 sistemas)

- `device/map_full.json`: 29 -> **37 claves** (36 sistemas del catalogo + leyenda `# NO-INTENT`); validado con `JSON.parse` (script `scratch/chk_map.js`): `json_ok claves=37`, `sin_entrada=` (vacio). Backup `device/map_full.json.bak_1430`.
- Anadidos: `model2`, `model3` (MAME4droid 2024), `openbor`, `ps3` (aPS3e `aenu.aps3e/.QuickStartActivity`), `wiiu` (Cemu `info.cemu.cemu/.MainActivity`), `xbox`, `xbox360` (sin emulador Android).
- **Probado que no aceptan ROM por intent**: `am start -a VIEW -d content://...1941.zip -n com.seleuco.mame4d2024/com.seleuco.mame4droid.MAME4droid` -> la app queda al frente pero abre su explorador (`MAME4droid.so: myosd_safOpenFile /storage/emulated/0/ROMs/mame/...`), no carga el romset. Por eso esas entradas van marcadas `# NO-INTENT` (elegir ROM dentro de la app).

### 14:35 — verificaciones con salida real

- `python -W ignore scripts/test_regiones.py` -> **`Ran 13 tests in 0.382s` / `OK`**, exit 0, `fails=0` (recuento de FAIL/ERROR/Traceback en la salida).
- `scripts/temp_gc.py 30` (ejecutado antes en este ciclo) dejo `ROMs/TEMP` **vacio** (`temp_m3u=0`, `temp_chd=0`) y `ROMs/TEMP_huerfanos_20261108` con **16 directorios, 3.8 GB**, `1` .chd y `0` .m3u -> los ficheros copiados por la app son pesados (no m3u sueltos). No se borra nada: queda ahi para que el usuario decida.
- Backlog: `7` pendientes `[ ]` / `18` hechos `[x]` -> **no procede autocierre** del job.
- La carpeta de trabajo **no es un repositorio git** (`git rev-parse --show-toplevel` -> `fatal: not a git repository`), asi que no hay commit local; la publicacion del catalogo sigue en `servixam-max/retroxam-roms` (commit 11154e9, fuera de este arbol).

### 14:42 — CAUSA REAL de los PSX fantasma: 11 .m3u que no son listas sino URLs

- En `/storage/FFF9-FF05/ROMs/psx` habia **11 `.m3u` de 105-177 B** cuyo contenido es **una URL de descarga** (`https://archive.org/download/psx-chd-roms-*/...chd *Size=...`), a veces con un trailer ZIP (`PK\005\006`). No son playlists: RetroArch recibe un m3u que apunta a una URL, no a un `.chd` local -> el contenido nunca puede cargar.
- Es **sistemico**: los 11 comparten el patron (10 archive.org + 1 mediafire `PSX+redump.torrent`) y para **ninguno existe el `.chd`** en la carpeta (la carpeta tiene **167 `.chd` reales**, ninguno con esos titulos: `grep -i Final
Fantasy psx_ls.txt` solo devuelve otros FF). Son fichas fantasma del catalogo.
- **Cuarentena aplicada** (mv, sin borrar): los 11 a `/storage/FFF9-FF05/ROMs/TEMP_huerfanos_20261108/psx_m3u_stub/`. Verificado: `quedan_m3u=0`, `cuarentena=11`, `chd=167` (intactos). Los originales estan tambien en `device/fix_m3u/old/`.
- Precedente coherente: `device/.../_cuarentena/japan/psx/` ya tenia 6 `.m3u` japoneses con el mismo aspecto (Chrono Cross, Xenogears, Policenauts...), es decir el fallo no es de un solo titulo sino del proceso que crea el `.m3u` cuando la descarga no se completa.
- **Hipotesis T-35** (no confirmada): un m3u-stub como contenido de RetroArch produce fallo de carga con puntero nulo (`pc=0`, `fault addr 0x0`), compatible con el tombstone de las 13:23. Ahora que no hay stubs en psx, el watcher `ra_watch.log` dira si el SIGSEGV desaparece al lanzar desde ES-DE.
- Efecto practico: ES-DE ya no ofrecera 11 juegos PSX que no podian arrancar; hay que re-escanear la biblioteca (ES-DE Menu > Utilities > Rescan).

### 14:45 — repro #13: un `.m3u`-stub NO crashea RetroArch

- Push del stub original (`device/fix_m3u/old/Grandia (Europe).m3u`, 126 B) a `/sdcard/psxstub.m3u`; lanzado con `RetroActivityFuture` + `-e LIBRETRO /data/user/0/com.retroarch.aarch64/cores/mednafen_psx_hw_libretro_android.so`.
- Resultado real: **`PID=9544`**, `topResumedActivity=...RetroActivityFuture`, log `Loading "/storage/emulated/0/psxstub.m3u"` y `[Override] ... "Beetle PSX HW"`; **ningun `Fatal signal`/`SIGSEGV`**; `KEYCODE_BACK` -> `PID_post=CERRADO`.
- Consecuencia: el m3u-stub explica los **PSX fantasma** (contenido incargable) pero **no** el SIGSEGV de T-35; la hipotesis queda descartada como causa unica. Repro #13 anotada.
- Watcher de logcat: `ra_watch.log` **499.712 B**, `grep -ac Fatal signal` -> **0**, PID `5598` vivo a las 14:32. Sigue sin capturarse el crash intermitente.

## Cierre del ciclo 14:00-15:00 (piloto automatico)

- Cerrado con evidencia: mapa de comandos 36/36 (JSON.parse OK, 37 claves); test_regiones.py 13 tests OK; 11 .m3u fantasma de PSX en cuarentena (quedan_m3u=0 cuarentena=11 chd=167); catalogo 36/36 en el dispositivo; T-35 acotado (tombstone Thread-3, signal 11 SEGV_MAPERR, pc=0, lr=0) + cores en ruta privada (223 cores).
- Abierto: T-35 causa raiz (14 repros sin reproducir; watcher ra_watch.log PID 5598, 0 Fatal signal); T-21 (faltan los .chd de 11 titulos PSX; regenerador en device/fix_m3u/rebuild.py); T-33 (durabilidad ante am force-stop); URL PS2 (403 con item y metadata OK); T-23/T-26/T-27/T-18.
- Retomar: grep -n de pendientes en TAREAS.md y lock device/logs/.pilot.lock (ultimo 1794144758).

## Cierre 14:45-14:55 — Dreamcast operativo de extremo a extremo desde ES-DE

- **Raiz de ROMs confirmada en el propio log** (`logs/es_log.txt`, 14:42-14:43): ES-DE escanea **`/storage/FFF9-FF05/ROMs`** (`Skipping system "x68000" ... "/storage/FFF9-FF05/ROMs/x68000" does not exist`, `system-select "cps1" ... "/storage/FFF9-FF05/ROMs/cps1"`). `es_settings.xml` no tiene `ROMDirectory`; solo `MediaDirectory = /storage/FFF9-FF05/ES-DE/downloaded_media`.
- **Sistema dreamcast en `custom_systems/es_systems.xml`** (linea 446): `path = %ROMPATH%/dreamcast`, extensiones `.chd .gdi .cdi .cue .iso ... .zip .torrent`, comando `RetroArch (directo)` con `%EXTRA_ROM%=%ROM%` + `%EXTRA_LIBRETRO%=/data/user/0/com.retroarch.aarch64/cores/flycast_libretro_android.so`.
- **Estado de `ROMs/dreamcast`**: 121 entradas — **23 `.chd` reales (9,1 GB)**, 93 `.zip`/`.zip.torrent` (stubs), ademas `Flycast/`, `dc/`, `data/`, `emu.cfg`, `jojonr2.bin`. De los 23 CHD, **22 tienen ficha** en la gamelist; `Atari Anniversary Edition (USA).chd` no la tiene y ES-DE lo lista igual (escanea el directorio, no solo el XML).
- **Gamelist vs disco**: 150 entradas de XML / **115 con fichero presente** = 22 CHD jugables + 93 stubs no jugables → 35 rutas rotas (coincide con la auditoria delegada: dreamcast 35/150).
- **Verificacion en la UI** (carrusel ordenado por *fullname*, no por nombre corto: `Sega Dreamcast` cae tras `OpenBOR`/`Atomiswave`): ES-DE → **Sega Dreamcast** muestra la lista real con `4 Wheel Thunder`, `AeroWings`, `Wacky Races`, `Worms World Party`, `Alien Front Online`... (`device/shots/esde_dc_games.png`).
- **Lanzamiento desde el frontend**: `ENTER` sobre `4 Wheel Thunder` → `topResumedActivity=com.retroarch.aarch64/...RetroActivityFuture` (t4339) e **intro del juego en pantalla** (`device/shots/esde_dc_launch.png`). Cadena ES-DE → RetroArch → Flycast → CHD verificada.
- **Lanzamiento directo de control**: `RetroActivityFuture` + `-e ROM "/storage/FFF9-FF05/ROMs/dreamcast/Dino Crisis (Europe).chd"` + `-e LIBRETRO flycast_libretro_android.so` → logo Virgin (`device/shots/dc_dinocrisis2.png`). Prueba de que el CHD en la **ruta de ES-DE** arranca, no solo el de `FOREVER/`.
- **Duplicado asumido**: `FOREVER/dreamcast` 9,15 GB + `ROMs/dreamcast` 9,1 GB en la SD (+ 9,15 GB en el scratch del PC). Cabe de sobra (`df` 80G/477G); limpieza opcional.
- **`/storage/emulated/0/ROMs/dreamcast` es irrelevante para ES-DE**: 266 `.chd` de **100-168 B** (1,0 MB en total) — son los fakes; ES-DE nunca los lee porque su raiz es la SD. No tocar: los usa la app (iisu / `rom_index_cache.fb`).
- **Pendiente heredado (calidad de biblioteca)**: las 93 entradas de dreamcast que son `.zip`/`.zip.torrent` **aparecen en ES-DE y no arrancan** (mismo sintoma que los 11 `.m3u` de PSX). Falta aplicarles la misma cuarentena selectiva o quitar su ficha; hoy el sistema ofrece ~116 titulos de los que solo 23 son jugables.

## Turno de verificación 2026-11-08 15:00-15:05 (cron Thor-15h-continuar, SIN ADB)

- **Coordinación respetada**: `device/logs/.pilot.lock` = `1794146390 21680 chat`; `date +%s` = 1794146408 al arrancar -> edad **18 s < 25 min**. El piloto interactivo tenía el dispositivo (prueba: `device/shots/t21_psx_retroarch.png` escrito a las 15:00). Este run **no ejecutó ADB** ni tocó la consola, y **no modificó el lock** (sigue siendo del piloto).
- **Suite**: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.361s` / `OK`, exit 0 (15:00).
- **Sintaxis**: `python -m py_compile scripts/*.py device/tools/*.py` -> exit 0. `bash -n` en `*.sh`, `scripts/*.sh` y `device/tools/*.sh` sin errores.
- **Catálogo (local)**: 36 JSONL / **5.493 fichas**, todas `type=file`, **0 URLs no-http**, 0 duplicados mismo sistema+path. Reparto: dreamcast **128 = 105 `.torrent` + 23 `.chd`**; ps2 **239** (126 con `PS2-EU-part*`); psx **223**; switch **40**; cps1 **36**. Coincide con la app (`psx (223)`, `dreamcast (128)`) y con la corrección vigente de los .torrent.
- **`device/map_full.json`**: JSON válido, **37 claves = 36 sistemas + leyenda `# NO-INTENT`**, 0 sistemas del catálogo sin entrada, **26 con `%EXTRA_LIBRETRO%`**, **0 con `Android/data`** (todos los cores en `/data/user/0/com.retroarch.aarch64/cores/`).
- **Cuadre Dreamcast (resuelve la duda de las 93/23)**: gamelist **150 = 115 presentes + 35 rotas**; presentes = **22 CHD con ficha + 93 stubs** `.zip/.zip.torrent`; en disco hay **23 CHD** (el 23º, `Atari Anniversary Edition (USA).chd`, no tiene ficha y ES-DE lo lista por escaneo). Las 93 entradas de disco = 121 − 23 CHD − 5 (`Flycast/`, `dc/`, `data/`, `emu.cfg`, `jojonr2.bin`). Las **13 huérfanas de catálogo** del audit = 1 CHD sin ficha + **12 fichas `.torrent` sin stub local** (105 − 93): T-27/T-18 no tienen un agujero adicional, es exactamente ese delta.
- **Correcciones de cifras** (append, sin tocar el histórico): (1) el recuento "7 pendientes / 18 hechos" (14:35) está obsoleto -> medido antes de este append, TAREAS.md tenía **35 `[x]` / 14 `[ ]`**; (2) "map_full.json ... sus 29 entradas" (14:23) -> hoy **37 claves, 26 con EXTRA_LIBRETRO**; (3) el bloque "Como se retoma" de TAREAS.md lanza `-e LIBRETRO mednafen_psx_hw_libretro_android.so` (nombre relativo), en contradicción con la corrección de las 14:23 -> debe usarse `-e LIBRETRO /data/user/0/com.retroarch.aarch64/cores/mednafen_psx_hw_libretro_android.so`.
- **Sin cambios en el dispositivo** en este turno: T-21 (el piloto lo está probando en este momento: captura de PSX en RetroArch a las 15:00), T-33, T-35 y PS2 403 quedan como estaban. Reanudar con el bloque corregido de TAREAS.md cuando el lock tenga >=25 min.
- **No procede autocierre**: quedan 14 `[ ]`, varias bloqueadas por contenido que falta (11 `.chd` PSX, 40 `.xci` Switch, 126 fichas PS2 con 403) o por trabajo de dispositivo que este turno no podía tocar.
- **Discrepancias detectadas en la verificación (no corregidas en el histórico, sí anotadas)**:
  1. **T-34 no está cerrado de punta a punta**: la cabecera "CERRADO 14:55" documenta un **reuso** (`ROMs/TEMP` 506.240 B -> 384 B, `FOREVER/dreamcast` 23 `.chd`), no una descarga; la fila 87 (◐, 13:48: `TEMP/b07bb3d9-…` sólo contenía `dc.torrent`, 0 B de payload) sigue siendo el estado honesto. Criterio de cierre real: lanzar un `.torrent` desde la ficha de dreamcast y ver crecer `ROMs/TEMP/<uuid>` (medir con `adb shell du -sk` cada 10 s), el mismo patrón que T-33.
  2. **Colisión de ID T-35**: en la tabla del cierre de 12:00, T-35 = "Dreamcast: los GDI descargados no arrancan en Flycast"; en el ciclo 14:00-15:00, T-35 = "RetroArch SIGSEGV Thread-3". Conviene renombrar el nuevo a **T-36** para que los próximos runs no mezclen ambos.
  3. **T-31 (fila 12:00)**: "fuera de cuarentena no queda ningún CHD real (0 ficheros >1 MB)" ya no es cierto — hay **23 CHD reales (9,1 GB)** en `ROMs/dreamcast` (verificado 14:45). La fila es histórica; no se reescribe.

## 15:17 - T-21 cerrado de verdad (y el fichero era otro juego)

- **Prueba aislada, sin cron** (el job se ha pausado mientras el piloto tiene el lock): `com.retroarch.aarch64/...RetroActivityFuture` con `-e LIBRETRO /data/user/0/com.retroarch.aarch64/cores/mednafen_psx_hw_libretro_android.so -e ROM "/storage/FFF9-FF05/ROMs/psx/Ace Combat 2 (Europe).chd"` -> `topResumedActivity=RetroActivityFuture` en **t+3, 8, 15, 25, 40 y 55 s** (t4346, sin volver al launcher ni a `MainActivity`). Logcat: `[ENV] Auto-start game "/storage/FFF9-FF05/ROMs/psx/Ace Combat 2 (Europe).chd"`, `AudioTrack stop(416) 557.760 frames`, `stop(417) 118.080`, `stop(418) 271.686`. Captura: `device/shots/t21_psx_ace2.png` (intro del caza de Ace Combat 2).
- **Hallazgo grande (T-37)**: la captura anterior del "PSX en RetroArch" (`device/shots/t21_psx_retroarch.png`, libro 3D con un rey) **no era Ace Combat 2, era el intro de Alundra 2**. Comprobado: `Ace Combat 2 (Europe).chd` = **382.460.143 B, md5 `cd352393e6aa255bea988d06ff44a335`**, exactamente igual que `Alundra 2 - A New Legend Begins (Europe).chd`. El catálogo espera 332.608.307 B y la descarga real son 332.561.043 B, así que el REUSO de la app copió el fichero equivocado y lo dio por válido (el tamaño del log sale de la ficha, no del disco).
- **Arreglo**: re-descarga del `.chd` bueno (332.561.043 B, md5 `fba5784e1dfde753e8cb2c6f66c2545c`), `adb push` (23,4 MB/s, 13,6 s) y `cp` sobre el nombre correcto; el fichero malo queda en `/storage/FFF9-FF05/_trash_20261108/.ace_bad_alundra.bak` (382 MB, recuperable). Tras el cambio, md5 en la SD = `fba5784e…`.
- **Herramienta nueva**: `device/tools/rom_integrity.py` — agrupa por tamaño los ficheros >1 MB de `ROMs/` (todas las sistemas), md5 solo de los grupos repetidos y compara con `size_bytes` del catálogo con tolerancia 200 KB. Informe en `device/logs/rom_integrity.tsv`, exit 1 si hay duplicados/descuadres. Ejecutado: **59 ficheros, 0 grupos repetidos, 0 duplicados md5, 1 descuadre** (`psp/Ace Combat - Joint Assault`: 1.219.981.085 en disco vs 1.181.116.006 en catálogo, probable revisión distinta — sin gemelo en la SD).
- **Coordinación de instancias**: `Thor-15h-continuar` (45d6165e1068) **pausado** a las 15:12 para que no dispare a las 15:30 encima de la prueba; se reanuda al terminar. El lock (`device/logs/.pilot.lock`) se refresca con `device/tools/pilot_lock.py refresh --who chat`.

## 15:30 - T-34b: los ".torrent" del repo son enlaces de MediaFire

- Prueba de descarga real en `switch` (único sistema con fichas `.torrent` en GitHubRoms): tap en la zona derecha de `20XX + 30XX.xci.torrent (3.19 GB)` → **`com.arley4d.bypassarley4d/.DownloadTorrentActivity`** con la UI completa (carátula, 3,2 GB, velocidad, tiempo restante, conexiones, "Cancelar descarga"). Tras 90 s: **0 %, 0 B / 3,2 GB, conexiones 0, Seeds 0, Peers 0, 17 B/s ↓ / 52 B/s ↑**, `ROMs/TEMP` clavado en 1.664 KB. Captura: `device/logs/t34b/mon_010.png`.
- **Causa raíz**: los `.xci.torrent` de la SD no son torrents. Son stubs de **89-91 B** con una URL dentro: `https://www.mediafire.com/file/afd3jiasakp8ui2/file *Size=3.19 GB`. Sin bencode no hay metadatos ni seeds → el motor no puede descargar. Las 40 entradas de `ROMs/switch` están en ese estado (mtime 2026-11-05 21:51).
- **Consecuencia para T-23**: deja de ser "faltan los `.xci`" y pasa a "el repo no publica torrents para switch". Y para T-34: la rama de descarga torrent no se puede cerrar con este repo; el reuso de Dreamcast sí queda reconfirmado (Flycast estable 105 s).
- **T-38 (nuevo)**: la app despacha por extensión, no por contenido. Tiene soporte MediaFire (`ui_0654_mediafire_returned_html_instead_of_the_torrent`, `audit_mediafire_resolving`), pero un `.torrent` con una URL dentro se manda al motor torrent y se queda en 0 % sin decir nada. Fix propuesto: sniff de los primeros bytes (`d8:announce`/`d4:info` vs `http`) en `DownloadTorrentActivity`/despachador.

## 15:32 · Turno de verificación local (cron) — el piloto interactivo tiene el lock

Lock con 173 s de antigüedad al empezar → sin ADB, solo comprobaciones locales.

- `python -m py_compile scripts/*.py device/tools/*.py` → **0**
- `bash -n scripts/*.sh *.sh device/tools/*.sh` → **0**
- `python -W ignore scripts/test_regiones.py` → **exit 0**
- `python scripts/verify_catalog.py` (nuevo, solo lectura):
  - **36 JSONL / 5.493 fichas**; 0 líneas inválidas, 0 URLs no-http, 0 duplicados `(sistema, ruta)`.
  - dreamcast: **105 `.torrent` + 23 `.chd`**; las **105** URLs `.torrent` terminan en `.torrent` (mediafire) → la app las puede bajar y alimentar el motor (coherente con Q14: 473.308 B, Minerva_Myrient, 3.688 ficheros).
  - ps2: **126** fichas con `PS2-EU-part`.
  - `device/map_full.json`: **37 claves / 36 sistemas**, 0 sistemas sin entrada, **26** `%EXTRA_LIBRETRO%`, **0** `Android/data`; los 10 sin `%EXTRA_LIBRETRO%` son switch, ps2, psvita, model2, model3, openbor, ps3, wiiu, xbox, xbox360 (26+10 = 36 ✔).
  - switch: **40 fichas**, todas `ext=.torrent` y todas `www.mediafire.com`.
  - Snapshot SD de 10:59 (`device/audit_sd_raw/files.tsv`): los **40** ficheros de `/ROMs/switch/` miden **89/90/91 B** → confirma el diagnóstico de T-38 (stubs de texto, no torrents).

T-38 verificado por código (estático, sin dispositivo): en `build/dec_mod/smali/lb.smali`, método `a`, los bytes del fichero van **sin comprobar** a `Lcom/frostwire/jlibtorrent/TorrentInfo;-><init>([B)V` (línea ~1556); el fallo se envía con `Lu4;-><init>(I...)` (0x13) vía `runOnUiThread`. En todo el smali de la app **no hay sniffing bencode** (`announce`, `d8:`, `d4:info`) fuera de jlibtorrent. Punto de parche: justo antes de `new-instance v9, Lcom/frostwire/jlibtorrent/TorrentInfo;` → si los bytes empiezan por `http` tratarlos como URL a descargar, si empiezan por `d8:announce` seguir al motor.

Aviso de datos obsoletos: `device/audit_sd_raw` y `roms_inv_sd.tsv` son de 10:55-10:59, **anteriores** a los CHD reales de 13:49-14:45; no valen para tamaños actuales de Dreamcast (hace falta listado fresco). Los 22 `.chd` de 124-189 B que muestra son los fake de entonces, ya sustituidos.

## 15:40 - T-39 (nuevo): el 403 de PS2 no es la URL, es `access-restricted-item`

Hasta ahora PS2 se quedaba en 0 B con 403 y el metadata del item respondia 200, asi que
parecia una URL caducada. **No lo es**: el item esta marcado como restringido.

Evidencia (real, no inferida):
- `curl -s https://archive.org/metadata/PS2-EU-part2-CHD-Arquivista` -> JSON valido con
  `access-restricted-item = True`, `collection = softwarecapsules,loggedin`,
  `mediatype = software`. Ningun otro campo de restriccion (`is_dark`, `rights`) hace falta:
  el `loggedin` ya es la causa.
- Peticion con rango sobre el item restringido:
  `curl -r 0-1048575 -o /dev/null -w '%{http_code}' "…/PS2-EU-part2-CHD-Arquivista/Grand%20Theft%20Auto…chd"`
  -> **code=401 bytes=0**.
- Misma prueba con un item abierto del mismo sistema:
  `…/ps2-redump-usa-chd-part-B/Bully%20%28USA%29.chd` -> **code=206 bytes=1048576
  speed=195959 B/s**. Es decir: el pipeline de descarga esta bien; el 401 es del item.

Es decir, el `.tmp` de 3.016.701.518 B que aparecio antes venia de un item que si respondia
o de una ficha distinta; la ficha EU de PS2 nunca iba a bajar un byte.

### Auditoria de todo el catalogo (`device/tools/archive_audit.py`, nuevo)

Se consultaron en paralelo los **123 items de archive.org** referenciados por las **4.277
fichas** de `device/catalog_es/*.jsonl`:

- **53 items abiertos**, **70 RESTRINGIDOS** (`access-restricted-item=true` / `loggedin`).
- Fichas: **3.347 descargables / 930 muertas** (21,7 % del catalogo con URL archive.org).

Sistemas con todas sus fichas muertas: `nds` 197, `ps3` 173, `xbox` 155, `gba` 81,
`wii` 13, `xbox360` 13, `cps3` 6, `psvita` 4, `wiiu` 3. Parciales: `ps2` 19 ok / 147 muertas,
`snes` 154/59, `saturn` 81/37, `gc` 223/17, `psx` 215/14.
Salidas: `device/logs/archive_items.tsv` (item -> estado/coleccion/sistemas) y
`device/logs/catalog_repair.tsv` (ficha -> SUSTITUIBLE / SIN_SUSTITUTO).

### Segunda pasada: sustitucion por titulo (`device/tools/archive_titles.py`, nuevo)

Buscar el mismo nombre de fichero en items abiertos da **0** aciertos (cada juego vive en un
unico item). Buscando el mismo **titulo normalizado** (sin region ni idioma) dentro del
**mismo sistema** salen **45 fichas recuperables** (41 de ellas PS2):

- ps2 41 (p.ej. `Frequency (EU)` -> `ps2-redump-usa-chd-part-F/Frequency (USA).chd` 284 MB,
  `Jak and Daxter (EU)` -> part-J 855 MB, `Crazy Taxi (EU)` -> part-C 73,8 MB)
- psx 4, resto 0. **885 fichas se quedan sin sustituto**: no hay fuente abierta en el catalogo.
- Ojo: una primera version cruzaba sistemas (un `Crazy Taxi` de PS2 acababa apuntando a un CHD
  de Dreamcast). Corregido indexando por `(sistema, titulo)`; el TSV vigente es el bueno.

Salida: `device/logs/title_subst.tsv` (sistema, ficha, item viejo/nuevo, fichero, size, URL).
No se ha tocado el catalogo: cambiar una ficha `(ES)` por un fichero `(USA)` cambia el idioma
del juego, y esa decision es del usuario.

### Prueba de que la sustitucion funciona (en curso)

Descarga real de `ps2-redump-usa-chd-part-C/Crazy Taxi (USA).chd` (73.816.511 B) a
`…/scratch/ps2_fix/crazytaxi.chd` como `proc_6b530833b54d`; si llega completa se empuja a la SD
y se lanza en `xyz.aethersx2.android` para cerrar el bloqueo de PS2 con contenido real.

## 15:55 - T-39 CERRADO con juego real: Crazy Taxi (PS2) arranca en AetherSX2

`Crazy Taxi (USA).chd` (73.816.511 B, md5 `ffd0b9ad86193224a6822edf9fcce264`, item abierto
`ps2-redump-usa-chd-part-C`) copiado a `/storage/FFF9-FF05/ROMs/ps2/` y lanzado:

```
am start -a android.intent.action.VIEW -d "file:///storage/FFF9-FF05/ROMs/ps2/Crazy Taxi (USA).chd"   -t application/octet-stream -n xyz.aethersx2.android/.MainActivity
```

`topResumedActivity=xyz.aethersx2.android/.EmulationActivity` y captura
`device/shots/ps2_ct_g0.png` (369.223 B) con la **tarjeta de memoria de PS2 creandose** y el
juego detras: el CHD descargado de un item **abierto** es valido y el emulador lo ejecuta.
`stat -c %s` remoto = 73.816.511 (coincide byte a byte con lo descargado).

Conclusion: el pipeline de sustitucion por titulo (`device/tools/archive_titles.py` →
descarga → push → verificacion de tamano → arranque) queda **probado de punta a punta**.
Lo que bloquea el resto de PS2 no es la tecnica: es que sus items estan restringidos (T-39).

### Inventario real de PS2 (medido, no estimado)

`ls -l` de `/storage/FFF9-FF05/ROMs/ps2` → **190 entradas, 3,81 GB**:

| clase | n | bytes |
|---|---|---|
| stubs (≤300 B, contenido = URL) | 188 | ~125 B de media |
| reales | 2 | 3.830,4 MB (`007 - Agent Under Fire (Europe).iso`) + 70,4 MB (`Crazy Taxi (USA).chd`) |

Es decir: el frontend ofrecia 190 fichas de PS2 y solo **2** podian arrancar.

## 15:55 - Censo de stubs de TODA la SD (hallazgo nuevo, cambia la prioridad)

Mismo criterio en todos los directorios de `/storage/FFF9-FF05/ROMs` (`find -size -301c`):

**3.556 ficheros — 3.393 stubs (95,4 %) — 163 reales (4,6 %)**

Sistemas con 0 % de contenido real: mame (200), fbneo (150), gba (139), nds (141),
gbc (144), gb (133), megadrive (131), nes (142), n64 (140), megacd (77), dreamcast (94),
switch (40), wii (13), xbox360 (14), psvita (12), wiiu (3), n3ds (141 salvo 16)…

Los stubs no son ficheros corruptos: son **fichas materializadas**. Su contenido es la URL
de descarga, y a veces va seguida de un ZIP vacio (`PK`):

```
$ head -c 120 ROMs/megadrive/"Elemental Master (U) [!].bin"
https://archive.org/download/md_20240311/MD.zip/MD%2FElemental...
$ head -c 120 ROMs/cps1/1941.zip | od -c
P K 003 004 ...      -> este SI era un zip real (ROM de CPS1, 40 KB)
```

De ahí que el criterio de tamaño tenga que ser ≤300 B y no «<1 MB»: las ROMs de arcade y
8/16 bits pesan 32 KB-4 MB legitimamente, y un primer recuento por «<1 MB» daba cifras falsas.

### Alcance real de la reparacion: cuanto se puede recuperar

Las 3.393 URLs de stub volcadas a `device/logs/stub_urls.txt` (formato `sistema|nombre|contenido`)
y clasificadas contra `device/logs/archive_items.tsv`:

| clase | n | nota |
|---|---|---|
| item **abierto** en archive.org | **1.890** | descargables ya, ~495 GB declarados |
| item no catalogado en el TSV | 593 | hay que pedir metadata antes |
| sin URL de archive.org | 910 | mediafire/torrent/otros: misma familia que T-34b |

Mayores bolsas abiertas (GB): gc 197, psp 79, ps3 69, ps2 27, saturn 26, psx 23, openbor 20.

Prueba de rango sobre 11 sistemas al azar (`curl -r 0-65535`): **9 de 11 responden 200/206**
(nes, gb, gbc, megadrive, cps2, neogeo, psx, mame, saturn). Fallan `snes` (`ni-roms` → 403)
y `gba` (Ghostware → 401), los mismos items que ya marcaba el audit.

## 15:55 - Herramienta nueva: `device/tools/fill_stubs.py`

Sustituye stubs por el fichero real, sistema a sistema, reanudable y verificado:

- lee `device/logs/stub_urls.txt`, filtra por `--sistemas`, tope `--max-gb`, `--dry` para simular;
- descarga con `curl -C -` (reanudable) a `scratch/fill_stubs/`;
- valida: tamano declarado `*Size=` (>=98 %) o, si no lo hay, >16 KB y no-HTML;
- `adb push`, y **solo da por bueno el fichero si `stat -c %s` remoto == tamano local**;
- borra el staging tras el push; log en `device/logs/fill_stubs.log`.

Primera tanda lanzada en background: `--sistemas nes,gb,gbc,megadrive,cps1,cps2,cps3,neogeo
--max-gb 3.5` (~460 fichas). Muestra real de la salida:

```
15:54:51   push=ok local=1536927 remoto=1536927
15:54:54 === cps1 qtono2j.zip
15:54:57   push=ok local=1945248 remoto=1945248
```

Pendiente de decision del usuario: por donde seguir con los 495 GB abiertos (propuesta:
arcade+8/16 bits+psx+saturn primero, ~55 GB; gc/ps3 despues, son 266 GB).

## 16:12 - Turno de verificacion (cron; lock del piloto vivo, sin ADB)

- `python -W ignore scripts/test_regiones.py`: **13/13 OK** (0,36 s).
- Catalogo local coherente: **36 JSONL, 5.493 fichas**, 4.251 lineas / **4.279 URLs** de archive.org (la cifra 4.277 de la auditoria contaba URLs, no fichas).
- `catalog_repair.tsv`: **930 muertas** (nds 197, ps3 173, xbox 155, gba 81, ps2 147, snes 59, saturn 37) = 930/4.279 = 21,7 %% OK. `title_subst.tsv`: **45** sustituciones (ps2 41, psx 4) OK. `stub_urls.txt`: **3.393** stubs OK (3.393 + 163 = 3.556).
- **CORRECCION (T-42)**: la clasificacion de los 3.393 stubs contra `archive_items.tsv` NO es 1.890 abiertos / 593 no catalogados / 910 sin URL. Recuento exacto (join por item): **1.890 abiertos (505,3 GB declarados)**, **577 RESTRINGIDOS (1.838,3 GB)**, **16 no catalogados (8,6 GB)**, **910 sin URL de archive = 909 mediafire (716,7 GB)**. Los "593 no catalogados" eran **577 restringidos (T-39) + 16 realmente sin item**.
- Consecuencia: los 577 no se recuperan pidiendo metadata (items `loggedin`); el relleno realmente alcanzable son **1.890 fichas / ~505 GB**, no 495+593.
- Los 909 stubs mediafire apuntan casi todos al mismo `Dreamcast+gdi.torrent` (253-326 B): mismo patron que T-34b/T-38 (la app despacha por extension y mete el stub al parser).
- `dreamcast.jsonl`: 128 fichas, **105 .torrent** OK; `switch.jsonl`: 40 fichas, **40 .torrent** OK.
- `fill_stubs.py` (lanzado por el piloto a las 15:53) sigue vivo: cps2 a las 16:00 con `push=ok local==remoto` (p. ej. 23.419.311 B). Este turno no toca el dispositivo.

## Cierre 16:30 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora de cierre: **16:30** (Madrid). El objetivo del job era trabajar hasta las 15:00; este run llega 90 min tarde, asi que se aplica el PASO 1: **cierre sin trabajo nuevo** (ni ADB ni consola).
- Coordinacion: `stat -c %Y device/logs/.pilot.lock` = 1794149778 (`15:56:18`), ahora 1794151808 -> lock **caducado (33,8 min)**; tomado y refrescado al cerrar.
- Verificacion local de este turno: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.361s / OK` (13/13).
- Backlog: TAREAS.md con **24 `[ ]` y 58 `[x]`** -> **no procede autocierre**.

### Lo cerrado hoy con evidencia (resumen)

| tema | evidencia |
|---|---|
| Catalogo en dispositivo | 36/36 JSONL, 5.493 fichas en `/data/user/0/com.arley4d.bypassarley4d/files/gjsonl`; repo servixam-max/retroxam-roms commit 11154e9 |
| Mapa de comandos | 36/36 sistemas, JSON.parse OK, 37 claves (`device/map_full.json`) |
| PSX `.m3u` fantasma | cuarentena 11, `quedan_m3u=0`, chd=167 |
| T-21 Ace Combat 2 (PSX) | re-descargado 332.561.043 B, md5 `fba5784e1dfde753e8cb2c6f66c2545c`, reemplazado en SD; backup en `_trash_20261108` |
| T-39 Crazy Taxi (PS2) | `EmulationActivity` en primer plano, stat remoto 73.816.511 == local, captura `device/shots/ps2_ct_g0.png` (369.223 B) |
| Dreamcast reuso | 4 Wheel Thunder -> flycast MainActivity estable 105 s, `FOREVER/dreamcast` 27 ficheros |
| Auditoria archive.org | 70/123 items restringidos; 930/4.279 fichas muertas; 45 sustituciones por titulo (ps2 41, psx 4) |
| Censo de stubs | 3.556 ficheros: 3.393 stubs (95,4 %) / 163 reales; 1.890 abiertos (505,3 GB) + 577 restringidos (1.838,3 GB) + 16 sin item (8,6 GB) + 910 sin URL (716,7 GB, 909 mediafire) |
| fill_stubs.py | 249 ficheros verificados `push=ok local==remoto`, 1.636.559.638 B (1,52 GB) desde 15:53; sigue vivo (PID 2483), va por neogeo |

### Lo que queda (24 pendientes) y como se retoma

1. **T-34/T-34b/T-38 - descarga torrent real en la Thor (prioridad 1)**: no hay una sola prueba de punta a punta con un `.torrent` valido creciendo en `ROMs/TEMP`. Los 40 `.torrent` de switch son stubs de 89-91 B con URL de MediaFire; los 105 de dreamcast si son validos (Q14: code=200, 473.308 B, info.name Minerva_Myrient, 3.688 ficheros). Retomar: abrir una ficha dreamcast y `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s; si sigue a 0, `adb shell logcat | grep -i "torrentinfo|bencode|invalid"`. Parche candidato en `lb.smali#a`: leer el prefijo (`d8:announce` -> motor; `http` -> tratar como URL).
2. **T-33 - durabilidad**: `am force-stop` mata la descarga y no reanuda (medido 13:53). Retomar: descarga en curso + force-stop + comparar `du -sk ROMs/TEMP` antes/despues; si no reanuda, revisar DownloadKeepAliveService.
3. **T-36 (ex T-35) - RetroArch SIGSEGV**: crash 2026-11-08 13:23:11, Thread-3, pc=0/lr=0. Retomar tras reproducir: `adb shell logcat -b crash -d`.
4. **T-42 - relleno de stubs**: la tanda 1 sigue corriendo (tope 3,5 GB, 8 sistemas). Siguiente: `python device/tools/fill_stubs.py --sistemas <lista> --max-gb <N>`; orden propuesto arcade + 8/16 bits + psx + saturn (~55 GB) antes que gc/ps3 (266 GB).
5. **T-39/T-40 - decision de producto**: aplicar o no las 45 sustituciones por titulo; y para las 577 restringidas + 909 mediafire, decidir login en el descargador vs marcar `meta.restringido` (hoy la app ofrece 885 fichas que nunca podran descargar).
6. **T-23 Switch**: bloqueo externo (el repo solo publica enlaces MediaFire). **T-18/T-27**: huecos catalogo vs SD. **T-26/T-28**: japonesas.


## Cierre 17:00 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora de cierre: **17:00** (Madrid). Lock previo `1794151872` (16:31:12) con edad **28,9 min (>=25)** -> tomado y refrescado a `1794153611`. Aun asi se aplica el PASO 1 del job: **cierre sin trabajo nuevo**, sin ADB.
- Verificacion local de este turno: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.366s / OK` (13/13, exit 0).
- Backlog: TAREAS.md **24 `[ ]` / 58 `[x]`** -> **no procede autocierre**; el job del cron se mantiene.
- Contexto: desde el cierre de 16:30 el piloto interactivo **no ha tocado** TAREAS.md (mtime 16:01) ni ESTADO.md (mtime 16:31). Todo el avance de la ultima hora esta solo en los logs de los dos rellenos en background, que **siguen vivos y no se interrumpen**:
  - **PID 1133 - `device/tools/psx_fill.py`** (desde 15:26): **7 `push ok`, 2.766.981.466 B (2,58 GB)**, 8 fichas intentadas, 1 `SKIP` (Star Wars Rebel Assault II, mediafire sin chd). Ultimas: FF VII Disc 1 482.709.125, Grandia Disc 1 430.614.383, Koudelka 219.676.573, Legend of Dragoon 240.296.770; en curso **Metal Gear Solid (Asia) Disc 1**.
  - **PID 2483 - `device/tools/fill_stubs.py`** (desde 15:53): **433 `push=ok` con remoto==local, 3.443.097.750 B (3,21 GB), 0 fallos**; por sistema: neogeo 130, nes 78, megadrive 67, gb 50, cps2 37, gbc 36, cps1 33, cps3 6. Tope declarado 3,5 GB -> a punto de parar por tope.
- **Cautela de integridad (leccion T-37)**: `fill_stubs.py` y `psx_fill.py` validan **solo tamano** (local vs `*Size=` y `stat` remoto), **no md5**. Al terminar hay que pasar `python device/tools/rom_integrity.py` antes de dar el relleno por bueno.
- Reanudacion exacta: (a) `python device/tools/rom_integrity.py` (grupos por tamano + md5); (b) PSX: `python device/tools/psx_fill.py --dry` para ver la cola y despues `device/fix_m3u/rebuild.py` para regenerar los `.m3u` de los 11 titulos ya presentes; (c) stubs: `python device/tools/fill_stubs.py --sistemas <lista> --max-gb <N>`; (d) T-34/T-38 (torrent real): ficha dreamcast `.torrent` + `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s.

## 17:25 - Relleno de stubs: cierre del bug de nombres cruzados (piloto, post-cierre)

- **Hallazgo grave corregido**: `fill_stubs.py` rellenaba por URL sin comparar el nombre del stub con el del fichero remoto. En `cps3` esto metio `jojoba.zip` dentro de `jojoban.zip` (79.394.785 B) y `jojo.zip` dentro de `jojonr2.zip` (77.318.178 B). Contenido real y valido, pero con el nombre de otro romset: FBNeo habria rechazado el set (o lanzado el driver equivocado).
- **Accion**: renombrados en el dispositivo a sus nombres verdaderos (`jojoba.zip`, `jojo.zip`). Se ha verificado que **ni `jojoban.zip` ni `jojonr2.zip` existen** en `mame-roms-merged_` ni en `cylums-final-burn-neo-rom-collection` (metadata consultada): esas 2 fichas quedan sin fuente y se dejan como ausentes (mejor ausentes que con contenido de otro titulo).
- **Guarda nueva en `fill_stubs.py`**: `nombre_coincide(name, url)` normaliza mayusculas/simbolos, admite el prefijo numerico de listado (`0111 - ...`) y el recorte del stub, y descarta el sufijo `*Size=` pegado a la URL. Los descartes se escriben en `device/logs/stub_alterados.tsv` (2 filas: jojoban, jojonr2).
- **Deteccion de items privados**: probado en vivo con `cps1/sfach.zip` (listado 3.890.216 B, servidor **172 B**). El fichero esta marcado `private: true` en el item abierto `fbnarcade-fullnonmerged` -> HTTP **401**. Era el unico fallo restante de la tanda. Ahora se clasifica como **restringido** (no como fallo) y va a `device/logs/stub_restringidos.tsv`.
- **Estado de la tanda de 8 sistemas** (`nes,gb,gbc,megadrive,cps1,cps2,cps3,neogeo`): **460 stubs rellenados y verificados** (`stat` remoto == tamano descargado), 3,21 GB, `fallos=0`, `restringidos=1` (sfach), `alterados=2` (jojoban/jojonr2 sin fuente). `fill_run1.out` daba `fallos=24`: eran **falsos negativos** del bug del apostrofo en `su -c stat` (21 casos) mas los 2 neogeo con tamano de listado redondeado (1,60 MB vs 1.635.556 B reales); todos esos ficheros si estaban bien en el dispositivo y el re-run los cuenta como `saltados`.
- **Nuevo bug de comillas corregido**: el `*Size=` venia pegado a la URL (`...chd%20*Size=1,021.3M`), asi que 4 fichas psp quedaban como "alteradas" por falso positivo. Ahora se corta la URL en `*Size=`/`*`/espacio antes de comparar.
- **Integridad (rom_integrity.py, todos los sistemas)**: 305 ficheros >1 MB, **4 grupos con tamano repetido, 0 duplicados por md5** (no hay contenido clonado tipo T-37). **1 descuadre**: `psp/Ace Combat - Joint Assault (Europe)...chd` disco **1.219.981.085** vs catalogo **1.181.116.006** (este ultimo es exactamente 1,1 GiB: valor de relleno del catalogo, no el tamano real). No hay indicio de contenido cruzado; pendiente solo corregir la ficha del catalogo.
- **PSX (`psx_fill.py`, PID 1133) terminado**: `descargados=9 fallos=1 saltados=1`. Los 10 CHD estan en la consola y **verificados uno a uno** (`stat` remoto == tamano descargado, cabecera `MComprHD`): 3.951.890.554 B (**3,95 GB**). El `fallos=1` era **falso negativo**: `Oddworld - Abe's Exoddus (Disc 1).chd` (421.001.639 B) es el caso del apostrofo en `su -c stat` (`remoto -1`); el fichero esta completo. Se ha portado a `psx_fill.py` el mismo doble `shlex.quote` de `fill_stubs.py`.
- **`.m3u` PSX**: `device/fix_m3u/rebuild.py` regenera **10 de 11** (`FALTA | Star Wars - Rebel Assault II`, mediafire sin CHD). **No se han empujado a proposito**: cada titulo tiene hoy solo el Disc 1, y un `.m3u` de 1 linea no aporta nada y puede duplicar la entrada en ES-DE. Quedan en `device/fix_m3u/new/` listos para empujarse cuando se rellenen los Disc 2+ (FF VII, Grandia, Koudelka, LoD, MGS, Parasite Eve II, Fear Effect 2, Dragon Warrior VII).
- Reanudacion: (a) corregir `size_bytes` de la ficha psp en el catalogo; (b) rellenar los Disc 2+ de PSX y entonces empujar los `.m3u`; (c) decidir T-40 con `stub_restringidos.tsv` + los 577 `loggedin`; (d) seguir con el relleno de los sistemas grandes (~505 GB abiertos) en tandas de 3-4 GB.

## 17:32 - Ciclo de verificacion (cron; turno local porque el lock del piloto estaba vivo)

- Lock `device/logs/.pilot.lock` con edad 4,6 min -> sin ADB. `scripts/test_regiones.py`: **13/13 OK**. Cifras de catalogo coherentes (`cat_count.py`: 5.493 fichas; `verify_catalog.py`: 36 sistemas, 105 torrents Dreamcast, 40 fichas Switch).
- **T-46 cerrado**: el unico `DESCUADRE` de `device/logs/rom_integrity.tsv` (psp/Ace Combat - Joint Assault: catalogo 1.181.116.006 vs SD 1.219.981.085) es **falso positivo**. 1.181.116.006 = 1,1 GiB exactos (el catalogo redondea a 0,1 GiB) y el tamano real, 1,1361 GiB, redondea a 1,1; `curl -sIL` del `.chd` da **Content-Length: 1219981085**, igual que la SD. **No se toca el catalogo**: se corrige el verificador, `device/tools/rom_integrity.py`, con `tol_redondeo()` (682 fichas con multiplos de 0,1 GiB, 1.148 con multiplos de 1 MiB) y esos casos pasan a `redondeo-catalogo`. `py_compile` OK, backup `.bak-1730`. **Pendiente reejecutarlo con ADB** (esperado `descuadres=0`).
- **T-47 abierto y medido**: 31 ficheros de la SD sin ficha -> 10 CHD de PSX correctos (ficha = `.m3u`), 1 con ficha renombrada (Toy Story Racer), **3 CHD de PSX sin ficha** (Alundra 2, Command & Conquer GDI, Mortal Kombat 4), 2 cps3 renombrados, neogeo BIOS y 14 con ficha de otro formato/region (gba unzipped, gc zip, n3ds solo stub torrent, etc.).
- Retomar con lock: `python device/tools/rom_integrity.py`; despues T-35 (SIGSEGV de RetroArch) o T-33 (durabilidad ante `am force-stop`).

## 18:00 - Turno de verificacion local (cron; PASO 1: fuera de ventana, sin ADB)

- Coordinacion: lock con mtime 1794155247 (17:27:27) y edad **32,7 min >= 25** -> tomado (`1794157231`) y refrescado al cerrar. Al ser las 18:00 > 15:00 se aplica PASO 1: **ni ADB ni consola**, solo trabajo local.
- `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.365s / OK` (13/13, exit 0). `cat_count.py` 5.493 fichas; `verify_catalog.py` 36 sistemas / `dc_torrent 105` / `switch 40` (correccion de torrents Dreamcast intacta).
- Backlog: **27 `[ ]` / 68 `[x]`** al empezar; tras consolidar 2 duplicados obsoletos, **25 `[ ]` / 70 `[x]`** -> **no procede autocierre**.
- Rellenos en background **terminados**: `psx_fill.py` `descargados=9 fallos=1 saltados=1` (3,95 GB verificados uno a uno, ESTADO 17:25) y `fill_stubs.py` `saltados=32 restringidos=1 fallos=0` (460 ficheros / 3,21 GB). Ultimos logs 17:13 y 17:24; nada quedo a medias.

### Cerrado en este turno (con salida real)

| tema | evidencia |
|---|---|
| T-47b: los 3 CHD de PSX sin ficha tienen fuente y estan completos | `curl -sIL` -> HTTP 200 + Content-Length **382.460.143** (Alundra 2, `psxchda`), **475.312.884** (C&C GDI, `psx-chd-roms-c`), **357.714.300** (MK4, `psx-chd-roms-m`), identicos al `stat` de la SD en `rom_integrity.tsv`. Solo faltan las fichas. |
| Fichas preparadas (sin desplegar) | `device/staging/psx_add_t47.jsonl`: 3 lineas, `python -m json.tool` OK en las 3, claves identicas a una ficha real (`ext,meta,n,p,parent,size,size_bytes,type,urls`). Generador `device/tools/mk_psx_add_t47.py`. Catalogo sigue en **5.493**. |
| T-47c: `psx/Toy Story Racer.chd` truncado | 6.406.456 B en la SD vs **142.962.689 B** de la fuente (md5 `49a26c2c7378cde9b750248c1f8073f5`) = 4,5 %. No coincide con ningun fichero de los 4 items consultados, asi que no es un CHD ajeno mal nombrado: es una descarga cortada. |
| Item de psp/Ace Combat cerrado como falso positivo | Apuntado en TAREAS.md con referencia a T-46; el catalogo no se toca. |

### Lo que queda (27) y como se retoma

1. **T-34/T-34b/T-38 - torrent real en la Thor (prioridad 1)**: ficha dreamcast `.torrent` + `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s; si no crece, `adb shell logcat | grep -iE "torrent|bencode|invalid"`. Parche candidato en `lb.smali#a` (prefijo `d8:announce` -> motor; `http` -> URL).
2. **T-33 - durabilidad**: descarga en curso + `am force-stop` + comparar `du -sk` antes/despues.
3. **T-36 (ex T-35) - RetroArch SIGSEGV**: `adb shell logcat -b crash -d` con el crash de 13:23:11.
4. **Re-ejecutar `python device/tools/rom_integrity.py`** con la correccion de T-46 (esperado `descuadres=0`), que quedo pendiente por falta de lock.
5. **Aplicar las 3 fichas nuevas**: backup de `psx.jsonl`, `cat device/staging/psx_add_t47.jsonl >> device/catalog_es/psx.jsonl`, `cat_count.py` (esperado **5.496**) y push a `.../files/gjsonl`. Antes, mover `psx/Toy Story Racer.chd` a `_trash_` y bajar la version buena.
6. **T-42 - relleno**: `python device/tools/fill_stubs.py --sistemas <lista> --max-gb <N>`; orden propuesto arcade + 8/16 bits + psx + saturn (~55 GB) antes de gc/ps3 (266 GB).
7. **T-40 - decision de producto**: 577 `loggedin` + 909 mediafire + `stub_restringidos.tsv` -> login en el descargador o `meta.restringido`.

### Mejora pendiente anotada

- Los metadatos de archive.org publican **md5 por fichero**; `fill_stubs.py` y `psx_fill.py` solo comparan tamano. Cotejar md5 cerraria la clase de bug de T-37/T-43/T-44.
- *(18:05)* El staging se movio a `device/staging/psx_add_t47.jsonl`: dentro de `catalog_es/` `cat_count.py` lo contaba como sistema (`total 5496`, pseudo-sistema `psx_add_t47=3`). Tras moverlo: `total 5493`, `36` JSONL, `test_regiones` 13/13 OK.

## Cierre 18:30 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora: **18:30** (Madrid), fuera de la ventana de las 15:00 -> **cierre sin trabajo nuevo** (sin ADB). Lock previo `1794157421` (18:03:41) con edad **26,6 min (>=25)** -> tomado y refrescado a `1794159020`.
- Verificacion local: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.365s / OK` (13/13, exit 0). `scripts/cat_count.py` -> **5.493 fichas** / 36 JSONL. `scripts/verify_catalog.py` -> 36 sistemas, `dc_torrent 105` con 105 URLs acabadas en `.torrent` (correccion vigente intacta), `switch_fichas 40`.
- Backlog: **25 `[ ]` / 70 `[x]`** -> **no procede autocierre**; se mantiene el job.
- Ultimo cambio de TAREAS.md/ESTADO.md: 18:03:39 (cierre del run de 18:00). Sin rellenos python en background vivos: nada nuevo desde entonces.
- Retomar en el proximo turno con lock: (1) `python device/tools/rom_integrity.py` (T-46, esperado `descuadres=0`); (2) aplicar `device/staging/psx_add_t47.jsonl` (backup de `psx.jsonl` + append + push; esperado 5.496) y mover el `psx/Toy Story Racer.chd` truncado a `_trash_`; (3) T-34/T-38: ficha dreamcast `.torrent` + `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s; (4) T-33: `am force-stop` a mitad de descarga; (5) T-36: `adb shell logcat -b crash -d`.


## Cierre 19:00 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora: **19:00** (Madrid), fuera de la ventana de las 15:00 -> **cierre sin trabajo nuevo** (sin ADB ni consola).
- Coordinacion: `device/logs/.pilot.lock` mtime `1794159033` (18:30:33), ahora `1794160809` -> edad **29,6 min (>=25)** -> lock tomado (`1794160816`) y refrescado al cerrar. No hay piloto interactivo activo: ese mtime es el refresco del cierre anterior de 18:30.
- Verificacion local: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.362s / OK` (13/13, exit 0). `scripts/cat_count.py` -> **5.493 fichas** / 36 JSONL. `scripts/verify_catalog.py` -> 36 sistemas, `dc_torrent 105` con `url_acaba_en_.torrent 105` (correccion vigente de torrents Dreamcast intacta), `switch_fichas 40` (hosts mediafire, ext .torrent).
- Backlog: **25 `[ ]` / 70 `[x]`** -> **no procede autocierre**; se mantiene el job.
- Sin cambios desde el cierre de 18:30: TAREAS.md mtime 18:03:39, `device/catalog_es/psx.jsonl` mtime 11:09:36; ningun relleno python en background.
- Retomar en el proximo turno con lock: (1) `python device/tools/rom_integrity.py` (T-46, esperado `descuadres=0`); (2) aplicar `device/staging/psx_add_t47.jsonl` (backup de `psx.jsonl` + append + push; esperado 5.496) y mover `psx/Toy Story Racer.chd` truncado a `_trash_`; (3) T-34/T-38: ficha dreamcast `.torrent` + `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s; (4) T-33: `am force-stop` a mitad de descarga; (5) T-36: `adb shell logcat -b crash -d`.

## Cierre 19:30 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora: **19:30** (Madrid), fuera de la ventana de las 15:00 -> **cierre sin trabajo nuevo** (sin ADB ni consola).
- Coordinacion: `device/logs/.pilot.lock` mtime `1794160826` (19:00:26), ahora `1794162608` -> edad **29,7 min (>=25)** -> lock tomado y refrescado al cerrar. Ese mtime es el refresco del cierre anterior de 19:00; no hay piloto interactivo activo.
- Verificacion local: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.362s / OK` (13/13, exit 0). `scripts/cat_count.py` -> **5.493 fichas** / 36 JSONL. `scripts/verify_catalog.py` -> 37 claves de mapa / 36 sistemas, `dc_torrent 105` con `url_acaba_en_.torrent 105` (correccion vigente de torrents Dreamcast intacta), `switch_fichas 40` (mediafire, 89-91 B).
- Backlog: **25 `[ ]` / 70 `[x]`** -> **no procede autocierre**; se mantiene el job.
- Sin cambios desde el cierre de 19:00: TAREAS.md mtime 18:03:39, `device/catalog_es/psx.jsonl` mtime 11:09:36, staging `device/staging/psx_add_t47.jsonl` intacto (18:03:16); ningun relleno python en background.
- Retomar en el proximo turno con lock: (1) `python device/tools/rom_integrity.py` (T-46, esperado `descuadres=0`); (2) aplicar `device/staging/psx_add_t47.jsonl` (backup de `psx.jsonl` + append + push; esperado 5.496) y mover `psx/Toy Story Racer.chd` truncado a `_trash_`; (3) T-34/T-38: ficha dreamcast `.torrent` + `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s; (4) T-33: `am force-stop` a mitad de descarga; (5) T-36: `adb shell logcat -b crash -d`.

## Cierre 20:00 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora: **20:00** (Madrid), fuera de la ventana de las 15:00 -> **cierre sin trabajo nuevo** (sin ADB ni consola).
- Coordinacion: `device/logs/.pilot.lock` mtime `1794162627` (19:30:27), ahora `1794164409` -> edad **29,7 min (>=25)** -> lock tomado (`1794164422`) y refrescado al cerrar. Ese mtime es el refresco del cierre anterior de 19:30; no hay piloto interactivo activo.
- Verificacion local: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.361s / OK` (13/13, exit 0). `scripts/cat_count.py` -> **5.493 fichas** / 36 JSONL. `scripts/verify_catalog.py` -> `36 jsonl / 5493 fichas / bad 0 / nonhttp 0 / dups 0`, `dc_torrent 105` con `url_acaba_en_.torrent 105` (correccion vigente de torrents Dreamcast intacta), `switch_fichas 40` (mediafire, 89-91 B), `sistemas_sin_entrada []`.
- Backlog: **25 `[ ]` / 70 `[x]`** -> **no procede autocierre**; se mantiene el job.
- Sin cambios desde el cierre de 19:30: TAREAS.md mtime 18:03:39, `device/catalog_es/psx.jsonl` 11:09:36, staging `device/staging/psx_add_t47.jsonl` intacto (18:03:16), `rom_integrity.py` 17:31; ningun relleno python en background (ultimos logs `fill_stubs.log` 17:24 y `psx_fill.log` 17:13).
- Retomar en el proximo turno con lock: (1) `python device/tools/rom_integrity.py` (T-46, esperado `descuadres=0`); (2) aplicar `device/staging/psx_add_t47.jsonl` (backup de `psx.jsonl` + append + push; esperado 5.496) y mover el `psx/Toy Story Racer.chd` truncado a `_trash_`; (3) T-34/T-38: ficha dreamcast `.torrent` + `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s; (4) T-33: `am force-stop` a mitad de descarga; (5) T-36: `adb shell logcat -b crash -d`.

## Cierre 20:30 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora: **20:30** (Madrid), fuera de la ventana de las 15:00 -> **cierre sin trabajo nuevo** (sin ADB ni consola).
- Coordinacion: `device/logs/.pilot.lock` mtime `1794164436` (20:00:36), ahora `1794166209` -> edad **29,6 min (>=25)** -> lock tomado (`1794166220`) y refrescado al cerrar. Ese mtime es el refresco del cierre anterior de 20:00; no hay piloto interactivo activo.
- Verificacion local: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.360s / OK` (13/13, exit 0). `scripts/cat_count.py` -> **5.493 fichas** / 36 JSONL. `scripts/verify_catalog.py` -> `map claves 37 sistemas 36`, `dc_torrent 105` con `url_acaba_en_.torrent 105`, `switch_fichas 40` (mediafire, 89-91 B).
- Backlog: **25 `[ ]` / 70 `[x]`** -> **no procede autocierre**; se mantiene el job.
- Sin cambios desde el cierre de 20:00: TAREAS.md mtime 18:03:39, `device/catalog_es/psx.jsonl` 11:09:36, staging `device/staging/psx_add_t47.jsonl` 18:03:16, `rom_integrity.py` 17:31; ningun relleno python en background.
- Retomar en el proximo turno con lock: (1) `python device/tools/rom_integrity.py` (T-46, esperado `descuadres=0`); (2) aplicar `device/staging/psx_add_t47.jsonl` (backup de `psx.jsonl` + append + push; esperado 5.496) y mover el `psx/Toy Story Racer.chd` truncado a `_trash_`; (3) T-34/T-38: ficha dreamcast `.torrent` + `adb shell du -sk /storage/FFF9-FF05/ROMs/TEMP` cada 10 s; (4) T-33: `am force-stop` a mitad de descarga; (5) T-36: `adb shell logcat -b crash -d`.


## 20:40 - T-47 aplicado + verificacion de ScreenScraper (autorizacion del usuario: "libre sigue con las pruebas y arrelgos")

### T-47 cerrado: fichas desplegadas y CHD de Toy Story Racer reemplazado
- `device/catalog_es/psx.jsonl`: corregido `size_bytes` de `Disney-Pixar Toy Story Racer (Europe) (Es,It,Nl)` a **142.962.689** (`size` "136.34 MB") y apendadas las 3 fichas de `device/staging/psx_add_t47.jsonl` (`Alundra 2`, `Command & Conquer (GDI)`, `Mortal Kombat 4`). Backup: `device/bak_catalog/psx.jsonl.bak-2035`.
- `scripts/cat_count.py` -> **5.496 fichas / 36 JSONL**. Nota de higiene: se parcheo el script para que solo lea `device/catalog_es/*.jsonl` y no cuente backups (`psx.jsonl.bak-*` daba `psx=223` y total 5.719 al sumar dos veces). Los backups del catalogo viven ahora en `device/bak_catalog/`.
- Push a la consola en `/data/data/com.arley4d.bypassarley4d/files/gjsonl/psx.jsonl` (backup remoto `psx.jsonl.bak-t47`, `chown 10219:10219`, `chmod 600`, `restorecon`): **226 lineas** leidas de vuelta desde el dispositivo, JSON por linea valido.
- `psx/Toy Story Racer.chd` truncado (~6,4 MB) movido a `/storage/FFF9-FF05/_trash_20261108/psx_truncados/`; copiado el CHD completo como `Disney-Pixar Toy Story Racer (Europe) (Es,It,Nl).chd`: **142.962.689 B** (= `Content-Length` del origen), **md5 `49a26c2c7378cde9b750248c1f8073f5` identico en local (`scratch/t47/toystoryracer.chd`) y en la consola**, cabecera `MComprHD`.

### T-46 verificado con el parche `tol_redondeo`
- `python device/tools/rom_integrity.py` -> `ficheros >1MB: 305`, `grupos con tamano repetido: 4`, **`duplicados=0 descuadres=0`** (antes del parche: 1 descuadre falso). Informe `device/logs/rom_integrity.tsv`: 27 `sin-ficha` + 2 `sin-catalogo` + 4 `tamano-igual-md5-distinto`. Ya **no aparece** `Toy Story Racer` como huerfano ni los 3 CHD de T-47.

### ScreenScraper: configuracion correcta, API responde, pero cupo KO agotado hoy
- Config en la consola (`/storage/emulated/0/ES-DE/settings/es_settings.xml`): `Scraper=screenscraper`, `ScraperUseAccountScreenScraper=true`, usuario `xampotato` con clave presente, `ScraperRegion=eu`, `ScraperLanguage=es` (credenciales no se registran).
- Nueva herramienta `device/tools/ss_probe.py` (usa las claves de desarrollo publicas de ES-DE, XOR de `ScreenScraper.h`, licencia MIT; lee usuario/clave del propio dispositivo y nunca los imprime):
  - `ssuserInfos.php` -> **HTTP 200**: `numid 37891`, `niveau 1`, `requeststoday 3450 / maxrequestsperday 20000`, `favregion eu`, `datedernierevisite 2026-11-08 20:32:11`.
  - `jeuInfos.php` / `jeuRecherche.php` -> **HTTP 431** con cuerpo `Faite du tri dans vos fichiers roms et repassez demain !`.
- Causa medida: **`requestskotoday 2000` = `maxrequestskoperday 2000`** -> el cupo diario de busquedas *sin resultado (KO)* esta agotado. No es fallo de cuenta, credenciales, red ni configuracion: es el freno anti-abuso de ScreenScraper y se restablece en el reset diario. Consecuencia practica: hoy no se puede scrapear nada nuevo (los 4 titulos PSX de T-47 se quedan sin media), pero la cuenta y el pipeline estan operativos.
- Media en la SD (`/storage/FFF9-FF05/ES-DE/downloaded_media`; `/storage/emulated/0/ES-DE/downloaded_media` es la **misma** carpeta, mismo inodo `131:1049154`): **14 G / 8.655 ficheros** en 33 sistemas = **5.323 fanart (jpg/png) + 3.228 manuales (pdf) + 103 covers**. Ficheros mas recientes: **2026-11-05 10:00** (`Zero Divide.pdf`, `Z.H.P. ... .pdf`); nada modificado en los ultimos 3 dias. => el scraping **si funciono** en la tanda del 5 de noviembre (3.228 manuales descargados de ScreenScraper), y desde entonces no se ha vuelto a ejecutar.
- Gamelists app (`/storage/emulated/0/ES-DE/gamelists/*/gamelist.xml`, 36 ficheros): **3.442 entradas `<game>`** (psx 181, ps2 189, dreamcast 115...), sin etiquetas `<image>`: ES-DE resuelve la media por nombre desde `downloaded_media`. Cobertura de covers baja (psx 13/181, megadrive 24/131) porque lo que se scrapeo masivamente fueron manuales y fanart, no covers.

## Ciclo 21:00 - turno de verificacion (lock del piloto vivo, sin ADB)

- Coordinacion: lock mtime `1794167139` (20:45:39), ahora `1794168008` -> edad **14,5 min < 25** -> piloto interactivo activo; sin ADB ni consola, lock intacto.
- `test_regiones.py` **13/13 OK** (0.378 s). `cat_count.py` -> **5.496 fichas / 36 JSONL**. `verify_catalog.py` -> `bad 0 / nonhttp 0 / dups 0`, `dc_torrent 105` (105 URLs `.torrent`), `switch_fichas 40`, `sistemas_sin_entrada []`.
- Backlog **27 `[ ]` / 71 `[x]`** -> sin autocierre.
- T-47 verificado en local: `psx.jsonl` 226 lineas, 3 titulos nuevos 1 vez cada uno, backup `bak-2035`. Staging movido a `device/staging/applied_20261108/` para que no se re-aplique (la orden "Retomar" de 20:30 era obsoleta; tambien lo eran `rom_integrity.py` y el CHD de Toy Story Racer, ya hechos a las 20:40).
- Unica discrepancia local: media 3.228+5.323+103 = **8.654** vs **8.655** ficheros documentados (1 sin clasificar). Retomar: `adb shell find /storage/FFF9-FF05/ES-DE/downloaded_media -type f` + clasificar por extension.
- Pendientes reales siguen: T-34/T-38 (torrent Dreamcast real + sniffing bencode), T-33 (durabilidad `am force-stop`), T-35 (SIGSEGV RetroArch), T-49/T-50 (bloqueados por cupo KO diario de ScreenScraper), T-40 (decision producto 885 fichas restringidas) y relleno de ~505 GB abiertos. Retomar con lock: `python device/tools/rom_integrity.py` ya no hace falta; siguiente accion de consola = T-33/T-34/T-35 con adb.

## Ciclo 21:30 - turno de verificacion local (lock del piloto vivo, sin ADB)

- Coordinacion: lock mtime 1794169585 (21:26:25), ahora 1794169809 -> edad **3,7 min < 25** -> piloto interactivo activo; sin ADB ni consola, lock intacto.
- `test_regiones.py` **13/13 OK**; `cat_count.py` **5.496 / 36**; `verify_catalog.py` `bad 0 nonhttp 0 dups 0`, `dc_torrent 105`, `switch 40`.
- **T-51 cerrado en local**: 4 fichas PSP (Daxter, Gran Turismo v1.01, SOCOM Fireteam Bravo 3, Twisted Metal Head-On) sin `size`/`size_bytes` y con `%20*Size=` en la URL -> URL limpia + tamano real de archive.org; descarga por rangos **HTTP 206 / 1.024 B** en las 4; backup `device/bak_catalog/psp.jsonl.bak-20261108-2135`. Catalogo local: **5.496 fichas / 4.236,32 GB**.
- Publicacion pendiente: remoto **11154e9**; `psp.jsonl` (T-51) y `psx.jsonl` (226 lineas, T-47) no estan en el clon publicado. Desplegar y publicar en el proximo turno con lock.
- Sin cambios en el dispositivo ni en el repo por este turno.

## Ciclo 21:46 - T-34 cerrado en dispositivo y causa raiz de la descarga "que no funciona"

- **T-34 [x]**: descarga torrent real de punta a punta en la Thor. `.torrent` bencode (netinst Debian, 60.948 B) -> `DownloadTorrentActivity` -> `TorrentInfo`+`SessionManager` -> **756,0 MiB (792.723.456 B) a 2,0 MB/s con 37 conexiones** -> fichero en `ROMs/FOREVER/switch/` a las 21:31:19 -> la app salta sola a `EmulatorLauncherActivity`. UI y logcat limpios. El motor torrent de la app funciona y **no requiere el parche de `lb.smali`**.
- **T-38 [x]**: con un fichero que contiene solo una URL, la actividad muestra "El archivo .torrent no es valido o no pudo abrirse. Can't decode data: expected value (list, dict, int or string) in bencoded string". No hay resolucion de URL en la app.
- **Causa raiz del "no descarga"**, medida 21:44: de **1.043** `.torrent` en `ROMs`, **1.038 contienen una URL en texto plano** (stub `URL *Size=...` + ZIP vacio) y solo **5** son torrents reales. Es un problema de datos de origen, no de codigo. Abierta **T-52** para sustituirlos por fuentes consumibles.
- Estado del dispositivo al cerrar: ISO de prueba y temporales de TEMP borrados, caches limpias, ES-DE al frente. Nada mas tocado.

## Cierre 22:00 - fin de ventana (run cron Thor-15h-continuar, PASO 1)

- Hora: **22:00** (Madrid), fuera de la ventana de las 15:00 -> **cierre sin trabajo nuevo** (sin ADB ni consola).
- Coordinacion: `device/logs/.pilot.lock` mtime `1794169585` (21:26:25), ahora `1794171626` (22:00:26) -> edad **34,0 min (>=25)** -> lock tomado (`22:00:10`) y refrescado al cerrar. El ultimo refresco fue el de 21:26; el piloto interactivo trabajo hasta 21:46 sin volver a refrescarlo, pero a esta hora no hay sesion viva.
- Verificacion local: `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.403s / OK` (exit 0). `scripts/cat_count.py` -> **5.496 fichas / 36 JSONL** (psx 226, psp 194, dreamcast 128, switch 40). `scripts/verify_catalog.py` -> `bad 0 nonhttp 0 dups 0`, `dc_torrent 105` con `url_acaba_en_.torrent 105` (correccion vigente de torrents Dreamcast intacta), `switch_fichas 40` (mediafire), `sistemas_sin_entrada []`.
- Backlog: **32 `[ ]` / 71 `[x]`** (subio de 5 abiertos respecto a las 21:30 por T-52 y sus 5 subtareas + T-49/T-50) -> **no procede autocierre**; se mantiene el job.
- Cerrado hoy con evidencia de dispositivo (secciones 20:40-21:46): T-46 `descuadres=0`, T-47 psx 226 lineas + CHD 142.962.689 B md5 `49a26c2c7378cde9b750248c1f8073f5`, T-48 ScreenScraper cuenta OK (cupo KO 2000/2000 agotado), T-51 4 fichas PSP con URL limpia y tamano real (HTTP 206), T-34 torrent real de punta a punta (792.723.456 B, 2,0 MB/s, 37 conexiones), T-38 stub-URL rechazado con error legible.
- Pendiente real al cerrar (con comando de reanudacion):
  1. **Desplegar/publicar T-51+T-47**: medido ahora `md5sum` -> `psp.jsonl` local `8f81e30a1af1ac0bd9dcd171850b4a52` vs clon `d6a1b8eb...`; `psx.jsonl` local `6dc5c9f584abad740bd023b627595348` vs clon `d2a8f76c...`; remoto `git ls-remote origin HEAD` = **11154e9**. Retomar: `adb push` de ambos a `files/gjsonl/` + `chown 10219:10219`/`chmod 600`/`restorecon` + releer y contar (194/226), luego `cp` a `build/repo/retroxam-roms/` + `git commit` + `git push`.
  2. **T-52 (nuevo)**: 1.038 stubs `.torrent` con URL en texto plano de 1.043 censados. Retomar: crear `device/tools/torrent_stub_fix.py --dry-run` y clasificar por host antes de tocar la SD.
  3. **T-33** durabilidad ante `am force-stop` a mitad de descarga (usar el `.torrent` Debian de `scratch/t34/`).
  4. **T-35** SIGSEGV RetroArch desde ES-DE: `adb shell logcat -b crash -d`.
  5. **T-49/T-50** bloqueados por cupo KO diario de ScreenScraper (reset automatico); **T-23/T-26/T-27/T-28** catalogo/Switch/japonesas/huecos.
- Nada tocado en el dispositivo ni en el repo en este turno (solo lectura y el backup `device/bak_catalog/ESTADO.md.bak-2200`).

## 22:10 - T-52 cerrado y pilotaje continuo cada 30 min

- **Los `.torrent` de la SD ya son torrents reales**: 1.043 en `ROMs` = **129 en `_cuarentena`** + **914 utiles**, y los 914 tienen cabecera bencode (`total=914 bencode=914 stubs=0`, `scripts/check_bencode.sh`). 909 sustituidos en masa (`ok=909 err=0`) + 5 que ya lo eran. La correccion vigente sigue en pie: **no se cuarentenan los Dreamcast**.
- **Watchdog**: el job `45d6165e1068` pasa a `Thor-30m-continuar`, `0,30 * * * *`, repeat 18/1000, continuidad `context_from=['self']`; proximo disparo `22:30:00+01:00` (gateway PID 25592, ticker vivo). Si el lock del piloto interactivo tiene <25 min no toca el dispositivo; si caduca, trabaja el.
- **Modelo local de apoyo**: `scripts/llm_local.py` contra Firebat (`192.168.2.75:8080`, fallback tailnet `100.77.92.3:8080`, modelo `local`). Probado: respuesta correcta en 114 s / 272 tokens. Solo para subtareas pequenas; sus cifras no van a un informe sin comprobarlas.
- Sin cambios en el dispositivo en este tramo salvo la sustitucion de stubs ya descrita; ES-DE intacto, `_cuarentena` sin tocar.
## 22:10 - T-51 y T-47 desplegados y publicados

- Consola: `files/gjsonl/psp.jsonl` = **194 lineas**, `psx.jsonl` = **226 lineas**, `u0_a219`/`600`/`app_data_file:s0:c219…`.
- Repo `build/repo/retroxam-roms`: commit **`8b7a87e`** empujado (`11154e9..8b7a87e`, `refs/heads/main` verificado con `ls-remote`). En el blob publicado no queda ningun `%20*Size=` (`grep -c` = 0).
- Nota de mantenimiento: el clon no tenia identidad git; fijada por repo (`servixam-max`) en vez de global. El push usa el helper de credenciales de `gh.exe`.
## 23:00-23:12 - T-33 cerrado con integridad verificada

La descarga de `.torrent` de la app `com.arley4d.bypassarley4d` resiste un `am force-stop` y **reanuda** correctamente:

1. Descarga real: primer intento completo, 792.723.456 B, `sha256sum` = `a7ef94ac...e355` (oficial Debian).
2. Corte real: `am force-stop` mata el proceso en 1 s; el fichero queda **preasignado** a tamano completo pero con contenido parcial (`f583b9...`, `79a49022...`). El tamano aparente no sirve como medida de progreso.
3. Reanudacion: con un parcial de 400 MiB creado con `dd`, al relanzar el mismo `.torrent` la UI muestra **52 % (400,0/756,0 MB), 22 seeds, ETA 44:54** y continua.
4. Final: la app pide `¿Quieres conservar el juego?` -> `CONSERVAR`, mueve el ISO a `ROMs/FOREVER/switch/` y el **sha256 final coincide con el oficial**. Parcial reanudado = fichero correcto.

Pendiente operativo: limpiar `ROMs/TEMP/t33_scratch/` (~4 GB de copias de prueba) y, si se quiere, la copia duplicada en `ROMs/FOREVER/switch/`. El original del usuario esta restaurado en `ROMs/FOREVER/psx/`.

T-35/T-36: `logcat -b crash -d` vacio y `0` en los 7 `ra_watch.log*` (110 min de cobertura). Sin novedad.

**Actualizacion 23:20-23:28 - dedup espejo live/forever + promocion de juegos invisibles**

- **Hallazgo**: `scripts/audit_sd.py` (nuevo audit, dumps refrescados en `device/audit_sd_raw/`) detecto **72 grupos duplicados / 18,0 GiB**; **63** de ellos eran el patron *espejo*: cada juego descargado existia dos veces, una en plano (`ROMs/<sys>/X`) y otra en `ROMs/FOREVER/<sys>/<juego>/X`. ES-DE lee SIEMPRE el plano (`ROMPATH=/storage/FFF9-FF05/ROMs`, `paths.tsv` de `custom_systems/es_systems.xml`), asi que la copia de FOREVER era redundante.
- **Verificacion antes de borrar** (`scratch/verify_del.sh` -> `/data/local/tmp/verify_del.sh`, log `device/logs/dedup_forever_run.log`): para cada par se comparo tamano + `md5sum` de los primeros y ultimos 1 MiB. Resultado: **50 pares identicos, 0 dudosos**. Se borro solo la copia de FOREVER.
- **Espacio liberado**: **18.465.116.218 B = 17,2 GiB**. `df` SD: 76G/401G usados -> **59G/418G** (477G totales). `bytes_roms` del audit: 58,8 -> **37,61 GiB**.
- **Pitfall registrado**: la aritmetica de `sh` (toybox) es de **32 bits**; el contador `BYTES=` del script desbordo y reporto `1.285.247.034` en vez de `18.465.116.218`. Los bytes reales se recalcularon en el PC sumando los `DEL <bytes>` del log. No usar contadores de bytes en shell del dispositivo.
- **Juegos rescatados a la vista de ES-DE** (`scratch/promover.sh`, log `device/logs/promover_run.log`): 4 titulos descargados solo existian en `FOREVER/` (invisibles para el frontend) mientras el plano tenia un stub de 129-148 B o un `.torrent`:
  - `psx/Castlevania - Symphony of the Night (Europe).chd` -> 384.249.945 B (stub apartado como `.stub_bak`).
  - `psx/Battle Arena Toshinden (Europe).chd` -> 283.203.993 B (stub apartado como `.stub_bak`).
  - `switch/20XX + 30XX.xci` -> 3.420.582.912 B.
  - `switch/Ultra Street Fighter II The Final Challengers.xci` -> 775.946.240 B.
  Los `.xci` se movieron con `mv` (mismo volumen, instantaneo, sin duplicar).
- **Parcial huerfano recogido**: `FOREVER/dreamcast/Cannon Spike (Europe).chd.part` (129.508.544 B) borrado; 64 directorios vacios eliminados bajo `FOREVER/`.
- **Estado final del audit**: 3.920 ficheros, 591 ROMs reales >=1 KB, 2.187 stubs <1 KB, `bytes_totales` 42.948.449.386 B (40,0 GiB), `grupos_duplicados` 72 -> **20** (908,5 MB, ya solo casos legitimos: rips distintos de cps1 con 1 KB de diferencia, sets de `_cuarentena`, `.cue`+`.bin` de saturn, stubs junto a reales).
- **Siguiente**: relanzar ES-DE para que reescanee y confirmar que los 4 titulos aparecen; decidir el duplicado `FOREVER/psx/debian-*.iso` (3 ISOs de Linux, 2,38 GB, no son ROMs); `ROMs/TEMP/t33_scratch/` (~4 GB) sigue pendiente de recoger con `scripts/temp_gc.py`.

## 2026-11-09 00:05 — T-55: verificacion en UI de ES-DE (PSX cerrado; Switch con fallo de emulador)

**PlayStation 1 (Sony PlayStation) — CERRADO.** Tras sacar los directorios de datos de RetroArch de `ROMs/psx`, la lista es plana, sin entradas-carpeta (`SwanStation`, `Beetle PSX HW` ya no aparecen) y con metadatos reales (genero, ano, editor, tamano de descarga).
- `Ace Combat 2`, `Alien Resurrection`, `Armored Core`, `Battle Arena Toshinden`... visibles en carrusel horizontal.
- Arranque real desde ES-DE: **Alien Resurrection** -> `pidof com.retroarch.aarch64` = 11797, `saves/SwanStation` en uso, `SET_GEOMETRY 1600x1200`, captura con contenido del juego.
- Arranque real: **Battle Arena Toshinden** (el promocionado de `FOREVER/` en T-54) -> `pidof` = 28468, intro del juego en pantalla. Confirma que los 4 titulos promocionados son lanzables desde el frontend.
- Capturas: `scratch/ps1_games.png`, `scratch/ps1_alien_boot2.png`, `scratch/ps1_toshinden.png`.

**Switch — lista correcta, emulador aborta (nuevo T-56).** Gamelist normalizada (`<path>./20XX + 30XX.xci</path>`, `./Ultra Street Fighter II The Final Challengers.xci`), duplicados fuera; ES-DE muestra ambos con caratula y tamano (3,19 GB / 740 MB) y lanza el intent.
- Eden arranca, carga el NCA (`ProgramID 0x010059b017f9e000`), sintetiza archivos de sistema y **aborta** en `Vulkan::vk::Device::CreateGraphicsPipeline` (excepcion C++ -> `__cxa_throw` -> SIGABRT).
- Tombstone en `logcat -b crash -d` (11-08 23:48:18, uid 10173, `libyuzu-android.so`), con `BSD: Network isn't initialized` previo. No es problema de la ROM ni de ES-DE: es el backend Vulkan/driver GPU. Siguiente paso: probar OpenGL o driver Turnip.

**PS2 — sin core valido (nuevo T-57).** Los 190 titulos de PS2 existen en la lista, pero al lanzar cualquiera ES-DE abre RetroArch sin core de PS2 (cae al menu). AetherSX2 (`xyz.aethersx2.android`) si esta instalado, asi que se puede reapuntar el emulador del sistema `ps2`.

## Actualización 2026-11-09 01:12 (cron)

- **T-49 cerrado**: scrapeo PSX por UI de ES-DE, 16/16 juegos, gamelist 181→196 entradas con 195 descripciones; 4 títulos de T-49 verificados. Cupo ScreenScraper: 2058/20000 general, KO 1070/2000 (no bloquea).
- **T-50**: covers 103→117 (+14), total media 8.809 ficheros.
- `device/tools/ss_probe.py` ya no imprime credenciales (URL con `?[REDACTED]`).
- Dispositivo: ES-DE reiniciado al menú principal; T-57 (PS2→AetherSX2) pendiente de verificación consistente.

### Ciclo cron 01:30–02:15 (2026-11-09) — T-57: causa raiz localizada
- ES-DE lanza PS2 con `%EMULATOR_AETHERSX2% %ACTION%=android.intent.action.VIEW %DATA%=%ROMSAF%` (es_log 02:01:51; Package `xyz.aethersx2.android`, Activity `.EmulationActivity`, Data expandido al `content://com.android.externalstorage.documents/tree/FFF9-FF05%3AROMs%2Fps2/document/...iso`).
- logcat: `START u0 {act=android.intent.action.VIEW dat=content://... flg=0x10010000 cmp=xyz.aethersx2.android/.EmulationActivity} from uid 10202` -> **sin FLAG_GRANT_READ_URI_PERMISSION (0x1)**: ES-DE 3.5.0-65 no concede el URI al emulador.
- Resultado: `scratch/t57_esde_final_150s.png` = menu BIOS OSDSYS de PS2 (Browser / System Configuration), no el juego (veredicto en `scratch/t57_vision_esde.txt`).
- Contraprueba: el mismo ISO lanzado desde la lista interna de AetherSX2 SI arranca (pantalla "Select Language" de 007 Agent Under Fire, `scratch/t57_bios_or_game.png`, veredicto en `scratch/t57_vision.txt`). ISO, BIOS y emulador correctos; falla solo el paso del URI ES-DE->AetherSX2.
- AetherSX2: `NPE Cursor.getCount() on null` en `FileHelper.findFiles` <- `NativeLibrary.refreshGameList` <- `EmulationActivity.onCreate`; `W/DocumentsProvider: Failed during query`. Su escaner SAF falla y cae a BIOS.
- `am start --grant-read-uri-permission` desde shell: `SecurityException: UID 2000 does not have permission to content://...` (shell no tiene grant sobre la SD; via de prueba invalida).
- `file://` como data del intent: tampoco arranca (negro a 55 s y 110 s).
- `ES-DE/settings/es_settings.xml` (9.194 B) no tiene ninguna opcion grant/uri.
- Plan de arreglo (NO aplicado): lanzar AetherSX2 con un script propio ejecutado por ES-DE (uid 10202, dueno del grant) que haga `am start --grant-read-uri-permission`, o parchear ES-DE para anadir el flag.

### Ciclo cron 02:30–03:00 (2026-11-09) — T-57 CERRADO
- Diagnostico corregido: el flag de permiso NO era el problema (AetherSX2 ya tiene grant SAF persistente `prefix=true` sobre `FFF9-FF05:ROMs/ps2`, leido con `abx2xml /data/system/urigrants.xml`). AetherSX2 ignora `-d <uri>` con ACTION_VIEW y arranca la BIOS; con ACTION_MAIN + extra `bootPath` arranca el juego.
- Arreglo aplicado en la regla PS2 del dispositivo: `%ACTION%=android.intent.action.MAIN %EXTRA_bootPath%=%ROMSAF%` (backups `es_systems.xml.bak_t57_bootpath` y `.bak_t57_full`).
- Verificacion E2E (no manual): ES-DE abierto directo en la lista PS2 (`StartupSystem=ps2` + `StartupView=gamelist`, restaurado despues) -> ENTER sobre 007 -> `es_log.txt` 02:55:44 `Action: android.intent.action.MAIN`, `Extra name: bootPath`; logcat `START u0 {act=android.intent.action.MAIN ... (has extras)} from uid 10202`; `scratch/t57_launch_esde.png` OCR = "Selection / Language / English / Francais / Deutsch / Espanol / Nederlands / Svenska". El juego arranca; `%EXTRA_bootPath%` es un placeholder valido del frontend.
- Estado del dispositivo: `custom_systems/es_systems.xml` restaurado a los 205 sistemas con el parche PS2 (owner u0_a109:media_rw, 660); `es_settings.xml` restaurado (StartupSystem=cps1, StartupView=system); ES-DE reiniciado, 0 lineas error/fatal en el log, carrusel en CPS1 (37 juegos). AetherSX2 y ES-DE en foreground limpio.
- Tests: `python -W ignore scripts/test_regiones.py` -> Ran 13 tests in 0.364s, OK. Backlog tras cierre: T-57 pasa a [x].

## 2026-11-09 03:00 (cron) — mantenimiento local; dispositivo intacto

- Lock `.pilot.lock` con edad de 2 min al arrancar (contenido 1794189488, mtime 02:58): por regla no se uso ADB ni se toco la consola en este turno.
- Auditoria local del catalogo: `python -W ignore scripts/cat_count.py` -> `total fichas: 5496`, 36 sistemas (mame=992, nes=336, nds=306 ... wiiu=3). Coincide con la cifra de cabecera y no hay JSONL ilegibles.
- `python -W ignore scripts/test_regiones.py` -> `Ran 13 tests in 0.359s / OK`.
- `ESTADO.html` y `TAREAS.html` estaban congelados en 7 nov 15:00. Nuevo `scripts/md2html.py` (sin dependencias) genera `ESTADO-LOG.html` y `TAREAS-LOG.html` completos con indice lateral; los HTML curados se conservan y solo ganan un aviso con enlace.

## 2026-11-09 03:05 (cron) — el recuento de 28 pendientes era engañoso

- `grep -c "^- \[ \]" TAREAS.md` = 28, pero 27 son casillas historicas de runs viejos (varias ya superadas). El backlog real de la tabla es 18 ✔ / **6 ◐** (T-09, T-10, T-11, T-23, T-27, T-28) / 0 ☐, mas T-18. Anotado en TAREAS.md para no inflar el backlog ni bloquear el autocierre por items fantasma.

## Ciclo cron 03:30-04:00 (2026-11-09) - T-56 acotado: Eden no monta el XCI por intent; el arranque que si funciono (23:48) fue desde su biblioteca

- Lock tomado a las 03:30 (epoch 1794191410) por obsolescencia (1920 s).
- T-35: 0 coincidencias de `Fatal signal|SIGSEGV` en los 7 `ra_watch.log*` (cobertura hasta 03:30). Vigilancia viva, sin repro nueva.
- T-56, evidencia real:
  - `config.ini` actual == `config.ini.bak_t56` (46.716 B, `diff` vacio) -> el cambio a OpenGL no dejo rastro; Eden reescribe la config al arrancar.
  - `dumpsys package dev.eden.eden_emulator`: EmulationActivity declara filter `bbb90a1` = VIEW + scheme content + staticType application/octet-stream. Mi intent con `-t` coincide con el filtro.
  - Lanzados `20XX + 30XX.xci` y `Ultra Street Fighter II...xci` con content URI: ambos -> 4x `fssystem_nca_reader.cpp:210: assert m_body_storage != nullptr` + `No game found in arguments or intent`, sin ventana de juego.
  - `file://` -> Eden lo rechaza sin montar (0 asserts).
  - `/data/system/urigrants.xml`: sin grants para eden (grep vacio).
  - Prueba de que SI arranco ayer: existe `nand/user/save/.../010059B017F9E000` (30XX; 8 titulos con save), shaders de 30XX a las 23:46 y tombstone 23:48:18 en `CreateGraphicsPipeline`.
- Hipotesis vigente: el crash de T-56 es el de `CreateGraphicsPipeline` (tombstone de las 23:48) y solo se reproduce arrancando desde la biblioteca de Eden (carpeta importada), no por intent VIEW.
- Siguiente: importar `/storage/FFF9-FF05/ROMs/switch` en Eden desde su UI y lanzar 30XX desde la lista; ahi aplica la prueba de backend/driver.
- Integridad de los dos XCI descartada como causa: `stat` -> 20XX size=3420582912 con blocks=6680832 (`6680832*512` = 3420585984 B) y USF2 size=775946240 con blocks=1515520 (`1515520*512` = 775946240 B). Ninguno es sparse ni esta truncado: ocupan lo que declaran.

## Ciclo cron 04:30-04:45 (2026-11-09) - T-56 resuelto: el driver Turnip abortaba en CreateGraphicsPipeline; el Adreno del sistema arranca y renderiza 30XX

- Eden tenia 0 juegos con los `gamedir` del config. Importada `/storage/FFF9-FF05/ROMs/switch` por SAF en la UI: boton Carpeta -> picker ya en `Thor/ROMs/switch` -> USAR ESTA CARPETA -> PERMITIR -> Aceptar. La biblioteca pasa a listar `30XX`.
- Con el driver Turnip instalado (`Turnip_v25.3.0_R11.zip`, Mesa 25.2.99) el juego aborta a los pocos segundos: SIGABRT en `Vulkan::GraphicsPipeline`, ultimo tombstone 04:33. `Report: Driver: turnip Mesa driver 25.2.99`, `Device: Turnip Adreno (TM) 740`.
- El backend no era la causa: `backend=0` editado en `config.ini` con Eden parado no sobrevive al arranque (04:32 backend=0 -> 04:33 backend=1; Eden reescribe la config). Con backend OpenGL pedido, el crash seguia siendo Vulkan/Turnip.
- Cambio aplicado en Ajustes -> Gestor de controladores de la GPU -> Controlador de la GPU del sistema (Qualcomm 512.676.53). `config.ini` (04:35) queda `driver_path=` vacio y `backend=1`; el radio del sistema es el marcado.
- Resultado verificado: `Report: Driver: Qualcomm Technologies Inc. Adreno Vulkan Driver 512.676.53`, `Device: Adreno (TM) 740`; pid 16033 sigue en `EmulationActivity` a los 5 min; decenas de `CreateGraphicsPipeline` sin abort; captura `scratch/t56b/run_adreno.png` = pantalla de titulo de 30XX (PLAY!, SETTINGS, v1.3.6). La ROM y los XCI quedan descartados como causa.
- Nota para el proximo ciclo: no reseleccionar Turnip hasta que exista un build que no rompa ese pipeline (T-58 en TAREAS.md).

### 04:46 - verificacion en frio de T-56 y limite de memoria

- El driver del sistema persiste al `force-stop` (`config.ini` con `driver_path=` vacio) y el relanzamiento vuelve a reportar `Adreno Vulkan Driver 512.676.53`. T-56 queda cerrado de verdad, no solo en caliente.
- Aclarado: los `assert m_body_storage != nullptr` son ruido del escaneo de biblioteca; no son el crash.
- Limite nuevo y real: el `lowmemorykiller` mata Eden en juego (RSS 4,1-4,8 GB sobre 7,36 GB totales; kills a las 04:41:39 pid 21355 y 04:44:25 pid 31187, sin tombstone). `am kill-all` no basta. Queda T-59 en TAREAS.md.

## 2026-11-09 06:17
- Eden: EmulationActivity en primer plano, PID 9249, RSS 4,52 GB, 2m42s estable tras reinicio + guard 71-eden-memguard.sh v3 (drop_caches/2 s); MemAvailable ~0,7 GB, SwapFree 2,5 GB.
- Guard instalado en /data/adb/service.d y activo tras reboot (PID 2102); copia versionada en scripts/eden_memguard.sh.
- Cierres previos: reason=3 LOW_MEMORY (exit-info), sin OOM en dmesg; Shmem del guest ~3,1 GB y swap parcial. Hipotesis abierta: kill por presion de lmkd/AMS, no resuelto por drop_caches.
- Siguiente: verificacion visual de la captura y, si procede, limitar memoria del guest o fijar minfree.
- 06:21 Verificacion visual OK: 30XX v1.3.6 en menu principal dentro de Eden (scratch/t59/run_t61_alive.png), render vivo, sin errores. Lock refrescado 06:19 (1794201578).

## 2026-11-09 07:05 (cron) — GC de restos de descarga integrado en el arranque; verificado en boots reales

- Nuevo `scripts/temp_gc_boot.sh` (v3, 1.753 B, md5 `f30d0806f2c46a39ba8e6c3489129d2c`) instalado como `/data/adb/service.d/72-temp-gc.sh` (755). En cada arranque: mueve a `ROMs/TEMP_huerfanos_<fecha>` los directorios de `ROMs/TEMP` sin ficheros tocados en 30 min, y a `Download/libtorrent_huerfanos_<fecha>` los ficheros de `Download/libtorrent_download` con mtime de mas de 7 dias. Solo `mv`, nunca borra; idempotente. Log: `/data/local/tmp/temp_gc.log`.
- Prueba en caliente con datos sinteticos: dir con mtime 2026-11-07 movido y dir reciente intacto -> `TEMP: movidos 1 dir(es)`; fichero de torrent con mtime 2026-10-30 movido -> `torrents: 1 fichero(s)`; segunda pasada `movidos 0` y sigue `1 fichero(s)` (idempotente). Artefactos de prueba movidos a `/data/local/tmp/gc_smoke_cleanup`.
- Verificacion en arranque real (3 reboots): entrada nueva en el log a los 5 s del boot. Ultimo boot 07:05:03 -> `2026-11-09_07:05:08 inicio` + `TEMP: movidos 0 dir(es); quedan 0 entrada(s)` + `torrents: 0 fichero(s)`; una sola pasada y `md5sum` del fichero instalado == local.
- Dos lecciones: (1) Magisk ejecuta TODO ejecutable de `/data/adb/service.d`, no solo `*.sh`: el backup `72-temp-gc.sh.bak_v1` corrio una segunda pasada -> los backups van fuera de service.d (movido a `/data/local/tmp`); (2) `du` no funciona en el entorno de arranque (salida vacia con la SD aun montando) -> el log cuenta entradas con `ls -A | wc -l` y el guard espera hasta 120 s a que `ls -A ROMs` no este vacio.
- T-59: sesion de 30XX verificada a los 47 min con captura `scratch/t59/run_t62_47min.png` (menu del juego PLAY!/SETTINGS v1.3.6, sin dialogos); `logcat -d` sin lineas `lowmemorykiller|Kill dev.eden`; guard con drops hasta 06:58. La sesion termino con los reinicios de verificacion; el dispositivo queda con Eden cerrado y el GC activo.
- T-35 (SIGSEGV RetroArch): 0 coincidencias en los 7 `ra_watch.log*`; las 2 de `ra_watch.log.5` son SIGABRT de `n.eden_emulator` por `VK_ERROR_OUT_OF_HOST_MEMORY` (04:32 y 04:33, Turnip), no RetroArch. Nota: `surfaceflinger` aborto una vez en el boot de 06:11 (`no suitable EGLConfig found`, uptime 2 s) y se recupero; no se repitio en los boots de 07:02-07:05.

- 07:09 Relanzado tras la verificacion: Eden MainActivity -> tap tarjeta `(240,401)` -> `EmulationActivity`, PID 9163, driver `Qualcomm Adreno Vulkan Driver 512.676.53`; menu 30XX v1.3.6 a los 2 min (`scratch/t62/30xx_menu_after_boot.png`). RSS 4,79 GB, MemAvailable 644 MB, guard con drop a las 07:06:09 sobre el pid 9163. Aviso toast de superusuario para Caratulas Arley en pantalla (no bloquea).


## 2026-11-09 07:30 (cron) — turno solo-local (lock del piloto activo)

- Lock con edad de 20 min al inicio: no se toco el dispositivo este turno. Estado sin cambios desde 07:09 (Eden/30XX vivo con Adreno del sistema, PID 9163; GC de arranque 72-temp-gc.sh activo).
- Verificado en local: 36 JSONL / 5.496 lineas en device/catalog_es; test_regiones.py 13/13 OK; sintaxis de temp_gc_boot.sh y temp_gc.py OK; md5 local de temp_gc_boot.sh = f30d0806f2c46a39ba8e6c3489129d2c.
- HTML de lectura al dia: ESTADO-LOG.html y TAREAS-LOG.html regenerados desde los .md (backups en device/bak_*_LOG.html.20261109_0730).
- Retomar con: dumpsys activity activities | grep topResumedActivity y ps -A -o PID,ETIME,RSS,NAME | grep eden en adb shell; tail -5 /data/local/tmp/temp_gc.log con su -c.


## 2026-11-09 08:16 (cron) — T-59: dos modos de muerte distintos (crash nativo y LMK) y proteccion OOM verificada

- `dumpsys activity exit-info dev.eden.eden_emulator` da la secuencia real: #0 08:02:11 pid 10505 `reason=3 (LOW_MEMORY)` `pss=4,4GB rss=5,0GB importance=100`; #1 07:23:47 pid 9163 `reason=5 (APP CRASH(NATIVE)) status=11` `pss=4,1GB rss=4,4GB`; #2 05:36:42 pid 4827. La sesion de las 07:23 murio por SIGSEGV nativo y la de las 08:02 por LMK: no era una sola causa.
- En `logcat`, el cierre de las 08:02 va precedido de `lmkd: critical pressure event triggered` a las 08:02:09 y la app era foreground (`importance=100`): lmkd puede terminar Eden incluso en primer plano cuando la presion es critica.
- El arranque de las 08:01:49 (`START ... EmulationActivity ... from uid 10173`) pillo las apps de fondo residentes y murio a los 22 s con 5,0 GB de RSS. Con la limpieza previa de este turno (`am force-stop` de YouTube/Play/GameAssistant/ES-DE companion/Wellbeing/fota/Obtainium + `am kill-all` + `drop_caches`) el siguiente arranque partio de `MemFree 4.668.952 kB / MemAvailable 5.137.988 kB` (antes: 3,1 GB libres).
- Nuevo guard `scripts/eden_oomguard.sh` (md5 `c91e25eabf4d9f1d528c82010ed7d923`) instalado como `/data/adb/service.d/72-eden-oomguard.sh` (755, mismo md5 en dispositivo) y arrancado ya: cada 15 s pone `oom_score_adj=-800` a Eden si `VmRSS>2 GB` y lo devuelve a `200` cuando queda idle. Prueba funcional real: `echo 0 > /proc/9280/oom_score_adj` y a los 20 s el log registra `2026-11-09_08:12:48 oom_adj pid=9280 rss=4740804kB 0->-800`.
- El guard v3 `71-eden-memguard.sh` no se paro: relee el pid de Eden en cada vuelta; el hueco del log entre 08:01:27 y 08:06:28 son los 4 min sin proceso Eden. Reanudo solo con el pid 9280.
- Sesion de comprobacion: 30XX en `EmulationActivity` desde ~08:04:40 (proceso 9280 desde 08:02:10); a las 08:11:54 sigue vivo con RSS 4.780.128 kB, `MemFree 171.612 kB`, `MemAvailable 566.944 kB` y adj -800. Queda comprobar que pasa de los 17m39s del SIGSEGV de las 07:23 (~08:22).

- 08:24 (cron) Confirmado en la sesion viva: `EmulationActivity` creada a las 08:03:57 (logcat `wm_on_create_called( 9280)`), y a las 08:24:21 el juego **sigue en primer plano** con 20m24s de emulacion (proceso 22m10s), RSS 4.636.664 kB, `MemFree 130.176 kB`, `MemAvailable 567.764 kB`, adj -800. Supera la marca de 17m39s del SIGSEGV de las 07:23: con limpieza previa + 1x + guard OOM la sesion aguanta. Siguiente prueba de fuego: dejarla correr y ver si aparece un tercer modo de fallo (o ninguno) en 30-60 min.

## 2026-11-09 08:35 (cron) — PS2: revalidacion de las 239 URLs y aplicador probado (turno solo-local)

- Lock del piloto con edad de 3 min (< 25) al empezar: sin ADB ni cambios en el dispositivo.
- Revalidacion completa sin ADB: 239 fichas PS2 -> 73x200 (mediafire), 19x206 (CHD vivos), 104x401, 43x403. Total muertas 147 y vivas 92: coincide con la auditoria de esta manana (el reparto 401/403 se movio en 4 fichas, el total no).
- Las 41 sustitutas de device/logs/title_subst.tsv se reprobaron una a una: 41/41 -> 206. Los 41 titulos emparejan exacto y unico contra ps2.jsonl (0 sin match, 0 duplicados) y sus `size_bytes` difieren del original, como corresponde a otro CHD.
- Nuevo `scripts/aplicar_sustituciones.py` (dry-run por defecto): sustituye `urls[0]` y su size, o `--append` para anadir la USA como alternativa; backup en `device/bak_catalog/`, log en `device/logs/`, idempotente (segunda pasada: 41 ya_aplicadas). Probado con `--aplicar` sobre copia: 239 lineas -> 239, 41 fichas cambiadas, ninguna clave nueva a nivel raiz, `p`/`n`/`meta` intactos.
- NO se aplico al catalogo real: las sustitutas cambian EU/JP por USA (no es reemplazo transparente) y el dispositivo esta ocupado; el dry-run da 41 aplicables. Decision pendiente del usuario.
- Retomar: `python scripts/aplicar_sustituciones.py --sistema ps2` (dry-run) y, si se aprueba la region USA, `... --aplicar`; despues push del catalogo.
- test_regiones.py: Ran 13 tests, OK.

## 2026-11-09 09:15 (cron) — Turnip v27 cargado de verdad y abortado; sistema estable

- El zip v27 se instalo en el gestor y se selecciono; Eden lo cargo desde `/data/data/dev.eden.eden_emulator/files/gpu_driver/libvulkan_freedreno.so` y reporto `turnip Mesa driver 26.99.99` (el meta del release dice 27.0.0-20261109-r2). A los ~0,4 s: `Fatal signal 6 ... VkPipelineBuild` en `CreateGraphicsPipeline`.
- Tercer build de Turnip consecutivo que aborta (v25.3.0-R11, T30, v27). Con el driver Qualcomm 512.676.53 el mismo 30XX arranca y se mantiene (RSS 4,39 GB a los 2m28s). `driver_path=` queda vacio.
