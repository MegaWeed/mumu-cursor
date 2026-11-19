import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 统一开关：只要程序开着 + 彩蛋开着 + 绑了键，就必须在监听（和变身无关）
s = s.replace('''    void StartHook()
    {''',
'''    // 彩蛋监听只看「开没开 + 绑没绑键」，和有没有变身完全无关
    public void SyncEggWatch()
    {
        try
        {
            if (C.EggOn && C.EggKey != 0) StartHook();
            else StopEggWatch();
        }
        catch { }
    }

    void StartHook()
    {''')

# BindEgg：绑完就同步
s = s.replace('''            if (C.EggOn) StartHook();''', '''            SyncEggWatch();''')

# 彩蛋开关：变了就同步
s = s.replace('''            C.EggOn = eggSwitch.On;
            if (!C.EggOn) { UnbindEgg(); }
            else if (C.EggKey != 0) BindEgg(C.EggKey);
            Save(); RefreshThumbs();''',
'''            C.EggOn = eggSwitch.On;
            Save();
            SyncEggWatch();          // 立刻生效，不需要变身
            RefreshThumbs();''')

# 启动时：不光要在 OnShown 里绑，还要把监听拉起来
s = s.replace('''        // 上次绑过键且开着彩蛋：程序一起来就把热键挂回去
        if (C.EggOn && C.EggKey != 0) BindEgg(C.EggKey);''',
'''        // 上次绑过键且开着彩蛋：程序一起来就开始监听，不需要变身
        SyncEggWatch();''')

# 2) 绑定中的提示文案按用户要求改
s = s.replace('eggHint.Text = "现在按一下想绑的键——就是你在 Apex 里检视用的那个键，任意键都行。";',
              'eggHint.Text = "现在按一下想绑的键位，绑定后就可以按下按键触发彩蛋。";')

# 3) 自测：不经过变身，只开彩蛋 + 绑键，看监听有没有起来
s = s.replace('''        if (Array.IndexOf(args, "--eggkeys") >= 0)''',
'''        if (Array.IndexOf(args, "--eggnoapply") >= 0)
        {
            var f8 = new MainForm();
            f8.Shown += (a, b) =>
            {
                f8.EggSwitchOnForTest();
                var t2 = new System.Windows.Forms.Timer { Interval = 1500 };
                t2.Tick += (c, d) => { t2.Stop(); t2.Dispose(); f8.Close(); };
                t2.Start();
            };
            Application.Run(f8);
            return;
        }

        if (Array.IndexOf(args, "--eggkeys") >= 0)''')

s = s.replace('''    public void TestPoll()''',
'''    public void EggSwitchOnForTest()
    {
        // 完全走界面那条路：打开「开启彩蛋」→ 绑 H → 不调用 Apply
        if (eggSwitch != null) { eggSwitch.On = true; eggSwitch.Invalidate(); }
        C.EggOn = true;
        C.EggKey = 0x48;
        Save();
        SyncEggWatch();
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " noapply transformed=" + (overlay != null) + "\\n"); } catch { }
    }

    public void TestPoll()''')

p.write_text(s, encoding="utf-8")
print("sync ok", s.count("SyncEggWatch"))
