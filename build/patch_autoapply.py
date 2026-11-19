import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# MainForm: 自动变身开关（给 --autoapply 测试用）
s = s.replace('    bool binding;   // 正在等用户按键盘',
              '    bool binding;   // 正在等用户按键盘\n    public bool AutoApply;')

s = s.replace('''    protected override void OnShown(EventArgs e)
    {
        base.OnShown(e);
        KeyPreview = true;''',
'''    protected override void OnShown(EventArgs e)
    {
        base.OnShown(e);
        KeyPreview = true;
        if (AutoApply)
        {
            var t = new System.Windows.Forms.Timer { Interval = 1200 };
            t.Tick += (a, b) => { t.Stop(); t.Dispose(); Apply(); };
            t.Start();
        }''')

# Program: --autoapply
s = s.replace('''        if (Array.IndexOf(args, "--restore") >= 0)
''',
'''        if (Array.IndexOf(args, "--autoapply") >= 0)
        {
            var f2 = new MainForm { AutoApply = true };
            Application.Run(f2);
            return;
        }

        if (Array.IndexOf(args, "--restore") >= 0)
''', 1)

p.write_text(s, encoding="utf-8")
print("autoapply added", s.count("--autoapply"))
