import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) Nat：按内存播放
s = s.replace('''    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySoundFile(string file, IntPtr mod, int flags);''',
'''    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySoundFile(string file, IntPtr mod, int flags);
    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySoundBytes(byte[] data, IntPtr mod, int flags);
    [DllImport("winmm.dll")] public static extern int waveOutGetNumDevs();''')

# 2) Sfx：内存播放（和点击音效同一条路，不依赖磁盘文件）
s = s.replace('''    public static void PlayFile(string path, bool loop)''',
'''    static byte[] playing;   // 异步播放期间必须留住，别让 GC 回收

    public static bool PlayWav(byte[] data, bool loop)
    {
        try
        {
            if (data == null || data.Length < 44) return false;
            playing = data;
            int flags = Nat.SND_MEMORY | Nat.SND_ASYNC | Nat.SND_NODEFAULT | (loop ? Nat.SND_LOOP : 0);
            bool ok = Nat.PlaySoundBytes(data, IntPtr.Zero, flags);
            int err = Marshal.GetLastWin32Error();
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " playwav bytes=" + data.Length + " ok=" + ok + " err=" + err + " devs=" + Nat.waveOutGetNumDevs() + "\\n"); } catch { }
            return ok;
        }
        catch (Exception ex)
        {
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), "playwav ex " + ex.Message + "\\n"); } catch { }
            return false;
        }
    }

    public static void PlayFile(string path, bool loop)''')

# 3) PlayEgg：改成从内嵌资源直接播，不再往磁盘写 egg.wav
start = s.index("    void PlayEgg()")
end = s.index("    protected override void WndProc")
new = '''    void PlayEgg()
    {
        try
        {
            if (eggBytes == null)
            {
                var asm = Assembly.GetExecutingAssembly();
                foreach (var n in asm.GetManifestResourceNames())
                    if (n.EndsWith("egg_default.wav", StringComparison.OrdinalIgnoreCase))
                    {
                        using (var st = asm.GetManifestResourceStream(n))
                        using (var ms = new MemoryStream())
                        {
                            st.CopyTo(ms);
                            eggBytes = ms.ToArray();
                        }
                        break;
                    }
            }
            if (eggBytes == null)
            {
                if (eggHint != null) { eggHint.Text = "彩蛋音频没打进程序里，重装一下试试。"; eggHint.ForeColor = Color.FromArgb(255, 140, 140); }
                return;
            }
            bool ok = Sfx.PlayWav(eggBytes, false);
            if (eggHint != null)
            {
                if (ok) { eggHint.Text = "正在播放（" + (eggBytes.Length / 88200.0).ToString("0.0") + " 秒）。没听到的话：看看系统音量、或者这个程序在「音量合成器」里是不是被静音了。"; eggHint.ForeColor = Color.FromArgb(150, 255, 190); }
                else { eggHint.Text = "播放失败（系统没有可用的音频设备？）。换台设备或检查一下声音服务。"; eggHint.ForeColor = Color.FromArgb(255, 140, 140); }
            }
        }
        catch (Exception ex)
        {
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), "egg ex " + ex + "\\n"); } catch { }
        }
    }

'''
s = s[:start] + new + s[end:]

# 4) 字段
s = s.replace("    string eggWav;", "    string eggWav;\n    byte[] eggBytes;")

p.write_text(s, encoding="utf-8")
print("memory playback", s.count("eggBytes"), s.count("PlayWav"))
