# Genera los gráficos del tema "Escritorio XP" (originales, dibujados por código) para 640x480
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = 640, 480
OUT = "es-theme-xp/art/"
import os; os.makedirs(OUT, exist_ok=True)
F = "C:/Windows/Fonts/"
def font(n, s):
    try: return ImageFont.truetype(F + n, s)
    except: return ImageFont.truetype(F + "arial.ttf", s)

def lerp(a, b, t): return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
def vgrad(w, h, stops):
    im = Image.new("RGB", (w, h)); px = im.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                c = lerp(stops[i][1], stops[i + 1][1], (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])); break
        for x in range(w): px[x, y] = c
    return im

# 1) Fondo: cielo + nubes + colina verde (original)
random.seed(7)
bg = vgrad(W, H, [(0, (40, 100, 200)), (0.45, (110, 165, 235)), (0.7, (170, 205, 245)), (1, (170, 205, 245))])
clouds = Image.new("L", (W, H), 0); cd = ImageDraw.Draw(clouds)
for _ in range(38):
    cx, cy = random.randint(-40, W + 40), random.randint(30, 230)
    for _ in range(6):
        r = random.randint(14, 34)
        ox, oy = cx + random.randint(-40, 40), cy + random.randint(-8, 8)
        cd.ellipse([ox - r, oy - r // 2, ox + r, oy + r // 2], fill=random.randint(90, 170))
clouds = clouds.filter(ImageFilter.GaussianBlur(9))
bg.paste((255, 255, 255), (0, 0), clouds)
hill = Image.new("L", (W, H), 0); hd = ImageDraw.Draw(hill)
pts = [(x, 300 + 40 * math.sin((x + 60) / 230) - 55 * math.exp(-((x - 260) / 210) ** 2)) for x in range(0, W + 1, 4)]
hd.polygon(pts + [(W, H), (0, H)], fill=255)
green = vgrad(W, H, [(0, (120, 200, 60)), (0.55, (90, 175, 40)), (0.75, (55, 140, 30)), (1, (40, 110, 25))])
shade = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(shade)
for x0, y0, r in [(470, 330, 170), (120, 380, 140), (330, 430, 160)]:
    sd.ellipse([x0 - r, y0 - r // 2, x0 + r, y0 + r // 2], fill=70)
shade = shade.filter(ImageFilter.GaussianBlur(40))
green.paste((30, 85, 20), (0, 0), shade)
bg.paste(green, (0, 0), hill.filter(ImageFilter.GaussianBlur(1.2)))
bg.save(OUT + "fondo.jpg", quality=90)

# 2) Barra de tareas con botón Inicio
TB = 30
tb = vgrad(W, TB, [(0, (60, 130, 240)), (0.12, (36, 94, 220)), (0.5, (31, 84, 210)), (0.9, (28, 72, 190)), (1, (20, 55, 160))])
d = ImageDraw.Draw(tb)
st = vgrad(96, TB, [(0, (110, 190, 100)), (0.2, (60, 160, 60)), (0.7, (45, 140, 45)), (1, (35, 110, 35))])
mask = Image.new("L", (96, TB), 0); ImageDraw.Draw(mask).rounded_rectangle([-12, 0, 95, TB - 1], radius=12, fill=255)
tb.paste(st, (0, 0), mask)
for i, c in enumerate([(240, 80, 40), (100, 190, 40), (40, 120, 230), (250, 200, 30)]):  # banderita propia de 4 cuadros
    x, y = 12 + (i % 2) * 8, 8 + (i // 2) * 8
    d.rectangle([x, y, x + 6, y + 6], fill=c)
d.text((34, TB // 2), "inicio", font=font("arialbi.ttf", 17), fill=(255, 255, 255), anchor="lm")
tray = vgrad(128, TB, [(0, (20, 140, 230)), (0.5, (15, 120, 220)), (1, (10, 95, 190))])
tb.paste(tray, (W - 128, 0)); d.line([(W - 128, 0), (W - 128, TB)], fill=(10, 60, 150), width=1)
tb.save(OUT + "barra.png")

# 3) Ventana XP (Luna) para la lista de juegos: 624 x 412
WW, WH, T = 624, 412, 26
win = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
frame = vgrad(WW, WH, [(0, (0, 84, 227)), (1, (0, 70, 200))]).convert("RGBA")
m = Image.new("L", (WW, WH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, WW - 1, WH + 10], radius=9, fill=255)
win.paste(frame, (0, 0), m)
title = vgrad(WW, T, [(0, (60, 140, 255)), (0.1, (0, 90, 238)), (0.5, (0, 84, 227)), (0.85, (0, 75, 215)), (1, (0, 60, 190))]).convert("RGBA")
win.paste(title, (0, 0), m.crop((0, 0, WW, T)))
wd = ImageDraw.Draw(win)
wd.rectangle([4, T, WW - 5, WH - 5], fill=(236, 233, 216))  # gris crema clásico
wd.rectangle([8, T + 4, WW - 9, WH - 9], fill=(255, 255, 255), outline=(127, 157, 185))
def btn(x, col, glyph):
    b = vgrad(21, 21, [(0, lerp(col, (255, 255, 255), .35)), (1, col)]).convert("RGBA")
    mk = Image.new("L", (21, 21), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, 20, 20], radius=3, fill=255)
    win.paste(b, (x, 3), mk); wd.rounded_rectangle([x, 3, x + 20, 23], radius=3, outline=(255, 255, 255))
    g = ImageDraw.Draw(win)
    if glyph == "x": g.line([(x + 6, 9), (x + 14, 17)], fill="white", width=2); g.line([(x + 14, 9), (x + 6, 17)], fill="white", width=2)
    if glyph == "max": g.rectangle([x + 5, 7, x + 15, 17], outline="white", width=2)
    if glyph == "min": g.rectangle([x + 5, 15, x + 11, 17], fill="white")
btn(WW - 27, (200, 60, 30), "x"); btn(WW - 50, (40, 100, 230), "max"); btn(WW - 73, (40, 100, 230), "min")
# separador vertical entre lista y panel de detalle
wd.line([(330, T + 8), (330, WH - 14)], fill=(210, 210, 200), width=1)
win.save(OUT + "ventana.png")

# 4) Barra de selección y marco de carátula
Image.new("RGB", (8, 8), (49, 106, 197)).save(OUT + "sel.png")
print("ok", os.listdir(OUT))

# ===== v2: ventana tipo Explorador con barra de menú, panel azul de detalles y barra de estado =====
WW, WH, T, MB, SB = 624, 412, 26, 20, 20
win = Image.new("RGBA", (WW, WH), (0, 0, 0, 0))
frame = vgrad(WW, WH, [(0, (0, 84, 227)), (1, (0, 70, 200))]).convert("RGBA")
m = Image.new("L", (WW, WH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, WW - 1, WH + 10], radius=9, fill=255)
win.paste(frame, (0, 0), m)
title = vgrad(WW, T, [(0, (60, 140, 255)), (0.1, (0, 90, 238)), (0.5, (0, 84, 227)), (0.85, (0, 75, 215)), (1, (0, 60, 190))]).convert("RGBA")
win.paste(title, (0, 0), m.crop((0, 0, WW, T)))
wd = ImageDraw.Draw(win)
# icono de carpeta en el título
wd.rounded_rectangle([7, 7, 21, 19], radius=2, fill=(250, 210, 90), outline=(200, 150, 30)); wd.rectangle([7, 5, 13, 8], fill=(250, 210, 90))
# cuerpo
wd.rectangle([4, T, WW - 5, WH - 5], fill=(236, 233, 216))
# barra de menú
mf = font("tahoma.ttf", 12)
x = 10
for w_ in ["Archivo", "Edición", "Ver", "Favoritos", "Herramientas", "Ayuda"]:
    wd.text((x, T + MB // 2), w_, font=mf, fill=(0, 0, 0), anchor="lm"); x += wd.textlength(w_, font=mf) + 14
wd.line([(4, T + MB), (WW - 5, T + MB)], fill=(200, 196, 180))
top = T + MB + 3
# panel azul de tareas (derecha) estilo XP
PX = 336
pane = vgrad(WW - 9 - PX, WH - 5 - SB - top, [(0, (123, 162, 231)), (1, (99, 117, 214))]).convert("RGBA")
win.paste(pane, (PX, top))
# caja "Detalles"
bx0, by0, bx1, by1 = PX + 10, top + 10, WW - 19, WH - SB - 16
hdr = vgrad(bx1 - bx0, 24, [(0, (255, 255, 255)), (1, (198, 211, 247))]).convert("RGBA")
hm = Image.new("L", (bx1 - bx0, 24), 0); ImageDraw.Draw(hm).rounded_rectangle([0, 0, bx1 - bx0 - 1, 30], radius=6, fill=255)
win.paste(hdr, (bx0, by0), hm)
wd.text((bx0 + 10, by0 + 12), "Detalles del juego", font=font("tahomabd.ttf", 12), fill=(33, 93, 198), anchor="lm")
for i, yy in enumerate([by0 + 8, by0 + 13]):  # chevrones
    wd.line([(bx1 - 22, yy), (bx1 - 17, yy + 4), (bx1 - 12, yy)], fill=(33, 93, 198), width=2)
wd.rectangle([bx0, by0 + 24, bx1 - 1, by1], fill=(214, 223, 247))
wd.rectangle([bx0, by0 + 24, bx1 - 1, by1], outline=(255, 255, 255))
# lista blanca (izquierda) con borde
wd.rectangle([8, top, PX - 4, WH - SB - 9], fill=(255, 255, 255), outline=(127, 157, 185))
# barra de estado
wd.rectangle([4, WH - SB - 5, WW - 5, WH - 5], fill=(236, 233, 216)); wd.line([(4, WH - SB - 5), (WW - 5, WH - SB - 5)], fill=(200, 196, 180))
wd.line([(PX, WH - SB - 3), (PX, WH - 7)], fill=(200, 196, 180))
def btn(x, col, glyph):
    b = vgrad(21, 21, [(0, lerp(col, (255, 255, 255), .35)), (1, col)]).convert("RGBA")
    mk = Image.new("L", (21, 21), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, 20, 20], radius=3, fill=255)
    win.paste(b, (x, 3), mk); g = ImageDraw.Draw(win); g.rounded_rectangle([x, 3, x + 20, 23], radius=3, outline=(255, 255, 255))
    if glyph == "x": g.line([(x + 6, 9), (x + 14, 17)], fill="white", width=2); g.line([(x + 14, 9), (x + 6, 17)], fill="white", width=2)
    if glyph == "max": g.rectangle([x + 5, 7, x + 15, 17], outline="white", width=2)
    if glyph == "min": g.rectangle([x + 5, 15, x + 11, 17], fill="white")
btn(WW - 27, (200, 60, 30), "x"); btn(WW - 50, (40, 100, 230), "max"); btn(WW - 73, (40, 100, 230), "min")
win.save(OUT + "ventana.png")

# botón de tarea activa para la barra (ventana abierta)
tk = vgrad(150, 22, [(0, (30, 70, 170)), (0.5, (25, 60, 155)), (1, (20, 50, 140))]).convert("RGBA")
tm = Image.new("L", (150, 22), 0); ImageDraw.Draw(tm).rounded_rectangle([0, 0, 149, 21], radius=3, fill=255)
tarea = Image.new("RGBA", (150, 22), (0, 0, 0, 0)); tarea.paste(tk, (0, 0), tm)
td = ImageDraw.Draw(tarea); td.rounded_rectangle([0, 0, 149, 21], radius=3, outline=(15, 40, 120))
td.rounded_rectangle([6, 6, 18, 16], radius=2, fill=(250, 210, 90)); td.rectangle([6, 4, 11, 7], fill=(250, 210, 90))
tarea.save(OUT + "tarea.png")
print("v2 ok")
