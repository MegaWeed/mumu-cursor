import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:200]
    s = s.replace(old, new, 1)


# GetWindow 用于检查 z 序
rep('''    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, int flags);''',
'''    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, int flags);
    [DllImport("user32.dll")] public static extern IntPtr GetWindow(IntPtr h, int cmd);
    public const int GW_HWNDPREV = 3;''')

# 测试开关
rep('''    public bool EggImeTest;''',
'''    public bool EggImeTest;
    public bool TopProbe;         // 自测：建一个"抢 topmost"的窗口，看覆盖层能不能压回去''')

# 测试逻辑：放在 OnShown 末尾附近，用定时器串起来
rep('''        if (EggBindTest)''',
'''        if (TopProbe)
        {
            var a = new System.Windows.Forms.Timer { Interval = 900 };
            a.Tick += (s1, e1) =>
            {
                a.Stop(); a.Dispose();
                DoApply();
                var rival = new Form
                {
                    FormBorderStyle = FormBorderStyle.None,
                    StartPosition = FormStartPosition.Manual,
                    TopMost = true,
                    BackColor = Color.FromArgb(40, 40, 46),
                    Size = new Size(360, 200),
                };
                var sc = Screen.PrimaryScreen.WorkingArea;
                rival.Location = new Point(sc.Left + sc.Width / 2 - 180, sc.Top + sc.Height / 2 - 100);
                rival.Show();
                rival.BringToFront();

                var b = new System.Windows.Forms.Timer { Interval = 1500 };
                b.Tick += (s2, e2) =>
                {
                    b.Stop(); b.Dispose();
                    IntPtr above = Nat.GetWindow(rival.Handle, Nat.GW_HWNDPREV);
                    bool pass = overlay != null && above == overlay.hwnd;
                    Log("topprobe pass=" + pass + " above=" + above + " ov=" + (overlay != null ? overlay.hwnd : IntPtr.Zero)
                        + " topcalls=" + (overlay != null ? overlay.TopCalls : 0) + " frames=" + (overlay != null ? overlay.Frames : 0));
                    rival.Close();
                    DoRestore();
                    var c = new System.Windows.Forms.Timer { Interval = 500 };
                    c.Tick += (s3, e3) => { c.Stop(); c.Dispose(); Close(); };
                    c.Start();
                };
                b.Start();
            };
            a.Start();
        }

        if (EggBindTest)''')

p.write_text(s, encoding="utf-8")
print("topprobe added")
