// MUMU Cursor — 把 <指针 + 主体 + 连接线 + 吊起物品 变成会甩的桌面指针
// 只替换 IDC_ARROW（正常选择），其它系统光标不动；变身前备份。
// args: --apply --restore --shot <png>

using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Drawing.Text;
using System.IO;
using System.Media;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

// ================================================================ Win32
static class Nat
{
    public const int WS_POPUP = unchecked((int)0x80000000);
    public const int WS_EX_LAYERED = 0x00080000, WS_EX_TRANSPARENT = 0x20;
    public const int WS_EX_TOOLWINDOW = 0x80, WS_EX_TOPMOST = 0x08, WS_EX_NOACTIVATE = 0x08000000;
    public const int ULW_ALPHA = 0x02;
    public const byte AC_SRC_OVER = 0, AC_SRC_ALPHA = 1;
    public const int SPI_SETCURSORS = 0x0057, SPIF_SENDCHANGE = 0x02;
    public const int OCR_NORMAL = 32512;
    public const int VK_LBUTTON = 0x01;
    public const int SM_CXCURSOR = 13, SM_CYCURSOR = 14;
    public const int SWP_NOSIZE = 1, SWP_NOMOVE = 2, SWP_NOACTIVATE = 0x10, SWP_NOOWNERZORDER = 0x200;
    public const int PM_REMOVE = 1;
    public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);

    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int x, y; }
    [StructLayout(LayoutKind.Sequential)] public struct SIZE { public int cx, cy; }
    [StructLayout(LayoutKind.Sequential, Pack = 1)] public struct BLENDFUNCTION { public byte BlendOp, BlendFlags, SourceConstantAlpha, AlphaFormat; }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct WNDCLASSEX { public int cbSize, style; public IntPtr lpfnWndProc; public int cbClsExtra, cbWndExtra; public IntPtr hInstance, hIcon, hCursor, hbrBackground; public string lpszMenuName, lpszClassName; public IntPtr hIconSm; }
    [StructLayout(LayoutKind.Sequential)] public struct MSG { public IntPtr hwnd; public int message; public IntPtr wParam, lParam; public int time; public POINT pt; }
    public delegate IntPtr WndProcDel(IntPtr h, int m, IntPtr w, IntPtr l);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr CreateWindowExW(int ex, string cls, string name, int style, int x, int y, int w, int h, IntPtr parent, IntPtr menu, IntPtr inst, IntPtr param);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr DefWindowProcW(IntPtr h, int m, IntPtr w, IntPtr l);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern ushort RegisterClassExW(ref WNDCLASSEX wc);
    [DllImport("user32.dll")] public static extern bool UpdateLayeredWindow(IntPtr hwnd, IntPtr dst, ref POINT d, ref SIZE s, IntPtr src, ref POINT sp, int key, ref BLENDFUNCTION b, int flags);
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vk);

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
    }
    [DllImport("user32.dll")] public static extern bool PeekMessageW(out MSG msg, IntPtr h, int min, int max, int remove);
    [DllImport("user32.dll")] public static extern bool TranslateMessage(ref MSG msg);
    [DllImport("user32.dll")] public static extern IntPtr DispatchMessageW(ref MSG msg);
    [DllImport("user32.dll")] public static extern IntPtr CreateCursor(IntPtr inst, int x, int y, int w, int h, byte[] and, byte[] xor);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr LoadCursorW(IntPtr inst, IntPtr name);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr LoadImageW(IntPtr inst, string name, int type, int cx, int cy, int flags);
    [DllImport("user32.dll")] public static extern bool SetSystemCursor(IntPtr hcur, int id);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern bool SystemParametersInfoW(int act, int p, IntPtr pv, int win);
    [DllImport("user32.dll")] public static extern bool DestroyWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern IntPtr CopyIcon(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, int flags);
    [DllImport("user32.dll")] public static extern IntPtr GetWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern IntPtr GetTopWindow(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, System.Text.StringBuilder sb, int n);
    [DllImport("user32.dll")] public static extern int GetWindowLongW(IntPtr h, int idx);
    [DllImport("user32.dll")] public static extern int SetWindowLongW(IntPtr h, int idx, int val);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr SetFocus(IntPtr h);
    [DllImport("user32.dll")] public static extern bool GetCursorInfo(ref CURSORINFO pci);
    [DllImport("user32.dll")] public static extern bool GetClipCursor(out RECT rc);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT rc);
    [DllImport("user32.dll")] public static extern IntPtr MonitorFromWindow(IntPtr h, int flags);
    [DllImport("user32.dll")] public static extern bool GetMonitorInfo(IntPtr hMon, ref MONITORINFO mi);
    [DllImport("user32.dll")] public static extern IntPtr GetDesktopWindow();

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    [StructLayout(LayoutKind.Sequential)]
    public struct MONITORINFO
    {
        public int cbSize; public RECT rcMonitor; public RECT rcWork; public int dwFlags;
    }
    [DllImport("user32.dll")] public static extern int ShowCursor(bool show);

    [StructLayout(LayoutKind.Sequential)]
    public struct CURSORINFO { public int cbSize; public int flags; public IntPtr hCursor; public POINT ptScreenPos; }
    public const int CURSOR_SHOWING = 0x1;
    public const int GW_HWNDPREV = 3, GW_HWNDNEXT = 2;
    [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr h);
    [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr h, IntPtr dc);
    [DllImport("gdi32.dll")] public static extern IntPtr CreateCompatibleDC(IntPtr dc);
    [DllImport("gdi32.dll")] public static extern bool DeleteDC(IntPtr dc);
    [DllImport("gdi32.dll")] public static extern IntPtr SelectObject(IntPtr dc, IntPtr o);
    [DllImport("gdi32.dll")] public static extern bool DeleteObject(IntPtr o);
    [DllImport("gdi32.dll")] public static extern IntPtr CreateDIBSection(IntPtr dc, ref BITMAPINFO bmi, int usage, out IntPtr bits, IntPtr sec, int off);

    [StructLayout(LayoutKind.Sequential)] public struct BITMAPINFOHEADER { public int biSize, biWidth, biHeight; public short biPlanes, biBitCount; public int biCompression, biSizeImage, biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant; }
    [StructLayout(LayoutKind.Sequential)] public struct BITMAPINFO { public BITMAPINFOHEADER h; public int c0, c1, c2; }

    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySound(byte[] data, IntPtr mod, int flags);
    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySoundFile(string file, IntPtr mod, int flags);
    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")] public static extern bool PlaySoundBytes(byte[] data, IntPtr mod, int flags);
    [DllImport("winmm.dll")] public static extern int waveOutGetNumDevs();
    public const int SND_ASYNC = 1, SND_NODEFAULT = 2, SND_MEMORY = 4, SND_FILENAME = 0x20000, SND_LOOP = 8, SND_PURGE = 0x40;
    [DllImport("user32.dll")] public static extern bool RegisterHotKey(IntPtr hWnd, int id, int mods, int vk);
    [DllImport("user32.dll")] public static extern bool UnregisterHotKey(IntPtr hWnd, int id);

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
        public static extern IntPtr GetModuleHandle(string lpModuleName);

        [DllImport("user32.dll")]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, IntPtr dwExtraInfo);
}

// ================================================================ 配置
class Cfg
{
    public string PointerShape = "chevron";   // chevron|arrow|cross|ring|diamond|move
    public string PointerColor = "silver";    // silver|gold|neon|ink|bubble
    public string BodyKind = "default";   // default | avatar | custom
    public string ItemKind = "coin";      // coin | custom
    public bool RopeOn = true;
    public int RopeColor = 0;
    public bool RopeGlow = false;
    public bool ClickAnim = true;
    public bool ClickSound = true;
    public string Sfx = "coin";
    public int Volume = 20;
    public int Ver = 2;   // 配置版本：老配置里的音量会被迁移一次
    public string CustomBody = "", CustomItem = "";
    public bool EggOn = false;     // 彩蛋：默认关闭
    public int EggVolume = 20;     // 彩蛋音量 0-100
    public int EggKey = 0;         // 绑定的虚拟键码，0 = 没绑

    static string _dir;
    public static string Dir
    {
        get
        {
            if (_dir != null) return _dir;
            foreach (var d in new string[] {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MUMUCursor"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MUMUCursor"),
                Path.Combine(Path.GetTempPath(), "MUMUCursor") })
            {
                try { Directory.CreateDirectory(d); _dir = d; return d; }
                catch { }
            }
            _dir = Path.GetTempPath();
            return _dir;
        }
    }
    public static string SettingPath { get { return Path.Combine(Dir, "settings.ini"); } }
    public static string BackupDir
    {
        get
        {
            string b = Path.Combine(Dir, "backup");
            try { Directory.CreateDirectory(b); } catch { }
            return b;
        }
    }

    public static Cfg Load()
    {
        var c = new Cfg();
        int ver0 = 0;
        try
        {
            if (File.Exists(SettingPath))
                foreach (var line in File.ReadAllLines(SettingPath))
                {
                    int i = line.IndexOf('=');
                    if (i <= 0) continue;
                    string k = line.Substring(0, i).Trim(), v = line.Substring(i + 1).Trim();
                    switch (k)
                    {
                        case "Pointer":
                            // 老配置只有颜色名：当成「雪佛龙 + 那个颜色」
                            if (Array.IndexOf(new[] { "silver", "gold", "neon", "ink", "bubble" }, v) >= 0) { c.PointerShape = "chevron"; c.PointerColor = v; }
                            else if (Array.IndexOf(new[] { "arrow", "cross", "ring", "diamond", "move" }, v) >= 0) { c.PointerShape = v; }
                            break;
                        case "PointerShape": c.PointerShape = v; break;
                        case "PointerColor": c.PointerColor = v; break;
                        case "BodyKind": c.BodyKind = v; break;
                        case "ItemKind": c.ItemKind = v; break;
                        case "RopeOn": c.RopeOn = v == "1"; break;
                        case "RopeColor": c.RopeColor = int.Parse(v); break;
                        case "RopeGlow": c.RopeGlow = v == "1"; break;
                        case "ClickAnim": c.ClickAnim = v == "1"; break;
                        case "ClickSound": c.ClickSound = v == "1"; break;
                        case "Sfx": c.Sfx = v; break;
                        case "Volume": c.Volume = int.Parse(v); break;
                        case "Ver": c.Ver = int.Parse(v); ver0 = c.Ver; break;
                        case "CustomBody": c.CustomBody = v; break;
                        case "CustomItem": c.CustomItem = v; break;
                        case "EggOn": c.EggOn = v == "1"; break;
                        case "EggKey": c.EggKey = int.Parse(v); break;
                        case "EggVolume": c.EggVolume = int.Parse(v); break;
                    }
                }
        }
        catch { }
        // 老版本的默认音量是 60，这一版开始默认 25：只迁移一次，之后以用户自己的设置为准
        if (c.Ver < 2) { c.Volume = 25; c.Ver = 2; }
        // 老版本里“绑过键但开关存成关闭”的配置，按用户意图视为开启（绑了就是要用）
        if (c.Ver < 3) { if (c.EggKey != 0 && !c.EggOn) c.EggOn = true; c.Ver = 3; }
        // 用户反馈整体音量还是偏大：默认值再降 20%（25 → 20），只迁移一次
        if (c.Ver < 4) { c.Volume = 20; c.EggVolume = 20; c.Ver = 4; }
        // 造型 / 颜色 各留一个兜底，配置写坏了也不至于空白
        if (Array.IndexOf(new[] { "chevron", "arrow", "cross", "ring", "diamond", "move" }, c.PointerShape) < 0) c.PointerShape = "chevron";
        if (Array.IndexOf(new[] { "silver", "gold", "neon", "ink", "bubble" }, c.PointerColor) < 0) c.PointerColor = "silver";
        // 以前误绑过 VK_PROCESSKEY(229)/VK_NONAME(255) 的脏数据，直接清掉
        if (c.EggKey == 229 || c.EggKey == 255 || c.EggKey < 0) c.EggKey = 0;
        if (c.EggKey == 0x10 || c.EggKey == 0x11 || c.EggKey == 0x12 || c.EggKey == 0x5B || c.EggKey == 0x5C) c.EggKey = 0;
        if (c.Ver != ver0) { try { c.Save(); } catch { } }   // 迁移结果立刻落盘
        return c;
    }

    public void Save()
    {
        try
        {
            var lines = new List<string>();
            lines.Add("PointerShape=" + PointerShape);
            lines.Add("PointerColor=" + PointerColor);
            lines.Add("BodyKind=" + BodyKind);
            lines.Add("ItemKind=" + ItemKind);
            lines.Add("RopeOn=" + (RopeOn ? "1" : "0"));
            lines.Add("RopeColor=" + RopeColor);
            lines.Add("RopeGlow=" + (RopeGlow ? "1" : "0"));
            lines.Add("ClickAnim=" + (ClickAnim ? "1" : "0"));
            lines.Add("ClickSound=" + (ClickSound ? "1" : "0"));
            lines.Add("Sfx=" + Sfx);
            lines.Add("Volume=" + Volume);
            lines.Add("Ver=" + Ver);
            lines.Add("CustomBody=" + CustomBody);
            lines.Add("CustomItem=" + CustomItem);
            lines.Add("EggOn=" + (EggOn ? "1" : "0"));
            lines.Add("EggKey=" + EggKey);
            lines.Add("EggVolume=" + EggVolume);
            File.WriteAllLines(SettingPath, lines.ToArray());
        }
        catch { }
    }
}

// ================================================================ 澶栬
class Look
{
    public Bitmap Pointer; public float HotX, HotY;
    public Bitmap Body; public float PivFx = 0.42f, PivFy = 0.965f;
    public Bitmap Item; public int ItemW, ItemH;
    public Color RopeColor = Color.FromArgb(52, 44, 58);
    public bool RopeOn = true, RopeGlow = false;
    public bool ClickAnim = true;
    public bool ClickSound = true;
    public float BodyOffX = 21f, BodyOffY = 17f;

    public Look Clone()
    {
        var l = (Look)MemberwiseClone();
        return l;
    }
}

// ================================================================ 物理 + 渲染
class Pendant
{
    public const double FollowK = 1500, FollowD = 55;
    public const double TiltGain = 1.2e-6, TiltMax = 0.05;
    public const double RopeLen = 66;
    public const int NSEG = 7;
    public const double RopeGravity = 3200, RopeDamp = 0.988;
    public const double Step = 1.0 / 150.0;
    public const int Iterations = 4;
    public const int PAD = 96;

    public Look L;
    public double x, y, vx, vy, pvx, pvy, ax, ay, tilt, tv, tx, ty;
    public bool started, ropeInit;
    public readonly double[] nx = new double[NSEG + 1], ny = new double[NSEG + 1];
    public readonly double[] npx = new double[NSEG + 1], npy = new double[NSEG + 1];
    double acc;
    public double Glow;      // 0..1 点击发光
    public double Pop;       // 0..1 点击弹跳

    public Pendant(Look look) { L = look; }

    public void Reset(double px, double py)
    {
        x = tx = px; y = ty = py; vx = vy = 0; started = true;
        InitRope(px + L.PivFx * L.Body.Width + L.BodyOffX, py + L.PivFy * L.Body.Height + L.BodyOffY);
    }

    public void Pivot(double hx, double hy, out double px, out double py)
    {
        double cosT = Math.Cos(tilt), sinT = Math.Sin(tilt);
        double ox = L.BodyOffX + L.PivFx * L.Body.Width, oy = L.BodyOffY + L.PivFy * L.Body.Height;
        px = hx + ox * cosT - oy * sinT;
        py = hy + ox * sinT + oy * cosT;
    }

    void InitRope(double px, double py)
    {
        double seg = RopeLen / NSEG;
        for (int i = 0; i <= NSEG; i++) { nx[i] = px; ny[i] = py + i * seg; npx[i] = nx[i]; npy[i] = ny[i]; }
        ropeInit = true;
    }

