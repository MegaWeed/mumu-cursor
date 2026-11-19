import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert old in s, old[:60]
    s = s.replace(old, new, count)


# ---------- 1. 配置：彩蛋音量 + 默认音量 20 ----------
rep('''    public int Volume = 25;''', '''    public int Volume = 20;''')
rep('''    public bool EggOn = false;     // 彩蛋：默认关闭''',
    '''    public bool EggOn = false;     // 彩蛋：默认关闭
    public int EggVolume = 20;     // 彩蛋音量 0-100''')
rep('''                        case "EggKey": c.EggKey = int.Parse(v); break;''',
    '''                        case "EggKey": c.EggKey = int.Parse(v); break;
                        case "EggVolume": c.EggVolume = int.Parse(v); break;''')
rep('''        if (c.Ver < 3) { if (c.EggKey != 0 && !c.EggOn) c.EggOn = true; c.Ver = 3; }''',
    '''        if (c.Ver < 3) { if (c.EggKey != 0 && !c.EggOn) c.EggOn = true; c.Ver = 3; }
        // 用户反馈整体音量还是偏大：默认值再降 20%（25 → 20），只迁移一次
        if (c.Ver < 4) { c.Volume = 20; c.EggVolume = 20; c.Ver = 4; }''')
rep('''    static int vol = 25;''', '''    static int vol = 20;''')

# ---------- 2. PlayWav：支持按音量缩放 ----------
rep('''    public static bool PlayWav(byte[] data, bool loop)''',
    '''    static byte[] scalpBuf;
    static int scalpVol = -1, scalpLen = -1;

    public static bool PlayWavScaled(byte[] wav, int volume, bool loop)
    {
        try
        {
            if (volume < 0) volume = 0;
            if (volume > 100) volume = 100;
            if (volume >= 100) return PlayWav(wav, loop);
            if (scalpBuf == null || scalpVol != volume || scalpLen != wav.Length)
            {
                scalpBuf = ScaleWav(wav, volume);
                scalpVol = volume;
                scalpLen = wav.Length;
            }
            return PlayWav(scalpBuf, loop);
        }
        catch { return false; }
    }

    // 16bit PCM：直接按比例缩放采样点（PlaySound 本身没有音量参数）
    static byte[] ScaleWav(byte[] wav, int volume)
    {
        var b = (byte[])wav.Clone();
        if (b.Length < 44) return b;
        int off = 44;
        try
        {
            int i = 12;
            while (i + 8 <= b.Length)
            {
                string id = "" + (char)b[i] + (char)b[i + 1] + (char)b[i + 2] + (char)b[i + 3];
                int sz = BitConverter.ToInt32(b, i + 4);
                if (id == "data") { off = i + 8; break; }
                if (sz <= 0) break;
                i += 8 + sz + (sz & 1);
            }
        }
        catch { }
        double f = volume / 100.0;
        for (int i = off; i + 1 < b.Length; i += 2)
        {
            short sv = (short)(b[i] | (b[i + 1] << 8));
            int v = (int)(sv * f);
            if (v > 32767) v = 32767;
            if (v < -32768) v = -32768;
            b[i] = (byte)(v & 0xFF);
            b[i + 1] = (byte)((v >> 8) & 0xFF);
        }
        return b;
    }

    public static bool PlayWav(byte[] data, bool loop)''')

