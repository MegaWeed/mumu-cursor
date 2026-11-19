import pathlib

ROOT = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor")
src = ROOT / "build_assets.py"
s = src.read_text(encoding="utf-8")

start = s.index("# ---------------------------------------------------------------- 3.")
nxt = s.index("# ---------------------------------------------------------------- 4.", start)
block = (ROOT / "build" / "pointers_block.py").read_text(encoding="utf-8")
s = s[:start] + block + "\n" + s[nxt:]
src.write_text(s, encoding="utf-8")
print("spliced, new len", len(s))
