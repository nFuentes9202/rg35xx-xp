#!/usr/bin/env python3
# Reproductor XP (estilo reproductor de los 2000, diseño propio) para RG35XX Pro (Knulli) — hecho por Claude para Nahuel.
# - Reproduce /userdata/music con mpv (009 Sound System primero, después el resto en aleatorio).
# - Se dibuja en una capa propia del motor de pantalla (/dev/disp canal 3 capa 1), solo en el escritorio.
# - Controles por clic (modo mouse): anterior / play-pausa / stop / siguiente / volumen -/+ / lista.
# - Pausa solo con un juego abierto. Volumen = volumen del sistema (pactl).
import os, sys, json, time, random, socket, subprocess, struct, ctypes, mmap, platform, urllib.request, glob
try:
    import fcntl
except ImportError:
    fcntl = None
from PIL import Image, ImageDraw, ImageFont

ES_CONSOLA = os.path.exists("/dev/disp")
MUSICA = "/userdata/music"
SOCK = "/tmp/xp_player.sock"
CMD = "/tmp/xp_player.cmd"
ESTADO = "/tmp/xp_player.state"
PW, PH = 275, 116                 # ventana principal
LW, LH = 275, 190                 # lista desplegable
POS = (352, 70)                   # posición en el escritorio
FILAS = 11

def fuente(nombres, tam):
    for n in nombres:
        for d in ("/usr/share/fonts/dejavu/", "C:/Windows/Fonts/", ""):
            try: return ImageFont.truetype(d + n, tam)
            except Exception: pass
    return ImageFont.load_default()
F_TIT = fuente(["DejaVuSans-Bold.ttf", "tahomabd.ttf"], 9)
F_LCD = fuente(["DejaVuSansMono-Bold.ttf", "DejaVuSans-Bold.ttf", "consolab.ttf"], 22)
F_TXT = fuente(["DejaVuSansCondensed.ttf", "tahoma.ttf"], 10)
F_MIN = fuente(["DejaVuSansCondensed-Bold.ttf", "tahomabd.ttf"], 8)

