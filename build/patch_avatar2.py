import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\build_assets.py")
s = p.read_text(encoding="utf-8")

start = s.index("# ---------------------------------------------------------------- 2.")
end = s.index("# ---------------------------------------------------------------- 3.")
new = '''# ---------------------------------------------------------------- 2. 主体：圆形头像（用户给的成品圆图）
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

'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("ok")
