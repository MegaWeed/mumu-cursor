import pathlib, re

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\build_assets.py")
s = p.read_text(encoding="utf-8")

start = s.index("# ---------------------------------------------------------------- 2.")
end = s.index("# ---------------------------------------------------------------- 3.")
new = '''# ---------------------------------------------------------------- 2. 主体备选：圆形头像（用户给的新图）
av = Image.open(SRC_AVATAR).convert("RGB")
# 人脸在 896x875 里的位置：整颗头 x 60..760 / y 30..640，取一个把头发和下巴都包住的正方形
AV_BOX = (75, 20, 735, 680)
S = 200
face = av.crop(AV_BOX).resize((S * 2, S * 2), Image.LANCZOS).convert("RGBA")

disc = Image.new("L", (S * 4, S * 4), 0)
ImageDraw.Draw(disc).ellipse((0, 0, S * 4 - 1, S * 4 - 1), fill=255)
disc = disc.resize((S * 2, S * 2), Image.LANCZOS)
face.putalpha(disc)
face = face.resize((S, S), Image.LANCZOS)

RING = 5                     # 窄白描边
avatar = Image.new("RGBA", (S + 2 * RING + 8, S + 2 * RING + 8), (0, 0, 0, 0))

# 柔和投影
sh = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((RING + 4, RING + 6, RING + S + 6, RING + S + 8), fill=(20, 14, 24, 90))
avatar.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))

# 先铺一个白色圆盘（比照片大 RING 像素），再把照片贴上去 = 窄白圈
ring = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
d = ImageDraw.Draw(ring)
d.ellipse((4, 4, 4 + S + 2 * RING, 4 + S + 2 * RING), fill=(255, 255, 255, 250))
avatar.alpha_composite(ring)
avatar.alpha_composite(face, (4 + RING, 4 + RING))
avatar.save(ASSETS / "body_avatar.png")
print("avatar", avatar.size)

'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("avatar block replaced")
