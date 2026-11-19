import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- 1) 去掉跨线程 SetWindowPos（会与应用线程死锁），窗口创建时就是 TOPMOST ----------
start = s.index('                if (++topTick >= 25)')
end = s.index('                if (ok) { fails = 0;')
s = s[:start] + s[end:]

# ---------- 2) 每帧单独 try/catch：一帧画错不能把整个渲染线程带走 ----------
old_head = '''                Nat.POINT pt; Nat.GetCursorPos(out pt);
                if (!P.started) { P.started = true; P.Reset(pt.x, pt.y); }'''
new_head = '''                try
                {
                Nat.POINT pt; Nat.GetCursorPos(out pt);
                if (!P.started) { P.started = true; P.Reset(pt.x, pt.y); }'''
assert old_head in s
s = s.replace(old_head, new_head)

old_tail = '''                if (ok) { fails = 0; if (!stopped) HideReady = true; }
                else if (++fails > 90) running = false;'''
new_tail = '''                if (ok) { fails = 0; if (!stopped) HideReady = true; }
                else if (++fails > 90) running = false;
                }
                catch (Exception ex)
                {
                    // 单帧异常（比如素材被别的线程动了）不该整条线程挂掉
                    try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_overlay_err.txt"), "frame " + Frames + ": " + ex.Message + "\\n"); } catch { }
                    Thread.Sleep(15);
                }'''
assert old_tail in s
s = s.replace(old_tail, new_tail)

s = s.replace('                Thread.Sleep(6);\n            }', '                Thread.Sleep(6);\n            }')

p.write_text(s, encoding="utf-8")
print("render loop hardened", s.count('mumu_overlay_err'), s.count('topBusy'))
