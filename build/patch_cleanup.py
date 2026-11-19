import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 去掉调试输出
old = '''        Console.WriteLine("cover: " + (cover == null ? "null" : "ok " + cover.Bounds + " parent=" + (cover.Parent == null ? "null" : cover.Parent.Name)) + " settings=" + settings.Bounds);'''
if old in s:
    s = s.replace(old, "", 1)

start = s.find('                if (Environment.GetEnvironmentVariable("MUMU_FADE_DEBUG") == "1")')
if start >= 0:
    end = s.index("                }", s.index('Console.WriteLine("snap saved', start)) + len("                }\n")
    s = s[:start] + s[end:]

p.write_text(s, encoding="utf-8")
print("debug output removed")
