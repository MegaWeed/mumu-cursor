import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:160]
    s = s.replace(old, new, 1)


# 连续 3 次采样都"看不见光标"才判定为隐藏（每 4 帧采一次 ≈ 60ms 内 3 次），避免瞬时抖动导致闪烁
rep('''    void CheckSysCursor()
    {
        try
        {
            var ci = new Nat.CURSORINFO();
            ci.cbSize = Marshal.SizeOf(typeof(Nat.CURSORINFO));
            bool shown = Nat.GetCursorInfo(ref ci) && (ci.flags & Nat.CURSOR_SHOWING) != 0;
            SysCursorHidden = !shown;
        }
        catch { SysCursorHidden = false; }
    }''',
'''    int hiddenStreak;

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
    }''')

p.write_text(s, encoding="utf-8")
print("debounce ok")
