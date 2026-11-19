import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) dirty flag helpers inside CursorSwitch (before Restore())
old = """    public static void Restore()
    {"""
new = """    // 记录"当前处于变身状态"，进程被强杀后下次启动能自动救回来
    public static void SetDirty(bool on)
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
    }

    public static void Restore()
    {"""
assert old in s
s = s.replace(old, new, 1)

# 2) set flag when blanked
old = """        Blank();
        Applied = true;
        LastLog = "apply: snapshot " + (snapshot != IntPtr.Zero ? "ok" : "none");"""
new = """        Blank();
        Applied = true;
        SetDirty(true);
        LastLog = "apply: snapshot " + (snapshot != IntPtr.Zero ? "ok" : "none");"""
assert old in s
s = s.replace(old, new, 1)

# 3) clear flag after restore (finally block, after SPI)
old = """                try { Nat.SystemParametersInfoW(Nat.SPI_SETCURSORS, 0, IntPtr.Zero, Nat.SPIF_SENDCHANGE); } catch { }
                Applied = false;"""
new = """                try { Nat.SystemParametersInfoW(Nat.SPI_SETCURSORS, 0, IntPtr.Zero, Nat.SPIF_SENDCHANGE); } catch { }
                Applied = false;
                SetDirty(false);"""
assert old in s
s = s.replace(old, new, 1)

# 4) single instance + auto recovery at startup
old = """static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        try { Nat.SetProcessDPIAware(); } catch { }"""
new = """static class Program
{
    static Mutex instanceMutex;

    [STAThread]
    static void Main(string[] args)
    {
        bool created;
        instanceMutex = new Mutex(true, "MUMU_Cursor_SingleInstance", out created);
        if (!created) return;               // 已经在运行了，别再开第二个

        // 上次被强杀（标志还留着）→ 先把光标救回来
        try { if (CursorSwitch.IsDirty()) CursorSwitch.Restore(); } catch { }

        try { Nat.SetProcessDPIAware(); } catch { }"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("patched: single instance + dirty-flag auto recovery")
