import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- Nat: 加文件名播放 + 热键 ----------
s = s.replace('[DllImport("winmm.dll", CharSet = CharSet.Unicode)] public static extern bool PlaySound(byte[] data, IntPtr mod, int flags);\n    public const int SND_ASYNC = 1, SND_NODEFAULT = 2, SND_MEMORY = 4;',
'''[DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySound(byte[] data, IntPtr mod, int flags);
    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySoundFile(string file, IntPtr mod, int flags);
    public const int SND_ASYNC = 1, SND_NODEFAULT = 2, SND_MEMORY = 4, SND_FILENAME = 0x20000, SND_LOOP = 8, SND_PURGE = 0x40;
    [DllImport("user32.dll")] public static extern bool RegisterHotKey(IntPtr hWnd, int id, int mods, int vk);
    [DllImport("user32.dll")] public static extern bool UnregisterHotKey(IntPtr hWnd, int id);''')

# ---------- Sfx: 文件播放 ----------
s = s.replace('''    public static void Play()
    {''',
'''    public static void PlayFile(string path, bool loop)
    {
        try
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path)) return;
            Nat.PlaySoundFile(path, IntPtr.Zero, Nat.SND_FILENAME | Nat.SND_ASYNC | Nat.SND_NODEFAULT | (loop ? Nat.SND_LOOP : 0));
        }
        catch { }
    }

    public static void StopAll()
    {
        try { Nat.PlaySoundFile(null, IntPtr.Zero, Nat.SND_PURGE | Nat.SND_ASYNC); } catch { }
    }

    public static void Play()
    {''')

p.write_text(s, encoding="utf-8")
print("nat/sfx patched", s.count("PlaySoundFile"), s.count("RegisterHotKey"))