    void RopeStep(double px, double py)
    {
        if (!ropeInit) InitRope(px, py);
        double seg = RopeLen / NSEG;
        for (int i = 1; i <= NSEG; i++)
        {
            double dvx = (nx[i] - npx[i]) * RopeDamp, dvy = (ny[i] - npy[i]) * RopeDamp;
            npx[i] = nx[i]; npy[i] = ny[i];
            nx[i] += dvx; ny[i] += dvy + RopeGravity * Step * Step;
        }
        nx[0] = px; ny[0] = py;
        for (int k = 0; k < Iterations; k++)
        {
            for (int i = 0; i < NSEG; i++)
            {
                double dx = nx[i + 1] - nx[i], dy = ny[i + 1] - ny[i];
                double d = Math.Sqrt(dx * dx + dy * dy);
                if (d < 1e-6) continue;
                double diff = (d - seg) / d * 0.5;
                nx[i] += dx * diff; ny[i] += dy * diff;
                nx[i + 1] -= dx * diff; ny[i + 1] -= dy * diff;
            }
            nx[0] = px; ny[0] = py;
        }
        double ex = nx[NSEG] - nx[0], ey = ny[NSEG] - ny[0];
        double ang = Math.Atan2(ex, ey);
        const double MAX_ANG = 0.80;
        if (Math.Abs(ang) > MAX_ANG)
        {
            double adj = Math.Sign(ang) * (Math.Abs(ang) - MAX_ANG);
            double c = Math.Cos(adj), s = Math.Sin(adj);
            for (int i = 1; i <= NSEG; i++)
            {
                double rx = nx[i] - nx[0], ry = ny[i] - ny[0];
                nx[i] = nx[0] + rx * c - ry * s;
                ny[i] = ny[0] + rx * s + ry * c;
                npx[i] = nx[i] - (nx[i] - npx[i]) * 0.35;
                npy[i] = ny[i] - (ny[i] - npy[i]) * 0.35;
            }
        }
    }

    public void Click()
    {
        for (int i = 1; i <= NSEG; i++) { npx[i] -= 3.2; npy[i] -= 1.6; }
        Glow = 1.0; Pop = 0.5;
    }

    public void Update(double dt)
    {
        acc += dt;
        int guard = 0;
        while (acc >= Step && guard++ < 20)
        {
            acc -= Step;
            pvx = vx; pvy = vy;
            vx += ((tx - x) * FollowK - vx * FollowD) * Step;
            vy += ((ty - y) * FollowK - vy * FollowD) * Step;
            x += vx * Step; y += vy * Step;
            double dax = (vx - pvx) / Step;
            ax += (dax - ax) * Math.Min(1.0, 25 * Step);
            double tgt = Clamp(-ax * TiltGain, -TiltMax, TiltMax);
            tv += (tgt - tilt) * 90 * Step;
            tv *= 1 - 18 * Step;
            tilt += tv * Step;
            double px, py; Pivot(x, y, out px, out py);
            RopeStep(px, py);
        }
        Glow *= Math.Pow(0.006, dt);
        Pop *= Math.Pow(0.0009, dt);
    }

    static double Clamp(double v, double a, double b) { return v < a ? a : (v > b ? b : v); }

    // draw whole pendulum, (ox,oy) = hotspot position on canvas
    public void Draw(Graphics g, float ox, float oy)
    {
        if (L.RopeOn)
        {
            var pts = new PointF[NSEG + 1];
            for (int i = 0; i <= NSEG; i++)
                pts[i] = new PointF((float)(nx[i] - x + ox), (float)(ny[i] - y + oy));
            using (var pen = new Pen(L.RopeColor, 2.4f))
            {
                pen.LineJoin = LineJoin.Round; pen.StartCap = pen.EndCap = LineCap.Round;
                if (L.RopeGlow)
                {
                    for (int pass = 0; pass < 3; pass++)
                        using (var gl = new Pen(Color.FromArgb(26 + pass * 14, L.RopeColor), 7f - pass * 1.6f))
                        {
                            gl.LineJoin = LineJoin.Round; gl.StartCap = gl.EndCap = LineCap.Round;
                            g.DrawLines(gl, pts);
                        }
                }
                g.DrawLines(pen, pts);
            }
        }

        double dx = nx[NSEG] - nx[NSEG - 1], dy = ny[NSEG] - ny[NSEG - 1];
        double ang = Math.Atan2(dy, dx) * 180 / Math.PI - 90;
        double scale = 1 + 0.15 * Pop;
        float ix = (float)(nx[NSEG] - x + ox), iy = (float)(ny[NSEG] - y + oy);

        // 点击：暖色光晕 + 一圈往外扩的亮环
        if (Glow > 0.02)
        {
            float baseR = Math.Max(L.ItemW, L.ItemH);
            float r = baseR * (0.48f + 0.26f * (float)Glow);
            // 三层同心圆叠出柔和光晕（GDI+ 没有真正的模糊，这样最省也最像）
            float cy0 = iy + L.ItemH * 0.30f;
            for (int k = 0; k < 3; k++)
            {
                float rr = r * (1f + 0.20f * k);
                int a = (int)((84 - k * 26) * Glow);
                if (a <= 0) continue;
                using (var br = new SolidBrush(Color.FromArgb(a, 255, 236, 170)))
                    g.FillEllipse(br, ix - rr, cy0 - rr, rr * 2, rr * 2);
            }
            float ringR = baseR * (0.55f + 1.05f * (float)(1 - Glow));
            float cy = iy + L.ItemH * 0.30f;
            using (var pen = new Pen(Color.FromArgb((int)(70 * Glow), 255, 226, 140), 7f))
                g.DrawEllipse(pen, ix - ringR, cy - ringR, ringR * 2, ringR * 2);
            using (var pen = new Pen(Color.FromArgb((int)(220 * Glow), 255, 244, 190), 2.6f))
                g.DrawEllipse(pen, ix - ringR, cy - ringR, ringR * 2, ringR * 2);
        }

        var st = g.Save();
        g.TranslateTransform(ix, iy);
        g.RotateTransform((float)ang);
        g.DrawImage(L.Item, (float)(-L.ItemW * scale / 2), 0f, (float)(L.ItemW * scale), (float)(L.ItemH * scale));
        g.Restore(st);

        g.DrawImage(L.Pointer, ox - L.HotX, oy - L.HotY);

        st = g.Save();
        g.TranslateTransform(ox + L.BodyOffX, oy + L.BodyOffY);
        g.RotateTransform((float)(tilt * 180 / Math.PI));
        g.DrawImage(L.Body, 0f, 0f, L.Body.Width, L.Body.Height);
        g.Restore(st);
    }
}

// ================================================================ 光标切换（只动「正常选择」）
static class CursorSwitch
{
    public static bool Applied;
    static IntPtr snapshot;
    public static string LastLog = "";

    public static string BackupCur { get { return Path.Combine(Cfg.BackupDir, "arrow_backup.cur"); } }
    public static string BackupIni { get { return Path.Combine(Cfg.BackupDir, "cursors.ini"); } }

    public static bool IsBlank(IntPtr h)
    {
        try
        {
            using (var ic = Icon.FromHandle(h))
            using (var b = ic.ToBitmap())
            {
                for (int yy = 0; yy < b.Height; yy++)
                    for (int xx = 0; xx < b.Width; xx++)
                        if (b.GetPixel(xx, yy).A > 12) return false;
            }
        }
        catch { return false; }
        return true;
    }

    static readonly object gate = new object();

    public static void Apply() { lock (gate) ApplyCore(); }

    static void ApplyCore()
    {
        if (Applied) return;
        IntPtr cur = Nat.LoadCursorW(IntPtr.Zero, new IntPtr(Nat.OCR_NORMAL));
        if (cur != IntPtr.Zero && !IsBlank(cur))
        {
            snapshot = Nat.CopyIcon(cur);
            SaveBackup(cur);
        }
        Blank();
        Applied = true;
        SetDirty(true);
        LastLog = "apply: snapshot " + (snapshot != IntPtr.Zero ? "ok" : "none");
    }

    static void Blank()
    {
        var and = new byte[32 * 32 / 8]; var xor = new byte[32 * 32 / 8];
        for (int i = 0; i < and.Length; i++) and[i] = 0xFF;
        IntPtr h = Nat.CreateCursor(IntPtr.Zero, 0, 0, 32, 32, and, xor);
        Nat.SetSystemCursor(h, Nat.OCR_NORMAL);
    }

    static void SaveBackup(IntPtr hcur)
    {
        try
        {
            using (var ic = Icon.FromHandle(hcur))
            using (var bmp = ic.ToBitmap())
                WriteCur(bmp, BackupCur);

            var sb = new System.Text.StringBuilder();
            using (var key = Registry.CurrentUser.OpenSubKey(@"Control Panel\Cursors"))
            {
                if (key != null)
                    foreach (var name in key.GetValueNames())
                    {
                        var v = key.GetValue(name);
                        sb.AppendLine(name + "=" + (v == null ? "" : v.ToString()));
                    }
            }
            File.WriteAllText(BackupIni, sb.ToString());
        }
        catch { }
    }

    // 32bpp .cur：ICONDIR + ICONDIRENTRY + BITMAPINFOHEADER + BGRA + AND mask
    static void WriteCur(Bitmap bmp, string path)
    {
        int w = bmp.Width, h = bmp.Height;
        int maskStride = ((w + 31) / 32) * 4;
        int dataSize = 40 + w * h * 4 + maskStride * h;
        using (var fs = new FileStream(path, FileMode.Create, FileAccess.Write))
        using (var bw = new BinaryWriter(fs))
        {
            bw.Write((short)0); bw.Write((short)2); bw.Write((short)1);
            bw.Write((byte)(w >= 256 ? 0 : w)); bw.Write((byte)(h >= 256 ? 0 : h));
            bw.Write((byte)0); bw.Write((byte)0);
            bw.Write((short)0); bw.Write((short)0);
            bw.Write(dataSize); bw.Write(22);
            bw.Write(40); bw.Write(w); bw.Write(h * 2); bw.Write((short)1); bw.Write((short)32);
            bw.Write(0); bw.Write(w * h * 4); bw.Write(0); bw.Write(0); bw.Write(0); bw.Write(0);
            for (int yy = h - 1; yy >= 0; yy--)
                for (int xx = 0; xx < w; xx++)
                {
                    Color c = bmp.GetPixel(xx, yy);
                    bw.Write(c.B); bw.Write(c.G); bw.Write(c.R); bw.Write(c.A);
                }
            for (int yy = h - 1; yy >= 0; yy--)
            {
                var row = new byte[maskStride];
                for (int xx = 0; xx < w; xx++)
                    if (bmp.GetPixel(xx, yy).A < 8)
                        row[xx / 8] |= (byte)(0x80 >> (xx % 8));
                bw.Write(row);
            }
        }
    }

    // 记录"当前处于变身状态"，进程被强杀后下次启动能自动救回来
    static string FlagPath { get { return Path.Combine(Cfg.Dir, "active.flag"); } }

    public static void SetDirty(bool on)
    {
        // 注册表（主）+ 文件（备份，权限受限时仍可用）
        try
        {
            using (var k = Registry.CurrentUser.CreateSubKey(@"Software\MUMUCursor"))
                if (k != null) k.SetValue("Active", on ? 1 : 0, RegistryValueKind.DWord);
        }
        catch { }
        try
        {
            if (on) File.WriteAllText(FlagPath, "1");
            else if (File.Exists(FlagPath)) File.Delete(FlagPath);
        }
        catch { }
    }

    public static bool IsDirty()
    {
        try
        {
            using (var k = Registry.CurrentUser.OpenSubKey(@"Software\MUMUCursor"))
            {
                if (k != null)
                {
                    object v = k.GetValue("Active");
                    if (v != null && Convert.ToInt32(v) == 1) return true;
                }
            }
        }
        catch { }
        try { return File.Exists(FlagPath); } catch { return false; }
    }

    public static void Restore()
    {
        lock (gate)
        {
            try { RestoreCore(); }
            catch (Exception ex) { LastLog = "restore error: " + ex.Message; }
            finally
            {
                // 无论如何都让 Windows 重载一次方案，保证不会停留在透明光标
                try { Nat.SystemParametersInfoW(Nat.SPI_SETCURSORS, 0, IntPtr.Zero, Nat.SPIF_SENDCHANGE); } catch { }
                Applied = false;
                SetDirty(false);
            }
        }
    }

    static void RestoreCore()
    {
        // 1) 内存快照
        if (snapshot != IntPtr.Zero)
        {
            IntPtr c = Nat.CopyIcon(snapshot);
            if (c != IntPtr.Zero && Nat.SetSystemCursor(c, Nat.OCR_NORMAL))
            {
                LastLog = "restore: snapshot";
                return;
            }
        }
        // 2) backup .cur
        if (File.Exists(BackupCur))
        {
            IntPtr h = Nat.LoadImageW(IntPtr.Zero, BackupCur, 2, 0, 0, 0x10);
            if (h != IntPtr.Zero && Nat.SetSystemCursor(h, Nat.OCR_NORMAL))
            {
                LastLog = "restore: backup .cur";
                return;
            }
        }
        // 3) registry scheme
        try
        {
            if (File.Exists(BackupIni))
                using (var key = Registry.CurrentUser.CreateSubKey(@"Control Panel\Cursors"))
                    foreach (var line in File.ReadAllLines(BackupIni))
                    {
                        int i = line.IndexOf('=');
                        if (i <= 0) continue;
                        key.SetValue(line.Substring(0, i), line.Substring(i + 1));
                    }
        }
        catch { }
        LastLog = "restore: scheme";
    }
}

// ============ Overlay ============
class Overlay
{
    readonly Pendant P;
    Bitmap canvas;
    public IntPtr hwnd;
    IntPtr screenDc, memDc, dib, dibBits;
    public int W, H, PadX, PadY;
    volatile bool running = true;
    public volatile bool HideSystem = true;
    public volatile bool HideReady;
    int topTick;
    volatile bool topBusy;
    long lastTopMs;
    public int TopCalls, TopFails;
    public volatile bool SwitcherUp;
    public volatile bool SysCursorHidden;   // 系统光标不可见（游戏/全屏程序把指针收走了）
    public string HideReason = "";

    // 委托必须有个字段/静态引用拿着，否则被 GC 回收后窗口过程就飞了
    static readonly Nat.WndProcDel WndProcKeepAlive = WndProc;
    static volatile bool topDirty;

    static IntPtr WndProc(IntPtr h, int msg, IntPtr w, IntPtr l)
    {
        // 0x0047 WM_WINDOWPOSCHANGED / 0x001C WM_ACTIVATEAPP / 0x0006 WM_ACTIVATE
        // 我们自己的 z 序被动过、或者别的程序被切到前台，都赶紧把顶层补回来
        if (msg == 0x0047 || msg == 0x001C || msg == 0x0006) topDirty = true;
        return Nat.DefWindowProcW(h, msg, w, l);
    }

    public Overlay(Look l)
    {
        P = new Pendant(l);
        PadX = Pendant.PAD; PadY = 20;
        W = PadX * 2 + 150;
        H = PadY + 160 + (int)Pendant.RopeLen + 90;
        // 注意：窗口在 Run() 里由渲染线程自己创建（见 Create 调用处）
    }

    void Create()
    {
        var wc = new Nat.WNDCLASSEX();
        wc.cbSize = Marshal.SizeOf(typeof(Nat.WNDCLASSEX));
        wc.lpfnWndProc = Marshal.GetFunctionPointerForDelegate(WndProcKeepAlive);
        wc.hInstance = Marshal.GetHINSTANCE(typeof(Overlay).Module);
        wc.lpszClassName = "MUMUCursorWnd";
        Nat.RegisterClassExW(ref wc);
        hwnd = Nat.CreateWindowExW(Nat.WS_EX_LAYERED | Nat.WS_EX_TRANSPARENT | Nat.WS_EX_TOOLWINDOW | Nat.WS_EX_TOPMOST | Nat.WS_EX_NOACTIVATE,
            "MUMUCursorWnd", "MUMU光标", Nat.WS_POPUP, 0, 0, 8, 8, IntPtr.Zero, IntPtr.Zero, wc.hInstance, IntPtr.Zero);
        if (hwnd == IntPtr.Zero) throw new Exception("CreateWindowEx failed");
        Nat.ShowWindow(hwnd, 8);
        KeepTop();
    }

