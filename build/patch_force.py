import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = """        bool forceRestore = Array.IndexOf(args, "--restore") >= 0;
        if (!forceRestore)"""
new = """        bool forceRestore = Array.IndexOf(args, "--restore") >= 0;
        bool skipMutex = Array.IndexOf(args, "--force") >= 0;     // 测试用：忽略「已经在运行」的判断
        if (!forceRestore && !skipMutex)"""
assert old in s, "mutex guard"
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("force flag added")
