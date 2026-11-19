import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 测试入口：连切两次模式，验证重建 + 淡入淡出不炸
old = "    void SetMode(string m)"
new = ('''    public void TestSwitchModes()
    {
        var t = new System.Windows.Forms.Timer { Interval = 320 };
        int n = 0;
        t.Tick += (a, b) =>
        {
            n++;
            try
            {
                if (n == 1) { SetMode("static"); Console.WriteLine("switch -> static ok, size=" + Width + "x" + Height); }
                else if (n == 2) { SetMode("pendant"); Console.WriteLine("switch -> pendant ok, size=" + Width + "x" + Height); }
                else { t.Stop(); Close(); }
            }
            catch (Exception ex) { Console.WriteLine("switch err " + ex.GetType().Name + ": " + ex.Message); t.Stop(); Close(); }
        };
        t.Start();
    }

    void SetMode(string m)''')
assert old in s
s = s.replace(old, new, 1)

# 2) Main 里挂 --fadetest
old2 = '        int shot = Array.IndexOf(args, "--shot");'
new2 = ('''        if (Array.IndexOf(args, "--fadetest") >= 0)
        {
            var f0 = new MainForm();
            f0.Show();
            f0.TestSwitchModes();
            var sw = System.Diagnostics.Stopwatch.StartNew();
            while (sw.ElapsedMilliseconds < 1600) { Application.DoEvents(); Thread.Sleep(10); }
            Console.WriteLine("fadetest done");
            return;
        }

        int shot = Array.IndexOf(args, "--shot");''')
assert old2 in s
s = s.replace(old2, new2, 1)

p.write_text(s, encoding="utf-8")
print("fadetest added")
