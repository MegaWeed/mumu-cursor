import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) 点击音效改走和彩蛋同一条已验证的通道（PlayWav：自己钉住缓冲 + 记日志）
old = """    public static void Play()
    {
        try
        {
            var d = scaled;
            if (d == null) return;
            Nat.PlaySound(d, IntPtr.Zero, Nat.SND_MEMORY | Nat.SND_ASYNC | Nat.SND_NODEFAULT);
        }
        catch { }
    }"""
new = """    public static void Play()
    {
        try
        {
            var d = scaled;
            if (d == null) { LogWhy(\"click: no data\"); return; }
            // 和彩蛋走同一条路：PlaySound 异步播放时缓冲必须一直有效，
            // 直接传 byte[] 会被封送器复制后释放 → 听起来就是“没声音”。
            PlayWav(d, false);
        }
        catch { }
    }

    static void LogWhy(string msg)
    {
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), DateTime.Now.ToString(\"HH:mm:ss.fff\") + \" \" + msg + \"\\n\"); } catch { }
    }"""
assert old in s
s = s.replace(old, new, 1)

# 2) Set()：切音效时真的重新读资源（旧代码 raw 只读一次，切音效后一直播第一个）
old = """        if (raw == null || !cache.ContainsKey(sfx))"""
new = """        if (raw == null || lastSfx != sfx)"""
assert old in s
s = s.replace(old, new, 1)

old = """    static string name = \"coin\";"""
new = """    static string name = \"coin\";
    static string lastSfx = \"\";"""
assert old in s
s = s.replace(old, new, 1)

old = """                    break;
                }
        }
        if (raw == null) { scaled = null; return; }"""
new = """                    break;
                }
            lastSfx = sfx;
        }
        if (raw == null) { scaled = null; LogWhy(\"click: resource missing for \" + sfx); return; }"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("click sound routed through PlayWav")