    void Prepare()
    {
        canvas = new Bitmap(W, H, PixelFormat.Format32bppPArgb);
        IntPtr dc = Nat.GetDC(IntPtr.Zero);
        screenDc = Nat.CreateCompatibleDC(dc);
        memDc = Nat.CreateCompatibleDC(dc);
        Nat.ReleaseDC(IntPtr.Zero, dc);
        var bmi = new Nat.BITMAPINFO();
        bmi.h.biSize = Marshal.SizeOf(typeof(Nat.BITMAPINFOHEADER));
        bmi.h.biWidth = W; bmi.h.biHeight = -H; bmi.h.biPlanes = 1; bmi.h.biBitCount = 32;
        dib = Nat.CreateDIBSection(screenDc, ref bmi, 0, out dibBits, IntPtr.Zero, 0);
        Nat.SelectObject(memDc, dib);
    }

    public void Stop()
    {
        running = false; stopped = true; HideSystem = false;
        // 渲染线程可能正卡在某次 UpdateLayeredWindow 里，光靠标志位退不出来，
        // 画面就会“冻”在原地。这里直接从 UI 线程把窗口藏掉，保证点“恢复”立刻消失。
        try { var h = hwnd; if (h != IntPtr.Zero) Nat.ShowWindow(h, 0); } catch { }
    }

    public void SetLook(Look l)
    {
        try { P.L = l; } catch { }
    }
    volatile bool stopped;
    public int Frames;
    public double TUpd, TDraw, TPush, TTop;

    public void Run()
    {
        try
        {
            Create();              // 必须在本线程建窗，后续置顶/销毁才不会跨线程互等
            Prepare();
            var sw = System.Diagnostics.Stopwatch.StartNew();
            double last = 0;
            int fails = 0;
            bool lastClick = false;
            while (running)
            {
                double now = sw.Elapsed.TotalSeconds;
                double dt = Math.Min(0.05, Math.Max(0.001, now - last));
                last = now;

                try
                {
                if (SysCursorHidden)
                {
                    if (hwnd != IntPtr.Zero && Nat.IsWindowVisible(hwnd)) Nat.ShowWindow(hwnd, 0);
                    Thread.Sleep(12);
                    Frames++;
                    continue;
                }
                else if (hwnd != IntPtr.Zero && !Nat.IsWindowVisible(hwnd))
                {
                    Nat.ShowWindow(hwnd, 8);
                    KeepTop();
                }

                Nat.POINT pt; Nat.GetCursorPos(out pt);
                if (!P.started) { P.started = true; P.Reset(pt.x, pt.y); }
                P.tx = pt.x; P.ty = pt.y;

                bool pressed = (Nat.GetAsyncKeyState(Nat.VK_LBUTTON) & 0x8000) != 0;
                if (pressed && !lastClick)
                {
                    if (P.L.ClickAnim) P.Click();
                    if (P.L.ClickSound) Sfx.Play();
                }
                lastClick = pressed;

                var tw = System.Diagnostics.Stopwatch.StartNew();
                P.Update(dt);
                TUpd += tw.Elapsed.TotalMilliseconds; tw.Restart();
                using (var g = Graphics.FromImage(canvas))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    g.Clear(Color.Transparent);
                    P.Draw(g, PadX, PadY);
                }
                TDraw += tw.Elapsed.TotalMilliseconds; tw.Restart();
                bool ok = Push();
                TPush += tw.Elapsed.TotalMilliseconds;

                if (ok) { fails = 0; if (!stopped) HideReady = true; }
                else if (++fails > 90) running = false;
                }
                catch (Exception ex)
                {
                    // 单帧异常（比如素材被别的线程动了）不该整条线程挂掉
                    try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_overlay_err.txt"), "frame " + Frames + ": " + ex.Message + "\n"); } catch { }
                    Thread.Sleep(15);
                }
                Frames++;

                // 本线程就是窗口线程：这里调 SetWindowPos 是"自己给自己发消息"，
                // 同步处理、不会像之前那样跨线程互等。顺手把消息队列抽干。
                int nowMs = Environment.TickCount;
                if (topDirty)
                {
                    topDirty = false;
                    var tw0 = System.Diagnostics.Stopwatch.StartNew();
                    KeepTop();
                    TTop += tw0.Elapsed.TotalMilliseconds;
                }
                if (nowMs - lastTopMs > 300)
                {
                    lastTopMs = nowMs;
                    var tw2 = System.Diagnostics.Stopwatch.StartNew();
                    KeepTop();
                    if ((Nat.GetWindowLongW(hwnd, -20) & 0x8) == 0)
                    {
                        // 顶层样式被抹掉了（个别程序会这么干），重新加回去
                        int ex = Nat.GetWindowLongW(hwnd, -20) | 0x8;
                        Nat.SetWindowLongW(hwnd, -20, ex);
                        Nat.SetWindowPos(hwnd, Nat.HWND_TOPMOST, 0, 0, 0, 0,
                            Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
                    }
                    if (!Nat.IsWindowVisible(hwnd)) Nat.ShowWindow(hwnd, 8);   // 被谁藏了就重新露出来
                    TTop += tw2.Elapsed.TotalMilliseconds;
                }
                Pump();
                if (Frames % 8 == 0) CheckSwitcher();
                if (Frames % 4 == 0) CheckSysCursor();

                if (Frames % 20 == 0)
                {
                    try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hb.txt"), "f=" + Frames + " t=" + now.ToString("F2") + "s\n"); } catch { }
                }
                Thread.Sleep(6);
            }
        }
        catch (Exception ex)
        {
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_overlay_err.txt"), ex.ToString() + "\n"); } catch { }
        }
        finally
        {
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hb.txt"), "loop exit frames=" + Frames + "\n"); } catch { }
            if (hwnd != IntPtr.Zero) { Nat.DestroyWindow(hwnd); hwnd = IntPtr.Zero; }
        }
    }

    /// 把窗口重新顶到 topmost 带最前面。某些程序（Electron 全屏、聊天工具、播放器）
    /// 会把自己也设成 topmost 并排到我们前面，光靠创建时的 WS_EX_TOPMOST 会被压住，
    /// 表现就是"精灵钻到窗口下面去了"。这里每 0.6 秒补一次。
    void KeepTop()
    {
        try
        {
            if (hwnd == IntPtr.Zero) return;
            bool okTop = Nat.SetWindowPos(hwnd, Nat.HWND_TOPMOST, 0, 0, 0, 0,
                Nat.SWP_NOMOVE | Nat.SWP_NOSIZE | Nat.SWP_NOACTIVATE | Nat.SWP_NOOWNERZORDER);
            TopCalls++;
            TopFails += okTop ? 0 : 1;
        }
        catch { }
    }

    /// 抽干本线程的消息队列（WM_WINDOWPOSCHANGING 之类是 SendMessage 过来的，不抽会卡住对面）
    /// Alt+Tab / 任务视图 / 开始菜单这类系统界面在"比 topmost 更高的层"，
    /// 普通程序压不上去（它们由 UIAccess 系统进程绘制）。检测到它们出现就把
    /// 精灵让开、改用系统箭头 —— 至少那颗是真光标，会画在系统界面之上。
    void CheckSwitcher()
    {
        try
        {
            IntPtr fg = Nat.GetForegroundWindow();
            if (fg == IntPtr.Zero) { SwitcherUp = false; return; }
            var sb = new System.Text.StringBuilder(128);
            Nat.GetClassNameW(fg, sb, 128);
            string c = sb.ToString();
            SwitcherUp = c == "XamlExplorerHostIslandWindow" || c == "MultitaskingViewFrame" || c == "TaskSwitcherWnd";
        }
        catch { SwitcherUp = false; }
    }

    /// 游戏（Apex 等）会把系统光标"藏掉"，此时指针位置还停在屏幕中央。
    /// 我们画的是自己的一张图，不知道这件事，就会傻乎乎地在中间显示一个精灵。
    /// GetCursorInfo 的 CURSOR_SHOWING 位正是"当前有没有光标在显示"，用它就能对齐。
    public int hiddenStreak;
    bool hsFull, hsTiny;

    /// 这个窗口是不是"铺满显示器、且没有标题栏"的全屏窗口（游戏无边框全屏的典型样子）
    public bool LooksFullscreen(IntPtr h)
    {
        try
        {
            if (h == IntPtr.Zero || h == hwnd || h == Nat.GetDesktopWindow()) return false;
            Nat.RECT r;
            if (!Nat.GetWindowRect(h, out r)) return false;
            var mi = new Nat.MONITORINFO();
            mi.cbSize = Marshal.SizeOf(typeof(Nat.MONITORINFO));
            if (!Nat.GetMonitorInfo(Nat.MonitorFromWindow(h, 2), ref mi)) return false;
            var m = mi.rcMonitor;
            bool cover = Math.Abs(r.Left - m.Left) <= 2 && Math.Abs(r.Top - m.Top) <= 2
                      && Math.Abs(r.Right - m.Right) <= 2 && Math.Abs(r.Bottom - m.Bottom) <= 2;
            long st = Nat.GetWindowLongW(h, -16);
            bool noCaption = (st & 0x00C00000L) == 0;      // 没有标题栏（WS_CAPTION = 0x00C00000）
            return cover && noCaption;
        }
        catch { return false; }
    }

    /// 判断"现在这颗指针是不是被别的程序接管了"：
    /// ① CURSOR_SHOWING 为 0（有的程序会真的把光标关掉）
    /// ② 前台是一个铺满显示器的无边框窗口（游戏无边框全屏 / 全屏视频）
    /// ③ 指针被 ClipCursor 锁在一个很小的矩形里（游戏锁鼠标）
    void CheckSysCursor()
    {
        try
        {
            var ci = new Nat.CURSORINFO();
            ci.cbSize = Marshal.SizeOf(typeof(Nat.CURSORINFO));
            bool shown = Nat.GetCursorInfo(ref ci) && (ci.flags & Nat.CURSOR_SHOWING) != 0;

            bool full = LooksFullscreen(Nat.GetForegroundWindow());
            bool tiny = false;

            Nat.RECT clip;
            if (Nat.GetClipCursor(out clip))
                tiny = (clip.Right - clip.Left) <= 16 && (clip.Bottom - clip.Top) <= 16;

            if (shown && !full && !tiny) { hiddenStreak = 0; SysCursorHidden = false; hsFull = hsTiny = false; return; }

            if (hiddenStreak < 3) hiddenStreak++;
            if (hiddenStreak >= 3)
            {
                SysCursorHidden = true;
                if (!hsFull && !hsTiny)
                {
                    HideReason = !shown ? "cursor-hidden" : full ? "fullscreen" : "clip";
                    Program.Trace("hide sprite: " + HideReason);
                }
                hsFull = full; hsTiny = tiny;
            }
        }
        catch { hiddenStreak = 0; SysCursorHidden = false; }
    }

    void Pump()
    {
        try
        {
            Nat.MSG m;
            int n = 0;
            while (Nat.PeekMessageW(out m, IntPtr.Zero, 0, 0, Nat.PM_REMOVE) && n++ < 64)
            {
                Nat.TranslateMessage(ref m);
                Nat.DispatchMessageW(ref m);
            }
        }
        catch { }
    }

    bool Push()
    {
        var rect = new Rectangle(0, 0, W, H);
        var data = canvas.LockBits(rect, ImageLockMode.ReadOnly, PixelFormat.Format32bppPArgb);
        try
        {
            int row = W * 4;
            var buf = new byte[row];
            for (int yy = 0; yy < H; yy++)
            {
                Marshal.Copy(IntPtr.Add(data.Scan0, yy * data.Stride), buf, 0, row);
                Marshal.Copy(buf, 0, IntPtr.Add(dibBits, yy * row), row);
            }
        }
        finally { canvas.UnlockBits(data); }

        var blend = new Nat.BLENDFUNCTION { BlendOp = Nat.AC_SRC_OVER, BlendFlags = 0, SourceConstantAlpha = 255, AlphaFormat = Nat.AC_SRC_ALPHA };
        var dst = new Nat.POINT { x = (int)Math.Round(P.x) - PadX, y = (int)Math.Round(P.y) - PadY };
        var src = new Nat.POINT();
        var size = new Nat.SIZE { cx = W, cy = H };
        return Nat.UpdateLayeredWindow(hwnd, IntPtr.Zero, ref dst, ref size, memDc, ref src, 0, ref blend, Nat.ULW_ALPHA);
    }
}

// ================================================================ 音效
static class Sfx
{
    static byte[] raw;
    static byte[] scaled;
    static int vol = 20;
    static string name = "coin";
    static readonly Dictionary<string, byte[]> cache = new Dictionary<string, byte[]>();

    public static void Set(string sfx, int volume)
    {
        name = sfx; vol = volume;
        string key = sfx + "@" + volume;
        if (cache.TryGetValue(key, out scaled) && scaled != null) return;
        if (raw == null || !cache.ContainsKey(sfx))
        {
            var asm = Assembly.GetExecutingAssembly();
            foreach (var n in asm.GetManifestResourceNames())
                if (n.EndsWith("sfx_" + sfx + ".wav", StringComparison.OrdinalIgnoreCase))
                {
                    using (var s = asm.GetManifestResourceStream(n))
                    using (var ms = new MemoryStream())
                    {
                        s.CopyTo(ms);
                        raw = ms.ToArray();
                    }
                    break;
                }
        }
        if (raw == null) { scaled = null; return; }
        scaled = Scale(raw, volume / 100.0);
        cache[key] = scaled;
    }

    static byte[] Scale(byte[] src, double gain)
    {
        if (Math.Abs(gain - 1) < 0.01) return src;
        var dst = (byte[])src.Clone();
        for (int i = 44; i + 1 < dst.Length; i += 2)
        {
            short s = (short)(dst[i] | (dst[i + 1] << 8));
            s = (short)Math.Max(-32768, Math.Min(32767, s * gain));
            dst[i] = (byte)(s & 0xFF); dst[i + 1] = (byte)((s >> 8) & 0xFF);
        }
        return dst;
    }

    static byte[] playing;   // 异步播放期间必须留住，别让 GC 回收

    static byte[] scalpBuf;
    static int scalpVol = -1, scalpLen = -1;

    public static bool PlayWavScaled(byte[] wav, int volume, bool loop)
    {
        try
        {
            if (volume < 0) volume = 0;
            if (volume > 100) volume = 100;
            if (volume >= 100) return PlayWav(wav, loop);
            if (scalpBuf == null || scalpVol != volume || scalpLen != wav.Length)
            {
                // 日志里记一下缩放后的峰值，方便确认音量真的生效了
            }
            {
                scalpBuf = ScaleWav(wav, volume, out dataOff);
                scalpVol = volume;
                scalpLen = wav.Length;
            }
            int peak = 0;
            for (int i = dataOff; i + 1 < scalpBuf.Length; i += 2)
            {
                int v2 = Math.Abs((int)(short)(scalpBuf[i] | (scalpBuf[i + 1] << 8)));
                if (v2 > peak) peak = v2;
            }
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " scaled vol=" + volume + " peak=" + peak + "\n"); } catch { }
            return PlayWav(scalpBuf, loop);
        }
        catch { return false; }
    }

    // 16bit PCM：直接按比例缩放采样点（PlaySound 本身没有音量参数）
    static int dataOff = 44;

    static byte[] ScaleWav(byte[] wav, int volume, out int offOut)
    {
        var b = (byte[])wav.Clone();
        offOut = 44;
        if (b.Length < 44) return b;
        int off = 44;
        try
        {
            int i = 12;
            while (i + 8 <= b.Length)
            {
                string id = "" + (char)b[i] + (char)b[i + 1] + (char)b[i + 2] + (char)b[i + 3];
                int sz = BitConverter.ToInt32(b, i + 4);
                if (id == "data") { off = i + 8; break; }
                if (sz <= 0) break;
                i += 8 + sz + (sz & 1);
            }
        }
        catch { }
        offOut = off;
        double f = volume / 100.0;
        for (int i = off; i + 1 < b.Length; i += 2)
        {
            short sv = (short)(b[i] | (b[i + 1] << 8));
            int v = (int)(sv * f);
            if (v > 32767) v = 32767;
            if (v < -32768) v = -32768;
            b[i] = (byte)(v & 0xFF);
            b[i + 1] = (byte)((v >> 8) & 0xFF);
        }
        return b;
    }

    public static bool PlayWav(byte[] data, bool loop)
    {
        try
        {
            if (data == null || data.Length < 44) return false;
            playing = data;
            int flags = Nat.SND_MEMORY | Nat.SND_ASYNC | Nat.SND_NODEFAULT | (loop ? Nat.SND_LOOP : 0);
            bool ok = Nat.PlaySoundBytes(data, IntPtr.Zero, flags);
            int err = Marshal.GetLastWin32Error();
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " playwav bytes=" + data.Length + " ok=" + ok + " err=" + err + " devs=" + Nat.waveOutGetNumDevs() + "\n"); } catch { }
            return ok;
        }
        catch (Exception ex)
        {
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), "playwav ex " + ex.Message + "\n"); } catch { }
            return false;
        }
    }

    public static void PlayFile(string path, bool loop)
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
    {
        try
        {
            var d = scaled;
            if (d == null) return;
            Nat.PlaySound(d, IntPtr.Zero, Nat.SND_MEMORY | Nat.SND_ASYNC | Nat.SND_NODEFAULT);
        }
        catch { }
    }
}

