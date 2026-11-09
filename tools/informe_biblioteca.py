import os, re, glob, json, collections, html
BS=chr(92)
def key_of(p):
    parts=p.replace(BS,'/').split('/')
    i=parts.index('ROMs') if 'ROMs' in parts else 0
    rest=parts[i+1:]
    if rest and rest[0]=='FOREVER': rest=rest[1:]
    if len(rest)<2: return None
    return rest[0].lower()+'/'+re.sub(r'\s+',' ',rest[-1]).strip().lower()
ints=[]
for ln in open('device/internal_tree.txt',encoding='utf-8',errors='replace'):
    ln=ln.strip()
    if '|' not in ln: continue
    sz,p=ln.split('|',1)
    try: sz=int(sz)
    except: continue
    ints.append((sz,p))
sd=collections.defaultdict(list)
for ln in open('device/roms_index_1135.txt',encoding='utf-8',errors='replace'):
    p=ln.strip()
    if not p: continue
    k=key_of(p)
    if k: sd.setdefault(k.split('/')[0],[]).append(k)
intk=collections.defaultdict(list)
for sz,p in ints:
    k=key_of(p)
    if k: intk.setdefault(k.split('/')[0],[]).append((sz,k))
cat={}
for f in glob.glob('device/catalog_es/*'):
    s=os.path.basename(f).split('.')[0]; n=0
    for ln in open(f,encoding='utf-8',errors='replace'):
        ln=ln.strip()
        if ln:
            try: json.loads(ln); n+=1
            except: pass
    cat[s]=n
rows=[]
for s in sorted(set(list(cat)+list(sd)+list(intk))):
    stubs=[k for sz,k in intk.get(s,[]) if sz<2048]
    withreal=sum(1 for k in stubs if k in set(sd.get(s,[])))
    huecos=len(stubs)-without if False else len(stubs)-withreal
    rows.append((s,cat.get(s,0),len(stubs),withreal,huecos,len(sd.get(s,[]))))
rows.sort(key=lambda r:-(r[4]))
tot=[sum(r[i] for r in rows) for i in range(1,6)]
# TSV
with open('device/biblioteca_reporte.tsv','w',encoding='utf-8') as f:
    f.write('sistema\tfichas_catalogo\tstubs_indice\tcon_rom_real\thuecos\treales_en_sd\n')
    for r in rows: f.write('\t'.join(str(x) for x in r)+'\n')
print('sistema fichas stubs con_real huecos sd_reales')
for r in rows[:8]: print(r)
print('TOTAL', tot)
# HTML minimalista
def bar(a,b,color='#111'):
    w=0 if b==0 else int(120*a/b)
    return '<span class="bar"><i style="width:%dpx;background:%s"></i></span>' % (w,color)
h=[]
h.append('<!doctype html><html lang="es"><meta charset="utf-8"><title>Biblioteca real vs catálogo — AYN Thor</title>')
h.append('<style>body{background:#fff;color:#111;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;max-width:920px;margin:48px auto;padding:0 20px}'
 'h1{font-size:26px;font-weight:600;margin:0 0 4px}h2{font-size:17px;font-weight:600;margin:36px 0 10px;border-bottom:1px solid #e5e5e5;padding-bottom:6px}'
 'p{margin:8px 0}.muted{color:#777}table{border-collapse:collapse;width:100%;font-size:13px}th{text-align:left;font-weight:500;color:#777;border-bottom:1px solid #ddd;padding:6px 4px}'
 'td{padding:4px;border-bottom:1px solid #f0f0f0}td.n{text-align:right;font-variant-numeric:tabular-nums}.bar{display:inline-block;width:120px;height:6px;background:#eee;vertical-align:middle;margin-left:8px}'
 '.bar i{display:block;height:6px}code{background:#f5f5f5;padding:1px 4px;border-radius:3px}ul{margin:8px 0 8px 18px;padding:0}li{margin:4px 0}'
 'a{color:#111;text-decoration:none;border-bottom:1px solid #ccc}'
 '#idx{columns:2;font-size:13px}</style>')
