import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) PlayEgg 里加一行日志，方便验证“按键真的触发了播放”
old = """            if (eggWav == null) { eggHint.Text = "彩蛋音频丢了，重装一下程序吧。"; return; }
            Sfx.PlayFile(eggWav, false);"""
new = """            if (eggWav == null) { eggHint.Text = "彩蛋音频丢了，重装一下程序吧。"; return; }
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " play\\n"); } catch { }
            Sfx.PlayFile(eggWav, false);"""
assert old in s
s = s.replace(old, new)

# 2) 自测参数
s = s.replace("    public bool StressGlow;       // 自测：变身后反复切“发光线”",
"""    public bool StressGlow;       // 自测：变身后反复切“发光线”
    public string EggTestKey;     // 自测：绑这个键，等 6 秒看有没有放声音""")

s = s.replace("""        if (EggTry)
        {""",
"""        if (!string.IsNullOrEmpty(EggTestKey))
        {
            var kt = new System.Windows.Forms.Timer { Interval = 700 };
            kt.Tick += (a, b) =>
            {
                kt.Stop(); kt.Dispose();
                if (eggSwitch != null) { eggSwitch.On = true; eggSwitch.Invalidate(); }
                C.EggOn = true;
                int vk = EggTestKey.Length == 1
                    ? (int)char.ToUpperInvariant(EggTestKey[0])
                    : (int)(Keys)Enum.Parse(typeof(Keys), EggTestKey, true);
                BindEgg(vk);
                var cl = new System.Windows.Forms.Timer { Interval = 6000 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            kt.Start();
        }

        if (EggTry)
        {""")

s = s.replace("""        if (Array.IndexOf(args, "--stressglow") >= 0)""",
"""        if (Array.IndexOf(args, "--eggkeys") >= 0)
        {
            int ix = Array.IndexOf(args, "--eggkeys");
            string k = ix + 1 < args.Length ? args[ix + 1] : "H";
            var f6 = new MainForm { EggTestKey = k };
            Application.Run(f6);
            return;
        }

        if (Array.IndexOf(args, "--stressglow") >= 0)""")

p.write_text(s, encoding="utf-8")
print("egg test wired", s.count("mumu_egg.log"), s.count("EggTestKey"))
