import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- 1) 预览与覆盖层各用一份 Look，别让两个线程画同一批 Bitmap ----------
old = '''        var lk = Art.Build(C);
        if (preview != null) preview.Rebuild(lk);
        if (overlay != null) overlay.SetLook(lk);   // 已经变身的话，桌面上那只也跟着变'''
new = '''        if (preview != null) preview.Rebuild(Art.Build(C));
        // 桌面上那只必须用另一份 Look：两个线程同时 DrawImage 同一张 Bitmap，
        // GDI+ 会抛 “对象当前正在其他地方使用”（切换发光线时最容易踩到）
        if (overlay != null) overlay.SetLook(Art.Build(C));'''
assert old in s
s = s.replace(old, new)

# ---------- 2) 全局兜底：任何未处理异常都先还光标再提示 ----------
s = s.replace('static class Program\n{',
'''static class Guard
{
    public static Action Emergency;     // 由 MainForm 注册：停掉覆盖层 + 还原系统光标
    static int busy;

    public static void Trip(string where, Exception ex)
    {
        try { if (Emergency != null) Emergency(); } catch { }
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_crash.txt"), DateTime.Now.ToString("HH:mm:ss") + " [" + where + "] " + ex + "\\n"); } catch { }
        if (busy > 0) return;
        busy = 1;
        try
        {
            MessageBox.Show("程序遇到一个错误，已经先把你原来的系统光标换回来了。\\n\\n"
                + (ex == null ? "未知错误" : ex.Message)
                + "\\n\\n再点一次「变身为 MUMU 光标」就能接着用。", "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        catch { }
        finally { busy = 0; }
    }
}

static class Program
{''')

s = s.replace('''        try { Nat.SetProcessDPIAware(); } catch { }
        Application.EnableVisualStyles();''',
'''        try { Nat.SetProcessDPIAware(); } catch { }
        Application.EnableVisualStyles();
        // 任何没接住的异常：先还原系统光标，再给一句人话，而不是弹 .NET 的原始对话框
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
        Application.ThreadException += (a, b) => Guard.Trip("ui", b.Exception);
        AppDomain.CurrentDomain.UnhandledException += (a, b) => Guard.Trip("domain", b.ExceptionObject as Exception);''')

# ---------- 3) MainForm 注册 Emergency ----------
s = s.replace('''        BuildHeader();
        BuildLeft();
        BuildRight();''',
'''        Guard.Emergency = () =>
        {
            try { if (overlay != null) { overlay.Stop(); overlay = null; } } catch { }
            try { CursorSwitch.Restore(); } catch { }
            try { if (watchdog != null) watchdog.Stop(); } catch { }
            try { if (status != null) { status.Text = "已暂停"; applyBtn.Enabled = true; applyBtn.Text = "重新变身为 MUMU 光标"; } } catch { }
        };

        BuildHeader();
        BuildLeft();
        BuildRight();''')

# ---------- 4) 压测开关：变身后反复切发光线 ----------
s = s.replace('    public bool EggTry;           // 自测：绑 F9 并播一次彩蛋',
              '    public bool EggTry;           // 自测：绑 F9 并播一次彩蛋\n    public bool StressGlow;       // 自测：变身后反复切“发光线”')

s = s.replace('''        if (AutoApply)
        {''',
'''        if (StressGlow)
        {
            var st = new System.Windows.Forms.Timer { Interval = 1200 };
            st.Tick += (a, b) =>
            {
                st.Stop(); st.Dispose();
                Apply();
                int n = 0;
                var tt = new System.Windows.Forms.Timer { Interval = 350 };
                tt.Tick += (c, d) =>
                {
                    C.RopeGlow = !C.RopeGlow;
                    if (glowSwitch != null) { glowSwitch.On = C.RopeGlow; glowSwitch.Invalidate(); }
                    RefreshThumbs();
                    if (++n >= 14) { tt.Stop(); tt.Dispose(); Restore(); var q = new System.Windows.Forms.Timer { Interval = 800 }; q.Tick += (e2, f2) => { q.Stop(); q.Dispose(); Close(); }; q.Start(); }
                };
                tt.Start();
            };
            st.Start();
        }

        if (AutoApply)
        {''')

s = s.replace('''        if (Array.IndexOf(args, "--eggtry") >= 0)''',
'''        if (Array.IndexOf(args, "--stressglow") >= 0)
        {
            var f5 = new MainForm { StressGlow = true };
            Application.Run(f5);
            return;
        }

        if (Array.IndexOf(args, "--eggtry") >= 0)''')

p.write_text(s, encoding="utf-8")
print("fix applied", s.count("Guard."), s.count("StressGlow"))
