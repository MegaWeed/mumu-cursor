import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:200]
    s = s.replace(old, new, 1)


# 1) 前台窗口类名 → 判断是不是系统任务切换界面（Alt+Tab / 任务视图 / 开始菜单）
rep('''    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);''',
'''    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();''')

# 2) Overlay: 每 120ms 采样一次
rep('''    void Pump()''',
'''    /// Alt+Tab / 任务视图 / 开始菜单这类系统界面在"比 topmost 更高的层"，
    /// 普通程序压不上去（它们由 UIAccess 系统进程绘制）。检测到它们出现就把
    /// 精灵让开、改用系统箭头 —— 至少那颗是真光标，会画在系统界面之上。
    void CheckSwitcher()
    {
        try
        {
            IntPtr fg = Nat.GetForegroundWindow();
            if (fg == IntPtr.Zero) { SwitcherUp = false; return; }
            var sb = new System.Text.StringBuilder(128);
            Nat.GetClassNameW(fg, sb, 128);
            string c = sb.ToString();
            SwitcherUp = c == "XamlExplorerHostIslandWindow" || c == "MultitaskingViewFrame" || c == "TaskSwitcherWnd";
        }
        catch { SwitcherUp = false; }
    }

    void Pump()''')

rep('''    public int TopCalls, TopFails;''',
'''    public int TopCalls, TopFails;
    public volatile bool SwitcherUp;''')

rep('''                Pump();

                if (Frames % 20 == 0)''',
'''                Pump();
                if (Frames % 8 == 0) CheckSwitcher();

                if (Frames % 20 == 0)''')

# 3) MainForm：一个 150ms 的定时器负责"让开/回来"
rep('''            StartWatchdog();
            RefreshStatus();''',
'''            StartWatchdog();
            StartHandoff();
            RefreshStatus();''')

rep('''    // 看门狗：渲染线程一旦卡住''',
'''    // 系统切换界面出现时：把系统箭头还回去、精灵暂时让开
    System.Windows.Forms.Timer handoff;
    bool handedOff;

    void StartHandoff()
    {
        if (handoff != null) { handoff.Stop(); handoff.Dispose(); }
        handedOff = false;
        handoff = new System.Windows.Forms.Timer { Interval = 150 };
        handoff.Tick += (a, b) =>
        {
            if (overlay == null) { handoff.Stop(); return; }
            bool up;
            try { up = overlay.SwitcherUp; } catch { return; }
            if (up == handedOff) return;
            handedOff = up;
            try
            {
                if (up)
                {
                    CursorSwitch.Restore();                 // 先用真光标顶上（画在系统界面之上）
                    if (overlay.hwnd != IntPtr.Zero) Nat.ShowWindow(overlay.hwnd, 0);
                }
                else
                {
                    if (overlay.hwnd != IntPtr.Zero) Nat.ShowWindow(overlay.hwnd, 8);
                    CursorSwitch.Apply();
                }
            }
            catch { }
        };
        handoff.Start();
    }

    // 看门狗：渲染线程一旦卡住''')

p.write_text(s, encoding="utf-8")
print("switcher handoff ok")
