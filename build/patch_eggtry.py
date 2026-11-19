import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

s = s.replace('    public int AutoRestoreSecs;   // >0 时自动“点一下恢复”，用于自测',
              '    public int AutoRestoreSecs;   // >0 时自动“点一下恢复”，用于自测\n    public bool EggTry;           // 自测：绑 F9 并播一次彩蛋')

s = s.replace('''        var q = new System.Windows.Forms.Timer { Interval = 800 };''',
'''        var q = new System.Windows.Forms.Timer { Interval = 800 };''')

s = s.replace('''        if (AutoApply)
        {''',
'''        if (EggTry)
        {
            var et = new System.Windows.Forms.Timer { Interval = 600 };
            et.Tick += (a, b) =>
            {
                et.Stop(); et.Dispose();
                C.EggOn = true;
                BindEgg((int)Keys.F9);
                PlayEgg();
                var cl = new System.Windows.Forms.Timer { Interval = 1500 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            et.Start();
        }

        if (AutoApply)
        {''')

s = s.replace('''        int ar = Array.IndexOf(args, "--autorestore");''',
'''        if (Array.IndexOf(args, "--eggtry") >= 0)
        {
            var f4 = new MainForm { EggTry = true };
            Application.Run(f4);
            return;
        }

        int ar = Array.IndexOf(args, "--autorestore");''')

p.write_text(s, encoding="utf-8")
print("eggtry added", s.count("EggTry"))
