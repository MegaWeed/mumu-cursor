import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) add timing fields
old = "    volatile bool stopped;\n    public int Frames;"
new = "    volatile bool stopped;\n    public int Frames;\n    public double TUpd, TDraw, TPush;"
assert old in s
s = s.replace(old, new, 1)

# 2) wrap phases with stopwatch
old2 = """                P.Update(dt);
                using (var g = Graphics.FromImage(canvas))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    g.Clear(Color.Transparent);
                    P.Draw(g, PadX, PadY);
                }
                bool ok = Push();"""
new2 = """                var tw = System.Diagnostics.Stopwatch.StartNew();
                P.Update(dt);
                TUpd += tw.Elapsed.TotalMilliseconds; tw.Restart();
                using (var g = Graphics.FromImage(canvas))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    g.Clear(Color.Transparent);
                    P.Draw(g, PadX, PadY);
                }
                TDraw += tw.Elapsed.TotalMilliseconds; tw.Restart();
                bool ok = Push();
                TPush += tw.Elapsed.TotalMilliseconds;"""
assert old2 in s
s = s.replace(old2, new2, 1)

# 3) print averages
old3 = 'Console.WriteLine("cpu avg " + cpuPct.ToString("F2") + "% of total, mem " + (me.WorkingSet64 / 1048576) + "MB, frames " + ov.Frames);'
new3 = ('Console.WriteLine("cpu avg " + cpuPct.ToString("F2") + "% of total, mem " + (me.WorkingSet64 / 1048576) + "MB, frames " + ov.Frames);\n'
        '            if (ov.Frames > 0) Console.WriteLine("per-frame ms: upd " + (ov.TUpd / ov.Frames).ToString("F2") + " draw " + (ov.TDraw / ov.Frames).ToString("F2") + " push " + (ov.TPush / ov.Frames).ToString("F2"));')
assert old3 in s
s = s.replace(old3, new3, 1)

p.write_text(s, encoding="utf-8")
print("patched timings")
