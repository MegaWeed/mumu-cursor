import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = '''        Text = "MUMU 光标";
        ClientSize = new Size(1000, 760);'''
new = '''        Text = "MUMU 光标";
        try
        {
            using (var st = typeof(MainForm).Assembly.GetManifestResourceStream("app.ico"))
                if (st != null) Icon = new Icon(st);
        }
        catch { }
        ClientSize = new Size(1000, 760);'''
assert old in s
s = s.replace(old, new)

p.write_text(s, encoding="utf-8")
print("form icon ok")
