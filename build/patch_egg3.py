import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 绑键即开启彩蛋 + 提示改成“监听中”
s = s.replace('''            C.EggKey = vk;
            C.EggOn = eggSwitch != null ? eggSwitch.On : C.EggOn;
            Save();
            binding = false;
            if (eggBtn != null) eggBtn.Text = "按键 " + KeyName(vk);
            SyncEggWatch();
            eggHint.Text = "绑定好了：按 " + KeyName(vk) + " 就会放声音（不吞键，正常打字/检视都不受影响）。";
            eggHint.ForeColor = Color.FromArgb(150, 255, 190);''',
'''            C.EggKey = vk;
            C.EggOn = true;                                   // 绑上了就等于要用，直接把开关打开
            if (eggSwitch != null) { eggSwitch.On = true; eggSwitch.Invalidate(); }
            Save();
            binding = false;
            if (eggBtn != null) eggBtn.Text = "按键 " + KeyName(vk);
            SyncEggWatch();''')

# 2) SyncEggWatch 同时负责把状态写给人看
s = s.replace('''    public void SyncEggWatch()
    {
        try
        {
            if (C.EggOn && C.EggKey != 0) StartHook();
            else StopEggWatch();
        }
        catch { }
    }''',
'''    public void SyncEggWatch()
    {
        try
        {
            bool live = C.EggOn && C.EggKey != 0;
            if (live) StartHook();
            else StopEggWatch();

            if (eggHint != null && !binding)
            {
                if (live)
                {
                    eggHint.Text = "监听中：按 " + KeyName(C.EggKey) + " 就会播放；连按会打断上一次、从头重播。";
                    eggHint.ForeColor = Color.FromArgb(150, 255, 190);
                }
                else if (C.EggKey != 0)
                {
                    eggHint.Text = "彩蛋已关闭，打开左边开关后按键才会响。";
                    eggHint.ForeColor = Color.FromArgb(205, 205, 215);
                }
                else
                {
                    eggHint.Text = "点「绑定按键」，然后按下想用的键（不吞键，正常打字/检视都不受影响）。";
                    eggHint.ForeColor = Color.FromArgb(150, 156, 172);
                }
            }
        }
        catch { }
    }''')

# 3) 去掉 120ms 冷却：每一次“按下沿”都重新播，PlaySound 再调会打断上一个
s = s.replace('''            if (down && !eggDown)
            {
                eggDown = true;
                int now = Environment.TickCount;
                if (now - lastEggTick > 120) { lastEggTick = now; PlayEgg(); }
            }''',
'''            if (down && !eggDown)
            {
                eggDown = true;
                PlayEgg();                                   // 再按就打断上一遍，从头开始，不叠音
            }''')

# 4) 试听不再写“正在播放”，只在真失败时提示
s = s.replace('''            bool ok = Sfx.PlayWav(eggBytes, false);
            if (eggHint != null)
            {
                if (ok) { eggHint.Text = "正在播放（" + (eggBytes.Length / 88200.0).ToString("0.0") + " 秒）。没听到的话：看看系统音量、或者这个程序在「音量合成器」里是不是被静音了。"; eggHint.ForeColor = Color.FromArgb(150, 255, 190); }
                else { eggHint.Text = "播放失败（系统没有可用的音频设备？）。换台设备或检查一下声音服务。"; eggHint.ForeColor = Color.FromArgb(255, 140, 140); }
            }''',
'''            bool ok = Sfx.PlayWav(eggBytes, false);
            if (!ok && eggHint != null)
            {
                eggHint.Text = "播放失败（系统没有可用的音频设备？）。换台设备或检查一下声音服务。";
                eggHint.ForeColor = Color.FromArgb(255, 140, 140);
            }''')

# 5) 自测：按住只响一次 → 松开立刻再按要能马上重播
s = s.replace('''        EggTick(true); EggTick(true); EggTick(true);   // 按住，只该响一次
        EggTick(false);
        System.Threading.Thread.Sleep(300);
        EggTick(true); EggTick(false);                  // 松开再按，该响第二次''',
'''        EggTick(true); EggTick(true); EggTick(true);   // 按住，只该响一次
        EggTick(false);
        EggTick(true); EggTick(false);                  // 松手马上再按：立刻重播，不叠音''')

p.write_text(s, encoding="utf-8")
print("ok", "lastEggTick" in s, s.count("PlayEgg();"))
