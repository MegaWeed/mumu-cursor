import pathlib, re

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- 1) Nat：低层键盘钩子 ----------
anchor = '    [DllImport("user32.dll")] public static extern bool UnregisterHotKey(IntPtr hWnd, int id);'
assert anchor in s
s = s.replace(anchor, anchor + '''

        // ---- 全局键盘钩子：任何键都能绑，而且不吞键 ----
        public const int WH_KEYBOARD_LL = 13;
        public const int WM_KEYDOWN = 0x0100;
        public const int WM_SYSKEYDOWN = 0x0104;

        [StructLayout(LayoutKind.Sequential)]
        public struct KBDLLHOOKSTRUCT
        {
            public int vkCode;
            public int scanCode;
            public int flags;
            public int time;
            public IntPtr dwExtraInfo;
        }

        public delegate IntPtr LowLevelProc(int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr SetWindowsHookEx(int idHook, LowLevelProc lpfn, IntPtr hMod, uint dwThreadId);

        [DllImport("user32.dll", SetLastError = true)]
        public static extern bool UnhookWindowsHookEx(IntPtr hhk);

        [DllImport("user32.dll")]
        public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);''')

# ---------- 2) 字段 ----------
s = s.replace('    int HOT_ID = 0xBEEF;',
'''    int HOT_ID = 0xBEEF;
    IntPtr kbdHook = IntPtr.Zero;
    Nat.LowLevelProc kbdProc;      // 必须留引用，否则委托被回收 = 钩子失效
    int lastEggTick;               // 防止长按连发一串声音''')

# ---------- 3) WndProc 不再处理热键 ----------
s = s.replace('''    override void WndProc(ref Message m)
    {
        if (m.Msg == 0x0312 && m.WParam.ToInt32() == HOT_ID)
        {
            if (C.EggOn) PlayEgg();
            return;
        }
        base.WndProc(ref m);
    }''',
'''    override void WndProc(ref Message m)
    {
        base.WndProc(ref m);
    }''')

