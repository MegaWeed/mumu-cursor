import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

anchor = "    // 测试用：把整个窗口拍成 png\n    void ShotTemp(string name)"
add = '''    // 测试用：直接从屏幕抓窗口那块（能拍到普通子控件，#DrawToBitmap 拍不到刚建的覆盖层）
    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern IntPtr GetDC(IntPtr h);
    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern int ReleaseDC(IntPtr h, IntPtr hdc);
    [System.Runtime.InteropServices.DllImport("gdi32.dll")] static extern bool BitBlt(IntPtr dst, int x, int y, int w, int h, IntPtr src, int sx, int sy, int rop);

    void ShotScreen(string name)
    {
        try
        {
            var r = Bounds;
            using (var bm = new Bitmap(r.Width, r.Height, System.Drawing.Imaging.PixelFormat.Format32bppArgb))
            {
                using (var g = Graphics.FromImage(bm))
                {
                    IntPtr dst = g.GetHdc();
                    IntPtr src = GetDC(IntPtr.Zero);
                    BitBlt(dst, 0, 0, r.Width, r.Height, src, r.X, r.Y, 0x00CC0020);
                    ReleaseDC(IntPtr.Zero, src);
                    g.ReleaseHdc(dst);
                }
                bm.Save(Path.Combine(Path.GetTempPath(), name), System.Drawing.Imaging.ImageFormat.Png);
            }
        }
        catch (Exception ex) { Console.WriteLine("shoot err " + ex.Message); }
    }

    // 测试用：把整个窗口拍成 png
    void ShotTemp(string name)'''
assert anchor in s
s = s.replace(anchor, add, 1)

s = s.replace('ShotTemp("fade_before.png");', 'ShotScreen("fade_before.png");')
s = s.replace('ShotTemp("fade_after0.png");', 'ShotScreen("fade_after0.png");')
s = s.replace('ShotTemp("fade_mid.png");', 'ShotScreen("fade_mid.png");')

p.write_text(s, encoding="utf-8")
print("screen capture added")