// ================================================================ 素材
static class Art
{
    static readonly Dictionary<string, Bitmap> cache = new Dictionary<string, Bitmap>();

    public static Bitmap Res(string suffix)
    {
        // 每次都返回一份独立副本：同一个 Bitmap 被渲染线程和 UI 线程同时用，
        // GDI+ 会抛 “对象当前正在其他地方使用”（InvalidOperationException）。
        Bitmap b;
        if (cache.TryGetValue(suffix, out b)) return new Bitmap(b);
        var asm = Assembly.GetExecutingAssembly();
        foreach (var n in asm.GetManifestResourceNames())
            if (n.EndsWith(suffix, StringComparison.OrdinalIgnoreCase))
                using (var s = asm.GetManifestResourceStream(n))
                using (var tmp = Image.FromStream(s))
                {
                    b = new Bitmap(tmp);
                    cache[suffix] = b;
                    return new Bitmap(b);
                }
        throw new Exception("missing " + suffix);
    }

    public static Bitmap LoadFile(string path, int targetH)
    {
        using (var tmp = Image.FromFile(path))
        {
            var src = new Bitmap(tmp);
            int h = targetH, w = Math.Max(1, (int)Math.Round(src.Width * (double)targetH / src.Height));
            var dst = new Bitmap(w, h, PixelFormat.Format32bppArgb);
            using (var g = Graphics.FromImage(dst))
            {
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.DrawImage(src, 0, 0, w, h);
            }
            return dst;
        }
    }

    public static Bitmap Resized(Bitmap src, int targetH)
    {
        int w = Math.Max(1, (int)Math.Round(src.Width * (double)targetH / src.Height));
        var dst = new Bitmap(w, targetH, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(dst))
        {
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.DrawImage(src, 0, 0, w, targetH);
        }
        return dst;
    }

    public static Look Build(Cfg c)
    {
        var l = new Look();
        l.Pointer = Res("pointer_" + c.PointerShape + "_" + c.PointerColor + ".png");
        if (c.PointerShape == "chevron") { l.HotX = 10f; l.HotY = 10f; }
        else if (c.PointerShape == "arrow") { l.HotX = 9f; l.HotY = 6f; }
        else { l.HotX = 21.5f; l.HotY = 21.5f; }   // 十字 / 圆环 / 菱形 / 四向：热点在正中

        if (c.BodyKind == "avatar") l.Body = Resized(Res("body_avatar.png"), 110);
        else if (c.BodyKind == "custom" && File.Exists(c.CustomBody)) l.Body = LoadFile(c.CustomBody, 110);
        else l.Body = Res("body_default.png");

        if (c.BodyKind == "default") { l.PivFx = 0.42f; l.PivFy = 0.965f; }
        else { l.PivFx = 0.5f; l.PivFy = 0.985f; }

        // 不管主体多大，绳子都从同一个点吊下来
        l.BodyOffX = 62.58f - l.PivFx * l.Body.Width;
        l.BodyOffY = 113.5f - l.PivFy * l.Body.Height;

        if (c.ItemKind == "custom" && File.Exists(c.CustomItem)) l.Item = LoadFile(c.CustomItem, 63);
        else l.Item = Res("item_coin.png");
        l.ItemW = l.Item.Width; l.ItemH = l.Item.Height;

        Color[] palette = {
            Color.FromArgb(52, 44, 58), Color.FromArgb(240, 240, 245), Color.FromArgb(255, 120, 170),
            Color.FromArgb(255, 190, 90), Color.FromArgb(110, 220, 255), Color.FromArgb(150, 255, 180)
        };
        l.RopeColor = palette[Math.Max(0, Math.Min(palette.Length - 1, c.RopeColor))];
        l.RopeOn = c.RopeOn; l.RopeGlow = c.RopeGlow; l.ClickAnim = c.ClickAnim; l.ClickSound = c.ClickSound;
        return l;
    }
}

// ================================================================ 自绘控件
class Card : Panel
{
    public int Radius = 16;
    public Color Fill = Color.FromArgb(30, 29, 38);
    public Color Line = Color.FromArgb(46, 44, 56);
    public Card() { SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint, true); }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        using (var p = Round(new Rectangle(0, 0, Width - 1, Height - 1), Radius))
        using (var b = new SolidBrush(Fill))
        using (var pen = new Pen(Line))
        { g.FillPath(b, p); g.DrawPath(pen, p); }
    }
    public static GraphicsPath Round(Rectangle r, int rad)
    {
        int d = rad * 2;
        var p = new GraphicsPath();
        p.AddArc(r.X, r.Y, d, d, 180, 90);
        p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
        p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
        p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
        p.CloseFigure();
        return p;
    }
}

class Btn : Control
{
    public bool Primary = true, Hover, Down;
    public Color C1 = Color.FromArgb(255, 96, 150), C2 = Color.FromArgb(255, 178, 96);
    public string Sub = "";
    public Btn()
    {
        SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint, true);
        Cursor = Cursors.Hand;
    }
    protected override void OnMouseEnter(EventArgs e) { Hover = true; Invalidate(); base.OnMouseEnter(e); }
    protected override void OnMouseLeave(EventArgs e) { Hover = false; Down = false; Invalidate(); base.OnMouseLeave(e); }
    protected override void OnMouseDown(MouseEventArgs e) { Down = true; Invalidate(); base.OnMouseDown(e); }
    protected override void OnMouseUp(MouseEventArgs e) { Down = false; Invalidate(); base.OnMouseUp(e); }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        var r = new Rectangle(1, 1, Width - 3, Height - 3);
        using (var path = Card.Round(r, 14))
        {
            if (Primary)
            {
                using (var b = new LinearGradientBrush(r, Down ? C2 : C1, Down ? C1 : C2, 12f))
                    g.FillPath(b, path);
                if (Hover)
                    using (var hi = new SolidBrush(Color.FromArgb(26, 255, 255, 255)))
                        g.FillPath(hi, path);
            }
            else
            {
                using (var b = new SolidBrush(Hover ? Color.FromArgb(44, 42, 54) : Color.FromArgb(34, 33, 42)))
                    g.FillPath(b, path);
                using (var pen = new Pen(Color.FromArgb(72, 70, 86)))
                    g.DrawPath(pen, path);
            }
        }
        using (var f = new Font("Microsoft YaHei UI", Sub.Length > 0 ? 12f : 11f, FontStyle.Bold))
        using (var sf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
        {
            var col = Primary ? Color.White : Color.FromArgb(236, 234, 244);
            var rect = new RectangleF(0, Sub.Length > 0 ? -8 : 0, Width, Height);
            g.DrawString(Text, f, new SolidBrush(col), rect, sf);
            if (Sub.Length > 0)
                using (var f2 = new Font("Microsoft YaHei UI", 7.5f))
                    g.DrawString(Sub, f2, new SolidBrush(Color.FromArgb(200, col)), new RectangleF(0, 10, Width, Height), sf);
        }
    }
}

class Thumb : Control
{
    public Bitmap Pic; public bool Selected, Hover, Upload; public int Pad = 8;
    public Thumb() { SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint, true); Cursor = Cursors.Hand; }
    protected override void OnMouseEnter(EventArgs e) { Hover = true; Invalidate(); base.OnMouseEnter(e); }
    protected override void OnMouseLeave(EventArgs e) { Hover = false; Invalidate(); base.OnMouseLeave(e); }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        var r = new Rectangle(1, 1, Width - 3, Height - 3);
        using (var p = Card.Round(r, 12))
        using (var b = new SolidBrush(Selected ? Color.FromArgb(52, 44, 64) : (Hover ? Color.FromArgb(40, 39, 50) : Color.FromArgb(34, 33, 42))))
            g.FillPath(b, p);
        if (Selected)
            using (var p = Card.Round(r, 12))
            using (var pen = new Pen(Color.FromArgb(255, 128, 170), 2f))
                g.DrawPath(pen, p);

        if (Upload && Pic == null)
        {
            // 虚线框 + 向上箭头，下面写“本地上传”
            var box = new Rectangle(Pad + 6, Pad + 2, Width - (Pad + 6) * 2, Height - 34 - Pad);
            using (var pen = new Pen(Color.FromArgb(Hover ? 200 : 150, 255, 255, 255), 1.3f))
            {
                pen.DashStyle = DashStyle.Dash;
                using (var p = Card.Round(box, 10)) g.DrawPath(pen, p);
            }
            float cx = box.X + box.Width / 2f, cy = box.Y + box.Height / 2f;
            float s = Math.Min(box.Width, box.Height) * 0.26f;
            using (var pen = new Pen(Selected ? Color.FromArgb(255, 190, 214) : Color.FromArgb(215, 210, 226), 2.2f))
            {
                pen.StartCap = LineCap.Round; pen.EndCap = LineCap.Round;
                g.DrawLine(pen, cx, cy + s * 0.55f, cx, cy - s * 0.55f);           // 竖杆
                g.DrawLines(pen, new[] {                                   // 箭头
                    new PointF(cx - s * 0.55f, cy - s * 0.05f),
                    new PointF(cx, cy - s * 0.62f),
                    new PointF(cx + s * 0.55f, cy - s * 0.05f) });
            }
        }
        else if (Pic != null)
        {
            int maxW = Width - Pad * 2, maxH = Height - Pad * 2 - 16;
            float s = Math.Min((float)maxW / Pic.Width, (float)maxH / Pic.Height);
            int w = Math.Max(1, (int)(Pic.Width * s)), h = Math.Max(1, (int)(Pic.Height * s));
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.DrawImage(Pic, (Width - w) / 2, Pad, w, h);
        }
        using (var f = new Font("Microsoft YaHei UI", 7.5f))
        using (var sf = new StringFormat { Alignment = StringAlignment.Center })
            g.DrawString(Text, f, new SolidBrush(Color.FromArgb(190, Selected ? Color.White : Color.FromArgb(200, 196, 210))),
                new RectangleF(0, Height - 18, Width, 16), sf);
    }
}

class Swatch : Control
{
    public Color Col; public bool Selected, Hover;
    public Swatch() { SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint, true); Cursor = Cursors.Hand; }
    protected override void OnMouseEnter(EventArgs e) { Hover = true; Invalidate(); base.OnMouseEnter(e); }
    protected override void OnMouseLeave(EventArgs e) { Hover = false; Invalidate(); base.OnMouseLeave(e); }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        int s = Math.Min(Width, Height) - 10;
        var r = new Rectangle((Width - s) / 2, (Height - s) / 2, s, s);
        using (var b = new SolidBrush(Col)) g.FillEllipse(b, r);
        using (var pen = new Pen(Selected ? Color.White : Color.FromArgb(70, 68, 84), Selected ? 2.5f : 1.5f))
            g.DrawEllipse(pen, r);
    }
}

class Switch : Control
{
    public bool On = true; public bool Hover;
    public Switch() { SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint, true); Cursor = Cursors.Hand; }
    protected override void OnMouseEnter(EventArgs e) { Hover = true; Invalidate(); base.OnMouseEnter(e); }
    protected override void OnMouseLeave(EventArgs e) { Hover = false; Invalidate(); base.OnMouseLeave(e); }
    protected override void OnClick(EventArgs e) { On = !On; Invalidate(); base.OnClick(e); }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        int h = 22, w = 42, y = (Height - h) / 2, x = Width - w - 4;
        using (var p = Card.Round(new Rectangle(x, y, w, h), 11))
        using (var b = new LinearGradientBrush(new Rectangle(x, y, w, h),
            On ? Color.FromArgb(255, 110, 160) : Color.FromArgb(58, 56, 70),
            On ? Color.FromArgb(255, 170, 110) : Color.FromArgb(48, 47, 58), 0f))
            g.FillPath(b, p);
        int k = 16, kx = On ? x + w - k - 3 : x + 3;
        using (var b = new SolidBrush(Color.FromArgb(255, 255, 255))) g.FillEllipse(b, kx, y + 3, k, k);
        using (var f = new Font("Microsoft YaHei UI", 8.5f))
            g.DrawString(Text, f, new SolidBrush(Color.FromArgb(210, 206, 220)), 2, (Height - 15) / 2f);
    }
}

class Slider : Control
{
    public int Min = 0, Max = 100, Value = 60; public bool Down;
    public Slider() { SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint, true); }
    public event EventHandler Changed;
    protected override void OnMouseDown(MouseEventArgs e) { Down = true; SetFromX(e.X); base.OnMouseDown(e); }
    protected override void OnMouseMove(MouseEventArgs e) { if (Down) SetFromX(e.X); base.OnMouseMove(e); }
    protected override void OnMouseUp(MouseEventArgs e) { Down = false; base.OnMouseUp(e); }
    void SetFromX(int x)
    {
        float t = Math.Max(0f, Math.Min(1f, (x - 10f) / Math.Max(1, Width - 68)));
        int v = (int)Math.Round(Min + t * (Max - Min));
        if (v != Value) { Value = v; Invalidate(); if (Changed != null) Changed(this, EventArgs.Empty); }
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        int y = Height / 2;
        float t = (Value - Min) / (float)Math.Max(1, Max - Min);
        using (var pen = new Pen(Color.FromArgb(58, 56, 70), 4f)) g.DrawLine(pen, 10, y, Width - 58, y);
        using (var pen = new Pen(Color.FromArgb(255, 128, 170), 4f)) g.DrawLine(pen, 10, y, 10 + (Width - 68) * t, y);
        int cx = (int)(10 + (Width - 68) * t);
        using (var b = new SolidBrush(Color.White)) g.FillEllipse(b, cx - 6, y - 6, 12, 12);
        using (var f = new Font("Microsoft YaHei UI", 8f))
        using (var sb = new SolidBrush(Color.FromArgb(200, 196, 214)))
            g.DrawString(Value + "%", f, sb, Width - 44, 4);
    }
}

// ================================================================ 主窗口
class MainForm : Form
{
    public Cfg C = Cfg.Load();
    PreviewPanel preview;
    Overlay overlay; Thread overlayThread; System.Windows.Forms.Timer hideTimer;
    Label status, hint;
    Btn applyBtn, restoreBtn;
    Card leftCard, shell;
    Panel settings;
    public int NeedH = 620;
    public Panel Settings { get { return settings; } }
    List<Thumb> pointerThumbs = new List<Thumb>();
    List<Thumb> colorThumbs = new List<Thumb>();
    Switch eggSwitch; Btn eggBtn, eggTest; Label eggHint;
    bool binding;   // 正在等用户按键盘
    public bool AutoApply;
    public int AutoRestoreSecs;   // >0 时自动“点一下恢复”，用于自测
    public bool EggTry;           // 自测：绑 F9 并播一次彩蛋
    public bool EggBindTest;
    public bool EggImeTest;
    System.Windows.Forms.Timer fsTimer;
    public bool FsTest;          // 自测：造一个无边框全屏前台窗口，验证精灵会不会让开
    public bool TopProbe;         // 自测：建一个"抢 topmost"的窗口，看覆盖层能不能压回去       // 自测：喂一个 VK_PROCESSKEY(229)，确认不会被绑上      // 自测：开关关着的情况下绑键，验证会自动开启
    public bool StressGlow;       // 自测：变身后反复切“发光线”
    public string EggTestKey;     // 自测：绑这个键，等 6 秒看有没有放声音
    List<Thumb> bodyThumbs = new List<Thumb>();
    List<Thumb> itemThumbs = new List<Thumb>();
    Switch ropeSwitch, glowSwitch, clickSwitch, soundSwitch;
    Slider vol;
    List<Swatch> swatches = new List<Swatch>();
    List<Btn> sfxBtns = new List<Btn>();
    int scrollY;

