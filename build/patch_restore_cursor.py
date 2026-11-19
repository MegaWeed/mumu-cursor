import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

anchor = "    public static void Apply() { lock (gate) ApplyCore(); }\n"
assert anchor in s

restore = '''    public static void Apply() { lock (gate) ApplyCore(); }

    static void ApplyCore()
    {
        if (Applied) return;
        IntPtr cur = Nat.LoadCursorW(IntPtr.Zero, new IntPtr(Nat.OCR_NORMAL));
        if (cur != IntPtr.Zero && !IsBlank(cur))
        {
            snapshot = Nat.CopyIcon(cur);
            SaveBackup(cur);
        }
        Blank();
        Applied = true;
        SetDirty(true);
        LastLog = "apply: snapshot " + (snapshot != IntPtr.Zero ? "ok" : "none");
    }

    static void Blank()
    {
        var and = new byte[32 * 32 / 8]; var xor = new byte[32 * 32 / 8];
        for (int i = 0; i < and.Length; i++) and[i] = 0xFF;
        IntPtr h = Nat.CreateCursor(IntPtr.Zero, 0, 0, 32, 32, and, xor);
        Nat.SetSystemCursor(h, Nat.OCR_NORMAL);
    }

    static void SaveBackup(IntPtr hcur)
    {
        try
        {
            using (var ic = Icon.FromHandle(hcur))
            using (var bmp = ic.ToBitmap())
                WriteCur(bmp, BackupCur);
        }
        catch { }
    }

    // 32x32 的经典 .cur（32bpp DIB 帧），恢复时用 LoadImage 读回来最稳
    static void WriteCur(Bitmap src, string file)
    {
        try
        {
            const int size = 32;
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
            bw.Write((byte)size); bw.Write((byte)size); bw.Write((byte)0); bw.Write((byte)0);
            bw.Write((ushort)0); bw.Write((ushort)0);                 // hotspot 0,0
            bw.Write((uint)blob); bw.Write((uint)(6 + 16));
            bw.Write((uint)40); bw.Write((int)size); bw.Write((int)(size * 2));
            bw.Write((ushort)1); bw.Write((ushort)32);
            bw.Write((uint)0); bw.Write((uint)0); bw.Write((int)0); bw.Write((int)0); bw.Write((uint)0); bw.Write((uint)0);
            bw.Write(xor); bw.Write(and);
            bw.Flush();
            Directory.CreateDirectory(Path.GetDirectoryName(file));
            File.WriteAllBytes(file, ms.ToArray());
        }
        catch { }
    }

    // 「已经变身过」的标记：注册表 + 文件双写，被强杀后下次启动也能救回来
    static void SetDirty(bool on)
    {
        try
        {
            using (var k = Registry.CurrentUser.CreateSubKey(@"Software\\MUMUCursor"))
                k.SetValue("Active", on ? 1 : 0);
        }
        catch { }
        try
        {
            var f = Path.Combine(Cfg.Dir, "active.flag");
            if (on) File.WriteAllText(f, "1");
            else if (File.Exists(f)) File.Delete(f);
        }
        catch { }
    }

    public static bool IsDirty()
    {
        try
        {
            using (var k = Registry.CurrentUser.OpenSubKey(@"Software\\MUMUCursor"))
                if (k != null && Convert.ToInt32(k.GetValue("Active", 0)) != 0) return true;
        }
        catch { }
        try { return File.Exists(Path.Combine(Cfg.Dir, "active.flag")); } catch { }
        return false;
    }

'''
s = s.replace(anchor, restore, 1)
p.write_text(s, encoding="utf-8")
print("cursor helpers restored")
