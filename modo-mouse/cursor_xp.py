#!/usr/bin/env python3
# Modo mouse XP para RG35XX Pro (Knulli) — hecho por Claude para Nahuel.
# - Dibuja una flecha en una capa extra del motor de pantalla Allwinner (/dev/disp, canal 1 capa 1).
# - Palanca derecha = mover, R3 = clic. Crea un mouse virtual (uinput) para los clics comunes.
# - Lee la pantalla para saber si estás en el escritorio o en una ventana, y hace funcionar los
#   botones del tema XP (cerrar, minimizar, maximizar, inicio, tareas, íconos del escritorio).
# Seguridad: verifica kernel y formato antes de tocar nada; usa solo memoria sobrante del framebuffer;
# apaga la capa al salir; se esconde con un juego abierto. Nada persiste tras un reinicio.
import json, ctypes, os, sys, struct, mmap, time, signal, select, fcntl, urllib.request, platform
import evdev, subprocess
from evdev import UInput, ecodes as e, ff

KERNEL = "4.9.170"
DIR = os.path.dirname(os.path.abspath(__file__))
SET, GET = 0x47, 0x48
FB_BASE, W, H = 0xff800000, 640, 480
OFF = 640 * 960 * 4
CW = CH = 32
DEAD, MAXV = 700, 4096
log = open("/tmp/cursor_xp.log", "a")
def L(*a): print(time.strftime("%H:%M:%S"), *a, file=log, flush=True)

if platform.release() != KERNEL:
    L("kernel distinto", platform.release(), "-> no hago nada"); sys.exit(1)

libc = ctypes.CDLL(None, use_errno=True)
disp = os.open("/dev/disp", os.O_RDWR)
def get_cfg(ch, ly):
    b = (ctypes.c_ubyte * 180)(); struct.pack_into("<III", b, 168, 0, ch, ly)
    a = (ctypes.c_ulong * 4)(0, ctypes.addressof(b), 1, 0)
    if libc.ioctl(disp, GET, a) != 0: raise OSError("GET falló")
    return b
base = get_cfg(1, 0)
if struct.unpack_from("<Q", base, 32)[0] != FB_BASE or struct.unpack_from("<II", base, 16) != (W, H):
    L("formato de capa distinto -> no hago nada"); sys.exit(1)

fbfd = os.open("/dev/fb0", os.O_RDWR)
mem = mmap.mmap(fbfd, OFF + CW * CH * 4, offset=0)
pix = open(os.path.join(DIR, "flecha.bgra"), "rb").read()
assert len(pix) == CW * CH * 4
mem[OFF:OFF + len(pix)] = pix

def pixel(px, py):
    """Color (r,g,b) del buffer que se está mostrando."""
    v = fcntl.ioctl(fbfd, 0x4600, bytes(160))            # FBIOGET_VSCREENINFO
    yoff = struct.unpack_from("<I", v, 20)[0]
    o = ((py + yoff) * W + px) * 4
    if o + 4 > OFF: return (0, 0, 0)
    b, g, r, _ = mem[o:o + 4]; return (r, g, b)
def cerca(c, ref, tol=22): return all(abs(c[i] - ref[i]) <= tol for i in range(3))

def vista():
    menu = pixel(500, 44); marco = pixel(10, 200)
    if cerca(menu, (236, 233, 216)) and marco[2] > 150 and marco[0] < 60: return "ventana"
    inicio = pixel(40, 470); cielo = pixel(320, 150)
    if inicio[1] > inicio[0] + 25 and cielo[2] > cielo[0] + 40: return "escritorio"
    return "otra"

cfg = (ctypes.c_ubyte * 180)(); ctypes.memmove(cfg, base, 180)
cfg[4] = 3; cfg[5] = 0; cfg[6] = 255   # canal 2 propio: transparencia real, encima de todo
struct.pack_into("<Q", cfg, 32, FB_BASE + OFF)
for o in (56, 64, 72): struct.pack_into("<II", cfg, o, CW, CH)
args = (ctypes.c_ulong * 4)(0, ctypes.addressof(cfg), 1, 0)
HL_OFF, HW = OFF + CW * CH * 4, 80
hl_pix = bytearray(HW * HW * 4)
for yy in range(HW):
    for xx in range(HW):
        borde = xx < 1 or yy < 1 or xx >= HW - 1 or yy >= HW - 1
        a = 200 if borde else 95
        hl_pix[(yy * HW + xx) * 4:(yy * HW + xx) * 4 + 4] = bytes((197, 106, 49, a)) if not borde else bytes((255, 170, 120, a))
