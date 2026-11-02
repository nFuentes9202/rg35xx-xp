# Baja carátulas de libretro-thumbnails para cada ROM de roms.txt (sistema|archivo)
# Salida: out/<sistema>/images/<rom sin ext>-image.png (máx 400 px de alto) + informe.tsv
import os, re, sys, io, json, html, urllib.parse, urllib.request, concurrent.futures as cf
from difflib import SequenceMatcher
from PIL import Image

BASE = "https://thumbnails.libretro.com/"
SYS = {
 "atari2600": "Atari - 2600", "fc": "Nintendo - Nintendo Entertainment System", "gamegear": "Sega - Game Gear",
 "gb": "Nintendo - Game Boy", "gba": "Nintendo - Game Boy Advance", "gbc": "Nintendo - Game Boy Color",
 "mastersystem": "Sega - Master System - Mark III", "megadrive": "Sega - Mega Drive - Genesis",
 "n64": "Nintendo - Nintendo 64", "nds": "Nintendo - Nintendo DS", "neogeo": "SNK - Neo Geo",
 "pcengine": "NEC - PC Engine - TurboGrafx 16", "pcenginecd": "NEC - PC Engine CD - TurboGrafx-CD",
 "psx": "Sony - PlayStation", "segacd": "Sega - Mega-CD - Sega CD", "snes": "Nintendo - Super Nintendo Entertainment System",
}
KINDS = ["Named_Boxarts", "Named_Titles", "Named_Snaps"]
OUT = "out"; MAXH = 400

def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = r.read()
    return d if binary else d.decode("utf-8", "replace")

def listing(sysname, kind):
    cache = f"cache/{sysname}__{kind}.json"
    if os.path.exists(cache): return json.load(open(cache, encoding="utf-8"))
    os.makedirs("cache", exist_ok=True)
    try:
        h = get(BASE + urllib.parse.quote(sysname) + "/" + kind + "/")
        names = [html.unescape(urllib.parse.unquote(m))[:-4] for m in re.findall(r'href="([^"?/]+\.png)"', h)]
    except Exception as e:
        print("  listado falló", sysname, kind, e); names = []
    json.dump(names, open(cache, "w", encoding="utf-8"))
    return names

def lr(name):  # caracteres que libretro reemplaza por _
    return re.sub(r'[&*/:`<>?\\|"]', "_", name)

def norm(s):
    s = re.sub(r"\[[^\]]*\]", "", s); s = re.sub(r"\([^)]*\)", "", s)
    s = s.lower().replace("&", "and").replace("_", " ")
    s = re.sub(r"^the |, the\b", "", s.strip()); s = s.replace(", the", "")
    return re.sub(r"[^a-z0-9]+", "", s)

def region_score(n):
    sc = 0
    if "(USA" in n: sc += 4
    if "World" in n: sc += 3
    if "Europe" in n: sc += 2
    if "Japan" in n: sc += 1
    if "Rev" in n or "Beta" in n or "Proto" in n or "Demo" in n: sc -= 1
    return sc

def neogeo_names():
    p = "cache/neogeo_names.json"
    if os.path.exists(p): return json.load(open(p, encoding="utf-8"))
    url = "https://raw.githubusercontent.com/libretro/FBNeo/master/dats/FinalBurn%20Neo%20(ClrMame%20Pro%20XML%2C%20Neogeo%20only).dat"
    x = get(url); m = {}
    for g in re.finditer(r'<game name="([^"]+)"[^>]*>\s*<description>([^<]+)</description>', x):
        m[g.group(1)] = html.unescape(g.group(2))
    json.dump(m, open(p, "w", encoding="utf-8")); return m

def pick(title, names, idx):
    t = lr(title)
    if t in names: return t, "exacto"
    k = norm(title)
    if k and k in idx:
        return max(idx[k], key=region_score), "mismo juego otra región"
    best, bs = None, 0
    for n in names:
        r = SequenceMatcher(None, k, norm(n)).ratio() if k else 0
        if r > bs: best, bs = n, r
    if best and bs >= 0.90: return best, f"parecido {bs:.2f}"
    return None, f"sin match (mejor {best} {bs:.2f})"

def main():
    rows = [l.rstrip("\n").split("|", 1) for l in open("roms.txt", encoding="utf-8") if "|" in l]
    only = set(sys.argv[1:])
    neo = neogeo_names() if (not only or "neogeo" in only) else {}
    m3u_bases = {(s, os.path.splitext(f)[0]) for s, f in rows if f.endswith(".m3u")}
    jobs, report = [], []
    for s in sorted({s for s, _ in rows}):
        if only and s not in only: continue
        lists = {k: listing(SYS[s], k) for k in KINDS}
        idxs = {}
        for k, names in lists.items():
            d = {}
            for n in names: d.setdefault(norm(n), []).append(n)
            idxs[k] = (set(names), d, names)
        for s2, f in rows:
            if s2 != s: continue
            base = os.path.splitext(f)[0]
            if s == "psx" and f.endswith(".chd"):
                b = re.sub(r" \(Disc \d\)$", "", base)
                if (s, b) in m3u_bases: continue
            title = neo.get(base, base) if s == "neogeo" else base
            title = re.sub(r" \(Disc 1\)$", "", title)
            got = None
            for k in KINDS:
                nset, d, names = idxs[k]
                n, why = pick(title, nset, d)
                if n: got = (k, n, why); break
            dest = f"{OUT}/{s}/images/{base}-image.png"
            if got: jobs.append((s, f, got, dest))
            else: report.append((s, f, "", "", why))
    def work(j):
        s, f, (k, n, why), dest = j
        if os.path.exists(dest): return (s, f, k, n, why)
        try:
            data = get(BASE + urllib.parse.quote(SYS[s]) + "/" + k + "/" + urllib.parse.quote(n) + ".png", True)
            im = Image.open(io.BytesIO(data)).convert("RGBA")
            if im.height > MAXH: im = im.resize((round(im.width * MAXH / im.height), MAXH), Image.LANCZOS)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            im.save(dest, optimize=True)
            return (s, f, k, n, why)
        except Exception as e:
            return (s, f, "", n, f"error {e}")
    with cf.ThreadPoolExecutor(6) as ex:
        for i, r in enumerate(ex.map(work, jobs), 1):
            report.append(r)
            if i % 100 == 0: print(f"  {i}/{len(jobs)}", flush=True)
    with open("informe.tsv", "w", encoding="utf-8") as fo:
        for r in sorted(report): fo.write("\t".join(map(str, r)) + "\n")
    tot = len(report); ok = sum(1 for r in report if r[2])
    print(f"TOTAL {ok}/{tot} con imagen")
    from collections import Counter
    c = Counter((r[0], bool(r[2])) for r in report)
    for s in sorted({r[0] for r in report}): print(f"  {s:13} {c[(s,True)]}/{c[(s,True)]+c[(s,False)]}")
main()
