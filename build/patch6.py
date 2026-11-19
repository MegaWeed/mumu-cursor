import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = "    int topTick;"
new = "    int topTick;\n    volatile bool topBusy;"
assert old in s
s = s.replace(old, new, 1)

old = """                if (false && ++topTick >= 25)
                {
                    topTick = 0;
                    var tt = System.Diagnostics.Stopwatch.StartNew();
                    Nat.SetWindowPos(hwnd, new IntPtr(-1), 0, 0, 0, 0,
                        Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
                    TTop += tt.Elapsed.TotalMilliseconds;
                }"""
new = """                if (++topTick >= 25)
                {
                    topTick = 0;
                    // SetWindowPos 在某些会话里会阻塞（实测本机直接卡死渲染线程），
                    // 所以放到后台线程里做，并用 topBusy 保证最多只有一个在飞：
                    // 一旦它卡住，topBusy 永远为真 -> 自动放弃重新置顶，渲染不受影响。
                    if (!topBusy)
                    {
                        topBusy = true;
                        IntPtr h = hwnd;
                        ThreadPool.QueueUserWorkItem(_ =>
                        {
                            try
                            {
                                Nat.SetWindowPos(h, new IntPtr(-1), 0, 0, 0, 0,
                                    Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
                                topBusy = false;
                            }
                            catch { topBusy = false; }
                        });
                    }
                }"""
assert old in s
s = s.replace(old, new, 1)

old = "                if (ok) { fails = 0; HideReady = true; }"
new = "                if (ok) { fails = 0; if (!stopped) HideReady = true; }"
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("patched: topmost on worker thread with busy guard")