mem2 = mmap.mmap(fbfd, HL_OFF + len(hl_pix), offset=0)
mem2[HL_OFF:HL_OFF + len(hl_pix)] = bytes(hl_pix)
hcfg = (ctypes.c_ubyte * 180)(); ctypes.memmove(hcfg, base, 180)
hcfg[4] = 2; hcfg[5] = 0; hcfg[6] = 255
struct.pack_into("<Q", hcfg, 32, FB_BASE + HL_OFF)
for o in (56, 64, 72): struct.pack_into("<II", hcfg, o, HW, HW)
hargs = (ctypes.c_ulong * 4)(0, ctypes.addressof(hcfg), 1, 0)
seleccion = None
def resaltar(r):
    """Muestra el recuadro azul sobre la zona r=(x0,y0,x1,y1) o lo oculta si r es None."""
    global seleccion
    seleccion = r
    if r is None:
        struct.pack_into("<III", hcfg, 168, 0, 3, 0)
    else:
        w, h = min(HW, r[2] - r[0]), min(HW, r[3] - r[1])
        struct.pack_into("<iiII", hcfg, 8, r[0], r[1], w, h)
        struct.pack_into("<qqqq", hcfg, 120, 0, 0, w << 32, h << 32)
        struct.pack_into("<III", hcfg, 168, 1, 3, 0)
    libc.ioctl(disp, SET, hargs)

def capa(x, y, on):
    w, h = min(CW, W - x), min(CH, H - y)
    struct.pack_into("<iiII", cfg, 8, x, y, w, h)
    struct.pack_into("<qqqq", cfg, 120, 0, 0, w << 32, h << 32)
    struct.pack_into("<III", cfg, 168, 1 if on else 0, 2, 0)
    libc.ioctl(disp, SET, args)

pad = evdev.InputDevice("/dev/input/event1")
# clic con "peso": sonido corto + vibración de 45 ms
try:
    VIB = pad.upload_effect(ff.Effect(e.FF_RUMBLE, -1, 0, ff.Trigger(0, 0), ff.Replay(45, 0),
          ff.EffectType(ff_rumble_effect=ff.Rumble(strong_magnitude=0xB000, weak_magnitude=0x6000))))
except Exception:
    VIB = None
SONIDO = os.path.join(DIR, "clic.wav")
def sentir():
    try:
        subprocess.Popen(["paplay", SONIDO], env={"XDG_RUNTIME_DIR": "/var/run"}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception: pass
    if VIB is not None:
        try: pad.write(e.EV_FF, VIB, 1)
        except Exception: pass
ui = UInput({e.EV_REL: [e.REL_X, e.REL_Y], e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT]}, name="XP Mouse")
time.sleep(1.0)
def rel(dx, dy):
    ui.write(e.EV_REL, e.REL_X, dx); ui.write(e.EV_REL, e.REL_Y, dy); ui.syn()
for _ in range(12): rel(-200, -200); time.sleep(0.01)
x, y = W // 2, H // 2; rel(x, y)

# --- Control "agarrado": la interfaz recibe un TECLADO virtual (no un joystick) con todo menos la palanca
# derecha y R3. Los juegos nunca toman un teclado como jugador 1, así que siempre usan el control real.
import xml.etree.ElementTree as ET
def leer_mapeo():
    r = ET.parse("/usr/share/emulationstation/es_input.cfg").getroot()
    teclas = {c.get("name"): int(c.get("id")) for c in r.find("inputConfig[@type='keyboard']")}
    pad_cfg = next(c for c in r.findall("inputConfig") if c.get("deviceName") == pad.name)
    boton_a_nombre = {int(i.get("code")): i.get("name") for i in pad_cfg if i.get("type") == "button" and i.get("code")}
    return teclas, boton_a_nombre
