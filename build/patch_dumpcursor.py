import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = """        if (Array.IndexOf(args, "--apply") >= 0) { CursorSwitch.Apply(); return; }"""
new = """        if (Array.IndexOf(args, "--apply") >= 0) { CursorSwitch.Apply(); return; }
        if (Array.IndexOf(args, "--applystatic") >= 0)
        {
            CursorSwitch.ApplyStatic();
            var f = Array.IndexOf(args, "--dump");
            if (f >= 0 && f + 1 < args.Length) DumpCursor(args[f + 1]);
            return;
        }
        if (Array.IndexOf(args, "--dumpcursor") >= 0)
        {
            var f2 = Array.IndexOf(args, "--dumpcursor");
            if (f2 + 1 < args.Length) DumpCursor(args[f2 + 1]);
            return;
        }"""
assert old in s
s = s.replace(old, new, 1)

# 把当前系统光标（OCR_NORMAL）dump 成 png，用来核对“真的换了”
anchor = """        if (Array.IndexOf(args, "--apply") >= 0) { CursorSwitch.Apply(); return; }"""
dump = """        static void DumpCursor(string file)
        {
            try
            {
                IntPtr h = Nat.LoadCursorW(IntPtr.Zero, new IntPtr(Nat.OCR_NORMAL));
                using (var ic = System.Drawing.Icon.FromHandle(h))
                using (var bmp = ic.ToBitmap())
                {
                    var big = new System.Drawing.Bitmap(bmp.Width * 6, bmp.Height * 6);
                    using (var g = System.Drawing.Graphics.FromImage(big))
                    {
                        g.Clear(System.Drawing.Color.FromArgb(30, 30, 34));
                        g.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.NearestNeighbor;
                        g.PixelOffsetMode = System.Drawing.Drawing2D.PixelOffsetMode.Half;
                        g.DrawImage(bmp, 0, 0, big.Width, big.Height);
                    }
                    big.Save(file, System.Drawing.Imaging.ImageFormat.Png);
                    Console.WriteLine("dump " + file + " " + bmp.Width + "x" + bmp.Height + " log=" + CursorSwitch.LastLog);
                }
            }
            catch (Exception ex) { Console.WriteLine("dump err " + ex.Message); }
        }

"""
assert anchor in s
s = s.replace(anchor, dump + anchor, 1)

p.write_text(s, encoding="utf-8")
print("dump cursor added")
