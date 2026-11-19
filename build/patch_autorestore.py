import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

s = s.replace('    public bool AutoApply;', '    public bool AutoApply;\n    public int AutoRestoreSecs;   // >0 时自动“点一下恢复”，用于自测')

s = s.replace('''        if (AutoApply)
        {
            var t = new System.Windows.Forms.Timer { Interval = 1200 };
            t.Tick += (a, b) => { t.Stop(); t.Dispose(); Apply(); };
            t.Start();
        }''',
'''        if (AutoApply)
        {
            var t = new System.Windows.Forms.Timer { Interval = 1200 };
            t.Tick += (a, b) =>
            {
                t.Stop(); t.Dispose();
                Apply();
                if (AutoRestoreSecs > 0)
                {
                    var r = new System.Windows.Forms.Timer { Interval = AutoRestoreSecs * 1000 };
                    r.Tick += (c, d) =>
                    {
                        r.Stop(); r.Dispose();
                        Restore();
                        var q = new System.Windows.Forms.Timer { Interval = 800 };
                        q.Tick += (e2, f2) => { q.Stop(); q.Dispose(); Close(); };
                        q.Start();
                    };
                    r.Start();
                }
            };
            t.Start();
        }''')

s = s.replace('''        if (Array.IndexOf(args, "--autoapply") >= 0)
        {
            var f2 = new MainForm { AutoApply = true };''',
'''        int ar = Array.IndexOf(args, "--autorestore");
        if (ar >= 0 && ar + 1 < args.Length)
        {
            var f3 = new MainForm { AutoApply = true, AutoRestoreSecs = int.Parse(args[ar + 1]) };
            Application.Run(f3);
            return;
        }

        if (Array.IndexOf(args, "--autoapply") >= 0)
        {
            var f2 = new MainForm { AutoApply = true };''')

p.write_text(s, encoding="utf-8")
print("autorestore added", s.count("AutoRestoreSecs"))
