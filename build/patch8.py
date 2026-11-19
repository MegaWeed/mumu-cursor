import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = """    public static void SetDirty(bool on)
    {
        try
        {
            using (var k = Registry.CurrentUser.CreateSubKey(@"Software\\MUMUCursor"))
                if (k != null) k.SetValue("Active", on ? 1 : 0, RegistryValueKind.DWord);
        }
        catch { }
    }

    public static bool IsDirty()
    {
        try
        {
            using (var k = Registry.CurrentUser.OpenSubKey(@"Software\\MUMUCursor"))
            {
                if (k == null) return false;
                object v = k.GetValue("Active");
                return v != null && Convert.ToInt32(v) == 1;
            }
        }
        catch { return false; }
    }"""
new = """    static string FlagPath { get { return Path.Combine(Cfg.Dir, "active.flag"); } }

    public static void SetDirty(bool on)
    {
        // 注册表（主）+ 文件（备份，权限受限时仍可用）
        try
        {
            using (var k = Registry.CurrentUser.CreateSubKey(@"Software\\MUMUCursor"))
                if (k != null) k.SetValue("Active", on ? 1 : 0, RegistryValueKind.DWord);
        }
        catch { }
        try
        {
            if (on) File.WriteAllText(FlagPath, "1");
            else if (File.Exists(FlagPath)) File.Delete(FlagPath);
        }
        catch { }
    }

    public static bool IsDirty()
    {
        try
        {
            using (var k = Registry.CurrentUser.OpenSubKey(@"Software\\MUMUCursor"))
            {
                if (k != null)
                {
                    object v = k.GetValue("Active");
                    if (v != null && Convert.ToInt32(v) == 1) return true;
                }
            }
        }
        catch { }
        try { return File.Exists(FlagPath); } catch { return false; }
    }"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("patched: flag also on disk")
