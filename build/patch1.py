import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor_fixed.cs")
s = p.read_text(encoding="utf-8")

old = "        catch { }\n        finally\n        {\n            if (hwnd != IntPtr.Zero) { Nat.DestroyWindow(hwnd); hwnd = IntPtr.Zero; }"
new = ("        catch (Exception ex)\n"
       "        {\n"
       "            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), \"mumu_overlay_err.txt\"), ex.ToString() + \"\\n\"); } catch { }\n"
       "        }\n"
       "        finally\n"
       "        {\n"
       "            if (hwnd != IntPtr.Zero) { Nat.DestroyWindow(hwnd); hwnd = IntPtr.Zero; }")
assert old in s, "catch block not found"
s = s.replace(old, new, 1)

old2 = "                Thread.Sleep(6);\n            }"
new2 = "                Frames++;\n                Thread.Sleep(6);\n            }"
assert old2 in s, "loop tail not found"
s = s.replace(old2, new2, 1)

old3 = "    volatile bool stopped;"
new3 = "    volatile bool stopped;\n    public int Frames;"
assert old3 in s, "stopped field not found"
s = s.replace(old3, new3, 1)

old4 = 'Console.WriteLine("cpu avg " + cpuPct.ToString("F2") + "% of total, mem " + (me.WorkingSet64 / 1048576) + "MB");'
new4 = 'Console.WriteLine("cpu avg " + cpuPct.ToString("F2") + "% of total, mem " + (me.WorkingSet64 / 1048576) + "MB, frames " + ov.Frames);'
assert old4 in s, "cpu line not found"
s = s.replace(old4, new4, 1)

p.write_text(s, encoding="utf-8")
print("patched ok")
