import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

start = s.index("    public void TestSwitchModes()")
end = s.index("    void SetMode(string m)", start)
new = '''    public void TestSwitchModes()
    {
        void Shot(string name)
        {
            try
            {
                using (var bm = new Bitmap(Width, Height))
                {
                    DrawToBitmap(bm, new Rectangle(0, 0, Width, Height));
                    bm.Save(Path.Combine(Path.GetTempPath(), name), System.Drawing.Imaging.ImageFormat.Png);
                }
            }
            catch (Exception ex) { Console.WriteLine("shot err " + ex.Message); }
        }

        var t = new System.Windows.Forms.Timer { Interval = 300 };
        int n = 0;
        t.Tick += (a, b) =>
        {
            n++;
            try
            {
                if (n == 1)
                {
                    SetMode("pendant");
                    Console.WriteLine("switch -> pendant ok, size=" + Width + "x" + Height);
                }
                else if (n == 2)
                {
                    Shot("fade_before.png");
                    SetMode("static");
                    Shot("fade_after0.png");                       // 刚切完：应该是旧内容的完整画面（不闪新内容）
                    Console.WriteLine("switch -> static ok, size=" + Width + "x" + Height);
                    for (int i = 0; i < 4; i++) { Application.DoEvents(); Thread.Sleep(16); }
                    Shot("fade_mid.png");
                }
                else { t.Stop(); Close(); }
            }
            catch (Exception ex) { Console.WriteLine("switch err " + ex.GetType().Name + ": " + ex.Message); t.Stop(); Close(); }
        };
        t.Start();
    }

'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("test rewritten")
