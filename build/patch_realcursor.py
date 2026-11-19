import pathlib

# ---------- 1) 编译器把 .cur 也打进去 ----------
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\build_exe.py")
s = p.read_text(encoding="utf-8")
old = 'if p.suffix.lower() in (".png", ".wav"):'
new = 'if p.suffix.lower() in (".png", ".wav", ".cur"):'
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# ---------- 2) 静态模式 = 真系统光标 ----------
c = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = c.read_text(encoding="utf-8")

# 2a) CursorSwitch 增加 ApplyStatic
anchor = """    public static void Apply() { lock (gate) ApplyCore(); }"""
add = """    public static void Apply() { lock (gate) ApplyCore(); }

    // 静态模式：直接把真正的系统光标换成那一张图（不是覆盖层），任何程序里都是它
    public static void ApplyStatic() { lock (gate) ApplyStaticCore(); }

    static void ApplyStaticCore()
    {
        if (Applied) return;
        IntPtr cur = Nat.LoadCursorW(IntPtr.Zero, new IntPtr(Nat.OCR_NORMAL));
        if (cur != IntPtr.Zero && !IsBlank(cur))
        {
            snapshot = Nat.CopyIcon(cur);
            SaveBackup(cur);
        }
        string path = StaticCurPath();
        IntPtr h = IntPtr.Zero;
        if (path != null) h = Nat.LoadImageW(IntPtr.Zero, path, 2, 0, 0, 0x10);   // IMAGE_CURSOR | LR_LOADFROMFILE
        if (h == IntPtr.Zero) { Blank(); LastLog = "static: load cur failed, blank"; }
        else
        {
            Nat.SetSystemCursor(h, Nat.OCR_NORMAL);
            LastLog = "static: set cur ok";
        }
        Applied = true;
        SetDirty(true);
    }

    // 把内嵌的 cursor_static.cur 落到磁盘（SetSystemCursor 只吃文件/句柄，LoadImage 走文件最稳）
    static string StaticCurPath()
    {
        try
        {
            var dir = Path.Combine(Cfg.Dir, "cursor");
            Directory.CreateDirectory(dir);
            var file = Path.Combine(dir, "static.cur");
            var asm = System.Reflection.Assembly.GetExecutingAssembly();
            using (var s2 = asm.GetManifestResourceStream("cursor_static.cur"))
            {
                if (s2 == null) return null;
                using (var f = File.Create(file)) s2.CopyTo(f);
            }
            return file;
        }
        catch { return null; }
    }"""
assert anchor in s
s = s.replace(anchor, add, 1)

# 2b) MainForm.Apply：静态模式不开覆盖层，直接换真光标
old = """            if (overlay != null) return;
            var look = Art.Build(C);"""
new = """            if (overlay != null) return;

            // 静态贴图 = 真系统光标：没有覆盖层，也不再藏系统光标，
            // 所以在任何程序（包括游戏菜单）里看到的就是它。
            if (C.Mode == "static")
            {
                CursorSwitch.ApplyStatic();
                RefreshStatus();
                return;
            }

            var look = Art.Build(C);"""
assert old in s
s = s.replace(old, new, 1)

c.write_text(s, encoding="utf-8")
print("static mode -> real cursor")