    public MainForm()
    {
        Text = "MUMU 光标";
        try
        {
            // 图标只走 exe 的 win32 资源，避免在托管资源里再存一份（省 150KB）
            using (var ic = Icon.ExtractAssociatedIcon(Application.ExecutablePath))
                if (ic != null) Icon = (Icon)ic.Clone();
        }
        catch { }
        ClientSize = new Size(1000, 760);
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(21, 20, 26);
        FormBorderStyle = FormBorderStyle.FixedSingle;
        MaximizeBox = false;
        DoubleBuffered = true;
        Font = new Font("Microsoft YaHei UI", 9f);

        Guard.Emergency = () =>
        {
            try { if (overlay != null) { overlay.Stop(); overlay = null; } } catch { }
            try { CursorSwitch.Restore(); } catch { }
            try { if (watchdog != null) watchdog.Stop(); } catch { }
            try { if (status != null) { status.Text = "已暂停"; applyBtn.Enabled = true; applyBtn.Text = "重新变身为 MUMU 光标"; } } catch { }
        };

        BuildHeader();
        BuildLeft();
        BuildRight();

        // 右栏内容有多高，窗口就有多高（放不下才滚动，尽量不出现滚动条）
        int want = 96 + NeedH + 26;
        int maxH = Screen.PrimaryScreen.WorkingArea.Height - 60;
        int h = Math.Max(700, Math.Min(want, maxH));
        ClientSize = new Size(1000, h);
        if (h < want)
        {
            int room = h - 96 - 26;
            shell.Size = new Size(438, room);
            settings.Size = new Size(434, room - 4);
            settings.AutoScroll = true;
        }
        LayoutLeft();

        RefreshStatus();
        Sfx.Set(C.Sfx, C.Volume);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        using (var b = new LinearGradientBrush(new Rectangle(0, 0, Width, 140),
            Color.FromArgb(34, 26, 44), Color.FromArgb(21, 20, 26), 90f))
            e.Graphics.FillRectangle(b, 0, 0, Width, 140);
        using (var b = new SolidBrush(Color.FromArgb(26, 24, 32)))
            e.Graphics.FillRectangle(b, 0, 140, Width, Height - 140);
    }

    void BuildHeader()
    {
        var t = new Label { Text = "MUMU 光标", ForeColor = Color.FromArgb(250, 246, 255), Font = new Font("Microsoft YaHei UI", 20f, FontStyle.Bold), AutoSize = true, Location = new Point(28, 22), BackColor = Color.Transparent };
        var s = new Label { Text = "小指针 · 主体 · 连接线 · 吊起物品 —— 一只会甩的桌面指针", ForeColor = Color.FromArgb(168, 162, 182), Font = new Font("Microsoft YaHei UI", 9f), AutoSize = true, Location = new Point(30, 60), BackColor = Color.Transparent };
        Controls.Add(t); Controls.Add(s);

        status = new Label
        {
            Text = "未变身",
            ForeColor = Color.FromArgb(255, 190, 120),
            Font = new Font("Microsoft YaHei UI", 9f, FontStyle.Bold),
            AutoSize = false,
            TextAlign = ContentAlignment.MiddleCenter,
            Size = new Size(96, 30),
            Location = new Point(ClientSize.Width - 130, 30),
            BackColor = Color.FromArgb(44, 38, 54)
        };
        Controls.Add(status);
    }

    void BuildLeft()
    {
        leftCard = new Card { Location = new Point(28, 96), Size = new Size(470, 470) };
        Controls.Add(leftCard);

        preview = new PreviewPanel(C) { Location = new Point(12, 12), Size = new Size(446, 446), BackColor = Color.Transparent };
        leftCard.Controls.Add(preview);

        hint = new Label
        {
            Text = "把鼠标移到上面甩一甩，看看手感",
            ForeColor = Color.FromArgb(120, 116, 134),
            Font = new Font("Microsoft YaHei UI", 8.5f),
            AutoSize = true,
            BackColor = Color.Transparent,
            Location = new Point(30, 572)
        };
        Controls.Add(hint);

        applyBtn = new Btn { Text = "变身为 MUMU 光标", Sub = "只换普通箭头，其它光标不动", Location = new Point(28, 598), Size = new Size(470, 60) };
        applyBtn.Click += (a, b) => Apply();
        Controls.Add(applyBtn);

        restoreBtn = new Btn { Text = "恢复系统光标", Sub = "装回你变身前的那一只", Primary = false, Location = new Point(28, 666), Size = new Size(470, 50) };
        restoreBtn.Click += (a, b) => Restore();
        Controls.Add(restoreBtn);
    }

    // 窗口高度定了以后，左列（预览 + 两个大按钮）贴着底部排
    void LayoutLeft()
    {
        int btnTop = ClientSize.Height - 28 - 118;
        int cardH = btnTop - 12 - 96;
        if (cardH < 320) cardH = 320;
        leftCard.Size = new Size(470, cardH);
        preview.Size = new Size(470 - 24, cardH - 24);
        hint.Top = btnTop - 26;
        applyBtn.Location = new Point(28, btnTop);
        restoreBtn.Location = new Point(28, btnTop + 68);
    }

    void Section(int y, string title, string sub)
    {
        var l = new Label { Text = title, ForeColor = Color.FromArgb(240, 236, 250), Font = new Font("Microsoft YaHei UI", 10.5f, FontStyle.Bold), AutoSize = true, Location = new Point(16, y - 2), BackColor = Color.Transparent };
        settings.Controls.Add(l);
        if (!string.IsNullOrEmpty(sub))
        {
            // 副标题跟标题同一行，省掉一行高度（原来会和下面的卡片/开关重叠）
            int w = TextRenderer.MeasureText(title, l.Font).Width;
            var s = new Label { Text = sub, ForeColor = Color.FromArgb(126, 122, 142), Font = new Font("Microsoft YaHei UI", 8f), AutoSize = true, Location = new Point(16 + w + 12, y + 7), BackColor = Color.Transparent };
            settings.Controls.Add(s);
        }
    }

