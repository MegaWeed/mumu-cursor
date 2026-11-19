import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:200]
    s = s.replace(old, new, 1)


rep('''    [DllImport("user32.dll")] public static extern IntPtr GetTopWindow(IntPtr h);''',
'''    [DllImport("user32.dll")] public static extern IntPtr GetTopWindow(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, System.Text.StringBuilder sb, int n);
    [DllImport("user32.dll")] public static extern int GetWindowLongW(IntPtr h, int idx);''')

# KeepTop 记录成功与否
rep('''            Nat.SetWindowPos(hwnd, Nat.HWND_TOPMOST, 0, 0, 0, 0,
                Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
            TopCalls++;''',
'''            bool okTop = Nat.SetWindowPos(hwnd, Nat.HWND_TOPMOST, 0, 0, 0, 0,
                Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
            TopCalls++;
            TopFails += okTop ? 0 : 1;''')

rep('''    public int TopCalls;''', '''    public int TopCalls, TopFails;''')

# 探针：打印 z 序前 14 个窗口的类名 + 是否 topmost
rep('''                    Program.Trace("topprobe pass=" + pass''',
'''                    try
                    {
                        IntPtr q = Nat.GetTopWindow(IntPtr.Zero);
                        for (int k = 0; k < 14 && q != IntPtr.Zero; k++)
                        {
                            var sb = new System.Text.StringBuilder(128);
                            Nat.GetClassNameW(q, sb, 128);
                            int ex = Nat.GetWindowLongW(q, -20);
                            Program.Trace("  z" + k + " h=" + q + " cls=" + sb + " topmost=" + ((ex & 0x8) != 0)
                                + (q == ovh ? " <== overlay" : ""));
                            q = Nat.GetWindow(q, Nat.GW_HWNDNEXT);
                        }
                    }
                    catch { }
                    Program.Trace("topprobe pass=" + pass''')

rep('''+ " topcalls=" + (overlay != null ? overlay.TopCalls : 0)''',
'''+ " topcalls=" + (overlay != null ? overlay.TopCalls : 0) + " topfails=" + (overlay != null ? overlay.TopFails : 0)''')

p.write_text(s, encoding="utf-8")
print("z dump ok")
