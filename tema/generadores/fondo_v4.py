# Fondo v3: cielo + cúmulos definidos (base plana, sombra azulada abajo) + colina + franja suave para los logos
import math, random
from PIL import Image, ImageDraw, ImageFilter
W, H = 640, 480
random.seed(11)

def lerp(a, b, t): return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
def vgrad(w, h, stops):
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                c = lerp(stops[i][1], stops[i + 1][1], (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])); break
        d.line([(0, y), (w, y)], fill=c)
    return im

S = 3  # supersampling
bg = vgrad(W * S, H * S, [(0, (22, 88, 200)), (0.35, (70, 140, 228)), (0.62, (150, 196, 245)), (1, (190, 220, 250))])

def cumulo(cx, cy, w, h):
    """Cúmulo: puffs con base plana. Devuelve máscara L (cuerpo) y máscara de sombra inferior."""
    body = Image.new("L", (W * S, H * S), 0); bd = ImageDraw.Draw(body)
    n = max(5, int(w / 22))
    for i in range(n):
        t = i / (n - 1)
        x = cx - w / 2 + t * w
        r = h * (0.55 + 0.45 * math.sin(math.pi * t)) * random.uniform(0.75, 1.05)
        y = cy - r * 0.55
        bd.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=255)
    for _ in range(n // 2):  # puffs superiores
        x = cx + random.uniform(-w * 0.3, w * 0.3); r = h * random.uniform(0.5, 0.8); y = cy - h * 0.9
        bd.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=255)
    bd.rectangle([0, int(cy * S), W * S, H * S], fill=0)  # base plana
    body = body.filter(ImageFilter.GaussianBlur(0.9 * S))
    shade = Image.new("L", body.size, 0)
    sd = ImageDraw.Draw(shade); sd.rectangle([0, int((cy - h * 0.55) * S), W * S, int(cy * S)], fill=150)
    shade = Image.composite(shade, Image.new("L", body.size, 0), body).filter(ImageFilter.GaussianBlur(4 * S))
    shade = Image.composite(shade, Image.new("L", body.size, 0), body)
    return body, shade

# pocas nubes: grandes arriba, chicas hacia el horizonte
for cx, cy, w, h in [(110, 95, 170, 34), (420, 70, 210, 40), (600, 150, 120, 26), (250, 175, 120, 24),
                     (40, 215, 90, 18), (520, 230, 90, 17), (360, 252, 70, 13)]:
    body, shade = cumulo(cx, cy, w, h)
    bg.paste((252, 253, 255), (0, 0), body)
    bg.paste((196, 210, 232), (0, 0), shade)

# colina
hill = Image.new("L", (W * S, H * S), 0); hd = ImageDraw.Draw(hill)
pts = [(x * S, (300 + 38 * math.sin((x + 60) / 230) - 52 * math.exp(-((x - 260) / 210) ** 2)) * S) for x in range(0, W + 1, 2)]
hd.polygon(pts + [(W * S, H * S), (0, H * S)], fill=255)
green = vgrad(W * S, H * S, [(0, (120, 200, 60)), (0.55, (92, 176, 42)), (0.75, (58, 142, 32)), (1, (42, 112, 26))])
sh = Image.new("L", (W * S, H * S), 0); sdd = ImageDraw.Draw(sh)
for x0, y0, r in [(470, 330, 170), (120, 390, 140), (330, 440, 160)]:
    sdd.ellipse([(x0 - r) * S, (y0 - r // 2) * S, (x0 + r) * S, (y0 + r // 2) * S], fill=60)
green.paste((30, 85, 20), (0, 0), sh.filter(ImageFilter.GaussianBlur(40 * S)))
import numpy as np
rng = np.random.default_rng(3)
g = np.asarray(green).astype(np.int16)
noise = rng.normal(0, 7, (H * S, W * S, 1)).astype(np.int16)
streak = (np.sin(np.linspace(0, 900, W * S))[None, :, None] * 3).astype(np.int16)
green = Image.fromarray(np.clip(g + noise + streak, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7 * S))
# luz en la cresta de la colina
crest = Image.new("L", (W * S, H * S), 0); cd2 = ImageDraw.Draw(crest)
cd2.line([(x, y + 6 * S) for x, y in pts], fill=90, width=14 * S)
green.paste((170, 225, 90), (0, 0), crest.filter(ImageFilter.GaussianBlur(10 * S)))
# franja suave detrás del carrusel de logos (y 264..394) para que se lean
band = Image.new("L", (W * S, H * S), 0); ImageDraw.Draw(band).rectangle([0, 270 * S, W * S, 392 * S], fill=70)
green.paste((10, 40, 10), (0, 0), band.filter(ImageFilter.GaussianBlur(22 * S)))
bg.paste(green, (0, 0), hill.filter(ImageFilter.GaussianBlur(0.6 * S)))
bg = bg.resize((W, H), Image.LANCZOS)
bg.save("es-theme-xp/art/fondo.png", optimize=True)
print("fondo v3 ok")
