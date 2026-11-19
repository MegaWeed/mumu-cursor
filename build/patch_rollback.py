import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 换光标时：先调大小再换光标（回档到能生效的那一版顺序），并记住原始大小
old = """            // 只换 OCR_NORMAL 这一个光标，不碰系统“指针大小”。
            // （改 CursorBaseSize 会把 I 型、缩放箭头等所有系统光标一起放大，等于把系统搞乱。）
            Nat.SetSystemCursor(h, Nat.OCR_NORMAL);"""
new = """            // 顺序：先调系统“指针大小”，再 SetSystemCursor。
            // 反过来的话 SPI_SETCURSORS 会按方案重载，把我们的光标换回箭头（表现为“点了没反应”）。
            SetBaseSize(bmp.Width);
            Thread.Sleep(60);
            Nat.SetSystemCursor(h, Nat.OCR_NORMAL);"""
assert old in s
s = s.replace(old, new, 1)

# 2) SetBaseSize 记住原值，恢复时写回，避免“整台电脑的光标都被放大”
old = """    public static void SetBaseSize(int px)
    {"""
new = """    static int baseBackup = -1;   // 我们改之前的 CursorBaseSize

    public static void SetBaseSize(int px)
    {
        try
        {
            using (var k = Registry.CurrentUser.OpenSubKey(@"Control Panel\\Cursors", false))
            {
                if (k != null && baseBackup < 0)
                {
                    object v = k.GetValue("CursorBaseSize");
                    baseBackup = (v == null) ? 32 : Convert.ToInt32(v);
                }
            }
        }
        catch { }"""
assert old in s
s = s.replace(old, new, 1)

# 3) 恢复时写回原值
old = """    // 旧版本曾把 CursorBaseSize 改成 128，恢复时顺手写回默认值
    public static void ResetBaseSizeIfBroken()
    {"""
new = """    // 把先前被我们改过的全局“指针大小”写回去
    public static void RestoreBaseSize()
    {
        try
        {
            int back = baseBackup >= 0 ? baseBackup : 32;
            using (var k = Registry.CurrentUser.OpenSubKey(@"Control Panel\\Cursors", true))
            {
                if (k == null) return;
                object v = k.GetValue("CursorBaseSize");
                int cur = (v == null) ? 32 : Convert.ToInt32(v);
                if (cur == back) { baseBackup = -1; return; }
                k.SetValue("CursorBaseSize", back, RegistryValueKind.DWord);
            }
            try { Nat.SystemParametersInfoW(Nat.SPI_SETCURSORS, 0, IntPtr.Zero, Nat.SPIF_SENDCHANGE); } catch { }
            baseBackup = -1;
        }
        catch { }
    }

    // 旧版本曾把 CursorBaseSize 改成 128，恢复时顺手写回默认值
    public static void ResetBaseSizeIfBroken()
    {"""
assert old in s
s = s.replace(old, new, 1)

old = """                ResetBaseSizeIfBroken();   // 旧版可能把全局指针大小改成 128，恢复时写回 32"""
new = """                RestoreBaseSize();         // 把被我们改过的全局“指针大小”写回去
                ResetBaseSizeIfBroken();   // 兜底：旧版留下的 128"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("rolled back to working apply order, with base-size restore")
