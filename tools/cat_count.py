import json,os,glob,collections
c=collections.Counter(); tot=0
for f in sorted(glob.glob('device/catalog_es/*.jsonl')):
    sysn=os.path.basename(f).split('.')[0]
    n=0
    for ln in open(f,encoding='utf-8',errors='replace'):
        ln=ln.strip()
        if not ln: continue
        try: json.loads(ln); n+=1
        except: pass
    c[sysn]=n; tot+=n
print('total fichas:', tot)
print(', '.join('%s=%d'%(k,v) for k,v in c.most_common(40)))
