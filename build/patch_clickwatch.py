import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 字段：静态模式下的独立左键监听
old = """    Btn applyBtn, applyStaticBtn, restoreBtn, previewDyn, previewStatic;"""
new = """    Btn applyBtn, applyStaticBtn, restoreBtn, previewDyn, previewStatic;

    // 静态模式没有覆盖层，所以单独起一个只读左键的轮询，用来放点击音效
    System.Windows.Forms.Timer clickWatch;
    bool clickDown = false;"""
assert old in s
s = s.replace(old, new, 1)

# 2) 方法：启停 + tick
old = """    public void SyncEggWatch()"""
new = """    public void SyncClickWatch()
    {
        try
        {
            bool need = C.ClickSound && staticOn && overlay == null;
            if (need && clickWatch == null)
            {
                clickDown = (Nat.GetAsyncKeyState(Nat.VK_LBUTTON) & 0x8000) != 0;
                clickWatch = new System.Windows.Forms.Timer { Interval = 25 };
                clickWatch.Tick += (a, b) =>
                {
                    try
                    {
                        bool down = (Nat.GetAsyncKeyState(Nat.VK_LBUTTON) & 0x8000) != 0;
                        if (down && !clickDown) Sfx.Play();
                        clickDown = down;
                    }
                    catch { }
                };
                clickWatch.Start();
            }
            else if (!need && clickWatch != null)
            {
                clickWatch.Stop(); clickWatch.Dispose(); clickWatch = null;
            }
        }
        catch { }
    }

    public void SyncEggWatch()"""
assert "public void SyncEggWatch()" in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("click watch added")
