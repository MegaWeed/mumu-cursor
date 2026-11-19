import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert old in s, "MISSING: " + old[:70]
    s = s.replace(old, new, count)


# 1) Nat：加进程完整性级别检测
rep('''    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vk);''',
    '''    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vk);

    [DllImport("kernel32.dll")] public static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
    [DllImport("advapi32.dll", SetLastError = true)] public static extern bool OpenProcessToken(IntPtr proc, int access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError = true)] public static extern bool GetTokenInformation(IntPtr token, int cls, IntPtr info, int len, out int retLen);
    [DllImport("advapi32.dll")] public static extern IntPtr GetSidSubAuthority(IntPtr sid, int index);
    [DllImport("advapi32.dll")] public static extern IntPtr GetSidSubAuthorityCount(IntPtr sid);

    // 低完整性级别（AppContainer / Low IL）的进程读不到全局按键状态：GetAsyncKeyState 永远返回 0。
    // 典型场景就是从聊天软件、沙箱工具里“点开” exe。这个检测用来给用户一个明确提示。
    public static bool IsLowIntegrity()
    {
        try
        {
            IntPtr tok;
            if (!OpenProcessToken(GetCurrentProcess(), 0x0008, out tok)) return false;
            try
            {
                int len;
                GetTokenInformation(tok, 25, IntPtr.Zero, 0, out len);   // TokenIntegrityLevel = 25
                if (len <= 0) return false;
                IntPtr buf = Marshal.AllocHGlobal(len);
                try
                {
                    if (!GetTokenInformation(tok, 25, buf, len, out len)) return false;
                    IntPtr sid = Marshal.ReadIntPtr(buf);                 // TOKEN_MANDATORY_LABEL.Label.Sid
                    if (sid == IntPtr.Zero) return false;
                    int cnt = Marshal.ReadByte(GetSidSubAuthorityCount(sid));
                    if (cnt <= 0) return false;
                    int rid = Marshal.ReadInt32(GetSidSubAuthority(sid, cnt - 1));
                    return rid < 0x2000;                                  // < Medium
                }
                finally { Marshal.FreeHGlobal(buf); }
            }
            finally { CloseHandle(tok); }
        }
        catch { return false; }
    }''')

# 2) SyncEggWatch 里先判断权限，低权限就别显示“监听中”骗人
rep('''            if (eggHint != null && !binding)
            {
                if (live)''',
'''            if (eggHint != null && !binding)
            {
                if (Nat.IsLowIntegrity())
                {
                    eggHint.Text = "⚠ 这个程序被以「低权限」启动了（比如从聊天窗口里点开），系统不让它读全局按键。请到资源管理器里双击 MUMU光标.exe 再试。";
                    eggHint.ForeColor = Color.FromArgb(255, 170, 120);
                    return;
                }
                if (live)''')

# 3) 启动时把权限结论写日志，方便排查
rep('''        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " watch start key=" + C.EggKey + "\\n"); } catch { }''',
    '''        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " watch start key=" + C.EggKey + " lowIL=" + Nat.IsLowIntegrity() + "\\n"); } catch { }''')

p.write_text(s, encoding="utf-8")
print("low IL detection added")
