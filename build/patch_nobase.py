import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 不再改全局「指针大小」——那会把所有系统光标（I 型、缩放箭头…）一起放大，看着就像“搞坏了”
old = """            // 顺序很关键：SPI_SETCURSORS 会按“方案”重载所有光标，
            // 如果先 SetSystemCursor 再调大小，我们的光标会被立刻换回箭头 —— 看起来就是“点了没反应”。
            SetBaseSize(bmp.Width);
            Thread.Sleep(60);
            Nat.SetSystemCursor(h, Nat.OCR_NORMAL);"""
new = """            // 只换 OCR_NORMAL 这一个光标，不碰系统“指针大小”。
            // （改 CursorBaseSize 会把 I 型、缩放箭头等所有系统光标一起放大，等于把系统搞乱。）
            Nat.SetSystemCursor(h, Nat.OCR_NORMAL);"""
assert old in s
s = s.replace(old, new, 1)

# 2) 恢复时把可能被旧版改过的全局大小写回 32
old = """    public static void SetBaseSize(int px)"""
new = """    // 旧版本曾把 CursorBaseSize 改成 128，恢复时顺手写回默认值
    public static void ResetBaseSizeIfBroken()
    {
        try
        {
            using (var k = Registry.CurrentUser.OpenSubKey(@"Control Panel\\Cursors", true))
            {
                if (k == null) return;
                object v = k.GetValue("CursorBaseSize");
                if (v == null) return;
                int cur = Convert.ToInt32(v);
                if (cur <= 40) return;
                k.SetValue("CursorBaseSize", 32, RegistryValueKind.DWord);
            }
            try { Nat.SystemParametersInfoW(Nat.SPI_SETCURSORS, 0, IntPtr.Zero, Nat.SPIF_SENDCHANGE); } catch { }
        }
        catch { }
    }

    public static void SetBaseSize(int px)"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("global size change removed")
