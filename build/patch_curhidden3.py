import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:200]
    s = s.replace(old, new, 1)


# ---------- 1. P/Invoke ----------
rep('''    [DllImport("user32.dll")] public static extern bool GetCursorInfo(ref CURSORINFO pci);''',
'''    [DllImport("user32.dll")] public static extern bool GetCursorInfo(ref CURSORINFO pci);
    [DllImport("user32.dll")] public static extern bool GetClipCursor(out RECT rc);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT rc);
    [DllImport("user32.dll")] public static extern IntPtr MonitorFromWindow(IntPtr h, int flags);
    [DllImport("user32.dll")] public static extern bool GetMonitorInfo(IntPtr hMon, ref MONITORINFO mi);
    [DllImport("user32.dll")] public static extern IntPtr GetDesktopWindow();

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    [StructLayout(LayoutKind.Sequential)]
    public struct MONITORINFO
    {
        public int cbSize; public RECT rcMonitor; public RECT rcWork; public int dwFlags;
    }''')

# ---------- 2. 状态字段 ----------
rep('''    public volatile bool SysCursorHidden;   // 系统光标被当前程序藏起来了（游戏/全屏视频常见）''',
'''    public volatile bool SysCursorHidden;   // 系统光标不可见（游戏/全屏程序把指针收走了）
    public string HideReason = "";''')

# ---------- 3. 判定：全屏前台程序 / 指针被锁死 ----------
rep('''    public int hiddenStreak;

    void CheckSysCursor()
    {
        try
        {
            var ci = new Nat.CURSORINFO();
            ci.cbSize = Marshal.SizeOf(typeof(Nat.CURSORINFO));
            bool shown = Nat.GetCursorInfo(ref ci) && (ci.flags & Nat.CURSOR_SHOWING) != 0;
            if (shown) { hiddenStreak = 0; SysCursorHidden = false; return; }
            if (hiddenStreak < 3) hiddenStreak++;
            if (hiddenStreak >= 3) SysCursorHidden = true;
        }
        catch { hiddenStreak = 0; SysCursorHidden = false; }
    }''',
'''    int hiddenStreak;
    bool hsFull, hsTiny;

    /// 判断"现在这颗指针是不是被别的程序接管了"：
    /// ① CURSOR_SHOWING 为 0（有的程序会真的把光标关掉）
    /// ② 前台是一个铺满显示器的无边框窗口（游戏无边框全屏 / 全屏视频）
    /// ③ 指针被 ClipCursor 锁在一个很小的矩形里（游戏锁鼠标）
    void CheckSysCursor()
    {
        try
        {
            var ci = new Nat.CURSORINFO();
            ci.cbSize = Marshal.SizeOf(typeof(Nat.CURSORINFO));
            bool shown = Nat.GetCursorInfo(ref ci) && (ci.flags & Nat.CURSOR_SHOWING) != 0;

            bool full = false, tiny = false;
            IntPtr fg = Nat.GetForegroundWindow();
            if (fg != IntPtr.Zero && fg != hwnd && fg != Nat.GetDesktopWindow())
            {
                Nat.RECT r;
                if (Nat.GetWindowRect(fg, out r))
                {
                    var mi = new Nat.MONITORINFO();
                    mi.cbSize = Marshal.SizeOf(typeof(Nat.MONITORINFO));
                    if (Nat.GetMonitorInfo(Nat.MonitorFromWindow(fg, 2), ref mi))
                    {
                        var m = mi.rcMonitor;
                        bool cover = Math.Abs(r.Left - m.Left) <= 2 && Math.Abs(r.Top - m.Top) <= 2
                                  && Math.Abs(r.Right - m.Right) <= 2 && Math.Abs(r.Bottom - m.Bottom) <= 2;
                        long st = Nat.GetWindowLongW(fg, -16);
                        bool popupNoCaption = (st & 0x80000000L) != 0 && (st & 0x00C00000L) == 0;
                        full = cover && popupNoCaption;
                    }
                }
            }

            Nat.RECT clip;
            if (Nat.GetClipCursor(out clip))
                tiny = (clip.Right - clip.Left) <= 16 && (clip.Bottom - clip.Top) <= 16;

            if (shown && !full && !tiny) { hiddenStreak = 0; SysCursorHidden = false; hsFull = hsTiny = false; return; }

            if (hiddenStreak < 3) hiddenStreak++;
            if (hiddenStreak >= 3)
            {
                SysCursorHidden = true;
                if (!hsFull && !hsTiny)
                {
                    HideReason = !shown ? "cursor-hidden" : full ? "fullscreen" : "clip";
                    Trace("hide sprite: " + HideReason);
                }
                hsFull = full; hsTiny = tiny;
            }
        }
        catch { hiddenStreak = 0; SysCursorHidden = false; }
    }''')

p.write_text(s, encoding="utf-8")
print("fullscreen/clip detect ok")
