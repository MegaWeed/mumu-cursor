import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:200]
    s = s.replace(old, new, 1)


rep('''    [DllImport("user32.dll")] public static extern IntPtr GetWindow(IntPtr h, int cmd);
    public const int GW_HWNDPREV = 3;''',
'''    [DllImport("user32.dll")] public static extern IntPtr GetWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern IntPtr GetTopWindow(IntPtr h);
    public const int GW_HWNDPREV = 3, GW_HWNDNEXT = 2;''')

# 正确的判据：从最顶层往下走，先遇到 ov 就算过
rep('''                    IntPtr above = Nat.GetWindow(rival.Handle, Nat.GW_HWNDPREV);
                    bool pass = overlay != null && above == overlay.hwnd;
                    Program.Trace("topprobe pass=" + pass + " above=" + above + " ov=" + (overlay != null ? overlay.hwnd : IntPtr.Zero)''',
'''                    IntPtr ovh = overlay != null ? overlay.hwnd : IntPtr.Zero;
                    IntPtr w = Nat.GetTopWindow(IntPtr.Zero);
                    int idx = 0, ovIdx = -1, rvIdx = -1;
                    while (w != IntPtr.Zero && idx < 64)
                    {
                        if (w == ovh) ovIdx = idx;
                        if (w == rival.Handle) rvIdx = idx;
                        w = Nat.GetWindow(w, Nat.GW_HWNDNEXT);
                        idx++;
                    }
                    bool pass = ovIdx >= 0 && (rvIdx < 0 || ovIdx < rvIdx);
                    Program.Trace("topprobe pass=" + pass + " ovIdx=" + ovIdx + " rivalIdx=" + rvIdx + " scanned=" + idx
                        + " ov=" + ovh''')

p.write_text(s, encoding="utf-8")
print("zorder probe fixed")
