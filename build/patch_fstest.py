import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:160]
    s = s.replace(old, new, 1)


rep('''        if (Array.IndexOf(args, "--topprobe") >= 0)''',
'''        if (Array.IndexOf(args, "--fstest") >= 0)
        {
            var f9 = new MainForm { FsTest = true };
            Application.Run(f9);
            return;
        }
        if (Array.IndexOf(args, "--topprobe") >= 0)''')

rep('''        public bool TopProbe;''',
'''        public bool FsTest;           // 自测：造一个"无边框全屏"前台窗口，验证精灵会不会让开
        public bool TopProbe;''')

# 在 Apply 之后插入自测逻辑：找 Apply() 的调用点附近不好定位，改成 OnShown 里判断
rep('''        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);''',
'''        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            if (FsTest) { var t = new System.Windows.Forms.Timer { Interval = 300 }; int step = 0; t.Tick += (a, b) =>
            {
                step++;
                if (step == 1)
                {
                    Apply();
                    var f = new Form { FormBorderStyle = FormBorderStyle.None, StartPosition = FormStartPosition.Manual, Bounds = Screen.PrimaryScreen.Bounds, TopMost = true, ShowInTaskbar = false, BackColor = Color.Black };
                    f.Show(); f.Activate(); Nat.SetForegroundWindow(f.Handle); Nat.SetFocus(f.Handle);
                    Program.Trace("fstest: fullscreen window shown " + f.Bounds);
                }
                else if (step == 4)
                {
                    bool vis = overlay != null && Nat.IsWindowVisible(overlay.hwnd);
                    Console.WriteLine("fstest hidden=" + (overlay != null && overlay.SysCursorHidden) + " reason=" + (overlay != null ? overlay.HideReason : "-") + " overlayVisible=" + vis);
                    Program.Trace("fstest hidden=" + (overlay != null && overlay.SysCursorHidden) + " reason=" + (overlay != null ? overlay.HideReason : "-"));
                    t.Stop();
                    foreach (Form fx in Application.OpenForms) if (fx != this) fx.Close();
                    if (overlay != null) { overlay.Stop(); overlay = null; }
                    CursorSwitch.Restore();
                    Close();
                }
            }; t.Start(); }''')

p.write_text(s, encoding="utf-8")
print("fstest added")
