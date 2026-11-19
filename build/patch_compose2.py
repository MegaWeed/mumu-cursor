import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- ApplyStatic 接收合成图 ----------
start = s.index("    public static void ApplyStatic()")
end = s.index("    // 把内嵌的 cursor_static.cur 落到磁盘", start)
new = '''    public static void ApplyStatic(Bitmap bmp, int hx, int hy) { lock (gate) ApplyStaticCore(bmp, hx, hy); }

    static void ApplyStaticCore(Bitmap bmp, int hx, int hy)
    {
        if (Applied) return;
        IntPtr cur = Nat.LoadCursorW(IntPtr.Zero, new IntPtr(Nat.OCR_NORMAL));
        if (cur != IntPtr.Zero && !IsBlank(cur))
        {
            snapshot = Nat.CopyIcon(cur);
            SaveBackup(cur);
        }

        string file = null;
        try
        {
            file = Path.Combine(Path.GetTempPath(), "mumu_static_cursor.cur");
            WriteCurEx(bmp, file, hx, hy);
        }
        catch { file = null; }

        IntPtr h = IntPtr.Zero;
        if (file != null) h = Nat.LoadImageW(IntPtr.Zero, file, 2, bmp.Width, bmp.Height, 0x10);

        if (h == IntPtr.Zero) { Blank(); LastLog = "static: load cur failed, blank"; }
        else
        {
            Nat.SetSystemCursor(h, Nat.OCR_NORMAL);
            SetBaseSize(bmp.Width);      // 同时把系统的“指针大小”调过去，不然 Windows 会按 32 画
            LastLog = "static: set cur ok " + bmp.Width + "px";
        }
        Applied = true;
        SetDirty(true);
    }

    // HKCU\\Control Panel\\Cursors\\CursorBaseSize + 让系统重载方案（Win10/11 的“辅助功能 → 指针大小”）
    public static void SetBaseSize(int px)
    {
        try
        {
            using (var k = Registry.CurrentUser.CreateSubKey(@"Control Panel\\Cursors"))
                k.SetValue("CursorBaseSize", px, RegistryValueKind.DWord);
        }
        catch { }
        try { Nat.SystemParametersInfoW(Nat.SPI_SETCURSORS, 0, IntPtr.Zero, Nat.SPIF_SENDCHANGE); } catch { }
    }

'''
s = s[:start] + new + s[end:]

# ---------- WriteCur 扩展为任意尺寸 + 热点 ----------
old_start = s.index("    // 32x32 的经典 .cur（32bpp DIB 帧），恢复时用 LoadImage 读回来最稳")
old_end = s.index("    // 「已经变身过」的标记", old_start)
new_writer = '''    // 经典 .cur（32bpp DIB 帧）：任意尺寸 + 指定热点，LoadImage 读回来最稳
    static void WriteCurEx(Bitmap src, string file, int hotX, int hotY)
    {
        int size = Math.Max(16, Math.Min(256, src.Width));
        var xor = new byte[size * size * 4];
        int p = 0;
        for (int y = size - 1; y >= 0; y--)
            for (int x = 0; x < size; x++)
            {
                var c = src.GetPixel(Math.Min(x, src.Width - 1), Math.Min(y, src.Height - 1));
                xor[p++] = c.B; xor[p++] = c.G; xor[p++] = c.R; xor[p++] = c.A;
            }
        var and = new byte[((size + 31) / 32) * 4 * size];

        var ms = new MemoryStream();
        var bw = new BinaryWriter(ms);
        int blob = 40 + xor.Length + and.Length;
        bw.Write((ushort)0); bw.Write((ushort)2); bw.Write((ushort)1);
        bw.Write((byte)(size >= 256 ? 0 : size)); bw.Write((byte)(size >= 256 ? 0 : size));
        bw.Write((byte)0); bw.Write((byte)0);
        bw.Write((ushort)Math.Max(0, Math.Min(255, hotX))); bw.Write((ushort)Math.Max(0, Math.Min(255, hotY)));
        bw.Write((uint)blob); bw.Write((uint)(6 + 16));
        bw.Write((uint)40); bw.Write((int)size); bw.Write((int)(size * 2));
        bw.Write((ushort)1); bw.Write((ushort)32);
        bw.Write((uint)0); bw.Write((uint)0); bw.Write((int)0); bw.Write((int)0); bw.Write((uint)0); bw.Write((uint)0);
        bw.Write(xor); bw.Write(and);
        bw.Flush();
        File.WriteAllBytes(file, ms.ToArray());
    }

    static void WriteCur(Bitmap src, string file) { try { WriteCurEx(src, file, 0, 0); } catch { } }

'''
s = s[:old_start] + new_writer + s[old_end:]

# ---------- MainForm.Apply 静态分支传入合成图 ----------
old = """            if (C.Mode == "static")
            {
                CursorSwitch.ApplyStatic();
                staticOn = true;
                RefreshStatus();
                return;
            }"""
new = """            if (C.Mode == "static")
            {
                var sl = Art.Build(C);
                CursorSwitch.ApplyStatic(sl.StaticCur, sl.StaticHotX, sl.StaticHotY);
                staticOn = true;
                RefreshStatus();
                return;
            }"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("static cursor = composed bitmap, size-aware")
