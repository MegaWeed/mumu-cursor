import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:200]
    s = s.replace(old, new, 1)


# 1) 保住 WndProc 委托（原来临时建、只被函数指针引用，GC 后可能崩），并监听“别人排到我们上面”
rep('''        wc.lpfnWndProc = Marshal.GetFunctionPointerForDelegate((Nat.WndProcDel)((h, m, w, l) => Nat.DefWindowProcW(h, m, w, l)));''',
'''        wc.lpfnWndProc = Marshal.GetFunctionPointerForDelegate(WndProcKeepAlive);''')

rep('''    public Overlay(Look l)''',
'''    // 委托必须有个字段/静态引用拿着，否则被 GC 回收后窗口过程就飞了
    static readonly Nat.WndProcDel WndProcKeepAlive = WndProc;
    static volatile bool topDirty;

    static IntPtr WndProc(IntPtr h, int msg, IntPtr w, IntPtr l)
    {
        // 0x0047 WM_WINDOWPOSCHANGED / 0x001C WM_ACTIVATEAPP / 0x0006 WM_ACTIVATE
        // 我们自己的 z 序被动过、或者别的程序被切到前台，都赶紧把顶层补回来
        if (msg == 0x0047 || msg == 0x001C || msg == 0x0006) topDirty = true;
        return Nat.DefWindowProcW(h, msg, w, l);
    }

    public Overlay(Look l)''')

# 2) 循环里：脏了就立刻置顶；周期从 600ms 缩到 300ms；每 2 秒复核 topmost 样式
rep('''                int nowMs = Environment.TickCount;
                if (nowMs - lastTopMs > 600)
                {
                    lastTopMs = nowMs;
                    var tw2 = System.Diagnostics.Stopwatch.StartNew();
                    KeepTop();
                    TTop += tw2.Elapsed.TotalMilliseconds;
                }
                Pump();''',
'''                int nowMs = Environment.TickCount;
                if (topDirty)
                {
                    topDirty = false;
                    var tw0 = System.Diagnostics.Stopwatch.StartNew();
                    KeepTop();
                    TTop += tw0.Elapsed.TotalMilliseconds;
                }
                if (nowMs - lastTopMs > 300)
                {
                    lastTopMs = nowMs;
                    var tw2 = System.Diagnostics.Stopwatch.StartNew();
                    KeepTop();
                    if ((Nat.GetWindowLongW(hwnd, -20) & 0x8) == 0)
                    {
                        // 顶层样式被抹掉了（个别程序会这么干），重新加回去
                        int ex = Nat.GetWindowLongW(hwnd, -20) | 0x8;
                        Nat.SetWindowLongW(hwnd, -20, ex);
                        Nat.SetWindowPos(hwnd, Nat.HWND_TOPMOST, 0, 0, 0, 0,
                            Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
                    }
                    TTop += tw2.Elapsed.TotalMilliseconds;
                }
                Pump();''')

rep('''    [DllImport("user32.dll")] public static extern int GetWindowLongW(IntPtr h, int idx);''',
'''    [DllImport("user32.dll")] public static extern int GetWindowLongW(IntPtr h, int idx);
    [DllImport("user32.dll")] public static extern int SetWindowLongW(IntPtr h, int idx, int val);''')

p.write_text(s, encoding="utf-8")
print("topmost hardening ok")
