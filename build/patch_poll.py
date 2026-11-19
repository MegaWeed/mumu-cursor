import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 去掉钩子实现，改成 GetAsyncKeyState 轮询（任何键都能用，不吞键，也不受安全软件 hook 拦截影响）
start = s.index("    void StartHook()")
end = s.index("    void UnbindEgg()")
new = '''    void StartHook()
    {
        StopEggWatch();
        eggTimer = new System.Windows.Forms.Timer { Interval = 35 };
        eggTimer.Tick += (a, b) => EggPoll();
        eggTimer.Start();
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " watch start key=" + C.EggKey + "\\n"); } catch { }
    }

    void StopEggWatch()
    {
        try { if (eggTimer != null) { eggTimer.Stop(); eggTimer.Dispose(); eggTimer = null; } } catch { }
        eggDown = false;
    }

    void EggPoll()
    {
        try
        {
            if (!C.EggOn || binding || C.EggKey == 0) { eggDown = false; return; }
            bool down = (Nat.GetAsyncKeyState(C.EggKey) & 0x8000) != 0;
            if (down && !eggDown)
            {
                eggDown = true;
                int now = Environment.TickCount;
                if (now - lastEggTick > 200) { lastEggTick = now; PlayEgg(); }
            }
            else if (!down) eggDown = false;
        }
        catch { }
    }

    void UnbindHook() { StopEggWatch(); }

'''
s = s[:start] + new + s[end:]

# 2) 字段替换
s = s.replace("""    IntPtr kbdHook = IntPtr.Zero;
    Nat.LowLevelProc kbdProc;      // 必须留引用，否则委托被回收 = 钩子失效
    int lastEggTick;               // 防止长按连发一串声音""",
"""    System.Windows.Forms.Timer eggTimer;   // 轮询按键状态用
    bool eggDown;                          // 防止长按连发
    int lastEggTick;""")

# 3) Nat 加 GetAsyncKeyState
s = s.replace("""        [DllImport("user32.dll")]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, IntPtr dwExtraInfo);""",
"""        [DllImport("user32.dll")]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, IntPtr dwExtraInfo);

        [DllImport("user32.dll")]
        public static extern short GetAsyncKeyState(int vKey);""")

# 4) 关窗口时停轮询
s = s.replace("        UnbindEgg();", "        UnbindEgg();\n        StopEggWatch();", 1)

p.write_text(s, encoding="utf-8")
print("polling version", s.count("GetAsyncKeyState"), s.count("eggTimer"))
