"""Build MUMU光标 assets: 主体(去掉指针)、圆形头像、5 种小指针、默认吊起物、6 个点击音效。"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import json, math, pathlib, wave, struct

ROOT = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SRC_CHAR = ROOT.parent / "cursor-coin" / "source" / "char.png"
SRC_COIN = ROOT.parent / "cursor-coin" / "assets" / "coin.png"
SRC_AVATAR = ROOT / "source" / "avatar_full.jpg"   # 用户给的新图 896x875
ASSETS.mkdir(parents=True, exist_ok=True)


def trim(im):
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


# ---------------------------------------------------------------- 1. 主体：人物（不带小指针）
char = trim(Image.open(SRC_CHAR).convert("RGBA"))
BODY_H = 100
w = max(1, round(char.width * BODY_H / char.height))
body = char.resize((w, BODY_H), Image.LANCZOS)
body.save(ASSETS / "body_default.png")
PIVOT = (round(w * 0.42), round(BODY_H * 0.965))
print("body", body.size, "pivot", PIVOT)

# ---------------------------------------------------------------- 2. 主体：圆形头像（用户给的成品圆图）
av = Image.open(ROOT / "source" / "avatar_round.png").convert("RGBA")
S = 218
face = av.resize((S, S), Image.LANCZOS)

avatar = Image.new("RGBA", (S + 10, S + 10), (0, 0, 0, 0))
sh = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((7, 8, S + 3, S + 4), fill=(20, 14, 24, 80))
avatar.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
avatar.alpha_composite(face, (5, 5))
avatar.save(ASSETS / "body_avatar.png")
print("avatar", avatar.size)

# ---------------------------------------------------------------- 2b. 静态模式的整张图（人物 + 金币一体，无绳子）
st = Image.open(ROOT / "source" / "static_full.png").convert("RGBA")
st = st.resize((150, 150), Image.LANCZOS)
st.save(ASSETS / "static_full.png")
print("static", st.size)

# ---------------------------------------------------------------- 3. 小指针 = 造型 × 颜色（6 × 5 = 30 张）
SS = 8          # 超采样
TILE = 43       # 成品尺寸

COLORS = {
    "silver": dict(c1=(255, 255, 255), c2=(176, 184, 198), outline=(26, 28, 38, 240),
                   glow=None, shadow=(12, 10, 26, 95), label="银"),
    "gold":   dict(c1=(255, 242, 196), c2=(226, 160, 54), outline=(62, 38, 10, 245),
                   glow=(255, 196, 64, 110), shadow=(40, 26, 8, 110), label="金"),
    "neon":   dict(c1=(196, 255, 252), c2=(34, 206, 220), outline=(6, 44, 60, 240),
                   glow=(70, 240, 255, 120), shadow=None, label="霓虹"),
    "ink":    dict(c1=(44, 44, 54), c2=(12, 12, 18), outline=(255, 255, 255, 240),
                   glow=None, shadow=(0, 0, 0, 120), label="墨"),
    "bubble": dict(c1=(255, 255, 255), c2=(206, 222, 255), outline=(40, 54, 96, 205),
                   glow=None, shadow=(60, 80, 140, 80), label="泡泡"),
}


def rrect(d, x0, y0, x1, y1, r, fill=255):
    d.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=fill)


def bar(d, x0, y0, x1, y1, w):
    """带圆头的粗线（低层 mask 用）"""
    d.line((x0 * SS, y0 * SS, x1 * SS, y1 * SS), fill=255, width=int(w * SS))
    for cx, cy in ((x0, y0), (x1, y1)):
        d.ellipse(((cx * SS) - w * SS / 2, (cy * SS) - w * SS / 2,
                   (cx * SS) + w * SS / 2, (cy * SS) + w * SS / 2), fill=255)


def draw_chevron(d):
    # 老样式：尖在左上 (10,10)，两臂分别朝右下 / 左下
    tip = (10.0, 10.0)
    bar(d, tip[0], tip[1], tip[0] + 19.0, tip[1] + 6.5, 5.4)
    bar(d, tip[0], tip[1], tip[0] + 6.5, tip[1] + 19.0, 5.4)


def draw_arrow(d):
    pts = [(9, 6), (9, 30.5), (15.6, 24.2), (20.2, 35.0), (24.8, 33.0), (20.2, 22.4), (28.2, 22.4)]
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=255)


def draw_cross(d):
    cx, cy = 21.5 * SS, 21.5 * SS
    arm_len, arm_w, gap = 12.0 * SS, 4.6 * SS, 4.6 * SS
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if dx:
            x0 = cx + (gap if dx > 0 else -arm_len)
            rrect(d, x0, cy - arm_w / 2, x0 + (arm_len - gap), cy + arm_w / 2, arm_w / 2)
        else:
            y0 = cy + (gap if dy > 0 else -arm_len)
            rrect(d, cx - arm_w / 2, y0, cx + arm_w / 2, y0 + (arm_len - gap), arm_w / 2)
    r = 2.6 * SS
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)


def draw_ring(d):
    cx, cy = 21.5 * SS, 21.5 * SS
    R, w = 11.2 * SS, 4.2 * SS
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=255, width=int(w))
    r = 2.4 * SS
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)


def draw_diamond(d):
    cx, cy = 21.5 * SS, 21.5 * SS
    R, w = 12.2 * SS, 4.0 * SS
    outer = [(cx, cy - R), (cx + R, cy), (cx, cy + R), (cx - R, cy)]
    inner = [(cx, cy - (R - w)), (cx + (R - w), cy), (cx, cy + (R - w)), (cx - (R - w), cy)]
    d.polygon(outer, fill=255)
    d.polygon(inner, fill=0)
    r = 2.2 * SS
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)


def draw_move(d):
    cx, cy = 21.5 * SS, 21.5 * SS
    arm_w, r1, tip = 4.4 * SS, 9.6 * SS, 13.2 * SS
    rrect(d, cx - arm_w / 2, cy - r1, cx + arm_w / 2, cy + r1, arm_w / 2)
    rrect(d, cx - r1, cy - arm_w / 2, cx + r1, cy + arm_w / 2, arm_w / 2)
    for sx, sy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        if sx == 0:
            pts = [(cx, cy + sy * tip), (cx - 3.6 * SS, cy + sy * r1), (cx + 3.6 * SS, cy + sy * r1)]
        else:
            pts = [(cx + sx * tip, cy), (cx + sx * r1, cy - 3.6 * SS), (cx + sx * r1, cy + 3.6 * SS)]
        d.polygon(pts, fill=255)


SHAPES = {
    "chevron": (draw_chevron, (10, 10), "雪佛龙"),
    "arrow":   (draw_arrow, (9, 6), "箭头"),
    "cross":   (draw_cross, (21, 21), "十字"),
    "ring":    (draw_ring, (21, 21), "圆环"),
    "diamond": (draw_diamond, (21, 21), "菱形"),
    "move":    (draw_move, (21, 21), "四向"),
}


def render_pointer(shape, color):
    st = COLORS[color]
    W = TILE * SS
    mask = Image.new("L", (W, W), 0)
    SHAPES[shape][0](ImageDraw.Draw(mask))

    def dilate(px):
        out = mask
        for _ in range(max(1, int(px))):
            out = out.filter(ImageFilter.MaxFilter(3))
        return out

    out = Image.new("RGBA", (W, W), (0, 0, 0, 0))

    if st["glow"]:
        g = Image.new("RGBA", (W, W), st["glow"])
        g.putalpha(dilate(3.2 * SS).filter(ImageFilter.GaussianBlur(2.6 * SS)).point(lambda v: int(v * 0.55)))
        out = Image.alpha_composite(out, g)

    if st["shadow"]:
        s = Image.new("RGBA", (W, W), st["shadow"])
        s.putalpha(dilate(1.2 * SS).filter(ImageFilter.GaussianBlur(1.6 * SS)))
        s = s.transform(s.size, Image.AFFINE, (1, 0, -1.6 * SS, 0, 1, -2.4 * SS))
        out = Image.alpha_composite(out, s)

    if st["outline"]:
        o = Image.new("RGBA", (W, W), st["outline"])
        o.putalpha(dilate(1.5 * SS))
        out = Image.alpha_composite(out, o)

    grad = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(W):
        t = i / (W - 1)
        c = tuple(round(st["c1"][k] + (st["c2"][k] - st["c1"][k]) * t) for k in range(3)) + (255,)
        gd.line([(0, i), (W, i)], fill=c)
    grad.putalpha(mask)
    out = Image.alpha_composite(out, grad)
    return out.resize((TILE, TILE), Image.LANCZOS)


names = {}
for sh in SHAPES:
    for co in COLORS:
        render_pointer(sh, co).save(ASSETS / f"pointer_{sh}_{co}.png")
        names[f"{sh}_{co}"] = list(SHAPES[sh][1])
print("pointers", len(names), "shapes", list(SHAPES), "colors", list(COLORS))


# ---------------------------------------------------------------- 4. 默认吊起物：AC 金币
coin = trim(Image.open(SRC_COIN).convert("RGBA"))
COIN_H = 63
coin = coin.resize((max(1, round(coin.width * COIN_H / coin.height)), COIN_H), Image.LANCZOS)
coin.save(ASSETS / "item_coin.png")
print("coin", coin.size)

# ---------------------------------------------------------------- 5. 六个点击音效（全部合成，无版权素材）
SR = 44100


def env(n, attack=0.004, decay=1.0, power=2.2):
    t = np.linspace(0, n / SR, n, endpoint=False)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(decay, 1e-4) * power)


def tone(freq, dur, wave_type="sine", decay=0.12, detune=0.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq * (1 + detune)
    if wave_type == "square":
        x = np.sign(np.sin(2 * np.pi * f * t))
    elif wave_type == "tri":
        x = 2 * np.abs(2 * ((f * t) % 1) - 1) - 1
    elif wave_type == "saw":
        x = 2 * ((f * t) % 1) - 1
    else:
        x = np.sin(2 * np.pi * f * t)
    return x * env(n, decay=decay)


def mix(dur, *parts):
    n = int(SR * dur)
    out = np.zeros(n)
    for start, sig in parts:
        i = int(start * SR)
        j = min(n, i + len(sig))
        out[i:j] += sig[: j - i]
    peak = np.max(np.abs(out)) or 1
    return out / peak * 0.75


def save_wav(name, data):
    data = np.clip(data, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(str(ASSETS / f"sfx_{name}.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


B5, E6, G6, C6, A5, A6, B6 = 987.77, 1318.51, 1567.98, 1046.50, 880.0, 1760.0, 1975.53

save_wav("coin", mix(0.30,
                     (0.000, tone(B5, 0.075, "square", 0.09)),
                     (0.065, tone(E6, 0.24, "square", 0.16))))
save_wav("jump", mix(0.26,
                     (0.000, tone(392.0, 0.07, "square", 0.07)),
                     (0.055, tone(523.25, 0.07, "square", 0.08)),
                     (0.110, tone(659.25, 0.14, "square", 0.12))))
save_wav("bell", mix(0.34,
                     (0.000, tone(C6, 0.32, "sine", 0.10) * 0.7
                      + tone(C6 * 2.01, 0.32, "sine", 0.06) * 0.3)))
save_wav("pop", mix(0.20,
                    (0.000, np.random.RandomState(1).randn(int(SR * 0.03)) * env(int(SR * 0.03), decay=0.01) * 0.5),
                    (0.010, tone(880.0, 0.18, "tri", 0.07))))
save_wav("chime", mix(0.42,
                      (0.000, tone(A5, 0.30, "sine", 0.14)),
                      (0.070, tone(E6, 0.30, "sine", 0.14) * 0.8),
                      (0.140, tone(A6, 0.26, "sine", 0.12) * 0.6)))
save_wav("arcade", mix(0.28,
                       (0.000, tone(C6, 0.06, "saw", 0.08) * 0.6),
                       (0.050, tone(E6, 0.06, "saw", 0.08) * 0.6),
                       (0.100, tone(G6, 0.16, "saw", 0.12) * 0.6)))

# ---------------------------------------------------------------- meta
meta = {
    "bodyDefault": list(body.size),
    "pivot": PIVOT,
    "bodyAvatar": list(avatar.size),
    "coin": list(coin.size),
    "pointers": {k: list(v) for k, v in names.items()},
}
(ASSETS / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
print("done", meta)
