import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = """        catch { if (cover != null) { if (cover.Parent != null) cover.Parent.Controls.Remove(cover); cover.Dispose(); cover = null; } }"""
new = """        catch (Exception ex)
        {
            Console.WriteLine("cover err: " + ex.GetType().Name + " " + ex.Message);
            if (cover != null) { if (cover.Parent != null) cover.Parent.Controls.Remove(cover); cover.Dispose(); cover = null; }
            if (snap != null) { snap.Dispose(); snap = null; }
        }
        Console.WriteLine("cover: " + (cover == null ? "null" : "ok " + cover.Bounds + " parent=" + (cover.Parent == null ? "null" : cover.Parent.Name)) + " settings=" + settings.Bounds);"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("cover diagnostics")
