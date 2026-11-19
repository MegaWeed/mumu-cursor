import pathlib, re

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

start = s.find("        static void DumpCursor(string file)")
assert start > 0
end = s.index("        if (Array.IndexOf(args, \"--apply\") >= 0)", start)
block = s[start:end]
s = s[:start] + s[end:]

# 变成 Program 的成员方法，放在 Main 之前
block = block.replace("        static void DumpCursor", "    static void DumpCursor", 1)
lines = block.rstrip().split("\n")
lines = [ln[4:] if ln.startswith("    ") else ln for ln in lines]   # 去掉一级缩进
block = "\n".join(lines) + "\n\n"

anchor = "    static void Main(string[] args)"
assert anchor in s
s = s.replace(anchor, block + anchor, 1)

p.write_text(s, encoding="utf-8")
print("DumpCursor moved to class level")