# ---------- 3. 轮询绑定：不再依赖窗口焦点，也不会卡在“等待按键” ----------
rep('''    void StartBind()
    {
        binding = true;
        eggBtn.Text = "按下任意键 …";
        eggHint.Text = "现在按一下想绑的键位，绑定后就可以按下按键触发彩蛋。";
        eggHint.ForeColor = Color.FromArgb(255, 190, 120);
        Activate();
    }''',
'''    static readonly int[] ScanKeys = BuildScanKeys();
    static int[] BuildScanKeys()
    {
        var L = new List<int>();
        for (int v = 0x30; v <= 0x39; v++) L.Add(v);          // 0-9
        for (int v = 0x41; v <= 0x5A; v++) L.Add(v);          // A-Z
        for (int v = 0x70; v <= 0x87; v++) L.Add(v);          // F1-F24
        for (int v = 0x60; v <= 0x69; v++) L.Add(v);          // 小键盘 0-9
        L.AddRange(new[]
        {
            0x20, 0x0D, 0x09, 0x1B, 0x08, 0x10, 0x11, 0x12, 0x14,          // 空格 回车 Tab Esc 退格 Shift Ctrl Alt Caps
            0x25, 0x26, 0x27, 0x28, 0x24, 0x23, 0x21, 0x22, 0x2D, 0x2E,    // 方向 Home End PgUp PgDn Ins Del
            0x6A, 0x6B, 0x6D, 0x6F,                                        // * + - /
            0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0xC0, 0xDB, 0xDC, 0xDD, 0xDE // ; = , - . / ` [ \\ ] '
        });
        return L.ToArray();
    }
    bool[] scanPrev = new bool[256];

    void StartBind()
    {
        if (binding) { CancelBind(); return; }        // 再点一次 = 取消
        binding = true;
        for (int i = 0; i < scanPrev.Length; i++) scanPrev[i] = false;
        eggBtn.Text = "按下任意键 …";
        eggHint.Text = "现在按一下想绑的键位，绑定后就可以按下按键触发彩蛋。";
        eggHint.ForeColor = Color.FromArgb(255, 190, 120);
        EnsureEggTimer();
        if (bindTimeout != null) { bindTimeout.Stop(); bindTimeout.Dispose(); }
        bindTimeout = new System.Windows.Forms.Timer { Interval = 10000 };
        bindTimeout.Tick += (a, b) =>
        {
            bindTimeout.Stop(); bindTimeout.Dispose(); bindTimeout = null;
            if (binding) { binding = false; if (eggBtn != null) eggBtn.Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键"; SyncEggWatch(); }
        };
        bindTimeout.Start();
        Activate();
    }

    void CancelBind()
    {
        binding = false;
        if (bindTimeout != null) { bindTimeout.Stop(); bindTimeout.Dispose(); bindTimeout = null; }
        if (eggBtn != null) eggBtn.Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键";
        SyncEggWatch();
    }

    // 绑定期间用轮询找“新按下的那个键”，不依赖窗口焦点：点完按钮去按就行，按不到也不会卡住
    void BindScan()
    {
        foreach (int vk in ScanKeys)
        {
            bool down = (Nat.GetAsyncKeyState(vk) & 0x8000) != 0;
            bool was = scanPrev[vk];
            scanPrev[vk] = down;
            if (down && !was) { BindEgg(vk); return; }
        }
    }''')

# ---------- 4. 定时器启停逻辑 ----------
rep('''    public void SyncEggWatch()
    {
        try
        {
            bool live = C.EggOn && C.EggKey != 0;''',
'''    public void SyncEggWatch()
    {
        try
        {
            bool live = binding || (C.EggOn && C.EggKey != 0);''')

rep('''    void StartHook()
    {
        StopEggWatch();
        eggTimer = new System.Windows.Forms.Timer { Interval = 35 };
        eggTimer.Tick += (a, b) => EggPoll();
        eggTimer.Start();''',
'''    void EnsureEggTimer()
    {
        if (eggTimer != null) return;
        eggTimer = new System.Windows.Forms.Timer { Interval = 35 };
        eggTimer.Tick += (a, b) => EggPoll();
        eggTimer.Start();
    }

    void StartHook()
    {
        EnsureEggTimer();''')

rep('''    void EggPoll()
    {
        bool down = false;
        try { if (C.EggOn && !binding && C.EggKey != 0) down = (Nat.GetAsyncKeyState(C.EggKey) & 0x8000) != 0; } catch { }
        EggTick(down);
    }''',
'''    void EggPoll()
    {
        try
        {
            if (binding) { BindScan(); return; }
            if (!C.EggOn || C.EggKey == 0) { eggDown = false; return; }
            EggTick((Nat.GetAsyncKeyState(C.EggKey) & 0x8000) != 0);
        }
        catch { }
    }''')

