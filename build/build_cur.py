"""静态贴图 → 真正的系统光标（.cur），多尺寸帧：32 起步，最大 256。
Windows 的「辅助功能 → 指针大小」放大时，会去 .cur 里挑最接近的尺寸，所以帧越全越清楚。"""
import struct
import pathlib
from PIL import Image, ImageDraw

ROOT = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor")
SRC = ROOT / "source" / "static_full.png"
OUT = ROOT / "assets" / "cursor_static.cur"

SIZES = (32, 40, 48, 64, 96, 128, 192, 256)
src = Image.open(SRC).convert("RGBA")


def frame(size):
    im = src.resize((size, size), Image.LANCZOS)
    ss = 8 if size <= 96 else 4
    mask = Image.new("L", (size * ss, size * ss), 0)
    pad = max(1, size // 32) * ss
    ImageDraw.Draw(mask).rounded_rectangle((pad, pad, size * ss - pad - 1, size * ss - pad - 1),
                                           radius=int(size * ss * 0.22), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    im.putalpha(mask)
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    w = max(1, size // 32)
    ImageDraw.Draw(ring).rounded_rectangle((w, w, size - w - 1, size - w - 1), radius=int(size * 0.22),
                                            outline=(255, 255, 255, 110), width=w)
    ring.putalpha(Image.composite(ring.getchannel("A"), Image.new("L", (size, size), 0), mask))
    return Image.alpha_composite(im, ring)


def dib(im):
    w, h = im.size
    px = im.load()
    xor = bytearray()
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[x, y]
            row += bytes((b, g, r, a))
        xor += row
    and_mask = bytearray(((w + 31) // 32) * 4 * h)
    bih = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    return bytes(bih) + bytes(xor) + bytes(and_mask)


frames = [frame(s) for s in SIZES]
blobs = [dib(f) for f in frames]

header = struct.pack("<HHH", 0, 2, len(frames))
offset = 6 + 16 * len(frames)
entries = b""
for im, blob in zip(frames, blobs):
    bw = 0 if im.width >= 256 else im.width
    bh = 0 if im.height >= 256 else im.height
    entries += struct.pack("<BBBBHHII", bw, bh, 0, 0, 1, 32, len(blob), offset, )[:12] + struct.pack("<II", 0, 0)[:0] + struct.pack("<II", offset, 0)[:0]
    offset += len(blob)

# 上面那行拼得太绕，重来（格式：w,h,colors,reserved,hotspotX,hotspotY,bytes,offset）
entries = b""
offset = 6 + 16 * len(frames)
for im, blob in zip(frames, blobs):
    bw = 0 if im.width >= 256 else im.width
    bh = 0 if im.height >= 256 else im.height
    entries += struct.pack("<BBBBHHII", bw, bh, 0, 0, im.width // 2, im.height // 2, len(blob), offset)   # 热点=圆心
    offset += len(blob)

OUT.write_bytes(header + entries + b"".join(blobs))
print("cur ok", OUT.stat().st_size, "bytes", "frames", list(SIZES))

check = Image.open(OUT)
print("readback", check.format, check.size)

big = Image.new("RGBA", (32 * 8 * 2 + 30, 32 * 8 + 20), (0, 0, 0, 0))
for i, bg in enumerate([(22, 22, 26, 255), (240, 240, 244, 255)]):
    cell = Image.new("RGBA", (32 * 8, 32 * 8), bg)
    cell.alpha_composite(frames[0].resize((32 * 8, 32 * 8), Image.NEAREST))
    big.alpha_composite(cell, (10 + i * (32 * 8 + 10), 10))
big.convert("RGB").save(ROOT / "preview" / "cur32.png")
frames[-1].resize((256, 256), Image.LANCZOS).convert("RGB").save(ROOT / "preview" / "cur256.png")
