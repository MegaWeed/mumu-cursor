import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:160]
    s = s.replace(old, new, 1)


# 窗口必须由"渲染线程自己"创建：
# 之前是 UI 线程创建、渲染线程去 SetWindowPos，等于跨线程同步调用，
# UI 线程若正忙就互等（就是那次 Alt+Tab 冻住的成因），销毁窗口也会因线程不对而失败。
rep('''        W = PadX * 2 + 150;
        H = PadY + 160 + (int)Pendant.RopeLen + 90;
        Create();''',
'''        W = PadX * 2 + 150;
        H = PadY + 160 + (int)Pendant.RopeLen + 90;
        // 注意：窗口在 Run() 里由渲染线程自己创建（见 Create 调用处）''')

rep('''            Prepare();
            var sw = System.Diagnostics.Stopwatch.StartNew();''',
'''            Create();              // 必须在本线程建窗，后续置顶/销毁才不会跨线程互等
            Prepare();
            var sw = System.Diagnostics.Stopwatch.StartNew();''')

p.write_text(s, encoding="utf-8")
print("create on render thread")
