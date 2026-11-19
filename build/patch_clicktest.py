import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = '''        if (Array.IndexOf(args, "--fstest") >= 0)'''
new = '''        if (Array.IndexOf(args, "--clicktest") >= 0)
        {
            var cc = Cfg.Load();
            var pp2 = new Pendant(Art.Build(cc));
            pp2.Reset(180, 70); pp2.tx = 180; pp2.ty = 70;
            pp2.Click();
            for (int f = 0; f < 30; f++)
            {
                pp2.Update(1.0 / 60);
                if (f == 1 || f == 5 || f == 12 || f == 22)
                {
                    using (var bmp = new Bitmap(360, 420))
                    using (var g = Graphics.FromImage(bmp))
                    {
                        g.Clear(Color.FromArgb(26, 24, 32));
                        pp2.Draw(g, 180, 56);
                        bmp.Save(Path.Combine(Cfg.Dir, "click_" + f + ".png"));
                    }
                }
            }
            Console.WriteLine("clicktest done -> " + Cfg.Dir);
            return;
        }
        if (Array.IndexOf(args, "--fstest") >= 0)'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("clicktest added")
