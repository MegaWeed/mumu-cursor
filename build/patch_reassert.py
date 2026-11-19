import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 记下最后一次的 .cur 路径与尺寸，供“稍后再钉一次”用
old = '''        IntPtr h = IntPtr.Zero;
        if (file != null) h = Nat.LoadImageW(IntPtr.Zero, file, 2, bmp.Width, bmp.Height, 0x10);'''
new = '''        IntPtr h = IntPtr.Zero;
        staticPath = file; staticW = bmp.Width; staticH = bmp.Height;
        if (file != null) h = Nat.LoadImageW(IntPtr.Zero, file, 2, bmp.Width, bmp.Height, 0x10);'''
assert old in s
s = s.replace(old, new, 1)

# Reassert：其它程序（或系统重载方案）把光标换回去之后，再钉一次
anchor = "    // HKCU\\Control Panel\\Cursors\\CursorBaseSize + 让系统重载方案（Win10/11 的“辅助功能 → 指针大小”）"
add = '''    static string staticPath;
    static int staticW, staticH;

    // 有些程序会调 SPI_SETCURSORS 把方案重载回去，隔一会儿再钉一次
    public static void Reassert()
    {
        try
        {
            if (string.IsNullOrEmpty(staticPath) || !File.Exists(staticPath)) return;
            var h2 = Nat.LoadImageW(IntPtr.Zero, staticPath, 2, staticW, staticH, 0x10);
            if (h2 != IntPtr.Zero) Nat.SetSystemCursor(h2, Nat.OCR_NORMAL);
        }
        catch { }
    }

'''
assert anchor in s
s = s.replace(anchor, add + anchor, 1)

p.write_text(s, encoding="utf-8")
print("reassert added")