h.append('<h1>Biblioteca real vs catálogo</h1><p class="muted">Generado el 2026-11-08 · datos: <code>device/internal_tree.txt</code>, <code>device/roms_index_1135.txt</code>, <code>device/catalog_es/</code></p>')
h.append('<h2 id="resumen">Resumen</h2><ul>')
h.append('<li>Fichas en el catálogo de la app: <b>%d</b></li>' % tot[0])
h.append('<li>Entradas del índice interno (stubs de 105 B con una URL dentro): <b>%d</b></li>' % tot[1])
h.append('<li>Stubs con ROM real en la SD: <b>%d</b></li>' % tot[2])
h.append('<li><b>Huecos reales</b> (entrada en la app sin fichero jugable): <b>%d</b></li>' % tot[3])
h.append('<li>Ficheros reales en la SD: <b>%d</b> (incluye cuarentena y sistema)</li>' % tot[4])
h.append('</ul><p>El árbol interno <code>/storage/emulated/0/ROMs</code> contiene %d ficheros, de los cuales <b>%d son stubs de menos de 2 KB</b> que solo guardan una URL a archive.org. Solo hay <b>1 fichero real</b> (%s).</p>' % (len(ints), sum(1 for sz,p in ints if sz<2048), html.escape([p for sz,p in ints if sz>=2048][0] if any(sz>=2048 for sz,p in ints) else '-')))
h.append('<h2 id="indice">Índice</h2><div id="idx"><p><a href="#resumen">Resumen</a><br><a href="#hallazgo">Hallazgo: el error de FBNeo</a><br><a href="#tabla">Tabla por sistema</a><br><a href="#leer">Cómo leer los números</a><br><a href="#siguiente">Qué hacer después</a></p></div>')
h.append('<h2 id="hallazgo">Hallazgo: por qué fallan lanzamientos que parecen buenos</h2>'
 '<p>Al cargar <code>/storage/emulated/0/ROMs/cps1/1941.zip</code> (105 B, contiene solo una URL) con el core FBNeo, el emulador responde:</p>'
 '<p class="muted" style="border-left:2px solid #ddd;padding-left:12px"><i>This game is known but one of your romsets is missing files for THIS VERSION of FBNeo. Verify the following romsets : 1941 — None of those archives was found in your paths</i></p>'
 '<p>El zip real de la SD (<code>/storage/FFF9-FF05/ROMs/cps1/1941.zip</code>, 1.420.289 B) tiene los 19 ficheros con <b>CRC exacto</b>, así que el set está bien: el fallo es que se lanzó el stub, no la ROM. Cualquier ficha sin fichero real acaba igual: error del core o pantalla negra, en vez de un aviso de «no descargado».</p>')
h.append('<h2 id="tabla">Tabla por sistema</h2><table><tr><th>Sistema</th><th class="n">Fichas</th><th class="n">Stubs</th><th class="n">Con ROM real</th><th class="n">Huecos</th><th>Cobertura</th></tr>')
for s,c,st,wr,hue,sdr in rows:
    if c==0 and st==0: continue
    h.append('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td>%s</td></tr>' % (html.escape(s),c,st,wr,hue,bar(wr,st if st else 1)))
h.append('</table><p class="muted">Barra = proporción de entradas con ROM real presente en la SD.</p>')
h.append('<h2 id="leer">Cómo leer los números</h2><ul>'
 '<li><b>Fichas</b>: entradas del catálogo (lo que la app ofrece).</li>'
 '<li><b>Stubs</b>: ficheros del índice interno que la app usa para pintar la lista.</li>'
 '<li><b>Con ROM real</b>: el stub tiene un fichero de verdad en la SD con el mismo nombre → lanzable.</li>'
 '<li><b>Huecos</b>: la app muestra el juego pero no hay fichero; lanzarlo da error del core.</li>'
 '<li>El arcade (mame, fbneo, cps1/2/3, neogeo, model2/3, naomi, atomiswave) es lo único con cobertura alta; consolas van casi vacías tras la cuarentena japonesa.</li></ul>')
h.append('<h2 id="siguiente">Qué hacer después</h2><ul>'
 '<li>Descargar desde la app solo lo que se vaya a jugar: 9.189 huecos son varios TB.</li>'
 '<li>Pedir a la app que, si el fichero no existe o pesa &lt;2 KB, muestre «Descargar» en vez de lanzar.</li>'
 '<li>Los 2.932 ficheros reales de la SD que no están en el índice interno no aparecen en la biblioteca de la app (ES-DE sí los ve por gamelist).</li></ul>')
h.append('</html>')
open('docs/INFORME_BIBLIOTECA.html','w',encoding='utf-8').write('\n'.join(h))
print('html ->', os.path.getsize('docs/INFORME_BIBLIOTECA.html'), 'bytes')
