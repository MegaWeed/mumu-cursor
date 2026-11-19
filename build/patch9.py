import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = """        bool created;
        instanceMutex = new Mutex(true, "MUMU_Cursor_SingleInstance", out created);
        if (!created) return;               // 已经在运行了，别再开第二个
"""
new = """        bool forceRestore = Array.IndexOf(args, "--restore") >= 0;
        if (!forceRestore)
        {
            bool created;
            instanceMutex = new Mutex(true, "MUMU_Cursor_SingleInstance", out created);
            if (!created) return;           // 已经在运行了，别再开第二个（--restore 例外）
        }
"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("patched: --restore bypasses single-instance")
