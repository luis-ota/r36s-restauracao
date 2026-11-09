#!/usr/bin/env python3
"""Gera os fundos do tema LAIN // nEther (640x480).

Sem argumentos, usa um fundo abstrato. Com --list e --systems, usa as suas
proprias imagens. O repositorio nao distribui imagens da serie.

  uv run --with pillow build_backgrounds.py [--list A.jpg] [--systems B.jpg]
"""
import argparse, os, math, random
from PIL import ImageOps
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 640, 480
ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art")

INK      = (5, 5, 6)
GRAPHITE = (13, 14, 17)
SMOKE    = (26, 27, 32)
CREAM    = (232, 225, 210)
DIMCREAM = (156, 150, 138)
BLOOD    = (193, 18, 31)
DARKRED  = (108, 6, 14)
GHOST    = (111, 208, 207)

def font(weight, size):
    return ImageFont.truetype(os.path.join(ART, f"plex-{weight.lower()}.ttf"), size)

BAYER8 = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]
BAYER = [[v / 64.0 - 0.5 for v in row] for row in BAYER8]

def dither_3tone(gray, c_dark, c_mid, c_light, t1=0.20, t2=0.58, spread=0.34):
    g = gray.load()
    out = Image.new("RGB", gray.size)
    o = out.load()
    for y in range(gray.size[1]):
        brow = BAYER[y % 8]
        for x in range(gray.size[0]):
            v = g[x, y] / 255.0 + brow[x % 8] * spread
            if v < t1:
                o[x, y] = c_dark
            elif v < t2:
                o[x, y] = c_mid
            else:
                o[x, y] = c_light
    return out

def gradient(w, h, stops):
    img = Image.new("RGB", (1, h))
    p = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / max(1e-6, t1 - t0)
                p[0, y] = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
    return img.resize((w, h), Image.BILINEAR)

def noise_layer(w, h, seed, blur=0.0):
    rnd = random.Random(seed)
    small = Image.new("L", (max(1, w // 2), max(1, h // 2)))
    px = small.load()
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            px[x, y] = rnd.randint(0, 255)
    small = small.resize((w, h), Image.NEAREST)
    if blur:
        small = small.filter(ImageFilter.GaussianBlur(blur))
    return small

def grain(img, amount=16, seed=1):
    n = noise_layer(*img.size, seed).filter(ImageFilter.GaussianBlur(0.4))
    n = n.point(lambda v: int(128 + (v - 128) * 1.6))
    im = ImageChops.overlay(img, Image.merge("RGB", (n, n, n)))
    return Image.blend(img, im, amount / 100.0)

def scanlines(img, period=3, darkness=0.30, offset=0):
    ov = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(ov)
    for y in range(offset, img.size[1], period):
        d.line([(0, y), (img.size[0], y)], fill=int(255 * darkness))
    black = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(black, img, ov.point(lambda v: int(v * 0.5)))

def vignette(img, strength=0.85, power=2.2):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    p = mask.load()
    cx, cy = w / 2, h / 2
    maxd = math.hypot(cx, cy)
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - cx) * 0.92, (y - cy) * 0.72) / maxd
            p[x, y] = max(0, min(255, int(255 * (1 - strength * (d ** power)))))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, black, mask)