SDL_A_LINUX = {1073741906: e.KEY_UP, 1073741905: e.KEY_DOWN, 1073741904: e.KEY_LEFT, 1073741903: e.KEY_RIGHT,
               27: e.KEY_ESC, 13: e.KEY_ENTER, 34: e.KEY_PAGEDOWN, 33: e.KEY_PAGEUP, 8: e.KEY_BACKSPACE,
               32: e.KEY_SPACE, 61: e.KEY_EQUAL, 45: e.KEY_MINUS}
TECLAS_SDL, BOTON_NOMBRE = leer_mapeo()
NOMBRE_TECLA = {n: SDL_A_LINUX[k] for n, k in TECLAS_SDL.items() if k in SDL_A_LINUX}
clon = None; ultimo_hat = {e.ABS_HAT0X: 0, e.ABS_HAT0Y: 0}
def agarrar():
    global clon
    if clon is not None: return
    clon = UInput({e.EV_KEY: sorted(set(NOMBRE_TECLA.values()))}, name="XP Mouse Teclado")
    time.sleep(0.6); pad.grab(); L("control agarrado (teclado virtual)")
def soltar():
    global clon
    try: pad.ungrab()
    except Exception: pass
    if clon is not None:
        try: clon.close()
        except Exception: pass
        clon = None; L("control suelto")
def tecla(nombre, valor):
    k = NOMBRE_TECLA.get(nombre)
    if k is not None and clon is not None:
        clon.write(e.EV_KEY, k, valor); clon.syn()
def reenviar(ev):
    """Traduce un evento del control real a teclas para la interfaz."""
    if ev.type == e.EV_KEY and ev.value in (0, 1):
        n = BOTON_NOMBRE.get(ev.code)
        if n: tecla(n, ev.value)
    elif ev.type == e.EV_ABS and ev.code in ultimo_hat:
        neg, pos = ("left", "right") if ev.code == e.ABS_HAT0X else ("up", "down")
        prev = ultimo_hat[ev.code]
        if prev < 0: tecla(neg, 0)
        if prev > 0: tecla(pos, 0)
        if ev.value < 0: tecla(neg, 1)
        if ev.value > 0: tecla(pos, 1)
        ultimo_hat[ev.code] = ev.value
NOMBRE_DE_CODIGO = {304: "a", 305: "b", 311: "start", 310: "select"}
def boton(code, mantener=0.12):
    if clon is not None:
        n = BOTON_NOMBRE.get(code, NOMBRE_DE_CODIGO.get(code))
        tecla(n, 1); time.sleep(mantener); tecla(n, 0); return
    pad.write(e.EV_KEY, code, 1); pad.write(e.EV_SYN, e.SYN_REPORT, 0); time.sleep(mantener)
    pad.write(e.EV_KEY, code, 0); pad.write(e.EV_SYN, e.SYN_REPORT, 0)
def cruceta(eje, v):
    if clon is not None:
        n = ("left" if v < 0 else "right") if eje == e.ABS_HAT0X else ("up" if v < 0 else "down")
        tecla(n, 1); time.sleep(0.12); tecla(n, 0); return
    pad.write(e.EV_ABS, eje, v); pad.write(e.EV_SYN, e.SYN_REPORT, 0); time.sleep(0.12)
    pad.write(e.EV_ABS, eje, 0); pad.write(e.EV_SYN, e.SYN_REPORT, 0)
# Botones de volumen físicos: mientras el control está agarrado, triggerhappy no los ve; los atiendo yo igual que él
def volumen_fisico(ev, l2):
    cmd = None
    if ev.value == 1:
        if ev.code == e.KEY_VOLUMEUP: cmd = ["/usr/bin/volume-button", "briup" if l2 else "volup"]
        if ev.code == e.KEY_VOLUMEDOWN: cmd = ["/usr/bin/volume-button", "bridown" if l2 else "voldown"]
    elif ev.value == 0: cmd = ["/usr/bin/volume-button-release"]
    if cmd:
        try: subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception: pass
def aviso(t):
    try: urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:1234/notify", data=t.encode(), method="POST"), timeout=1)
    except Exception: pass
A, B, START, SELECT = 304, 305, 311, 310   # códigos de ESTA consola (es_input.cfg)

