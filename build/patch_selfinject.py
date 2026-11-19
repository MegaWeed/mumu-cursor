import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

s = s.replace('''        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);''',
'''        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);

        [DllImport("user32.dll")]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, IntPtr dwExtraInfo);''')

# 自测：绑好键之后，自己合成一次按键，验证 钩子→回调→播放 整条链路
s = s.replace("""                BindEgg(vk);
                var cl = new System.Windows.Forms.Timer { Interval = 6000 };""",
"""                BindEgg(vk);
                var vol = new System.Windows.Forms.Timer { Interval = 600 };
                vol.Tick += (c2, d2) =>
                {
                    vol.Stop(); vol.Dispose();
                    Nat.keybd_event((byte)vk, 0, 0, IntPtr.Zero);
                    System.Threading.Thread.Sleep(30);
                    Nat.keybd_event((byte)vk, 0, 2, IntPtr.Zero);
                };
                vol.Start();
                var cl = new System.Windows.Forms.Timer { Interval = 6000 };""")

p.write_text(s, encoding="utf-8")
print("self-inject added")
