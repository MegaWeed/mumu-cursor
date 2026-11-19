import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new, n=1):
    global s
    assert old in s, "MISSING:\n" + old[:160]
    s = s.replace(old, new, n)


# 1) 常量：PM_REMOVE / HWND_TOPMOST
rep('''    public const int SWP_NOSIZE = 1, SWP_NOMOVE = 2, SWP_NOACTIVATE = 0x10, SWP_NOOWNERZORDER = 0x200;''',
'''    public const int SWP_NOSIZE = 1, SWP_NOMOVE = 2, SWP_NOACTIVATE = 0x10, SWP_NOOWNERZORDER = 0x200;
    public const int PM_REMOVE = 1;
    public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);''')

# 2) Overlay 字段
rep('''    int topTick;
    volatile bool topBusy;''',
'''    int topTick;
    volatile bool topBusy;
    long lastTopMs;
    public int TopCalls;''')

# 3) 创建后立刻置顶一次
rep('''        if (hwnd == IntPtr.Zero) throw new Exception("CreateWindowEx failed");
        Nat.ShowWindow(hwnd, 8);''',
'''        if (hwnd == IntPtr.Zero) throw new Exception("CreateWindowEx failed");
        Nat.ShowWindow(hwnd, 8);
        KeepTop();''')

# 4) 渲染循环：抽消息 + 定期重新置顶（都在本线程，不会死锁）
rep('''                Frames++;
                if (Frames % 20 == 0)''',
'''                Frames++;

                // 本线程就是窗口线程：这里调 SetWindowPos 是"自己给自己发消息"，
                // 同步处理、不会像之前那样跨线程互等。顺手把消息队列抽干。
                int nowMs = Environment.TickCount;
                if (nowMs - lastTopMs > 600)
                {
                    lastTopMs = nowMs;
                    var tw2 = System.Diagnostics.Stopwatch.StartNew();
                    KeepTop();
                    TTop += tw2.Elapsed.TotalMilliseconds;
                }
                Pump();

                if (Frames % 20 == 0)''')

# 5) KeepTop / Pump
rep('''    bool Push()''',
'''    /// 把窗口重新顶到 topmost 带最前面。某些程序（Electron 全屏、聊天工具、播放器）
    /// 会把自己也设成 topmost 并排到我们前面，光靠创建时的 WS_EX_TOPMOST 会被压住，
    /// 表现就是"精灵钻到窗口下面去了"。这里每 0.6 秒补一次。
    void KeepTop()
    {
        try
        {
            if (hwnd == IntPtr.Zero) return;
            Nat.SetWindowPos(hwnd, Nat.HWND_TOPMOST, 0, 0, 0, 0,
                Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
            TopCalls++;
        }
        catch { }
    }

    /// 抽干本线程的消息队列（WM_WINDOWPOSCHANGING 之类是 SendMessage 过来的，不抽会卡住对面）
    void Pump()
    {
        try
        {
            Nat.MSG m;
            int n = 0;
            while (Nat.PeekMessageW(out m, IntPtr.Zero, 0, 0, Nat.PM_REMOVE) && n++ < 64)
            {
                Nat.TranslateMessage(ref m);
                Nat.DispatchMessageW(ref m);
            }
        }
        catch { }
    }

    bool Push()''')

p.write_text(s, encoding="utf-8")
print("topmost pump ok")