def dentro(r): return r[0] <= x <= r[2] and r[1] <= y <= r[3]
# Zonas (coordenadas de pantalla 640x480)
INICIO = (0, 450, 99, 479)
V_CERRAR, V_MAX, V_MIN = (603, 9, 627, 33), (580, 9, 602, 33), (557, 9, 579, 33)
V_TAREA = (101, 452, 251, 478)
T_JUGAR, T_FAV, T_OPC = (352, 333, 600, 349), (352, 350, 600, 366), (352, 367, 600, 383)
E_MIPC, E_JUEGOS, E_PAPELERA = (4, 10, 84, 76), (4, 88, 84, 152), (4, 166, 84, 246)
E_IZQ, E_CENTRO, E_DER = (0, 280, 188, 400), (189, 280, 451, 400), (452, 280, 639, 400)

LISTA, FILA = (16, 60, 335, 392), 25.5
def fila_seleccionada():
    """Centro vertical de la franja azul de selección de la lista (o None)."""
    ys = [yy for yy in range(60, 392, 2) if cerca(pixel(22, yy), (49, 106, 197), 25)]
    return (min(ys) + max(ys)) / 2 if ys else None

def clic():
    v = vista()
    if dentro(INICIO) and v in ("ventana", "escritorio"): boton(START); return "inicio"
    if v == "ventana" and dentro(LISTA):
        sel = fila_seleccionada()
        if sel is None: return "lista: no encontré la selección"
        d = round((y - sel) / FILA)
        if d == 0: boton(A); return "abrir juego"
        for _ in range(abs(d)): cruceta(e.ABS_HAT0Y, 1 if d > 0 else -1); time.sleep(0.03)
        return "seleccionar %+d" % d
    if v == "ventana":
        if dentro(V_CERRAR) or dentro(V_MIN) or dentro(V_TAREA): boton(B); return "cerrar/minimizar"
        if dentro(V_MAX) or dentro(T_JUGAR): boton(A); return "jugar"
        if dentro(T_FAV): boton(A, 1.3); return "opciones/favoritos"
        if dentro(T_OPC): boton(SELECT); return "opciones"
    if v == "escritorio":
        try:
            pst = json.load(open("/tmp/xp_player.state"))
            if pst.get("visible"):
                for r in pst.get("rects", {}).values():
                    if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                        open("/tmp/xp_player.cmd", "a").write("click %d %d" % (x, y) + chr(10)); return "reproductor"
        except Exception: pass
        for zona, accion, nombre in ((E_MIPC, lambda: boton(START), "mi pc"), (E_JUEGOS, lambda: boton(A), "mis juegos"),
                                     (E_PAPELERA, lambda: aviso("La Papelera de reciclaje está vacía"), "papelera")):
            if dentro(zona):
                if seleccion == zona: resaltar(None); accion(); return "abrir " + nombre
                resaltar(zona); return "seleccionar " + nombre
        resaltar(None)
        if dentro(E_CENTRO): boton(A); return "abrir carpeta"
        if dentro(E_IZQ): cruceta(e.ABS_HAT0X, -1); return "izquierda"
        if dentro(E_DER): cruceta(e.ABS_HAT0X, 1); return "derecha"
        return "escritorio vacío (nada)"
    if v == "ventana" and not dentro(LISTA):
        return "ventana: zona sin acción"
    ui.write(e.EV_KEY, e.BTN_LEFT, 1); ui.syn(); time.sleep(0.05); ui.write(e.EV_KEY, e.BTN_LEFT, 0); ui.syn()
    return "clic normal (" + v + ")"

def salir(*_):
    try: soltar()
    except Exception: pass
    try:
        if VIB is not None: pad.erase_effect(VIB)
    except Exception: pass
    try: capa(0, 0, False)
    except Exception: pass
    try: resaltar(None)
    except Exception: pass
    try: ui.close()
    except Exception: pass
    L("salida limpia"); sys.exit(0)
signal.signal(signal.SIGTERM, salir); signal.signal(signal.SIGINT, salir)

# Guardián de volumen: ES usa la palanca derecha para el volumen; mientras la usamos de mouse, lo restauramos
PENV = {"XDG_RUNTIME_DIR": "/var/run", "PATH": "/usr/bin:/bin"}
def vol_get():
    try:
        o = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], env=PENV, capture_output=True, text=True, timeout=1).stdout
        return int(o.split("/")[1].strip().rstrip("%"))
    except Exception: return None
