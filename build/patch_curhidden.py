import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:200]
    s = s.replace(old, new, 1)


rep('''    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();''',
'''    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetCursorInfo(ref CURSORINFO pci);
    [DllImport("user32.dll")] public static extern int ShowCursor(bool show);

    [StructLayout(LayoutKind.Sequential)]
    public struct CURSORINFO { public int cbSize; public int flags; public IntPtr hCursor; public POINT ptScreenPos; }
    public const int CURSOR_SHOWING = 0x1;''')

rep('''    public volatile bool SwitcherUp;''',
'''    public volatile bool SwitcherUp;
    public volatile bool SysCursorHidden;   // 系统光标被当前程序藏起来了（游戏/全屏视频常见）''')

# 每帧采样"系统光标是否可见"
rep('''                Pump();
                if (Frames % 8 == 0) CheckSwitcher();''',
'''                Pump();
                if (Frames % 8 == 0) CheckSwitcher();
                if (Frames % 4 == 0) CheckSysCursor();''')

rep('''    void Pump()''',
'''    /// 游戏（Apex 等）会把系统光标"藏掉"，此时指针位置还停在屏幕中央。
    /// 我们画的是自己的一张图，不知道这件事，就会傻乎乎地在中间显示一个精灵。
    /// GetCursorInfo 的 CURSOR_SHOWING 位正是"当前有没有光标在显示"，用它就能对齐。
    void CheckSysCursor()
    {
        try
        {
            var ci = new Nat.CURSORINFO();
            ci.cbSize = Marshal.SizeOf(typeof(Nat.CURSORINFO));
            bool shown = Nat.GetCursorInfo(ref ci) && (ci.flags & Nat.CURSOR_SHOWING) != 0;
            SysCursorHidden = !shown;
        }
        catch { SysCursorHidden = false; }
    }

    void Pump()''')

# 系统光标不可见时：不画、不推、把窗口藏起来；恢复可见时再露出来
rep('''                try
                {
                Nat.POINT pt; Nat.GetCursorPos(out pt);''',
'''                try
                {
                if (SysCursorHidden)
                {
                    if (hwnd != IntPtr.Zero && Nat.IsWindowVisible(hwnd)) Nat.ShowWindow(hwnd, 0);
                    Thread.Sleep(12);
                    Frames++;
                    continue;
                }
                else if (hwnd != IntPtr.Zero && !Nat.IsWindowVisible(hwnd))
                {
                    Nat.ShowWindow(hwnd, 8);
                    KeepTop();
                }

                Nat.POINT pt; Nat.GetCursorPos(out pt);''')

p.write_text(s, encoding="utf-8")
print("cursor-hidden detect ok")
