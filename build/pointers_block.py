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

