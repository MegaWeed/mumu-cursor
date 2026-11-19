import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 补字段
old = """    const int HOT_ID = 0xBEEF;
    string eggWav;"""
new = """    const int HOT_ID = 0xBEEF;
    string eggWav;
    IntPtr kbdHook = IntPtr.Zero;
    Nat.LowLevelProc kbdProc;      // 必须留引用，否则委托被回收 = 钩子失效
    int lastEggTick;               // 防止长按连发一串声音"""
assert old in s
s = s.replace(old, new)

# 2) 去掉旧的 RegisterHotKey 分支
old = """    protected override void WndProc(ref Message m)
    {
        if (m.Msg == 0x0312 && m.WParam.ToInt32() == HOT_ID)
        {
            if (C.EggOn) PlayEgg();
            return;
        }
        base.WndProc(ref m);
    }"""
new = """    protected override void WndProc(ref Message m)
    {
        base.WndProc(ref m);
    }"""
assert old in s
s = s.replace(old, new)

p.write_text(s, encoding="utf-8")
print("fields+wndproc ok", s.count("kbdHook"))
