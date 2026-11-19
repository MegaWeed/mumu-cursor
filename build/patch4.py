import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = "    public double TUpd, TDraw, TPush;"
new = "    public double TUpd, TDraw, TPush, TTop;"
assert old in s
s = s.replace(old, new, 1)

old2 = """                if (++topTick >= 25)
                {
                    topTick = 0;
                    Nat.SetWindowPos(hwnd, new IntPtr(-1), 0, 0, 0, 0,
                        Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
                }"""
new2 = """                if (++topTick >= 25)
                {
                    topTick = 0;
                    var tt = System.Diagnostics.Stopwatch.StartNew();
                    Nat.SetWindowPos(hwnd, new IntPtr(-1), 0, 0, 0, 0,
                        Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
                    TTop += tt.Elapsed.TotalMilliseconds;
                }"""
assert old2 in s
s = s.replace(old2, new2, 1)

old3 = """                Frames++;
                Thread.Sleep(6);"""
new3 = """                Frames++;
                if (Frames % 20 == 0)
                {
                    try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hb.txt"), "f=" + Frames + " t=" + now.ToString("F2") + "s\\n"); } catch { }
                }
                Thread.Sleep(6);"""
assert old3 in s
s = s.replace(old3, new3, 1)

old4 = 'if (ov.Frames > 0) Console.WriteLine("per-frame ms: upd " + (ov.TUpd / ov.Frames).ToString("F2") + " draw " + (ov.TDraw / ov.Frames).ToString("F2") + " push " + (ov.TPush / ov.Frames).ToString("F2"));'
new4 = 'if (ov.Frames > 0) Console.WriteLine("per-frame ms: upd " + (ov.TUpd / ov.Frames).ToString("F2") + " draw " + (ov.TDraw / ov.Frames).ToString("F2") + " push " + (ov.TPush / ov.Frames).ToString("F2") + " topmost " + (ov.TTop / ov.Frames).ToString("F2"));'
assert old4 in s
s = s.replace(old4, new4, 1)

# loop exit trace
old5 = """        finally
        {
            if (hwnd != IntPtr.Zero) { Nat.DestroyWindow(hwnd); hwnd = IntPtr.Zero; }"""
new5 = """        finally
        {
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hb.txt"), "loop exit frames=" + Frames + "\\n"); } catch { }
            if (hwnd != IntPtr.Zero) { Nat.DestroyWindow(hwnd); hwnd = IntPtr.Zero; }"""
assert old5 in s
s = s.replace(old5, new5, 1)

p.write_text(s, encoding="utf-8")
print("patched topmost timing + heartbeat")
