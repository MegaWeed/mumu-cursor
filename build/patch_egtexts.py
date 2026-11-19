import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 初始说明文字
old = '''            Text = "先点「绑定按键」，然后直接按下想用的键（建议 F6~F12）。\\n绑好后按一下试听，满意再开「启用」。",'''
new = '''            Text = "绑一个「可以用 Apex 检视的键位」：点「绑定按键」，按一下那个键就行。\\n键盘上任意键都能绑，不吞键、也不会影响检视。",'''
assert old in s, "hint not found"
s = s.replace(old, new)

# 2) 绑定过程中的文字
s = s.replace('eggHint.Text = "现在按一下想绑的键（键盘上任意一个都行，比如 F、H、鼠标侧键之外的都支持）。";',
              'eggHint.Text = "现在按一下想绑的键——就是你在 Apex 里检视用的那个键，任意键都行。";')

# 3) 轮询逻辑抽成 EggTick(bool)，方便自测
s = s.replace('''    void EggPoll()
    {
        try
        {
            if (!C.EggOn || binding || C.EggKey == 0) { eggDown = false; return; }
            bool down = (Nat.GetAsyncKeyState(C.EggKey) & 0x8000) != 0;
            if (down && !eggDown)''',
'''    void EggPoll()
    {
        bool down = false;
        try { if (C.EggOn && !binding && C.EggKey != 0) down = (Nat.GetAsyncKeyState(C.EggKey) & 0x8000) != 0; } catch { }
        EggTick(down);
    }

    void EggTick(bool down)
    {
        try
        {
            if (down && !eggDown)''')

# 4) 自测参数：--eggpolltest 直接喂按下/按住，验证触发与防连发
s = s.replace('''        if (Array.IndexOf(args, "--eggkeys") >= 0)''',
'''        if (Array.IndexOf(args, "--eggpolltest") >= 0)
        {
            var f7 = new MainForm();
            f7.Shown += (a, b) =>
            {
                C.EggOn = true; C.EggKey = 0x48;   // H
                f7.TestPoll();
            };
            Application.Run(f7);
            return;
        }

        if (Array.IndexOf(args, "--eggkeys") >= 0)''')

s = s.replace('''    void StartHook()''',
'''    public void TestPoll()
    {
        // 模拟：按下 → 按住(不应重复) → 松开 → 再按
        EggTick(true); EggTick(true); EggTick(true);
        EggTick(false);
        EggTick(true);
        EggTick(false);
        var t = new System.Windows.Forms.Timer { Interval = 1200 };
        t.Tick += (a, b) => { t.Stop(); t.Dispose(); Close(); };
        t.Start();
    }

    void StartHook()''')

p.write_text(s, encoding="utf-8")
print("texts + seam ok")