# ---------- 4) 绑定 / 解绑 / 按键名 ----------
old_start = s.index('    static string KeyName(int vk)')
old_end = s.index('    void PlayEgg()')
new = '''    static string KeyName(int vk)
    {
        if (vk >= 0x70 && vk <= 0x87) return "F" + (vk - 0x6F);          // F1..F24
        if (vk >= 0x30 && vk <= 0x39) return ((char)vk).ToString();       // 0-9
        if (vk >= 0x41 && vk <= 0x5A) return ((char)vk).ToString();       // A-Z
        switch (vk)
        {
            case 0x20: return "空格";
            case 0x0D: return "回车";
            case 0x09: return "Tab";
            case 0x1B: return "Esc";
            case 0x08: return "退格";
            case 0x10: return "Shift";
            case 0x11: return "Ctrl";
            case 0x12: return "Alt";
            case 0x14: return "CapsLock";
            case 0x25: return "←";
            case 0x26: return "↑";
            case 0x27: return "→";
            case 0x28: return "↓";
            case 0x24: return "Home";
            case 0x23: return "End";
            case 0x21: return "PgUp";
            case 0x22: return "PgDn";
            case 0x2D: return "Insert";
            case 0x2E: return "Delete";
            case 0xBA: return ";";
            case 0xBB: return "=";
            case 0xBC: return ",";
            case 0xBD: return "-";
            case 0xBE: return ".";
            case 0xBF: return "/";
            case 0xC0: return "`";
            case 0xDB: return "[";
            case 0xDC: return "\\\\";
            case 0xDD: return "]";
            case 0xDE: return "'";
        }
        if (vk >= 0x60 && vk <= 0x69) return "小键盘" + (vk - 0x60);
        if (vk >= 0x6A && vk <= 0x6F) return "小键盘" + "*/+-.".Substring(vk - 0x6A, 1);
        return "键" + vk;
    }

    void StartBind()
    {
        binding = true;
        eggBtn.Text = "按下任意键 …";
        eggHint.Text = "现在按一下想绑的键（键盘上任意一个都行，比如 F、H、鼠标侧键之外的都支持）。";
        eggHint.ForeColor = Color.FromArgb(255, 190, 120);
        Activate();
    }

    void BindEgg(int vk)
    {
        try
        {
            UnbindHook();
            C.EggKey = vk;
            C.EggOn = eggSwitch != null ? eggSwitch.On : C.EggOn;
            Save();
            binding = false;
            if (eggBtn != null) eggBtn.Text = "按键 " + KeyName(vk);
            if (C.EggOn) StartHook();
            eggHint.Text = "绑定好了：按 " + KeyName(vk) + " 就会放声音（不吞键，正常打字/检视都不受影响）。";
            eggHint.ForeColor = Color.FromArgb(150, 255, 190);
        }
        catch { }
    }

    void StartHook()
    {
        UnbindHook();
        kbdProc = KbdHook;
        kbdHook = Nat.SetWindowsHookEx(Nat.WH_KEYBOARD_LL, kbdProc, Nat.GetModuleHandle(null), 0);
        if (kbdHook == IntPtr.Zero && eggHint != null)
        {
            eggHint.Text = "挂不上全局按键监听（可能被安全软件拦了），换 F 键试试。";
            eggHint.ForeColor = Color.FromArgb(255, 140, 140);
        }
    }

    void UnbindHook()
    {
        try { if (kbdHook != IntPtr.Zero) Nat.UnhookWindowsHookEx(kbdHook); } catch { }
        kbdHook = IntPtr.Zero;
    }

    IntPtr KbdHook(int nCode, IntPtr wParam, IntPtr lParam)
    {
        try
        {
            if (nCode >= 0 && C.EggOn && !binding &&
                (wParam == (IntPtr)Nat.WM_KEYDOWN || wParam == (IntPtr)Nat.WM_SYSKEYDOWN))
            {
                var info = (Nat.KBDLLHOOKSTRUCT)Marshal.PtrToStructure(lParam, typeof(Nat.KBDLLHOOKSTRUCT));
                if (info.vkCode == C.EggKey)
                {
                    int now = Environment.TickCount;
                    if (now - lastEggTick > 220) { lastEggTick = now; PlayEgg(); }
                }
            }
        }
        catch { }
        // 一律放行：不拦截按键，游戏和输入法照常收到
        return Nat.CallNextHookEx(kbdHook, nCode, wParam, lParam);
    }

    void UnbindEgg()
    {
        UnbindHook();
        C.EggKey = 0;
        if (eggBtn != null) eggBtn.Text = "绑定按键";
    }

'''
s = s[:old_start] + new + s[old_end:]

# ---------- 5) OnKeyDown：任何键都收 ----------
s = s.replace('''        if (binding)
        {
            if (e.KeyCode >= Keys.F1 && e.KeyCode <= Keys.F24) { BindEgg((int)e.KeyCode); e.Handled = true; e.SuppressKeyPress = true; return; }
            eggHint.Text = "这个键不行，只能用 F1~F24（推荐 F6~F12）。";
            eggHint.ForeColor = Color.FromArgb(255, 140, 140);
            e.Handled = true; e.SuppressKeyPress = true;
            return;
        }''',
'''        if (binding)
        {
            // 什么键都收：字母、数字、方向、小键盘、符号……
            if (e.KeyCode != Keys.None) BindEgg((int)e.KeyCode);
            e.Handled = true; e.SuppressKeyPress = true;
            return;
        }''')

# ---------- 6) 说明文字 ----------
s = s.replace('eggHint.Text = "先点「绑定按键」，然后直接按下想用的键（建议 F6~F12）。"\n                            + "绑好后先「试听」，满意再开「启用」。";',
              'eggHint.Text = "绑一个「可以用 Apex 检视的键位」——绑哪个，按它就会放出这段声音。";')
s = s.replace('"先点「绑定按键」，然后直接按下想用的键（建议 F6~F12）。"', '"绑一个「可以用 Apex 检视的键位」——绑哪个，按它就会放出这段声音。"')
s = s.replace('"绑好后先「试听」，满意再开「启用」。"', '"键盘任意键都行；它不吞键，游戏里检视照常可用。"')

p.write_text(s, encoding="utf-8")
print("patched; hook refs", s.count("kbdHook"), "| KeyName cases", s.count('return "←"'))