def vol_set(v):
    try: subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "%d%%" % v], env=PENV, timeout=1)
    except Exception: pass
vol_ref, t_mov, t_vol = vol_get(), 0.0, 0.0

def juego_corriendo():
    try:
        with urllib.request.urlopen("http://127.0.0.1:1234/runningGame", timeout=0.4) as r:
            return r.status == 200 and len(r.read().strip()) > 2
    except Exception:
        return False

ax = {e.ABS_RY: 0, e.ABS_RZ: 0}
l2 = False
fx = fy = 0.0; t_chk, en_juego = 0, False
capa(x, y, True); L("modo mouse activo")
if not juego_corriendo(): agarrar()
try:
    while True:
        r, _, _ = select.select([pad], [], [], 1 / 60)
        if r:
            for ev in pad.read():
                if ev.type == e.EV_KEY and ev.code == e.BTN_TL2: l2 = ev.value != 0
                if ev.type == e.EV_ABS and ev.code in ax:
                    ax[ev.code] = ev.value; continue
                if ev.type == e.EV_KEY and ev.code == e.BTN_MODE:
                    if ev.value == 1 and not en_juego: sentir(); L("clic", x, y, "->", clic())
                    continue
                if clon is not None:
                    if ev.type == e.EV_KEY and ev.code in (e.KEY_VOLUMEUP, e.KEY_VOLUMEDOWN):
                        volumen_fisico(ev, l2); continue
                    reenviar(ev)
        now = time.time()
        if os.path.exists("/tmp/cursor_xp.cmd"):
            for ln in open("/tmp/cursor_xp.cmd").read().splitlines():
                p = ln.split()
                if p[:1] == ["goto"]:
                    nx, ny = int(p[1]), int(p[2]); rel(nx - x, ny - y); x, y = nx, ny; capa(x, y, True)
                elif p[:1] == ["click"]: L("clic(prueba)", x, y, "->", clic()); time.sleep(0.6)
            os.remove("/tmp/cursor_xp.cmd")
        if now - t_chk > 1.0:
            # la interfaz puede limpiar la memoria al reiniciarse: redibujar flecha y selección
            if mem[OFF:OFF + len(pix)] != pix: mem[OFF:OFF + len(pix)] = pix; L("flecha redibujada")
            if mem2[HL_OFF:HL_OFF + len(hl_pix)] != bytes(hl_pix): mem2[HL_OFF:HL_OFF + len(hl_pix)] = bytes(hl_pix)
            if seleccion is not None and vista() != "escritorio": resaltar(None)
            t_chk = now; g = juego_corriendo()
            if g != en_juego:
                en_juego = g; capa(x, y, not g); L("juego" if g else "menú")
                if g: soltar()
                else: agarrar()
        if en_juego: continue
        def vel(v):
            if abs(v) < DEAD: return 0.0
            n = (abs(v) - DEAD) / (MAXV - DEAD); return (1 if v > 0 else -1) * (1.2 + 10 * n * n)
        moviendo = abs(ax[e.ABS_RY]) > DEAD or abs(ax[e.ABS_RZ]) > DEAD
        if moviendo: t_mov = now
        if clon is None and now - t_vol > 0.25:
            t_vol = now; v_act = vol_get()
            if v_act is not None:
                if now - t_mov < 1.2:                      # palanca en uso (o recién soltada): restaurar
                    if vol_ref is not None and v_act != vol_ref: vol_set(vol_ref)
                else:
                    vol_ref = v_act                         # quieta: aceptar cambios de los botones de volumen
        fx += vel(ax[e.ABS_RY]); fy += vel(ax[e.ABS_RZ])
        dx, dy = int(fx), int(fy); fx -= dx; fy -= dy
        if dx or dy:
            nx, ny = max(0, min(W - 1, x + dx)), max(0, min(H - 1, y + dy))
            if (nx, ny) != (x, y):
                rel(nx - x, ny - y); x, y = nx, ny; capa(x, y, True)
except SystemExit:
    raise
except Exception as ex:
    L("error:", repr(ex)); salir()
