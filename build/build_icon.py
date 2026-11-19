import pathlib, struct
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor")
src = Image.open(ROOT / "source" / "app_icon_src.png").convert("RGBA")

W, H = src.size
side = min(W, H)
src = src.crop(((W - side) // 2, (H - side) // 2, (W - side) // 2 + side, (H - side) // 2 + side))

S = 512
RAD_RATIO = 0.20
BORDER = 6


def make(full_img, zoom=1.0):
    """zoom>1 时往脸的方向裁一块再放大，用于 16/20/24 这种小图标"""
    if zoom > 1.0:
        c = int(S / zoom)
        x0 = (S - c) // 2
        y0 = int((S - c) * 0.42)          # 稍微偏上，留住光环
        art = full_img.crop((x0, y0, x0 + c, y0 + c)).resize((S, S), Image.LANCZOS)
    else:
        art = full_img

    RAD = int(S * RAD_RATIO)
    mask = Image.new("L", (S * 2, S * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S * 2 - 1, S * 2 - 1), radius=RAD * 2, fill=255)
    mask = mask.resize((S, S), Image.LANCZOS)
    art = art.copy()
    art.putalpha(mask)

    PAD = 16
    canvas = Image.new("RGBA", (S + PAD * 2, S + PAD * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((PAD + 4, PAD + 8, PAD + S + 4, PAD + S + 10), radius=RAD, fill=(15, 10, 22, 120))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))

    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((PAD - BORDER, PAD - BORDER, PAD + S + BORDER, PAD + S + BORDER),
                        radius=RAD + BORDER, fill=(255, 255, 255, 255))
    canvas.alpha_composite(art, (PAD, PAD))
    return canvas.resize((256, 256), Image.LANCZOS)


full = src.resize((S, S), Image.LANCZOS)
master = make(full)
master.save(ROOT / "preview" / "app_icon_256.png")

SIZES = [(16, 1.45), (20, 1.30), (24, 1.18), (32, 1.0), (40, 1.0), (48, 1.0), (64, 1.0), (128, 1.0), (256, 1.0)]
frames = []
for sz, z in SIZES:
    frames.append((sz, master.resize((sz, sz), Image.LANCZOS)))

# 自己写 ICO：每个尺寸一张独立 PNG，小尺寸用放大裁切版
ent = []
blobs = []
off = 6 + 16 * len(frames)
for sz, im in frames:
    import io
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    ent.append(struct.pack("<BBBBHHII", sz if sz < 256 else 0, sz if sz < 256 else 0, 0, 0, 1, 32, len(data), off))
    blobs.append(data)
    off += len(data)
ico = struct.pack("<HHH", 0, 1, len(frames)) + b"".join(ent) + b"".join(blobs)
(ROOT / "assets" / "app.ico").write_bytes(ico)

strip = Image.new("RGBA", (5 * 72 + 60, 2 * 72 + 40), (30, 30, 34, 255))
for i, (sz, im) in enumerate(frames[:5]):
    for row, bg in enumerate([(30, 30, 34, 255), (245, 245, 248, 255)]):
        cell = Image.new("RGBA", (72, 72), bg)
        cell.alpha_composite(im, ((72 - sz) // 2, (72 - sz) // 2))
        strip.alpha_composite(cell, (30 + i * 72, 20 + row * 72))
strip.convert("RGB").save(ROOT / "preview" / "app_icon_sizes.png")

print("ico ok", len(ico), "bytes, frames", [s for s, _ in frames])
