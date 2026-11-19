import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

s = s.replace('''    public bool EggTry;           // 自测：绑 F9 并播一次彩蛋''',
'''    public bool EggTry;           // 自测：绑 F9 并播一次彩蛋
    public bool EggBindTest;      // 自测：开关关着的情况下绑键，验证会自动开启''')

s = s.replace('''        if (EggTry)
        {''',
'''        if (EggBindTest)
        {
            var bt = new System.Windows.Forms.Timer { Interval = 500 };
            bt.Tick += (a, b) =>
            {
                bt.Stop(); bt.Dispose();
                if (eggSwitch != null) { eggSwitch.On = false; eggSwitch.Invalidate(); }   // 故意关着再来绑
                C.EggOn = false;
                BindEgg((int)Keys.F);
                try
                {
                    File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"),
                        DateTime.Now.ToString("HH:mm:ss.fff") + " bindtest EggOn=" + C.EggOn +
                        " switch=" + (eggSwitch != null && eggSwitch.On) + " key=" + C.EggKey +
                        " hint=[" + (eggHint != null ? eggHint.Text : "") + "]\\n");
                }
                catch { }
                var cl = new System.Windows.Forms.Timer { Interval = 800 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            bt.Start();
        }

        if (EggTry)
        {''')

s = s.replace('''        if (Array.IndexOf(args, "--eggtry") >= 0)''',
'''        if (Array.IndexOf(args, "--eggbindtest") >= 0)
        {
            var f5 = new MainForm { EggBindTest = true };
            Application.Run(f5);
            return;
        }
        if (Array.IndexOf(args, "--eggtry") >= 0)''')

p.write_text(s, encoding="utf-8")
print("bindtest added", s.count("EggBindTest"))
