# Corre en la consola con ES detenido. Uso: python3 gamelist_img.py <sistema> [<sistema>...]
# Para cada images/<base>-image.png nuevo, setea <image> del juego cuyo archivo es <base>.<ext>.
# No pisa <image> existentes. Backup en /userdata/backup_claude/2026-11-02/gamelists/.
import os, re, sys, shutil
import xml.etree.ElementTree as ET

ROMS = "/userdata/roms"
BK = "/userdata/backup_claude/2026-11-02/gamelists"
SKIP = (".xml", ".txt", ".png", ".jpg", ".cfg", ".cue")

def clean(base):
    n = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", base).strip()
    m = re.match(r"^(.*), (The|A|An)$", n)
    return f"{m.group(2)} {m.group(1)}" if m else n

for s in sys.argv[1:]:
    d = os.path.join(ROMS, s); gl = os.path.join(d, "gamelist.xml"); img = os.path.join(d, "images")
    if not os.path.isdir(img): print(s, "sin carpeta images"); continue
    os.makedirs(BK, exist_ok=True)
    if os.path.exists(gl):
        if not os.path.exists(os.path.join(BK, s + ".xml")): shutil.copy2(gl, os.path.join(BK, s + ".xml"))
        tree = ET.parse(gl); root = tree.getroot()
    else:
        root = ET.Element("gameList"); tree = ET.ElementTree(root)
    bypath = {}
    for g in root.findall("game"):
        p = (g.findtext("path") or "").strip()
        if p: bypath[os.path.normpath(p.lstrip("./"))] = g
    files = {}
    for f in os.listdir(d):
        if os.path.isfile(os.path.join(d, f)) and not f.startswith(".") and not f.lower().endswith(SKIP):
            files.setdefault(os.path.splitext(f)[0], []).append(f)
    added = updated = kept = 0
    for im in sorted(os.listdir(img)):
        if not im.endswith("-image.png"): continue
        base = im[:-len("-image.png")]
        cands = files.get(base)
        if not cands: continue
        f = next((c for c in cands if c.endswith(".m3u")), cands[0])
        g = bypath.get(os.path.normpath(f))
        if g is None:
            g = ET.SubElement(root, "game")
            ET.SubElement(g, "path").text = "./" + f
            ET.SubElement(g, "name").text = clean(base)
            added += 1
        e = g.find("image")
        if e is not None and (e.text or "").strip():
            kept += 1; continue
        if e is None: e = ET.SubElement(g, "image")
        e.text = "./images/" + im; updated += 1
    if hasattr(ET, "indent"): ET.indent(tree, "\t")
    tree.write(gl, encoding="utf-8", xml_declaration=True)
    n_img = sum(1 for g in root.findall("game") if (g.findtext("image") or "").strip())
    print(f"{s}: +{updated} imágenes ({added} juegos nuevos en la lista, {kept} ya tenían) → {n_img} con imagen")