    void BuildRight()
    {
        shell = new Card { Location = new Point(514, 96), Size = new Size(438, 624) };
        Controls.Add(shell);

        settings = new Panel { Location = new Point(2, 2), Size = new Size(434, 620), AutoScroll = false, BackColor = Color.FromArgb(30, 29, 38) };
        shell.Controls.Add(settings);

        int y = 14;
        // ---- ① 小指针 = 造型 + 颜色（两行，共用一个小标题）
        Section(y, "① 小指针", "先挑造型，再挑颜色"); y += 30;
        var rowTag = new Label { Text = "造型", ForeColor = Color.FromArgb(150, 146, 164), Font = new Font("Microsoft YaHei UI", 8f), AutoSize = true, Location = new Point(16, y + 20), BackColor = Color.Transparent };
        settings.Controls.Add(rowTag);

        var shapeNames = new[] { new[] { "chevron", "雪佛龙" }, new[] { "arrow", "箭头" }, new[] { "cross", "十字" }, new[] { "ring", "圆环" }, new[] { "diamond", "菱形" }, new[] { "move", "四向" } };
        for (int i = 0; i < shapeNames.Length; i++)
        {
            var th = new Thumb { Pic = Art.Res("pointer_" + shapeNames[i][0] + "_" + C.PointerColor + ".png"), Text = shapeNames[i][1], Location = new Point(52 + i * 64, y), Size = new Size(60, 56), Selected = C.PointerShape == shapeNames[i][0] };
            string key = shapeNames[i][0];
            th.Click += (a, b) => { C.PointerShape = key; RefreshThumbs(); Save(); };
            pointerThumbs.Add(th); settings.Controls.Add(th);
        }
        y += 62;

        var colTag = new Label { Text = "颜色", ForeColor = Color.FromArgb(150, 146, 164), Font = new Font("Microsoft YaHei UI", 8f), AutoSize = true, Location = new Point(16, y + 20), BackColor = Color.Transparent };
        settings.Controls.Add(colTag);

        var colorNames = new[] { new[] { "silver", "银" }, new[] { "gold", "金" }, new[] { "neon", "霓虹" }, new[] { "ink", "墨" }, new[] { "bubble", "泡泡" } };
        for (int i = 0; i < colorNames.Length; i++)
        {
            var th = new Thumb { Pic = Art.Res("pointer_" + C.PointerShape + "_" + colorNames[i][0] + ".png"), Text = colorNames[i][1], Location = new Point(52 + i * 64, y), Size = new Size(60, 56), Selected = C.PointerColor == colorNames[i][0] };
            string key = colorNames[i][0];
            th.Click += (a, b) => { C.PointerColor = key; RefreshThumbs(); Save(); };
            colorThumbs.Add(th); settings.Controls.Add(th);
        }
        y += 66;

        Section(y, "② 主体", "挂件的身体，可以换图"); y += 30;
        var b1 = new Thumb { Pic = Art.Res("body_default.png"), Text = "默认", Location = new Point(16, y), Size = new Size(96, 90), Selected = C.BodyKind == "default" };
        b1.Click += (a, b) => { C.BodyKind = "default"; RefreshThumbs(); Save(); };
        var b2 = new Thumb { Pic = Art.Res("body_avatar.png"), Text = "圆形头像", Location = new Point(122, y), Size = new Size(96, 90), Selected = C.BodyKind == "avatar" };
        b2.Click += (a, b) => { C.BodyKind = "avatar"; RefreshThumbs(); Save(); };
        var b3 = new Thumb { Pic = C.BodyKind == "custom" && File.Exists(C.CustomBody) ? Art.LoadFile(C.CustomBody, 90) : null, Text = "本地上传", Upload = true, Location = new Point(228, y), Size = new Size(96, 90), Selected = C.BodyKind == "custom" };
        b3.Click += (a, b) => { UploadBody(); };
        bodyThumbs.Add(b1); bodyThumbs.Add(b2); bodyThumbs.Add(b3);
        foreach (var t in bodyThumbs) settings.Controls.Add(t);
        y += 96;

        // ---- 连接线
        Section(y, "③ 连接线", "那根把金币吊住的线"); y += 30;
        ropeSwitch = new Switch { Text = "显示连接线", On = C.RopeOn, Location = new Point(16, y), Size = new Size(200, 26) };
        ropeSwitch.Click += (a, b) => { C.RopeOn = ropeSwitch.On; Save(); RefreshThumbs(); };
        settings.Controls.Add(ropeSwitch);
        glowSwitch = new Switch { Text = "发光线", On = C.RopeGlow, Location = new Point(226, y), Size = new Size(170, 26) };
        glowSwitch.Click += (a, b) => { C.RopeGlow = glowSwitch.On; Save(); RefreshThumbs(); };
        settings.Controls.Add(glowSwitch);
        y += 30;
        Color[] palette = { Color.FromArgb(52, 44, 58), Color.FromArgb(240, 240, 245), Color.FromArgb(255, 120, 170), Color.FromArgb(255, 190, 90), Color.FromArgb(110, 220, 255), Color.FromArgb(150, 255, 180) };
        for (int i = 0; i < palette.Length; i++)
        {
            var sw = new Swatch { Col = palette[i], Location = new Point(16 + i * 40, y), Size = new Size(30, 30), Selected = C.RopeColor == i };
            int idx = i;
            sw.Click += (a, b) => { C.RopeColor = idx; RefreshThumbs(); Save(); };
            swatches.Add(sw); settings.Controls.Add(sw);
        }
        y += 40;

        // ---- 吊起物品
        Section(y, "④ 吊起物品", "绳子末端那个会跳的"); y += 30;
        var i1 = new Thumb { Pic = Art.Res("item_coin.png"), Text = "金币", Location = new Point(16, y), Size = new Size(96, 90), Selected = C.ItemKind == "coin" };
        i1.Click += (a, b) => { C.ItemKind = "coin"; RefreshThumbs(); Save(); };
        var i2 = new Thumb { Pic = C.ItemKind == "custom" && File.Exists(C.CustomItem) ? Art.LoadFile(C.CustomItem, 90) : null, Text = "本地上传", Upload = true, Location = new Point(122, y), Size = new Size(96, 90), Selected = C.ItemKind == "custom" };
        i2.Click += (a, b) => { UploadItem(); };
        itemThumbs.Add(i1); itemThumbs.Add(i2);
        foreach (var t in itemThumbs) settings.Controls.Add(t);
        y += 96;

        // ---- 点击动画
        Section(y, "⑤ 左键点击", "吊起物品跳一下 + 发光 + 音效"); y += 30;
        clickSwitch = new Switch { Text = "开启点击动画", On = C.ClickAnim, Location = new Point(16, y), Size = new Size(200, 26) };
        clickSwitch.Click += (a, b) => { C.ClickAnim = clickSwitch.On; Save(); };
        settings.Controls.Add(clickSwitch);
        soundSwitch = new Switch { Text = "点击音效", On = C.ClickSound, Location = new Point(226, y), Size = new Size(170, 26) };
        soundSwitch.Click += (a, b) => { C.ClickSound = soundSwitch.On; Save(); };
        settings.Controls.Add(soundSwitch);
        y += 30;
        var sfxNames = new[] { new[] { "coin", "金币" }, new[] { "jump", "跳跃" }, new[] { "bell", "铃" }, new[] { "pop", "啵" }, new[] { "chime", "风铃" }, new[] { "arcade", "街机" } };
        for (int i = 0; i < sfxNames.Length; i++)
        {
            var sb = new Btn { Text = sfxNames[i][1], Primary = C.Sfx == sfxNames[i][0], Location = new Point(16 + (i % 3) * 130, y + (i / 3) * 34), Size = new Size(120, 30) };
            string key = sfxNames[i][0];
            sb.Click += (a, b) => { C.Sfx = key; Sfx.Set(key, C.Volume); Sfx.Play(); RefreshThumbs(); Save(); };
            sfxBtns.Add(sb); settings.Controls.Add(sb);
        }
        y += 74;
        var vl = new Label { Text = "音量", ForeColor = Color.FromArgb(200, 196, 214), AutoSize = true, Location = new Point(16, y + 4), BackColor = Color.Transparent };
        settings.Controls.Add(vl);
        vol = new Slider { Min = 0, Max = 100, Value = C.Volume, Location = new Point(60, y), Size = new Size(300, 24) };
        vol.Changed += (a, b) => { C.Volume = vol.Value; Sfx.Set(C.Sfx, C.Volume); Save(); };
        settings.Controls.Add(vol);
        y += 30;

        // ---- ⑦ 彩蛋
        Section(y, "⑥ 彩蛋", "绑一个键，按一下就放一段声音（默认关闭）"); y += 30;
        eggSwitch = new Switch { Text = "开启彩蛋", On = C.EggOn, Location = new Point(16, y), Size = new Size(150, 26) };
        eggSwitch.Click += (a, b) =>
        {
            C.EggOn = eggSwitch.On;
            if (!C.EggOn) Sfx.StopAll();     // 关掉就立刻掐掉正在放的声音
            Save();
            SyncEggWatch();          // 立刻生效，不需要变身
            RefreshThumbs();
        };
        settings.Controls.Add(eggSwitch);

        eggBtn = new Btn { Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键", Location = new Point(176, y), Size = new Size(130, 26) };
        eggBtn.Click += (a, b) => StartBind();
        settings.Controls.Add(eggBtn);

        eggTest = new Btn { Text = "试听", Location = new Point(312, y), Size = new Size(76, 26) };
        eggTest.Click += (a, b) => { PlayEgg(); };
        settings.Controls.Add(eggTest);
        y += 32;

        var evl = new Label { Text = "彩蛋音量", ForeColor = Color.FromArgb(200, 196, 214), AutoSize = true, Location = new Point(16, y + 4), BackColor = Color.Transparent };
        settings.Controls.Add(evl);
        eggVol = new Slider { Min = 0, Max = 100, Value = C.EggVolume, Location = new Point(88, y), Size = new Size(238, 24) };
        eggVol.Changed += (a, b) => { C.EggVolume = eggVol.Value; Save(); };
        settings.Controls.Add(eggVol);
        y += 30;

        eggHint = new Label
        {
            Text = "点「绑定按键」再按一下想用的键（任意键都行），绑好后按它就会播放。",
            ForeColor = Color.FromArgb(128, 124, 142),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(390, 38),      // 两行高度，长提示不会被裁
            Location = new Point(16, y),
            BackColor = Color.Transparent
        };
        settings.Controls.Add(eggHint);
        y += 40;

        var tip = new Label
        {
            Text = "提示：只换普通箭头这一个光标，变身前会自动备份。",
            ForeColor = Color.FromArgb(120, 116, 134),
            Font = new Font("Microsoft YaHei UI", 8f),
            AutoSize = false,
            Size = new Size(390, 20),
            Location = new Point(16, y),
            BackColor = Color.Transparent
        };
        settings.Controls.Add(tip);
        y += 26;

        NeedH = y + 12;
        settings.Size = new Size(434, NeedH - 4);
        shell.Size = new Size(438, NeedH);
    }

    void RefreshThumbs()
    {
        var shapeKeys = new[] { "chevron", "arrow", "cross", "ring", "diamond", "move" };
        var colorKeys = new[] { "silver", "gold", "neon", "ink", "bubble" };
        for (int i = 0; i < pointerThumbs.Count && i < shapeKeys.Length; i++)
        {
            pointerThumbs[i].Selected = C.PointerShape == shapeKeys[i];
            pointerThumbs[i].Pic = Art.Res("pointer_" + shapeKeys[i] + "_" + C.PointerColor + ".png");
        }
        for (int i = 0; i < colorThumbs.Count && i < colorKeys.Length; i++)
        {
            colorThumbs[i].Selected = C.PointerColor == colorKeys[i];
            colorThumbs[i].Pic = Art.Res("pointer_" + C.PointerShape + "_" + colorKeys[i] + ".png");
        }
        if (eggBtn != null) eggBtn.Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键";
        var bnames = new[] { "默认", "圆形头像", "上传…" };
        for (int i = 0; i < bodyThumbs.Count; i++) bodyThumbs[i].Selected = (C.BodyKind == (i == 0 ? "default" : i == 1 ? "avatar" : "custom"));
        for (int i = 0; i < itemThumbs.Count; i++) itemThumbs[i].Selected = (C.ItemKind == (i == 0 ? "coin" : "custom"));
        for (int i = 0; i < swatches.Count; i++) swatches[i].Selected = C.RopeColor == i;
        var keys = new[] { "coin", "jump", "bell", "pop", "chime", "arcade" };
        for (int i = 0; i < sfxBtns.Count; i++) sfxBtns[i].Primary = C.Sfx == keys[i];
        foreach (Control c in settings.Controls) c.Invalidate();
        if (preview != null) preview.Rebuild(Art.Build(C));
        // 桌面上那只必须用另一份 Look：两个线程同时 DrawImage 同一张 Bitmap，
        // GDI+ 会抛 “对象当前正在其他地方使用”（切换发光线时最容易踩到）
        if (overlay != null) overlay.SetLook(Art.Build(C));
    }

    static string NameOf(string key)
    {
        switch (key) { case "silver": return "银"; case "gold": return "金"; case "neon": return "霓虹"; case "ink": return "墨"; case "bubble": return "泡泡"; }
        return key;
    }

    void Save() { C.Save(); }

    // 找一个真的能写文件的目录（沙箱 / 只读盘 / 被策略限制的 AppData 都可能踩坑）
    string CustomDir()
    {
        var cands = new List<string>();
        cands.Add(Path.Combine(Cfg.Dir, "custom"));
        try { cands.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MUMUCursor", "custom")); } catch { }
        try { cands.Add(Path.Combine(Path.GetTempPath(), "MUMUCursor", "custom")); } catch { }
        try { cands.Add(Path.Combine(Cfg.BackupDir, "custom")); } catch { }
        cands.Add(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "custom"));

        foreach (var d in cands)
        {
            try
            {
                Directory.CreateDirectory(d);
                string probe = Path.Combine(d, ".probe");
                File.WriteAllText(probe, "1");
                File.Delete(probe);
                return d;
            }
            catch { }
        }
        return null;
    }

    void UploadBody()
    {
        using (var d = new OpenFileDialog { Filter = "图片|*.png;*.jpg;*.jpeg;*.bmp;*.gif", Title = "选择主体图片" })
        {
            if (d.ShowDialog(this) != DialogResult.OK) return;
            using (var cf = new CropForm(d.FileName, 256, true, "圆形遮罩"))
            {
                if (cf.ShowDialog(this) != DialogResult.OK) return;
                try
                {
                    string dir = CustomDir();
                    if (dir == null) { MessageBox.Show(this, "找不到可写入的目录，无法保存这张图。\n试试把程序放到桌面或文档文件夹里再上传。", "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                    string outPath = Path.Combine(dir, "body.png");
                    cf.Result.Save(outPath, ImageFormat.Png);
                    C.CustomBody = outPath; C.BodyKind = "custom";
                    bodyThumbs[2].Pic = Art.LoadFile(outPath, 90);
                    bodyThumbs[2].Upload = false;
                    RefreshThumbs(); Save();
                }
                catch (Exception ex)
                {
                    MessageBox.Show(this, "保存失败：" + ex.Message, "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
        }
    }

    void UploadItem()
    {
        using (var d = new OpenFileDialog { Filter = "图片|*.png;*.jpg;*.jpeg;*.bmp;*.gif", Title = "选择吊起物品图片" })
        {
            if (d.ShowDialog(this) != DialogResult.OK) return;
            using (var cf = new CropForm(d.FileName, 192, false, ""))
            {
                if (cf.ShowDialog(this) != DialogResult.OK) return;
                try
                {
                    string dir = CustomDir();
                    if (dir == null) { MessageBox.Show(this, "找不到可写入的目录，无法保存这张图。\n试试把程序放到桌面或文档文件夹里再上传。", "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                    string outPath = Path.Combine(dir, "item.png");
                    cf.Result.Save(outPath, ImageFormat.Png);
                    C.CustomItem = outPath; C.ItemKind = "custom";
                    itemThumbs[1].Pic = Art.LoadFile(outPath, 90);
                    itemThumbs[1].Upload = false;
                    RefreshThumbs(); Save();
                }
                catch (Exception ex)
                {
                    MessageBox.Show(this, "保存失败：" + ex.Message, "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
        }
    }

    void Apply()
    {
        try
        {
            if (overlay != null) return;
            var look = Art.Build(C);
            overlay = new Overlay(look);
            overlayThread = new Thread(overlay.Run) { IsBackground = true };
            overlayThread.Start();
            // 等渲染线程真的推上去一帧，再在 UI 线程换光标（SetSystemCursor 可能在非消息泵线程上卡死）
            hideTimer = new System.Windows.Forms.Timer { Interval = 80 };
            hideTimer.Tick += (a1, a2) =>
            {
                if (overlay == null) { hideTimer.Stop(); return; }
                if (!overlay.HideReady) return;
                hideTimer.Stop();
                try { CursorSwitch.Apply(); } catch { }
            };
            hideTimer.Start();
            StartWatchdog();
            StartHandoff();
            RefreshStatus();
        }
        catch (Exception ex)
        {
            // 出任何错，先把系统光标救回来，再告诉用户 —— 绝不留下“没光标”的状态
            try { if (overlay != null) { overlay.Stop(); overlay = null; } } catch { }
            try { CursorSwitch.Restore(); } catch { }
            RefreshStatus();
            MessageBox.Show(this, "变身失败（已自动恢复系统光标）：\n" + ex.Message, "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    // 系统切换界面出现时：把系统箭头还回去、精灵暂时让开
    System.Windows.Forms.Timer handoff;
    bool handedOff;

    void StartHandoff()
    {
        if (handoff != null) { handoff.Stop(); handoff.Dispose(); }
        handedOff = false;
        handoff = new System.Windows.Forms.Timer { Interval = 150 };
        handoff.Tick += (a, b) =>
        {
            if (overlay == null) { handoff.Stop(); return; }
            bool up;
            try { up = overlay.SwitcherUp; } catch { return; }
            if (up == handedOff) return;
            handedOff = up;
            try
            {
                if (up)
                {
                    CursorSwitch.Restore();                 // 先用真光标顶上（画在系统界面之上）
                    if (overlay.hwnd != IntPtr.Zero) Nat.ShowWindow(overlay.hwnd, 0);
                }
                else
                {
                    if (overlay.hwnd != IntPtr.Zero) Nat.ShowWindow(overlay.hwnd, 8);
                    CursorSwitch.Apply();
                }
            }
            catch { }
        };
        handoff.Start();
    }

    // 看门狗：渲染线程一旦卡住（Alt+Tab、切全屏、远程桌面都可能导致），
    // 就把系统光标立刻还回去，避免“屏幕上既没有光标、精灵也不动”。
    System.Windows.Forms.Timer watchdog;
    int wdFrames = -1, wdStall;

    void StartWatchdog()
    {
        if (watchdog != null) { watchdog.Stop(); watchdog.Dispose(); }
        wdFrames = -1; wdStall = 0;
        watchdog = new System.Windows.Forms.Timer { Interval = 500 };
        watchdog.Tick += (a, b) =>
        {
            if (overlay == null) { watchdog.Stop(); return; }
            int f = overlay.Frames;
            if (f == wdFrames)
            {
                wdStall++;
                if (wdStall >= 3)   // 1.5 秒没有新帧 -> 判定卡死
                {
                    watchdog.Stop();
                    try { overlay.Stop(); } catch { }
                    overlay = null;
                    try { CursorSwitch.Restore(); } catch { }
                    RefreshStatus();
                    status.Text = "已暂停";
                    status.ForeColor = Color.FromArgb(255, 210, 140);
                    applyBtn.Enabled = true;
                    applyBtn.Text = "重新变身为 MUMU 光标";
                    MessageBox.Show(this, "指针卡住了（常见于 Alt+Tab 切换后），已经自动帮你恢复成系统光标。\n再点一次「变身为 MUMU 光标」就好。", "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            else { wdStall = 0; wdFrames = f; }
        };
        watchdog.Start();
    }

    void Restore()
    {
        try
        {
            if (watchdog != null) { watchdog.Stop(); watchdog.Dispose(); watchdog = null; }
            if (handoff != null) { handoff.Stop(); handoff.Dispose(); handoff = null; }
            handedOff = false;
            if (hideTimer != null) { hideTimer.Stop(); hideTimer.Dispose(); hideTimer = null; }
            if (overlay != null) { overlay.Stop(); overlay = null; Thread.Sleep(220); }
            CursorSwitch.Restore();
            RefreshStatus();
        }
        catch (Exception ex)
        {
            try { overlay = null; CursorSwitch.Restore(); } catch { }
            RefreshStatus();
            MessageBox.Show(this, "恢复时出错（已尽力恢复系统光标）：\n" + ex.Message,
                "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            if (!CursorSwitch.IsDirty()) Environment.Exit(0);
        }
    }

    // ---------------------------------------------------------- 彩蛋：热键 + 音频
    const int HOT_ID = 0xBEEF;
    string eggWav;
    byte[] eggBytes;
    System.Windows.Forms.Timer eggTimer;   // 轮询按键状态用
    bool eggDown;                          // 防止长按连发
    int lastEggTick;
    System.Windows.Forms.Timer bindTimeout;
    Slider eggVol;
    Label eggVolLabel;

    static string KeyName(int vk)
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
            case 0xDC: return "\\";
            case 0xDD: return "]";
            case 0xDE: return "'";
        }
        if (vk >= 0x60 && vk <= 0x69) return "小键盘" + (vk - 0x60);
        if (vk >= 0x6A && vk <= 0x6F) return "小键盘" + "*/+-.".Substring(vk - 0x6A, 1);
        return "VK" + vk + " 键";
    }

    static readonly int[] ScanKeys = BuildScanKeys();
    static int[] BuildScanKeys()
    {
        var L = new List<int>();
        for (int v = 0x30; v <= 0x39; v++) L.Add(v);          // 0-9
        for (int v = 0x41; v <= 0x5A; v++) L.Add(v);          // A-Z
        for (int v = 0x70; v <= 0x87; v++) L.Add(v);          // F1-F24
        for (int v = 0x60; v <= 0x69; v++) L.Add(v);          // 小键盘 0-9
        L.AddRange(new[]
        {
            0x20, 0x0D, 0x09, 0x1B, 0x08, 0x10, 0x11, 0x12, 0x14,          // 空格 回车 Tab Esc 退格 Shift Ctrl Alt Caps
            0x25, 0x26, 0x27, 0x28, 0x24, 0x23, 0x21, 0x22, 0x2D, 0x2E,    // 方向 Home End PgUp PgDn Ins Del
            0x6A, 0x6B, 0x6D, 0x6F,                                        // * + - /
            0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0xC0, 0xDB, 0xDC, 0xDD, 0xDE // ; = , - . / ` [ \ ] '
        });
        return L.ToArray();
    }
    bool[] scanPrev = new bool[256];

    void StartBind()
    {
        if (binding) { CancelBind(); return; }        // 再点一次 = 取消
        binding = true;
        for (int i = 0; i < scanPrev.Length; i++) scanPrev[i] = false;
        // 按下「绑定按键」时已经按住的键（比如 Shift）不算数，等松手再按才算
        foreach (int vk in ScanKeys) scanPrev[vk] = (Nat.GetAsyncKeyState(vk) & 0x8000) != 0;
        eggBtn.Text = "按下任意键 …";
        eggHint.Text = "现在按一下想绑的键位，绑定后就可以按下按键触发彩蛋。";
        eggHint.ForeColor = Color.FromArgb(255, 190, 120);
        EnsureEggTimer();
        if (bindTimeout != null) { bindTimeout.Stop(); bindTimeout.Dispose(); }
        bindTimeout = new System.Windows.Forms.Timer { Interval = 10000 };
        bindTimeout.Tick += (a, b) =>
        {
            bindTimeout.Stop(); bindTimeout.Dispose(); bindTimeout = null;
            if (binding) { binding = false; if (eggBtn != null) eggBtn.Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键"; SyncEggWatch(); }
        };
        bindTimeout.Start();
        Activate();
    }

    void CancelBind()
    {
        binding = false;
        if (bindTimeout != null) { bindTimeout.Stop(); bindTimeout.Dispose(); bindTimeout = null; }
        if (eggBtn != null) eggBtn.Text = C.EggKey != 0 ? "按键 " + KeyName(C.EggKey) : "绑定按键";
        SyncEggWatch();
    }

    // 绑定期间用轮询找“新按下的那个键”，不依赖窗口焦点：点完按钮去按就行，按不到也不会卡住
    void BindScan()
    {
        foreach (int vk in ScanKeys)
        {
            bool down = (Nat.GetAsyncKeyState(vk) & 0x8000) != 0;
            bool was = scanPrev[vk];
            scanPrev[vk] = down;
            if (down && !was) { BindEgg(vk); return; }
        }
    }

    void BindEgg(int vk)
    {
        try
        {
            // 单独的 Shift / Ctrl / Alt / Win 绑了也用不了（要一直按着），直接拦掉
            if (vk == 0x10 || vk == 0x11 || vk == 0x12 || vk == 0x5B || vk == 0x5C)
            {
                if (eggHint != null)
                {
                    eggHint.Text = "别绑单独的 Shift / Ctrl / Alt，换一个（比如 F6~F12）。";
                    eggHint.ForeColor = Color.FromArgb(255, 170, 120);
                }
                return;
            }
            if (vk == 0 || vk == 229 || vk == 255 || vk == -1)
            {
                if (eggHint != null)
                {
                    eggHint.Text = "这个键被输入法/系统占用了，换一个（比如 F6~F12）。";
                    eggHint.ForeColor = Color.FromArgb(255, 170, 120);
                }
                return;
            }
            UnbindHook();
            C.EggKey = vk;
            C.EggOn = true;                                   // 绑上了就等于要用，直接把开关打开
            if (eggSwitch != null) { eggSwitch.On = true; eggSwitch.Invalidate(); }
            Save();
            binding = false;
            if (bindTimeout != null) { bindTimeout.Stop(); bindTimeout.Dispose(); bindTimeout = null; }
            if (eggBtn != null) eggBtn.Text = "按键 " + KeyName(vk);
            SyncEggWatch();
        }
        catch { }
    }

    public void EggSwitchOnForTest()
    {
        // 完全走界面那条路：打开「开启彩蛋」→ 绑 H → 不调用 Apply
        if (eggSwitch != null) { eggSwitch.On = true; eggSwitch.Invalidate(); }
        C.EggOn = true;
        C.EggKey = 0x48;
        Save();
        SyncEggWatch();
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " noapply transformed=" + (overlay != null) + "\n"); } catch { }
    }

    public void TestPoll()
    {
        C.EggOn = true; C.EggKey = 0x48;   // H
        // 模拟：按下 → 按住(不应重复) → 松开 → 再按
        EggTick(true); EggTick(true); EggTick(true);   // 按住，只该响一次
        EggTick(false);
        EggTick(true); EggTick(false);                  // 松手马上再按：立刻重播，不叠音
        var t = new System.Windows.Forms.Timer { Interval = 1200 };
        t.Tick += (a, b) => { t.Stop(); t.Dispose(); Close(); };
        t.Start();
    }

    // 彩蛋监听只看「开没开 + 绑没绑键」，和有没有变身完全无关
    public void SyncEggWatch()
    {
        try
        {
            bool live = binding || (C.EggOn && C.EggKey != 0);
            if (live) StartHook();
            else StopEggWatch();

            if (eggHint != null && binding)
            {
                eggHint.Text = "现在按一下想绑的键位，绑定后就可以按下按键触发彩蛋。";
                eggHint.ForeColor = Color.FromArgb(255, 190, 120);
                return;
            }
            if (eggHint != null)
            {
                if (Nat.IsLowIntegrity())
                {
                    eggHint.Text = "⚠ 权限受限，读不到键盘按键。请关掉本程序，再到文件夹里双击 MUMU光标.exe 打开。";
                    eggHint.ForeColor = Color.FromArgb(255, 170, 120);
                    return;
                }
                if (live)
                {
                    eggHint.Text = "监听中：按 " + KeyName(C.EggKey) + " 就会播放；连按会打断上一次、从头重播。";
                    eggHint.ForeColor = Color.FromArgb(150, 255, 190);
                }
                else if (C.EggKey != 0)
                {
                    eggHint.Text = "彩蛋已关闭，打开左边开关后按键才会响。";
                    eggHint.ForeColor = Color.FromArgb(205, 205, 215);
                }
                else
                {
                    eggHint.Text = "点「绑定按键」，然后按下想用的键（不会影响你正常打字和游戏按键）。";
                    eggHint.ForeColor = Color.FromArgb(150, 156, 172);
                }
            }
        }
        catch { }
    }

    void EnsureEggTimer()
    {
        if (eggTimer != null) return;
        eggTimer = new System.Windows.Forms.Timer { Interval = 35 };
        eggTimer.Tick += (a, b) => EggPoll();
        eggTimer.Start();
    }

    void StartHook()
    {
        EnsureEggTimer();
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " watch start key=" + C.EggKey + " lowIL=" + Nat.IsLowIntegrity() + "\n"); } catch { }
    }

    void StopEggWatch()
    {
        try { if (eggTimer != null) { eggTimer.Stop(); eggTimer.Dispose(); eggTimer = null; } } catch { }
        eggDown = false;
    }

    void EggPoll()
    {
        try
        {
            if (binding) { BindScan(); return; }
            if (!C.EggOn || C.EggKey == 0) { eggDown = false; return; }
            EggTick((Nat.GetAsyncKeyState(C.EggKey) & 0x8000) != 0);
        }
        catch { }
    }

    void EggTick(bool down)
    {
        try
        {
            if (down && !eggDown)
            {
                eggDown = true;
                PlayEgg();                                   // 再按就打断上一遍，从头开始，不叠音
            }
            else if (!down) eggDown = false;
        }
        catch { }
    }

    void UnbindHook() { StopEggWatch(); }

    void UnbindEgg()
    {
        UnbindHook();
        C.EggKey = 0;
        if (eggBtn != null) eggBtn.Text = "绑定按键";
    }

    void PlayEgg()
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
            bool ok = Sfx.PlayWavScaled(eggBytes, C.EggVolume, false);
            if (!ok && eggHint != null)
            {
                eggHint.Text = "播放失败（系统没有可用的音频设备？）。换台设备或检查一下声音服务。";
                eggHint.ForeColor = Color.FromArgb(255, 140, 140);
            }
        }
        catch (Exception ex)
        {
            try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_egg.log"), "egg ex " + ex + "\n"); } catch { }
        }
    }

    protected override void WndProc(ref Message m)
    {
        base.WndProc(ref m);
    }

    protected override void OnKeyDown(KeyEventArgs e)
    {
        if (binding)
        {
            // 中文输入法开着时，按键会被系统“吞”成 VK_PROCESSKEY(229)，不能拿来绑
            int kv = (int)e.KeyCode;
            if (kv != 229 && e.KeyCode != Keys.None && e.KeyCode != Keys.ProcessKey) BindEgg(kv);
            e.Handled = true; e.SuppressKeyPress = true;
            return;
        }
        base.OnKeyDown(e);
    }

    void RefreshStatus()
    {
        bool on = overlay != null;
        status.Text = on ? "已变身" : "未变身";
        status.ForeColor = on ? Color.FromArgb(140, 250, 190) : Color.FromArgb(255, 190, 120);
        status.BackColor = on ? Color.FromArgb(30, 48, 40) : Color.FromArgb(44, 38, 54);
        applyBtn.Enabled = !on;
        applyBtn.Text = on ? "正在使用 MUMU 光标" : "变身为 MUMU 光标";
        if (preview != null) preview.Rebuild(Art.Build(C));
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        try { UnbindEgg(); } catch { }
        try { Sfx.StopAll(); } catch { }
        try { if (overlay != null) { overlay.Stop(); Thread.Sleep(220); CursorSwitch.Restore(); } } catch { }
        base.OnFormClosing(e);
    }

    protected override void OnShown(EventArgs e)
    {
        base.OnShown(e);
        KeyPreview = true;
        if (FsTest)
        {
            fsTimer = new System.Windows.Forms.Timer { Interval = 320 };
            var ft = fsTimer;
            int step = 0;
            ft.Tick += (a, b) =>
            {
                step++;
                if (step == 1)
                {
                    Program.Trace("fstest step1 begin");
                    Apply();
                    Program.Trace("fstest apply done");
                    var fsWin = new Form
                    {
                        FormBorderStyle = FormBorderStyle.None,
                        StartPosition = FormStartPosition.Manual,
                        Bounds = Screen.PrimaryScreen.Bounds,
                        TopMost = true,
                        ShowInTaskbar = false,
                        BackColor = Color.Black
                    };
                    fsWin.Show();
                    Program.Trace("fstest shown");
                    fsWin.Activate();
                    Program.Trace("fstest activated");
                    Nat.SetForegroundWindow(fsWin.Handle);
                    Nat.RECT fr; Nat.GetWindowRect(fsWin.Handle, out fr);
                    var fmi = new Nat.MONITORINFO(); fmi.cbSize = Marshal.SizeOf(typeof(Nat.MONITORINFO));
                    bool fok = Nat.GetMonitorInfo(Nat.MonitorFromWindow(fsWin.Handle, 2), ref fmi);
                    long fst = Nat.GetWindowLongW(fsWin.Handle, -16);
                    Program.Trace("fstest rect=" + fr.Left + "," + fr.Top + "," + fr.Right + "," + fr.Bottom + " miok=" + fok + " mon=" + fmi.rcMonitor.Left + "," + fmi.rcMonitor.Top + "," + fmi.rcMonitor.Right + "," + fmi.rcMonitor.Bottom + " style=0x" + fst.ToString("X8"));
                    Program.Trace("fstest: fullscreen " + fsWin.Bounds + " looksFull=" + (overlay != null && overlay.LooksFullscreen(fsWin.Handle)) + " fg=" + Nat.GetForegroundWindow() + " fgLooksFull=" + (overlay != null && overlay.LooksFullscreen(Nat.GetForegroundWindow())));
                }
                else if (step == 5)
                {
                    bool hid = overlay != null && overlay.SysCursorHidden;
                    bool vis = overlay != null && Nat.IsWindowVisible(overlay.hwnd);
                    Console.WriteLine("fstest hidden=" + hid + " reason=" + (overlay != null ? overlay.HideReason : "-") + " overlayVisible=" + vis);
                    Program.Trace("fstest hidden=" + hid + " reason=" + (overlay != null ? overlay.HideReason : "-") + " vis=" + vis);
                    ft.Stop();
                    foreach (Form fx in Application.OpenForms) if (fx != this) { try { fx.Close(); } catch { } }
                    if (overlay != null) { overlay.Stop(); overlay = null; }
                    CursorSwitch.Restore();
                    Close();
                }
            };
            ft.Start();
        }
        if (!string.IsNullOrEmpty(EggTestKey))
        {
            var kt = new System.Windows.Forms.Timer { Interval = 700 };
            kt.Tick += (a, b) =>
            {
                kt.Stop(); kt.Dispose();
                if (eggSwitch != null) { eggSwitch.On = true; eggSwitch.Invalidate(); }
                C.EggOn = true;
                int vk = EggTestKey.Length == 1
                    ? (int)char.ToUpperInvariant(EggTestKey[0])
                    : (int)(Keys)Enum.Parse(typeof(Keys), EggTestKey, true);
                BindEgg(vk);
                var vol = new System.Windows.Forms.Timer { Interval = 600 };
                vol.Tick += (c2, d2) =>
                {
                    vol.Stop(); vol.Dispose();
                    Nat.keybd_event((byte)vk, 0, 0, IntPtr.Zero);
                    System.Threading.Thread.Sleep(150);
                    Nat.keybd_event((byte)vk, 0, 2, IntPtr.Zero);
                };
                vol.Start();
                var cl = new System.Windows.Forms.Timer { Interval = 6000 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            kt.Start();
        }

        if (EggImeTest)
        {
            var it = new System.Windows.Forms.Timer { Interval = 400 };
            it.Tick += (a, b) =>
            {
                it.Stop(); it.Dispose();
                C.EggKey = 0;
                BindEgg(229);
                string h1 = eggHint != null ? eggHint.Text : "";
                int k1 = C.EggKey;
                BindEgg(70);
                string h2 = eggHint != null ? eggHint.Text : "";
                try
                {
                    File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"),
                        DateTime.Now.ToString("HH:mm:ss.fff") + " ime k1=" + k1 + " h1=[" + h1 + "] k2=" + C.EggKey + " h2=[" + h2 + "]\n");
                }
                catch { }
                var cl = new System.Windows.Forms.Timer { Interval = 600 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            it.Start();
        }

        if (TopProbe)
        {
            var a = new System.Windows.Forms.Timer { Interval = 900 };
            a.Tick += (s1, e1) =>
            {
                a.Stop(); a.Dispose();
                Apply();
                var rival = new Form
                {
                    FormBorderStyle = FormBorderStyle.None,
                    StartPosition = FormStartPosition.Manual,
                    TopMost = true,
                    BackColor = Color.FromArgb(40, 40, 46),
                    Size = new Size(360, 200),
                };
                var sc = Screen.PrimaryScreen.WorkingArea;
                rival.Location = new Point(sc.Left + sc.Width / 2 - 180, sc.Top + sc.Height / 2 - 100);
                rival.Show();
                rival.BringToFront();

                var b = new System.Windows.Forms.Timer { Interval = 1500 };
                b.Tick += (s2, e2) =>
                {
                    b.Stop(); b.Dispose();
                    IntPtr ovh = overlay != null ? overlay.hwnd : IntPtr.Zero;
                    IntPtr w = Nat.GetTopWindow(IntPtr.Zero);
                    int idx = 0, ovIdx = -1, rvIdx = -1;
                    while (w != IntPtr.Zero && idx < 64)
                    {
                        if (w == ovh) ovIdx = idx;
                        if (w == rival.Handle) rvIdx = idx;
                        w = Nat.GetWindow(w, Nat.GW_HWNDNEXT);
                        idx++;
                    }
                    bool pass = ovIdx >= 0 && (rvIdx < 0 || ovIdx < rvIdx);
                    try
                    {
                        IntPtr q = Nat.GetTopWindow(IntPtr.Zero);
                        for (int k = 0; k < 14 && q != IntPtr.Zero; k++)
                        {
                            var sb = new System.Text.StringBuilder(128);
                            Nat.GetClassNameW(q, sb, 128);
                            int ex = Nat.GetWindowLongW(q, -20);
                            Program.Trace("  z" + k + " h=" + q + " cls=" + sb + " topmost=" + ((ex & 0x8) != 0)
                                + (q == ovh ? " <== overlay" : ""));
                            q = Nat.GetWindow(q, Nat.GW_HWNDNEXT);
                        }
                    }
                    catch { }
                    Program.Trace("topprobe pass=" + pass + " ovIdx=" + ovIdx + " rivalIdx=" + rvIdx + " scanned=" + idx
                        + " ov=" + ovh
                        + " topcalls=" + (overlay != null ? overlay.TopCalls : 0) + " topfails=" + (overlay != null ? overlay.TopFails : 0) + " frames=" + (overlay != null ? overlay.Frames : 0));
                    rival.Close();
                    Restore();
                    var c = new System.Windows.Forms.Timer { Interval = 500 };
                    c.Tick += (s3, e3) => { c.Stop(); c.Dispose(); Close(); };
                    c.Start();
                };
                b.Start();
            };
            a.Start();
        }

        if (EggBindTest)
        {
            var bt = new System.Windows.Forms.Timer { Interval = 500 };
            bt.Tick += (a, b) =>
            {
                bt.Stop(); bt.Dispose();
                if (eggSwitch != null) { eggSwitch.On = false; eggSwitch.Invalidate(); }   // 故意关着再来绑
                C.EggOn = false;
                BindEgg((int)Keys.F);
                try
                {
                    File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"),
                        DateTime.Now.ToString("HH:mm:ss.fff") + " bindtest EggOn=" + C.EggOn +
                        " switch=" + (eggSwitch != null && eggSwitch.On) + " key=" + C.EggKey +
                        " hint=[" + (eggHint != null ? eggHint.Text : "") + "]\n");
                }
                catch { }
                var cl = new System.Windows.Forms.Timer { Interval = 800 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            bt.Start();
        }

        if (EggTry)
        {
            var et = new System.Windows.Forms.Timer { Interval = 600 };
            et.Tick += (a, b) =>
            {
                et.Stop(); et.Dispose();
                if (eggSwitch != null) { eggSwitch.On = true; eggSwitch.Invalidate(); }
                BindEgg((int)Keys.F9);
                PlayEgg();
                var cl = new System.Windows.Forms.Timer { Interval = 1500 };
                cl.Tick += (c, d) => { cl.Stop(); cl.Dispose(); Close(); };
                cl.Start();
            };
            et.Start();
        }

        if (StressGlow)
        {
            var st = new System.Windows.Forms.Timer { Interval = 1200 };
            st.Tick += (a, b) =>
            {
                st.Stop(); st.Dispose();
                Apply();
                int n = 0;
                var tt = new System.Windows.Forms.Timer { Interval = 350 };
                tt.Tick += (c, d) =>
                {
                    C.RopeGlow = !C.RopeGlow;
                    if (glowSwitch != null) { glowSwitch.On = C.RopeGlow; glowSwitch.Invalidate(); }
                    RefreshThumbs();
                    if (++n >= 14) { tt.Stop(); tt.Dispose(); Restore(); var q = new System.Windows.Forms.Timer { Interval = 800 }; q.Tick += (e2, f2) => { q.Stop(); q.Dispose(); Close(); }; q.Start(); }
                };
                tt.Start();
            };
            st.Start();
        }

        if (AutoApply)
        {
            var t = new System.Windows.Forms.Timer { Interval = 1200 };
            t.Tick += (a, b) =>
            {
                t.Stop(); t.Dispose();
                Apply();
                if (AutoRestoreSecs > 0)
                {
                    var r = new System.Windows.Forms.Timer { Interval = AutoRestoreSecs * 1000 };
                    r.Tick += (c, d) =>
                    {
                        r.Stop(); r.Dispose();
                        Restore();
                        var q = new System.Windows.Forms.Timer { Interval = 800 };
                        q.Tick += (e2, f2) => { q.Stop(); q.Dispose(); Close(); };
                        q.Start();
                    };
                    r.Start();
                }
            };
            t.Start();
        }
        // 上次绑过键且开着彩蛋：程序一起来就开始监听，不需要变身
        SyncEggWatch();
    }
}

// ================================================================ 预览面板
class PreviewPanel : Panel
{
    Pendant P;
    readonly System.Windows.Forms.Timer t = new System.Windows.Forms.Timer();
    double phase;
    bool hover;
    bool lastClick;

    public PreviewPanel(Cfg c)
    {
        SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint | ControlStyles.ResizeRedraw, true);
        P = new Pendant(Art.Build(c));
        t.Interval = 16;
        t.Tick += (a, b) => { Phase(); };
        t.Start();
        MouseEnter += (a, b) => { hover = true; };
        MouseLeave += (a, b) => { hover = false; };
        MouseDown += (a, b) => { if (P.L.ClickAnim) P.Click(); if (P.L.ClickSound) Sfx.Play(); };
    }

    public void Rebuild(Look l)
    {
        var old = P;
        P = new Pendant(l);
        P.x = old.x; P.y = old.y; P.tx = old.tx; P.ty = old.ty; P.tilt = old.tilt;
    }

    void Phase()
    {
        phase += 0.016;
        double cx, cy;
        if (hover)
        {
            var p = PointToClient(Cursor.Position);
            cx = p.X; cy = p.Y;
        }
        else
        {
            cx = Width * 0.5 + Math.Sin(phase * 1.1) * Width * 0.22;
            cy = Height * 0.42 + Math.Cos(phase * 1.7) * Height * 0.06;
        }
        if (!P.started) P.Reset(cx, cy);
        P.tx = cx; P.ty = cy;
        bool pressed = (Nat.GetAsyncKeyState(Nat.VK_LBUTTON) & 0x8000) != 0;
        if (pressed && !lastClick && hover) { if (P.L.ClickAnim) P.Click(); if (P.L.ClickSound) Sfx.Play(); }
        lastClick = pressed;
        P.Update(0.016);
        Invalidate();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.TextRenderingHint = TextRenderingHint.ClearTypeGridFit;
        using (var b = new LinearGradientBrush(ClientRectangle, Color.FromArgb(38, 36, 48), Color.FromArgb(26, 25, 33), 90f))
            g.FillRectangle(b, ClientRectangle);
        using (var pen = new Pen(Color.FromArgb(16, 255, 255, 255)))
            for (int xx = 0; xx < Width; xx += 26)
                for (int yy = 0; yy < Height; yy += 26)
                    g.FillEllipse(new SolidBrush(Color.FromArgb(20, 255, 255, 255)), xx, yy, 2, 2);
        if (P.started) P.Draw(g, (float)P.x, (float)P.y);
    }

    protected override void Dispose(bool disposing) { if (disposing) t.Stop(); base.Dispose(disposing); }
}

// ================================================================ 裁剪对话框
class CropForm : Form
{
    readonly Bitmap src;
    readonly int outSize;
    readonly bool circle;
    float zoom = 1f;
    PointF pan = PointF.Empty;
    bool drag; Point lastPt;
    public Bitmap Result;

    public CropForm(string path, int outSize, bool circle, string label)
    {
        this.outSize = outSize; this.circle = circle;
        using (var tmp = Image.FromFile(path)) src = new Bitmap(tmp);
        Text = "调整图片";
        ClientSize = new Size(560, 560);
        StartPosition = FormStartPosition.CenterParent;
        BackColor = Color.FromArgb(24, 23, 30);
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false; MinimizeBox = false;
        var tip = new Label { Text = label + "：拖动移动，滚轮缩放", ForeColor = Color.FromArgb(170, 166, 184), AutoSize = true, Location = new Point(18, 12) };
        Controls.Add(tip);
        var ok = new Btn { Text = "确定", Location = new Point(330, 500), Size = new Size(200, 44) };
        ok.Click += (a, b) => { Result = Render(); DialogResult = DialogResult.OK; Close(); };
        Controls.Add(ok);
        var cancel = new Btn { Text = "取消", Primary = false, Location = new Point(180, 500), Size = new Size(140, 44) };
        cancel.Click += (a, b) => { DialogResult = DialogResult.Cancel; Close(); };
        Controls.Add(cancel);
        MouseWheel += (a, b) => { zoom = Math.Max(0.2f, Math.Min(4f, zoom * (b.Delta > 0 ? 1.1f : 0.9f))); Invalidate(); };
        MouseDown += (a, b) => { drag = true; lastPt = b.Location; };
        MouseUp += (a, b) => { drag = false; };
        MouseMove += (a, b) => { if (drag) { pan.X += b.X - lastPt.X; pan.Y += b.Y - lastPt.Y; lastPt = b.Location; Invalidate(); } };
    }

    Bitmap Render()
    {
        int side = Math.Min(src.Width, src.Height);
        float s = (float)side / outSize;
        var dst = new Bitmap(outSize, outSize, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(dst))
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            if (circle)
            {
                using (var p = new GraphicsPath())
                {
                    p.AddEllipse(0, 0, outSize - 1, outSize - 1);
                    g.SetClip(p);
                }
            }
            float draw = outSize * zoom;
            float cx = outSize / 2f + pan.X, cy = outSize / 2f + pan.Y;
            g.DrawImage(src, new RectangleF(cx - draw / 2, cy - draw / 2, draw, draw));
        }
        return dst;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        var box = new Rectangle(18, 44, 524, 440);
        using (var b = new SolidBrush(Color.FromArgb(16, 15, 20))) g.FillRectangle(b, box);
        float draw = Math.Min(box.Width, box.Height) * zoom;
        float cx = box.X + box.Width / 2f + pan.X, cy = box.Y + box.Height / 2f + pan.Y;
        var st = g.Save();
        g.SetClip(box);
        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
        g.DrawImage(src, new RectangleF(cx - draw / 2, cy - draw / 2, draw, draw));
        g.Restore(st);
        using (var pen = new Pen(Color.FromArgb(255, 128, 170), 2f))
        {
            if (circle) g.DrawEllipse(pen, cx - outSize / 2f, cy - outSize / 2f, outSize, outSize);
            else g.DrawRectangle(pen, cx - outSize / 2f, cy - outSize / 2f, outSize, outSize);
        }
    }
}

// ================================================================ 入口
static class Guard
{
    public static Action Emergency;     // 由 MainForm 注册：停掉覆盖层 + 还原系统光标
    static int busy;

    public static void Trip(string where, Exception ex)
    {
        try { if (Emergency != null) Emergency(); } catch { }
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_crash.txt"), DateTime.Now.ToString("HH:mm:ss") + " [" + where + "] " + ex + "\n"); } catch { }
        if (busy > 0) return;
        busy = 1;
        try
        {
            MessageBox.Show("程序遇到一个错误，已经先把你原来的系统光标换回来了。\n\n"
                + (ex == null ? "未知错误" : ex.Message)
                + "\n\n再点一次「变身为 MUMU 光标」就能接着用。", "MUMU 光标", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        catch { }
        finally { busy = 0; }
    }
}

static class Program
{
    static Mutex instanceMutex;
    internal static void Trace(string m)
    {
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_main.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " " + m + "\n"); } catch { }
    }

    [STAThread]
    static void Main(string[] args)
    {
        Trace("main start args=" + string.Join(" ", args));
        bool forceRestore = Array.IndexOf(args, "--restore") >= 0;
        if (!forceRestore)
        {
            bool created;
            instanceMutex = new Mutex(true, "MUMU_Cursor_SingleInstance", out created);
            if (!created) return;           // 已经在运行了，别再开第二个（--restore 例外）
        }

        // 上次被强杀（标志还留着）→ 先把光标救回来
        try { if (CursorSwitch.IsDirty()) CursorSwitch.Restore(); } catch { }

        try { Nat.SetProcessDPIAware(); } catch { }
        Application.EnableVisualStyles();
        // 任何没接住的异常：先还原系统光标，再给一句人话，而不是弹 .NET 的原始对话框
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
        Application.ThreadException += (a, b) => Guard.Trip("ui", b.Exception);
        AppDomain.CurrentDomain.UnhandledException += (a, b) => Guard.Trip("domain", b.ExceptionObject as Exception);

        int shot = Array.IndexOf(args, "--shot");
        if (shot >= 0 && shot + 1 < args.Length)
        {
            var f = new MainForm();
            f.Show();
            for (int i = 0; i < 40; i++) { Application.DoEvents(); Thread.Sleep(20); }
            using (var b = new Bitmap(f.Width, f.Height))
            {
                f.DrawToBitmap(b, new Rectangle(0, 0, f.Width, f.Height));
                b.Save(args[shot + 1], ImageFormat.Png);
            }
            if (Array.IndexOf(args, "--full") >= 0)
            {
                string basePath = args[shot + 1];
                for (int k = 1; k <= 2; k++)
                {
                    f.Settings.AutoScrollPosition = new Point(0, k * 320);
                    for (int i = 0; i < 10; i++) { Application.DoEvents(); Thread.Sleep(20); }
                    using (var b = new Bitmap(f.Width, f.Height))
                    {
                        f.DrawToBitmap(b, new Rectangle(0, 0, f.Width, f.Height));
                        b.Save(Path.Combine(Path.GetDirectoryName(basePath), Path.GetFileNameWithoutExtension(basePath) + "_s" + k + ".png"), ImageFormat.Png);
                    }
                }
            }
            f.Close();
            return;
        }

        if (Array.IndexOf(args, "--eggpolltest") >= 0)
        {
            var f7 = new MainForm();
            f7.Shown += (a, b) =>
            {
                f7.TestPoll();
            };
            Application.Run(f7);
            return;
        }

        if (Array.IndexOf(args, "--eggnoapply") >= 0)
        {
            var f8 = new MainForm();
            f8.Shown += (a, b) =>
            {
                f8.EggSwitchOnForTest();
                var t2 = new System.Windows.Forms.Timer { Interval = 1500 };
                t2.Tick += (c, d) => { t2.Stop(); t2.Dispose(); f8.Close(); };
                t2.Start();
            };
            Application.Run(f8);
            return;
        }

        if (Array.IndexOf(args, "--eggkeys") >= 0)
        {
            int ix = Array.IndexOf(args, "--eggkeys");
            string k = ix + 1 < args.Length ? args[ix + 1] : "H";
            var f6 = new MainForm { EggTestKey = k };
            Application.Run(f6);
            return;
        }

        if (Array.IndexOf(args, "--stressglow") >= 0)
        {
            var f5 = new MainForm { StressGlow = true };
            Application.Run(f5);
            return;
        }

        if (Array.IndexOf(args, "--clicktest") >= 0)
        {
            try
            {
            var cc = Cfg.Load();
            Console.WriteLine("dir=" + Cfg.Dir);
            var pp2 = new Pendant(Art.Build(cc));
            pp2.Reset(180, 70); pp2.tx = 180; pp2.ty = 70;
            pp2.Click();
            for (int f = 0; f < 30; f++)
            {
                pp2.Update(1.0 / 60);
                if (f == 1 || f == 5 || f == 12 || f == 22)
                {
                    using (var bmp = new Bitmap(360, 420))
                    using (var g = Graphics.FromImage(bmp))
                    {
                        g.Clear(Color.FromArgb(26, 24, 32));
                        pp2.Draw(g, 180, 56);
                        bmp.Save(Path.Combine(Path.GetTempPath(), "click_" + f + ".png"));
                        Console.WriteLine("saved " + f);
                    }
                }
            }
            Console.WriteLine("clicktest done -> " + Cfg.Dir);
            }
            catch (Exception ex) { Console.WriteLine("clicktest FAIL: " + ex.GetType().Name + " | " + ex.Message); }
            return;
        }
        if (Array.IndexOf(args, "--fstest") >= 0)
        {
            var fz = new MainForm { FsTest = true };
            Application.Run(fz);
            return;
        }
        if (Array.IndexOf(args, "--topprobe") >= 0)
        {
            var f8 = new MainForm { TopProbe = true };
            Application.Run(f8);
            return;
        }
        if (Array.IndexOf(args, "--eggime") >= 0)
        {
            var f7 = new MainForm { EggImeTest = true };
            Application.Run(f7);
            return;
        }
        if (Array.IndexOf(args, "--eggbindtest") >= 0)
        {
            var f5 = new MainForm { EggBindTest = true };
            Application.Run(f5);
            return;
        }
        if (Array.IndexOf(args, "--eggtry") >= 0)
        {
            var f4 = new MainForm { EggTry = true };
            Application.Run(f4);
            return;
        }

        int ar = Array.IndexOf(args, "--autorestore");
        if (ar >= 0 && ar + 1 < args.Length)
        {
            var f3 = new MainForm { AutoApply = true, AutoRestoreSecs = int.Parse(args[ar + 1]) };
            Application.Run(f3);
            return;
        }

        if (Array.IndexOf(args, "--autoapply") >= 0)
        {
            var f2 = new MainForm { AutoApply = true };
            Application.Run(f2);
            return;
        }

        if (Array.IndexOf(args, "--restore") >= 0)
        {
            try { CursorSwitch.Restore(); Console.WriteLine("restore ok " + CursorSwitch.LastLog); }
            catch (Exception ex) { Console.WriteLine("ERR " + ex.GetType().FullName + " | " + ex.Message); }
            return;
        }
        if (Array.IndexOf(args, "--apply") >= 0) { CursorSwitch.Apply(); return; }
        int ti = Array.IndexOf(args, "--test");
        if (ti >= 0)
        {
            double secs = 4;
            if (ti + 1 < args.Length) double.TryParse(args[ti + 1], out secs);
            var ov = new Overlay(Art.Build(Cfg.Load()));
            var th = new Thread(ov.Run) { IsBackground = true };
            th.Start();
            var sw2 = System.Diagnostics.Stopwatch.StartNew();
            for (int i = 0; i < 100 && !ov.HideReady; i++) Thread.Sleep(20);
            try { CursorSwitch.Apply(); } catch (Exception ex) { Console.WriteLine("apply err " + ex.GetType().Name); }
            bool applied = false;
            for (int i = 0; i < (int)(secs * 10); i++)
            {
                Thread.Sleep(100);
                if (!applied && CursorSwitch.Applied) { applied = true; Console.WriteLine("applied at " + (i * 100) + "ms"); }
            }
            ov.Stop();
            Thread.Sleep(250);
            CursorSwitch.Restore();
            Console.WriteLine("test done: applied=" + applied + " " + CursorSwitch.LastLog);
            var me = System.Diagnostics.Process.GetCurrentProcess();
            double cpuPct = me.TotalProcessorTime.TotalMilliseconds / Math.Max(1, sw2.Elapsed.TotalMilliseconds) * 100 / Environment.ProcessorCount;
            Console.WriteLine("cpu avg " + cpuPct.ToString("F2") + "% of total, mem " + (me.WorkingSet64 / 1048576) + "MB, frames " + ov.Frames + " hidden=" + ov.SysCursorHidden + " streak=" + ov.hiddenStreak + " vis=" + Nat.IsWindowVisible(ov.hwnd));
            if (ov.Frames > 0) Console.WriteLine("per-frame ms: upd " + (ov.TUpd / ov.Frames).ToString("F2") + " draw " + (ov.TDraw / ov.Frames).ToString("F2") + " push " + (ov.TPush / ov.Frames).ToString("F2") + " topmost " + (ov.TTop / ov.Frames).ToString("F2"));
            return;
        }

        Trace("form creating");
        try
        {
            var f = new MainForm();
            Trace("form created, entering loop");
            Application.Run(f);
            Trace("loop exited");
        }
        catch (Exception ex) { Trace("FATAL " + ex); throw; }
    }
}
