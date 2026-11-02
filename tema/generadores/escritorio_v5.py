# Vuelta 5: íconos de escritorio, globo de aviso, selección y botón inicio mejorado (todo dibujado por código)
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = "C:/Windows/Fonts/"; A = "es-theme-xp/art/"
def font(n, s): return ImageFont.truetype(F + n, s)
def lerp(a, b, t): return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))
def vgrad(w, h, stops):
    im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                c = lerp(stops[i][1], stops[i + 1][1], (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])); break
        d.line([(0, y), (w, y)], fill=c)
    return im

# ---- 1) Íconos de escritorio (columna izquierda, 76x230) ----
S = 3
ic = Image.new("RGBA", (76 * S, 236 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(ic)
def sc(v): return [x * S for x in v]
# Mi PC: monitor
d.rounded_rectangle(sc([20, 6, 56, 32]), radius=3 * S, fill=(205, 210, 220), outline=(90, 95, 110), width=S)
d.rectangle(sc([24, 10, 52, 28]), fill=(40, 110, 220))
d.polygon(sc([24, 10, 52, 10, 24, 22]), fill=(90, 160, 240))
d.rectangle(sc([33, 32, 43, 36]), fill=(150, 155, 165)); d.rounded_rectangle(sc([24, 36, 52, 40]), radius=S, fill=(190, 195, 205), outline=(90, 95, 110))
# Mis juegos: carpeta con joystick
y0 = 82
d.rounded_rectangle(sc([18, y0 + 4, 58, y0 + 34]), radius=3 * S, fill=(242, 196, 70), outline=(180, 130, 20), width=S)
d.rounded_rectangle(sc([18, y0, 34, y0 + 8]), radius=2 * S, fill=(242, 196, 70), outline=(180, 130, 20), width=S)
d.rounded_rectangle(sc([18, y0 + 10, 58, y0 + 34]), radius=3 * S, fill=(252, 216, 100), outline=(180, 130, 20), width=S)
d.rounded_rectangle(sc([28, y0 + 17, 48, y0 + 29]), radius=5 * S, fill=(70, 75, 90))
d.ellipse(sc([31, y0 + 21, 35, y0 + 25]), fill=(230, 60, 50)); d.ellipse(sc([41, y0 + 21, 45, y0 + 25]), fill=(60, 140, 230))
# Papelera
y0 = 160
d.polygon(sc([24, y0 + 8, 52, y0 + 8, 49, y0 + 36, 27, y0 + 36]), fill=(200, 215, 230), outline=(90, 110, 130))
for x in (31, 38, 45): d.line(sc([x, y0 + 12, x - 0.5, y0 + 33]), fill=(120, 140, 160), width=S)
d.rounded_rectangle(sc([21, y0 + 4, 55, y0 + 9]), radius=2 * S, fill=(170, 190, 210), outline=(90, 110, 130))
ic = ic.resize((76, 236), Image.LANCZOS); d = ImageDraw.Draw(ic)
# etiquetas con sombra
lab = font("tahoma.ttf", 11)
for (t, y) in [("Mi PC", 46), ("Mis juegos", 122), ("Papelera de", 200), ("reciclaje", 213)]:
    d.text((39, y + 1), t, font=lab, fill=(0, 0, 0, 200), anchor="ma"); d.text((38, y), t, font=lab, fill=(255, 255, 255), anchor="ma")
ic.save(A + "iconos.png")

# ---- 2) Globo de aviso (tooltip XP) 236x54 + cola hacia la bandeja ----
BW, BH = 236, 58
bal = Image.new("RGBA", (BW, BH + 12), (0, 0, 0, 0)); b = ImageDraw.Draw(bal)
sh = Image.new("RGBA", bal.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([3, 3, BW - 1, BH + 1], radius=8, fill=(0, 0, 0, 70))
bal.alpha_composite(sh.filter(ImageFilter.GaussianBlur(2)))
b.rounded_rectangle([0, 0, BW - 4, BH - 2], radius=8, fill=(255, 255, 225), outline=(0, 0, 0))
b.polygon([(BW - 52, BH - 3), (BW - 30, BH - 3), (BW - 22, BH + 10)], fill=(255, 255, 225))
b.line([(BW - 52, BH - 2), (BW - 22, BH + 10), (BW - 30, BH - 2)], fill=(0, 0, 0))
# icono "i"
b.ellipse([9, 8, 25, 24], fill=(40, 100, 220), outline=(20, 60, 160)); b.text((17, 16), "i", font=font("georgiab.ttf", 12), fill="white", anchor="mm")
b.text((32, 9), "Juegos disponibles", font=font("tahomabd.ttf", 11), fill=(0, 0, 0))
# cruz de cerrar
b.rectangle([BW - 22, 6, BW - 10, 18], outline=(150, 150, 150)); b.line([(BW - 19, 9), (BW - 13, 15)], fill=(90, 90, 90)); b.line([(BW - 13, 9), (BW - 19, 15)], fill=(90, 90, 90))
bal.save(A + "globo.png")

# ---- 3) Selección del ícono central (azul translúcido) 250x140 ----
sel = Image.new("RGBA", (250, 140), (0, 0, 0, 0)); s = ImageDraw.Draw(sel)
s.rounded_rectangle([0, 0, 249, 139], radius=8, fill=(49, 106, 197, 70), outline=(120, 170, 255, 170), width=1)
sel.save(A + "seleccion.png")

# ---- 4) Barra de tareas con botón inicio brillante ----
W, TB = 640, 30
tb = vgrad(W, TB, [(0, (70, 140, 245)), (0.1, (38, 98, 225)), (0.5, (31, 84, 210)), (0.88, (28, 72, 190)), (1, (16, 50, 150))])
st = vgrad(100, TB, [(0, (140, 210, 120)), (0.15, (75, 170, 70)), (0.55, (52, 150, 50)), (0.85, (40, 125, 40)), (1, (28, 95, 28))])
m = Image.new("L", (100, TB), 0); ImageDraw.Draw(m).rounded_rectangle([-14, 0, 99, TB + 6], radius=14, fill=255)
tb.paste(st, (0, 0), m)
gl = Image.new("RGBA", (100, TB), (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle([-14, 1, 96, 12], radius=8, fill=(255, 255, 255, 45))
tb.alpha_composite(Image.composite(gl, Image.new("RGBA", gl.size, (0, 0, 0, 0)), m))
d = ImageDraw.Draw(tb)
d.line([(99, 2), (99, TB)], fill=(20, 70, 20))
for i, c in enumerate([(240, 80, 40), (100, 190, 40), (40, 120, 230), (250, 200, 30)]):
    x, y = 11 + (i % 2) * 8, 8 + (i // 2) * 8
    d.rounded_rectangle([x, y, x + 6, y + 6], radius=1, fill=c)
fi = font("trebucbi.ttf", 18) if __import__("os").path.exists(F + "trebucbi.ttf") else font("arialbi.ttf", 17)
d.text((35, TB // 2 + 1), "inicio", font=fi, fill=(20, 60, 20), anchor="lm"); d.text((34, TB // 2), "inicio", font=fi, fill=(255, 255, 255), anchor="lm")
# separador de inicio rápido
d.line([(108, 6), (108, TB - 6)], fill=(20, 50, 140)); d.line([(109, 6), (109, TB - 6)], fill=(90, 150, 255))
tray = vgrad(128, TB, [(0, (30, 150, 235)), (0.5, (15, 125, 225)), (1, (10, 95, 190))])
tb.paste(tray, (W - 128, 0)); d.line([(W - 128, 0), (W - 128, TB)], fill=(10, 60, 150)); d.line([(W - 127, 0), (W - 127, TB)], fill=(90, 190, 255))
tb.save(A + "barra.png")
print("vuelta 5 ok")