def add_glow(img, box, color, radius=40, strength=0.5):
    layer = Image.new("RGB", img.size, (0, 0, 0))
    ImageDraw.Draw(layer).ellipse(box, fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    return ImageChops.add(img, layer.point(lambda v: int(v * strength)))

def bez(p0, p1, p2, p3, n=90):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return pts

def screenprint(img, dark=INK, mid=BLOOD, light=CREAM, t1=0.20, t2=0.58):
    return dither_3tone(img.convert("L"), dark, mid, light, t1=t1, t2=t2)

def glitch(img, seed=3, count=7, maxdx=9):
    rnd = random.Random(seed)
    out = img.copy()
    for _ in range(count):
        y = rnd.randint(0, img.size[1] - 12)
        hgt = rnd.randint(2, 8)
        dx = rnd.randint(-maxdx, maxdx)
        strip = img.crop((0, y, img.size[0], y + hgt))
        out.paste(strip, (dx, y))
    return out

def perspective_grid(img, horizon, color, alpha=1.0, vpx=None, spread=54):
    w, h = img.size
    vpx = w // 2 if vpx is None else vpx
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    for i in range(-18, 19):
        d.line([(vpx + i * spread, h), (vpx, horizon)], fill=1, width=1)
    y = float(h)
    step = 2.6
    while y > horizon + 1:
        d.line([(0, int(y)), (w, int(y))], fill=1, width=1)
        step *= 1.30
        y -= step
    layer = layer.point(lambda v: int(v * 255 * alpha))
    return Image.composite(Image.new("RGB", img.size, color), img, layer)

def hairline(img, y=None, x=None, color=(30, 31, 36), width=1):
    d = ImageDraw.Draw(img)
    if y is not None:
        d.rectangle([0, y, img.size[0] - 1, y + width - 1], fill=color)
    if x is not None:
        d.rectangle([x, 0, x + width - 1, img.size[1] - 1], fill=color)

def vtext(img, x, y, text, fnt, fill, tracking=2, topdown=True):
    d = ImageDraw.Draw(img)
    cy = y
    for ch in text:
        d.text((x, cy), ch, font=fnt, fill=fill)
        cy += fnt.size + tracking

# ---------------------------------------------------------------- backgrounds
def load_frame(path, target=(W, H), anchor_x=0.5, anchor_y=0.5, zoom=1.0, flip=False):
    im = Image.open(path).convert("RGB")
    tw, th = target
    dst_ar = tw / th
    src_ar = im.width / im.height
    if src_ar > dst_ar:
        nw = int(im.height * dst_ar / zoom); nh = int(im.height / zoom)
    else:
        nh = int(im.width / dst_ar / zoom); nw = int(im.width / zoom)
    x = int((im.width - nw) * anchor_x); y = int((im.height - nh) * anchor_y)
    im = im.crop((x, y, x + nw, y + nh)).resize(target, Image.LANCZOS)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im

def grade(im, keep_color=0.20, gamma=1.0):
    l = im.convert("L")
    l = ImageOps.autocontrast(l, cutoff=0.4)
    if gamma != 1.0:
        l = l.point(lambda v: int(255 * (v / 255.0) ** gamma))
    duo = ImageOps.colorize(l, black=(6, 6, 8), white=(226, 219, 204))
    # warm graphite midtones
    duo = Image.blend(duo, ImageOps.colorize(l, black=(6, 6, 8), white=(210, 186, 160)), 0.35)
    out = Image.blend(duo, im, keep_color)
    # blood cast in the shadows
    red = Image.new("RGB", im.size, (46, 3, 6))
    mask = l.point(lambda v: max(0, 150 - v))
    out = Image.composite(ImageChops.add(out, red.point(lambda v: v // 3)), out,
                          mask.point(lambda v: min(255, v)))
    return out

def scrim_h(img, stops):
    """Horizontal alpha scrim from (x_fraction, opacity) stops."""
    w, h = img.size
    black = Image.new("RGB", img.size, (0, 0, 0))
    mask = Image.new("L", (w, 1), 0)
    mp = mask.load()
    for x in range(w):
        t = x / (w - 1)
        op = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, o0 = stops[i]
            t1, o1 = stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / max(1e-6, t1 - t0)
                op = o0 + (o1 - o0) * k
                break
        mp[x, 0] = int(255 * op)
    return Image.composite(black, img, mask.resize((w, h)))

def bands(bg, top=57, footer=428):
    d = ImageDraw.Draw(bg)
    # header: fade the photo into black, then a hairline
    topfade = Image.new("L", (W, 90), 0)
    tp = topfade.load()
    for y in range(90):
        v = int(255 * max(0.0, 1.0 - (y / 78.0) ** 1.25))
        for x in range(W):
            tp[x, y] = v
    bg.paste(Image.new("RGB", (W, 90), (4, 4, 5)), (0, 0), topfade)
    d.rectangle([0, top, W - 1, top + 1], fill=(30, 31, 37))
    d.rectangle([0, top, 44, top + 1], fill=BLOOD)
    # footer: solid ink plate with a hairline and crop marks
    d.rectangle([0, footer, W - 1, H - 1], fill=(6, 6, 8))
    d.rectangle([0, footer, W - 1, footer], fill=(30, 31, 37))
    d.rectangle([0, footer, 30, footer], fill=BLOOD)
    for (x, y, sx, sy) in [(13, 435, 1, 1), (626, 435, -1, 1), (13, 466, 1, -1), (626, 466, -1, -1)]:
        d.line([(x, y), (x + 6 * sx, y)], fill=(48, 49, 56))
        d.line([(x, y), (x, y + 6 * sy)], fill=(48, 49, 56))
    return bg

def finish(bg, grain_amt=12, seed=5):
    bg = grain(bg, grain_amt, seed=seed)
    bg = vignette(bg, 0.82, 2.0)
    bg = scanlines(bg, 3, 0.16)
    return bg

def abstract_frame(seed):
    bg = gradient(W, H, [(0.0, GRAPHITE), (0.55, SMOKE), (1.0, INK)])
    bg = add_glow(bg, (250, 120, 620, 430), DARKRED, radius=70, strength=0.75)
    bg = perspective_grid(bg, 210, (46, 18, 22), alpha=1.0, vpx=430)
    d = ImageDraw.Draw(bg)
    rnd = random.Random(seed)
    for _ in range(9):
        x0 = rnd.randint(300, 640)
        pts = bez((x0, 0), (x0 - rnd.randint(20, 140), 120),
                  (x0 + rnd.randint(20, 120), 260), (x0 - rnd.randint(40, 200), 330))
        d.line(pts, fill=(58, 56, 60), width=1)
    return glitch(bg, seed=seed)

def build_bg_list(source=None):
    if source:
        im = load_frame(source, anchor_x=0.52, anchor_y=0.42, flip=True)
        bg = grade(im, keep_color=0.20, gamma=0.86)
        bg = bg.point(lambda v: min(255, int(v * 1.18 + 6)))
    else:
        bg = abstract_frame(5)
    # keep the left column readable
    bg = scrim_h(bg, [(0.0, 0.66), (0.30, 0.58), (0.50, 0.34), (0.70, 0.12), (1.0, 0.04)])
    bg = bands(bg)
    bg = finish(bg, 12, 5)
    bg.save(os.path.join(ART, "bg_list.png"))
    return bg

def build_bg_systems(source=None):
    if source:
        im = load_frame(source, anchor_x=0.55, anchor_y=0.22, zoom=1.02)
        bg = grade(im, keep_color=0.22, gamma=0.90)
        bg = bg.point(lambda v: min(255, int(v * 1.10 + 4)))
    else:
        bg = abstract_frame(9)
    bg = scrim_h(bg, [(0.0, 0.55), (0.30, 0.40), (0.62, 0.12), (1.0, 0.06)])
    bg = bands(bg)
    d = ImageDraw.Draw(bg)
    _f = font("SemiBold", 18)
    _lbl = "SYSTEM SELECT"
    _w = sum(d.textlength(c, font=_f) + 1.4 for c in _lbl)
    tracking_text(d, (618 - _w, 22), _lbl, _f, CREAM, 1.4)
    d.rectangle([618 - _w - 12, 24, 618 - _w - 8, 38], fill=BLOOD)
    vtext(bg, 12, 78, "nEther://systems", font("Light", 7), (86, 82, 76), 2)
    bg = finish(bg, 12, 9)
    bg.save(os.path.join(ART, "bg_systems.png"))
    return bg

# ---------------------------------------------------------------- wordmark
def tracking_text(d, xy, text, fnt, fill, tracking=0):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + tracking
    return x

def build_mark():
    """Wordmark: trimmed to its ink, so ES can scale it predictably."""
    S = 4
    tmp = Image.new("RGBA", (600 * S, 120 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.rectangle([0, 4 * S, 6 * S, 62 * S], fill=BLOOD + (255,))
    tracking_text(d, (16 * S, 0), "LAIN", font("Bold", 40 * S), CREAM + (255,), tracking=3.0 * S)
    bbox = tmp.getbbox()
    img = tmp.crop(bbox).resize(((bbox[2] - bbox[0]) // S, (bbox[3] - bbox[1]) // S), Image.LANCZOS)
    # one-pixel interference line through the wordmark
    px = img.load()
    for x in range(img.size[0]):
        y = 25
        r, g, b, a = px[x, y]
        if a:
            px[x, y] = (min(255, r + 26), g, b, a)
    img.save(os.path.join(ART, "mark.png"))
    print("mark", img.size)

    # stamped label: CLOSE THE WORLD
    w2, h2 = 236, 18
    im2 = Image.new("RGBA", (w2 * S, h2 * S), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(im2)
    d2.rectangle([0, 0, (w2 - 1) * S, (h2 - 1) * S], outline=(58, 59, 68, 255), width=S)
    tracking_text(d2, (8 * S, 4 * S), "CLOSE THE WORLD,", font("Regular", 6 * S), DIMCREAM + (255,), 1.0 * S)
    tracking_text(d2, (8 * S + 110 * S, 4 * S), "OPEN THE nEther", font("Regular", 6 * S), BLOOD + (255,), 0.6 * S)
    im2 = im2.resize((w2, h2), Image.LANCZOS)
    im2.save(os.path.join(ART, "tag.png"))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gera os fundos do tema.")
    ap.add_argument("--list", help="imagem do fundo da lista de jogos")
    ap.add_argument("--systems", help="imagem do fundo da tela de sistemas")
    args = ap.parse_args()
    build_bg_list(args.list)
    build_bg_systems(args.systems)
    build_mark()
    print("ok")
