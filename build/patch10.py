import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# tiny trace helper
old = "static class Program\n{\n    static Mutex instanceMutex;"
new = ("static class Program\n{\n    static Mutex instanceMutex;\n"
       "    static void Trace(string m)\n    {\n"
       "        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), \"mumu_main.log\"), DateTime.Now.ToString(\"HH:mm:ss.fff\") + \" \" + m + \"\\n\"); } catch { }\n"
       "    }")
assert old in s
s = s.replace(old, new, 1)

old = """        bool forceRestore = Array.IndexOf(args, "--restore") >= 0;"""
new = """        Trace("main start args=" + string.Join(" ", args));
        bool forceRestore = Array.IndexOf(args, "--restore") >= 0;"""
assert old in s
s = s.replace(old, new, 1)

old = """        Application.Run(new MainForm());"""
new = """        Trace("form creating");
        try
        {
            var f = new MainForm();
            Trace("form created, entering loop");
            Application.Run(f);
            Trace("loop exited");
        }
        catch (Exception ex) { Trace("FATAL " + ex); throw; }"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("patched: startup trace")