# ---------------- dibujo ----------------
def grad(d, box, c1, c2):
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        d.line([(x0, y), (x1, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))

def bisel(d, box, luz=(120, 125, 140), sombra=(18, 20, 28)):
    x0, y0, x1, y1 = box
    d.line([(x0, y1), (x0, y0), (x1, y0)], fill=luz); d.line([(x0, y1), (x1, y1), (x1, y0)], fill=sombra)

BOTONES = {  # nombre: caja relativa a la ventana
    "prev": (16, 88, 38, 106), "play": (39, 88, 61, 106), "pause": (62, 88, 84, 106),
    "stop": (85, 88, 107, 106), "next": (108, 88, 130, 106),
    "voldown": (178, 88, 198, 106), "volup": (199, 88, 219, 106), "pl": (228, 88, 258, 106),
}

def base_ventana():
    im = Image.new("RGB", (PW, PH)); d = ImageDraw.Draw(im)
    grad(d, (0, 0, PW - 1, PH - 1), (62, 66, 84), (34, 36, 48))
    bisel(d, (0, 0, PW - 1, PH - 1), (130, 136, 156), (10, 10, 16))
    # barra de título
    grad(d, (3, 3, PW - 4, 13), (40, 90, 200), (16, 40, 120))
    d.text((PW // 2, 8), "REPRODUCTOR XP", font=F_TIT, fill=(230, 235, 255), anchor="mm")
    for xx in (8, 14): d.line([(xx, 6), (xx + 3, 6)], fill=(200, 210, 255))
    # pantalla LCD izquierda
    d.rectangle([10, 18, 102, 54], fill=(4, 8, 6)); bisel(d, (10, 18, 102, 54), (14, 18, 16), (90, 96, 110))
    # pantalla de título derecha
    d.rectangle([108, 18, 266, 34], fill=(4, 8, 6)); bisel(d, (108, 18, 266, 34), (14, 18, 16), (90, 96, 110))
    d.rectangle([108, 38, 266, 54], fill=(4, 8, 6)); bisel(d, (108, 38, 266, 54), (14, 18, 16), (90, 96, 110))
    # barra de progreso (fondo)
    d.rectangle([10, 66, 266, 74], fill=(18, 20, 28)); bisel(d, (10, 66, 266, 74), (14, 14, 20), (90, 96, 110))
    # botones
    for n, (x0, y0, x1, y1) in BOTONES.items():
        grad(d, (x0, y0, x1, y1), (150, 156, 176), (82, 86, 104)); bisel(d, (x0, y0, x1, y1), (210, 214, 230), (30, 32, 42))
        cx, cy, c = (x0 + x1) // 2, (y0 + y1) // 2, (20, 22, 30)
        if n == "prev": d.polygon([(cx + 4, cy - 5), (cx + 4, cy + 5), (cx - 3, cy)], fill=c); d.rectangle([cx - 6, cy - 5, cx - 4, cy + 5], fill=c)
        if n == "play": d.polygon([(cx - 4, cy - 6), (cx - 4, cy + 6), (cx + 6, cy)], fill=c)
        if n == "pause": d.rectangle([cx - 5, cy - 5, cx - 2, cy + 5], fill=c); d.rectangle([cx + 2, cy - 5, cx + 5, cy + 5], fill=c)
        if n == "stop": d.rectangle([cx - 5, cy - 5, cx + 5, cy + 5], fill=c)
        if n == "next": d.polygon([(cx - 4, cy - 5), (cx - 4, cy + 5), (cx + 3, cy)], fill=c); d.rectangle([cx + 4, cy - 5, cx + 6, cy + 5], fill=c)
        if n == "voldown": d.rectangle([cx - 5, cy - 1, cx + 5, cy + 1], fill=c)
        if n == "volup": d.rectangle([cx - 5, cy - 1, cx + 5, cy + 1], fill=c); d.rectangle([cx - 1, cy - 5, cx + 1, cy + 5], fill=c)
        if n == "pl": d.text((cx, cy), "PL", font=F_MIN, fill=c, anchor="mm")
    d.text((150, 97), "VOL", font=F_MIN, fill=(170, 176, 196), anchor="mm")
    return im
BASE = base_ventana()

def mmss(s): s = int(max(0, s)); return "%02d:%02d" % (s // 60, s % 60)

def render(st, tick):
    im = BASE.copy(); d = ImageDraw.Draw(im)
    verde, verde_osc = (60, 255, 90), (20, 90, 30)
    # tiempo grande
    d.text((14, 20), "▶" if st["estado"] == "play" else ("❚❚" if st["estado"] == "pause" else "■"), font=F_MIN, fill=verde)
    d.text((98, 22), mmss(st["pos"]), font=F_LCD, fill=verde, anchor="ra")
    # mini "espectro" animado
    random.seed(int(tick * 4))
    for i in range(14):
        h = random.randint(2, 12) if st["estado"] == "play" else 1
        x = 14 + i * 6; d.rectangle([x, 52 - h, x + 4, 52], fill=verde if h < 9 else (220, 230, 60))
    # título con marquesina
    titulo = "%d. %s  ***  " % (st["idx"] + 1, st["titulo"])
    ancho = d.textlength(titulo, font=F_TXT); off = int(tick * 30) % max(1, int(ancho))
    tw = Image.new("RGB", (156, 14), (4, 8, 6)); td = ImageDraw.Draw(tw)
    td.text((-off, 1), titulo * 3, font=F_TXT, fill=verde)
    im.paste(tw, (110, 20))
    d.text((112, 41), "192 kbps   44 kHz   estéreo", font=F_MIN, fill=verde_osc)
    # progreso
    if st["dur"] > 0:
        w = int(254 * min(1, st["pos"] / st["dur"])); d.rectangle([11, 67, 11 + w, 73], fill=(60, 140, 255))
    # volumen (barra)
    v = st["vol"]; d.rectangle([140, 104, 140 + int(30 * v / 100), 106], fill=(60, 255, 90))
    d.text((150, 89), "%d%%" % v, font=F_MIN, fill=(220, 225, 240), anchor="mm")
    return im

def render_lista(st, scroll):
    im = Image.new("RGB", (LW, LH)); d = ImageDraw.Draw(im)
    grad(d, (0, 0, LW - 1, LH - 1), (40, 42, 56), (28, 30, 40)); bisel(d, (0, 0, LW - 1, LH - 1), (130, 136, 156), (10, 10, 16))
    grad(d, (3, 3, LW - 4, 13), (40, 90, 200), (16, 40, 120))
    d.text((LW // 2, 8), "LISTA DE TEMAS", font=F_TIT, fill=(230, 235, 255), anchor="mm")
    d.rectangle([8, 18, LW - 22, LH - 8], fill=(4, 8, 6))
    for i in range(FILAS):
        k = scroll + i
        if k >= len(st["lista"]): break
        y = 20 + i * 15
        if k == st["idx"]: d.rectangle([9, y, LW - 23, y + 14], fill=(30, 70, 160))
        d.text((12, y + 1), "%d. %s" % (k + 1, st["lista"][k]), font=F_TXT, fill=(255, 255, 255) if k == st["idx"] else (60, 255, 90))
    # flechas de desplazamiento
    for (y0, up) in ((18, True), (LH - 26, False)):
        grad(d, (LW - 19, y0, LW - 8, y0 + 18), (150, 156, 176), (82, 86, 104)); bisel(d, (LW - 19, y0, LW - 8, y0 + 18), (210, 214, 230), (30, 32, 42))
        cx, cy = LW - 13, y0 + 9
        d.polygon([(cx - 4, cy + 2), (cx + 4, cy + 2), (cx, cy - 3)] if up else [(cx - 4, cy - 2), (cx + 4, cy - 2), (cx, cy + 3)], fill=(20, 22, 30))
    return im

if __name__ == "__main__" and not ES_CONSOLA:
    st = {"estado": "play", "pos": 83, "dur": 236, "idx": 0, "titulo": "009 Sound System - Dreamscape", "vol": 75,
          "lista": ["009 Sound System - Dreamscape", "009 Sound System - With A Spirit", "009 Sound System - Trinity",
                    "009 Sound System - Born to Be Wasted", "Elektronomia - Sky High", "Disfigure - Blank", "Janji - Heroes Tonight",
                    "Cartoon - On & On", "Different Heaven - My Heart", "Electro-Light - Symbolism", "Jim Yosef - Firefly", "Lost Sky - Dreams"]}
    fondo = Image.open(sys.argv[1]).convert("RGB")
    fondo.paste(render(st, 1.3), POS); fondo.paste(render_lista(st, 0), (POS[0], POS[1] + PH))
    fondo.save(sys.argv[2]); print("preview ok")

# ================= servicio en la consola =================
PENV = {"XDG_RUNTIME_DIR": "/var/run", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": "/userdata/system"}
def log(*a):
    with open("/tmp/xp_player.log", "a") as f: print(time.strftime("%H:%M:%S"), *a, file=f)

def armar_lista():
    todos = sorted(f for f in os.listdir(MUSICA) if f.lower().endswith((".mp3", ".ogg", ".flac", ".wav")))
    primeros_orden = ["Dreamscape", "With A Spirit", "Trinity", "Born to Be Wasted"]
    nueve = [f for n in primeros_orden for f in todos if f.startswith("009") and n.lower() in f.lower()]
    nueve += [f for f in todos if f.startswith("009") and f not in nueve]
    resto = [f for f in todos if f not in nueve]; random.shuffle(resto)
    return nueve + resto

class Mpv:
    def __init__(self):
        if os.path.exists(SOCK): os.remove(SOCK)
        self.p = subprocess.Popen(["mpv", "--no-video", "--idle=yes", "--ao=pulse", "--no-terminal",
                                   "--input-ipc-server=" + SOCK], env=PENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            if os.path.exists(SOCK): break
            time.sleep(0.1)
    def cmd(self, *args):
        try:
            s = socket.socket(socket.AF_UNIX); s.settimeout(0.5); s.connect(SOCK)
            s.sendall((json.dumps({"command": list(args)}) + "\n").encode()); r = s.recv(65536).decode(); s.close()
            for linea in r.splitlines():
                j = json.loads(linea)
                if "error" in j: return j.get("data")
        except Exception: return None
    def get(self, prop): return self.cmd("get_property", prop)

def vol_get():
    try:
        o = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], env=PENV, capture_output=True, text=True, timeout=1).stdout
        return int(o.split("/")[1].strip().rstrip("%"))
    except Exception: return 0
def vol_cambiar(delta):
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", ("+%d%%" if delta > 0 else "-%d%%") % abs(delta)], env=PENV, timeout=1)
    if vol_get() > 100: subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"], env=PENV, timeout=1)

def juego_corriendo():
    try:
        with urllib.request.urlopen("http://127.0.0.1:1234/runningGame", timeout=0.4) as r:
            return r.status == 200 and len(r.read().strip()) > 2
    except Exception: return False

class Capa:
    """Capa propia del motor de pantalla (canal 3, capa 1), en memoria sobrante del framebuffer."""
    W, H, FB = 640, 480, 0xff800000
    OFF = 640 * 960 * 4 + 32 * 32 * 4 + 80 * 80 * 4 + 4096
    def __init__(self):
        assert platform.release() == "4.9.170", "kernel distinto"
        self.libc = ctypes.CDLL(None, use_errno=True); self.disp = os.open("/dev/disp", os.O_RDWR)
        b = (ctypes.c_ubyte * 180)(); struct.pack_into("<III", b, 168, 0, 1, 0)
        a = (ctypes.c_ulong * 4)(0, ctypes.addressof(b), 1, 0); assert self.libc.ioctl(self.disp, 0x48, a) == 0
        assert struct.unpack_from("<Q", b, 32)[0] == self.FB and struct.unpack_from("<II", b, 16) == (self.W, self.H), "formato distinto"
        self.fb = os.open("/dev/fb0", os.O_RDWR)
        self.mem = mmap.mmap(self.fb, self.OFF + PW * (PH + LH) * 4, offset=0)
        self.c = (ctypes.c_ubyte * 180)(); ctypes.memmove(self.c, b, 180)
        self.c[4] = 2; self.c[5] = 1; self.c[6] = 255
        struct.pack_into("<Q", self.c, 32, self.FB + self.OFF)
        self.args = (ctypes.c_ulong * 4)(0, ctypes.addressof(self.c), 1, 0); self.on = None; self.h = PH
    def dibujar(self, im):
        r, g, b = im.split()
        self.mem[self.OFF:self.OFF + im.width * im.height * 4] = Image.merge("RGBA", (b, g, r, Image.new("L", im.size, 255))).tobytes()
    def mostrar(self, on, h):
        if on == self.on and h == self.h: return
        for o in (56, 64, 72): struct.pack_into("<II", self.c, o, PW, h)
        struct.pack_into("<iiII", self.c, 8, POS[0], POS[1], PW, h)
        struct.pack_into("<qqqq", self.c, 120, 0, 0, PW << 32, h << 32)
        struct.pack_into("<III", self.c, 168, 1 if on else 0, 3, 1)
        self.libc.ioctl(self.disp, 0x47, self.args); self.on, self.h = on, h
    def pixel(self, px, py):
        v = fcntl.ioctl(self.fb, 0x4600, bytes(160)); yoff = struct.unpack_from("<I", v, 20)[0]
        o = ((py + yoff) * self.W + px) * 4; bb, gg, rr, _ = self.mem[o:o + 4]; return (rr, gg, bb)
    def escritorio(self):
        cerca = lambda c, r, t=22: all(abs(c[i] - r[i]) <= t for i in range(3))
        menu, marco = self.pixel(500, 44), self.pixel(10, 200)
        if cerca(menu, (236, 233, 216)) and marco[2] > 150 and marco[0] < 60: return False
        ini, cielo = self.pixel(40, 470), self.pixel(180, 40)
        return ini[1] > ini[0] + 25 and cielo[2] > cielo[0] + 40

def main():
    open("/tmp/xp_player.log", "w").close()
    capa = Capa(); mpv = Mpv(); lista = armar_lista()
    st = {"estado": "stop", "pos": 0, "dur": 0, "idx": 0, "titulo": "", "vol": vol_get(),
          "lista": [os.path.splitext(f)[0] for f in lista]}
    ui = {"abierta": False, "scroll": 0, "pausado_por_juego": False, "visible": False}
    t0 = time.time()
    def tocar(i):
        st["idx"] = i % len(lista); mpv.cmd("loadfile", os.path.join(MUSICA, lista[st["idx"]]), "replace")
        mpv.cmd("set_property", "pause", False); st["titulo"] = st["lista"][st["idx"]]; st["estado"] = "play"; st["pos"] = 0
        log("tema", st["titulo"])
    def guardar():
        rects = {"ventana": [POS[0], POS[1], POS[0] + PW, POS[1] + PH]}
        if ui["abierta"]: rects["lista"] = [POS[0], POS[1] + PH, POS[0] + LW, POS[1] + PH + LH]
        json.dump({"visible": bool(capa.on), "rects": rects}, open(ESTADO + ".tmp", "w")); os.replace(ESTADO + ".tmp", ESTADO)
    def clic(x, y):
        rx, ry = x - POS[0], y - POS[1]
        for n, (x0, y0, x1, y1) in BOTONES.items():
            if x0 <= rx <= x1 and y0 <= ry <= y1:
                if n == "prev": tocar(st["idx"] - 1)
                if n == "next": tocar(st["idx"] + 1)
                if n == "play":
                    if st["estado"] == "stop": tocar(st["idx"])
                    else: mpv.cmd("set_property", "pause", False); st["estado"] = "play"
                if n == "pause":
                    p = st["estado"] == "play"; mpv.cmd("set_property", "pause", p); st["estado"] = "pause" if p else "play"
                if n == "stop": mpv.cmd("stop"); st["estado"] = "stop"; st["pos"] = 0
                if n == "voldown": vol_cambiar(-5)
                if n == "volup": vol_cambiar(5)
                if n == "pl":
                    ui["abierta"] = not ui["abierta"]; ui["scroll"] = max(0, min(st["idx"] - 2, len(lista) - FILAS))
                return n
        if 10 <= rx <= 266 and 66 <= ry <= 74 and st["dur"] > 0:
            mpv.cmd("seek", (rx - 10) / 256 * st["dur"], "absolute"); return "saltar"
        if ui["abierta"] and PH <= ry <= PH + LH:
            ly = ry - PH
            if LW - 19 <= rx <= LW - 8 and 18 <= ly <= 36: ui["scroll"] = max(0, ui["scroll"] - FILAS + 1); return "subir"
            if LW - 19 <= rx <= LW - 8 and LH - 26 <= ly <= LH - 8:
                ui["scroll"] = min(max(0, len(lista) - FILAS), ui["scroll"] + FILAS - 1); return "bajar"
            k = ui["scroll"] + (ly - 20) // 15
            if 8 <= rx <= LW - 22 and 20 <= ly and 0 <= k < len(lista): tocar(k); return "elegir %d" % k
        return "nada"
    tocar(0)
    t_lento = 0
    while True:
        now = time.time()
        if os.path.exists(CMD):
            for ln in open(CMD).read().splitlines():
                p = ln.split()
                if p[:1] == ["click"] and len(p) == 3: log("clic", p[1], p[2], "->", clic(int(p[1]), int(p[2])))
                elif p[:1] == ["next"]: tocar(st["idx"] + 1)
            os.remove(CMD)
        if now - t_lento > 1.0:
            t_lento = now; g = juego_corriendo()
            if g and st["estado"] == "play" and not ui["pausado_por_juego"]:
                mpv.cmd("set_property", "pause", True); ui["pausado_por_juego"] = True; log("pausa (juego)")
            if not g and ui["pausado_por_juego"]:
                mpv.cmd("set_property", "pause", False); ui["pausado_por_juego"] = False; log("sigue")
            st["vol"] = vol_get()
            if st["estado"] == "play" and not ui["pausado_por_juego"] and mpv.get("idle-active"): tocar(st["idx"] + 1)
            ui["en_juego"] = g
        if st["estado"] != "stop":
            st["pos"] = mpv.get("time-pos") or st["pos"]; st["dur"] = mpv.get("duration") or st["dur"]
        ui["visible"] = (not ui.get("en_juego", False)) and capa.escritorio()
        im = render(st, now - t0)
        if ui["abierta"]:
            full = Image.new("RGB", (PW, PH + LH)); full.paste(im, (0, 0)); full.paste(render_lista(st, ui["scroll"]), (0, PH)); im = full
        capa.dibujar(im); capa.mostrar(ui["visible"], im.height); guardar()
        time.sleep(0.2)

if __name__ == "__main__" and ES_CONSOLA:
    try:
        main()
    except Exception as ex:
        log("error", repr(ex))
        try: Capa().mostrar(False, PH)
        except Exception: pass
        raise
