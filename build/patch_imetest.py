import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert old in s, "MISSING: " + old[:70]
    s = s.replace(old, new, count)


rep('''    public bool EggBindTest;''', '''    public bool EggBindTest;
    public bool EggImeTest;       // 自测：喂一个 VK_PROCESSKEY(229)，确认不会被绑上''')

rep('''        if (EggBindTest)
        {''',
'''        if (EggImeTest)
        {
            var it = new System.Windows.Forms.Timer { Interval = 400 };
            it.Tick += (a, b) =>
            {
                it.Stop(); it.Dispose();
                C.EggKey = 0;
                BindEgg(229);
                string h1 = eggHint != null ? eggHint.Text : "";
                int k1 = C.EggKey;
                BindEgg(70);
                string h2 = eggHint != null ? eggHint.Text : "";
                try
                {
                    File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"),
                        DateTime.Now.ToString("HH:mm:ss.fff") + " ime k1=" + k1 + " h1=[" + h1 + "] k2=" + C.EggKey + " h2=[" + h2 + "]\\n");
                }
                catch { }
                var cl = new System.Windows.Forms.Timer { Interval = 600 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            it.Start();
        }

        if (EggBindTest)
        {''')

rep('''        if (Array.IndexOf(args, "--eggbindtest") >= 0)''',
'''        if (Array.IndexOf(args, "--eggime") >= 0)
        {
            var f7 = new MainForm { EggImeTest = true };
            Application.Run(f7);
            return;
        }
        if (Array.IndexOf(args, "--eggbindtest") >= 0)''')

p.write_text(s, encoding="utf-8")
print("ime test added")
