#!/usr/bin/env python3
"""Render ESTADO.md / TAREAS.md a HTML minimo con indice lateral."""
import re, html, unicodedata

def slug(t, used):
    s = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "s"
    if s in used:
        used[s] = used[s] + 1
        s = s + "-" + str(used[s])
    used[s] = used.get(s, 0) + 1
    return s

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r"<a href=\"\2\">\1</a>", s)
    return s

def render(md, title, sub):
    lines = md.splitlines(); out = []; toc = []; used = {}; i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            buf = []; i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl = len(m.group(1)); txt = m.group(2).strip()
            if lvl == 1:
                out.append("<h1>" + inline(txt) + "</h1>")
            else:
                sl = slug(txt, used)
                out.append("<h%d id=\"%s\">%s</h%d>" % (lvl, sl, inline(txt), lvl))
                if lvl == 2: toc.append((sl, re.sub(r"[`*]", "", txt)))
            i += 1; continue
        if ln.strip() == "---":
            out.append("<hr>"); i += 1; continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip()); i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue
        if ln.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = [c for c in cells if not all(re.match(r"^:?-{2,}:?$", x) for x in c)]
            if body:
                th = "".join("<th>" + inline(x) + "</th>" for x in body[0])
                trs = "".join("<tr>" + "".join("<td>" + inline(x) + "</td>" for x in row) + "</tr>" for row in body[1:])
                out.append("<table><thead><tr>" + th + "</tr></thead><tbody>" + trs + "</tbody></table>")
            continue
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", ln)
        if m:
            items = []; ordered = m.group(2)[0].isdigit()
            while i < len(lines):
                mm = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", lines[i])
                if not mm: break
                t = mm.group(3)
                cb = re.match(r"^\[([ xX])\]\s+(.*)$", t)
                if cb:
                    mark = "&#9745;" if cb.group(1).lower() == "x" else "&#9744;"
                    items.append("<li><span class=\"cb\">" + mark + "</span> " + inline(cb.group(2)) + "</li>")
                else:
                    items.append("<li>" + inline(t) + "</li>")
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<" + tag + ">" + "".join(items) + "</" + tag + ">")
            continue
        if not ln.strip():
            i += 1; continue
        buf = []
        while i < len(lines) and lines[i].strip() and lines[i].strip() != "---" and not re.match(r"^(#{1,4}\s|```|>|\s*[-*+]\s|\s*\d+\.\s|\|)", lines[i]):
            buf.append(lines[i].strip()); i += 1
        if buf: out.append("<p>" + inline(" ".join(buf)) + "</p>")
    nav = "".join("<a href=\"#%s\">%s</a>" % (sl, html.escape(t)) for sl, t in toc)
    css = """
:root{--bg:#0b0b0c;--fg:#ededed;--dim:#8a8a8e;--line:#232326}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,"Segoe UI",Inter,sans-serif}
.wrap{display:grid;grid-template-columns:280px 1fr;max-width:1200px;margin:0 auto;min-height:100vh}
nav{position:sticky;top:0;align-self:start;padding:28px 18px;border-right:1px solid var(--line);height:100vh;overflow:auto}
nav h1{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin:0 0 14px;font-weight:600}
nav a{display:block;color:var(--fg);text-decoration:none;padding:4px 0 4px 10px;font-size:13px;border-left:2px solid transparent;line-height:1.35}
nav a:hover{border-left-color:#fff;color:#fff}
main{padding:36px 44px 80px;min-width:0}
h1{font-size:26px;letter-spacing:-.02em;margin:0 0 4px}
h2{font-size:20px;margin:46px 0 12px;padding-top:16px;border-top:1px solid var(--line);letter-spacing:-.01em}
h3{font-size:14px;color:var(--dim);text-transform:uppercase;letter-spacing:.08em;margin:26px 0 8px}
h4{font-size:15px;margin:20px 0 6px}
p{margin:9px 0;color:#d4d4d8}
ul,ol{margin:8px 0;padding-left:22px}
li{margin:3px 0}
code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:13px;background:#151517;border:1px solid var(--line);border-radius:4px;padding:1px 5px;color:#fff}
pre{background:#111113;border:1px solid var(--line);border-radius:8px;padding:12px 14px;overflow:auto;font-size:12.5px;line-height:1.55}
pre code{background:none;border:0;padding:0;white-space:pre}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13.5px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
blockquote{margin:14px 0;padding:2px 0 2px 14px;border-left:2px solid #fff;color:#c9c9ce}
hr{border:0;border-top:1px solid var(--line);margin:36px 0}
.sub{color:var(--dim);font-size:13px;margin:0 0 20px}
.cb{color:var(--dim);font-size:13px}
a{color:#fff}
@media(max-width:860px){.wrap{grid-template-columns:1fr}nav{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}main{padding:24px 18px 60px}}
"""
    tpl = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>__CSS__</style>
</head>
<body>
<div class="wrap">
<nav>
<h1>__TITLE__</h1>
__NAV__
</nav>
<main>
<p class="sub">__SUB__</p>
__BODY__
</main>
</div>
</body>
</html>
"""
    page = tpl.replace("__TITLE__", html.escape(title)).replace("__CSS__", css).replace("__NAV__", nav).replace("__SUB__", sub).replace("__BODY__", "\n".join(out))
    page = page.lstrip()
    return page, len(toc)
def main():
    pairs = [("ESTADO.md", "ESTADO-LOG.html", "AYN Thor - registro completo"), ("TAREAS.md", "TAREAS-LOG.html", "AYN Thor - lista de tareas")]
    for src, dst, title in pairs:
        md = open(src, encoding="utf-8").read()
        sub = "Generado desde <code>" + src + "</code>; no editar a mano. Origen: " + str(len(md)) + " caracteres."
        page, n = render(md, title, sub)
        open(dst, "w", encoding="utf-8").write(page)
        print(dst, "bytes=" + str(len(page)), "h2=" + str(n))

if __name__ == "__main__":
    main()
