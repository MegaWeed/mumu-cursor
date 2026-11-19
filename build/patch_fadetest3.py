import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

local = '''        void Shot(string name)
        {
            try
            {
                using (var bm = new Bitmap(Width, Height))
                {
                    DrawToBitmap(bm, new Rectangle(0, 0, Width, Height));
                    bm.Save(Path.Combine(Path.GetTempPath(), name), System.Drawing.Imaging.ImageFormat.Png);
                }
            }
            catch (Exception ex) { Console.WriteLine("shot err " + ex.Message); }
        }

'''
assert local in s, "local func"
s = s.replace(local, "", 1)

# 变成类成员方法（老的 csc 是 C# 5，不支持局部函数）
anchor = '''    // 切换「动态 / 静态」：右栏要整套重建（静态没有③④）
    public void TestSwitchModes()'''
method = '''    // 测试用：把整个窗口拍成 png
    void ShotTemp(string name)
    {
        try
        {
            using (var bm = new Bitmap(Width, Height))
            {
                DrawToBitmap(bm, new Rectangle(0, 0, Width, Height));
                bm.Save(Path.Combine(Path.GetTempPath(), name), System.Drawing.Imaging.ImageFormat.Png);
            }
        }
        catch (Exception ex) { Console.WriteLine("shot err " + ex.Message); }
    }

    // 切换「动态 / 静态」：右栏要整套重建（静态没有③④）
    public void TestSwitchModes()'''
assert anchor in s
s = s.replace(anchor, method, 1)

s = s.replace('Shot("fade_before.png");', 'ShotTemp("fade_before.png");')
s = s.replace('Shot("fade_after0.png");', 'ShotTemp("fade_after0.png");')
s = s.replace('Shot("fade_mid.png");', 'ShotTemp("fade_mid.png");')

p.write_text(s, encoding="utf-8")
print("local func -> method")