# 绑定成功后清掉超时定时器
rep('''            binding = false;
            if (eggBtn != null) eggBtn.Text = "按键 " + KeyName(vk);
            SyncEggWatch();''',
'''            binding = false;
            if (bindTimeout != null) { bindTimeout.Stop(); bindTimeout.Dispose(); bindTimeout = null; }
            if (eggBtn != null) eggBtn.Text = "按键 " + KeyName(vk);
            SyncEggWatch();''')

# ---------- 5. 关开关就掐掉声音 ----------
rep('''            C.EggOn = eggSwitch.On;
            Save();
            SyncEggWatch();          // 立刻生效，不需要变身''',
'''            C.EggOn = eggSwitch.On;
            if (!C.EggOn) Sfx.StopAll();     // 关掉就立刻掐掉正在放的声音
            Save();
            SyncEggWatch();          // 立刻生效，不需要变身''')

# ---------- 6. 试听按彩蛋音量播 ----------
rep('''            bool ok = Sfx.PlayWav(eggBytes, false);''',
    '''            bool ok = Sfx.PlayWavScaled(eggBytes, C.EggVolume, false);''')

# ---------- 7. 界面：加彩蛋音量滑块 + 提示压成一行 ----------
rep('''        eggTest = new Btn { Text = "试听", Location = new Point(312, y), Size = new Size(76, 26) };
        eggTest.Click += (a, b) => { PlayEgg(); };
        settings.Controls.Add(eggTest);
        y += 32;''',
'''        eggTest = new Btn { Text = "试听", Location = new Point(312, y), Size = new Size(76, 26) };
        eggTest.Click += (a, b) => { PlayEgg(); };
        settings.Controls.Add(eggTest);
        y += 32;

        var evl = new Label { Text = "彩蛋音量", ForeColor = Color.FromArgb(200, 196, 214), AutoSize = true, Location = new Point(16, y + 4), BackColor = Color.Transparent };
        settings.Controls.Add(evl);
        eggVol = new Slider { Min = 0, Max = 100, Value = C.EggVolume, Location = new Point(88, y), Size = new Size(238, 24) };
        eggVol.Changed += (a, b) => { C.EggVolume = eggVol.Value; if (eggVolLabel != null) eggVolLabel.Text = eggVol.Value + "%"; Save(); };
        settings.Controls.Add(eggVol);
        eggVolLabel = new Label { Text = C.EggVolume + "%", ForeColor = Color.FromArgb(170, 166, 186), AutoSize = true, Location = new Point(336, y + 4), BackColor = Color.Transparent };
        settings.Controls.Add(eggVolLabel);
        y += 30;''')

rep('''            Text = "绑一个「可以用 Apex 检视的键位」：点「绑定按键」，按一下那个键就行。\\n键盘上任意键都能绑，不吞键、也不会影响检视。",
            ForeColor = Color.FromArgb(128, 124, 142),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(390, 34),''',
'''            Text = "点「绑定按键」再按一下想用的键（任意键都行），绑好后按它就会播放。",
            ForeColor = Color.FromArgb(128, 124, 142),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(390, 30),''')

rep('''            Text = "提示：只替换「正常选择」这一个系统光标，\\n变身前会自动备份你现在的指针。",
            ForeColor = Color.FromArgb(120, 116, 134),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = true,''',
'''            Text = "提示：只替换「正常选择」这一个系统光标，变身前自动备份。",
            ForeColor = Color.FromArgb(120, 116, 134),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(390, 20),''')

rep('''        y += 40;

        NeedH = y + 12;''',
'''        y += 26;

        NeedH = y + 12;''')

# ---------- 8. 字段 ----------
rep('''    int lastEggTick;''', '''    int lastEggTick;
    System.Windows.Forms.Timer bindTimeout;
    Slider eggVol;
    Label eggVolLabel;''')

# ---------- 9. Save 写 EggVolume ----------
rep('''            lines.Add("EggKey=" + EggKey);''',
    '''            lines.Add("EggKey=" + EggKey);
            lines.Add("EggVolume=" + EggVolume);''')

p.write_text(s, encoding="utf-8")
print("patched ok")
