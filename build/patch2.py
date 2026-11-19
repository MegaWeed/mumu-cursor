import pathlib, os
root = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor")
old = root / "MumuCursor.cs"
fixed = root / "MumuCursor_fixed.cs"
bak = root / "build" / "MumuCursor_corrupted_backup.cs"
bak.parent.mkdir(exist_ok=True)
if old.exists():
    old.replace(bak)
    print("archived old ->", bak)
if fixed.exists():
    fixed.replace(root / "MumuCursor.cs")
    print("renamed fixed -> MumuCursor.cs")
print([p.name for p in root.glob("*.cs")])
