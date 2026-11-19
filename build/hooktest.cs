using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

class HookTest
{
    delegate IntPtr LowLevelProc(int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    static extern IntPtr SetWindowsHookEx(int idHook, LowLevelProc lpfn, IntPtr hMod, uint dwThreadId);
    [DllImport("user32.dll")] static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);
    [DllImport("kernel32.dll", CharSet = CharSet.Auto)] static extern IntPtr GetModuleHandle(string name);
    [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint flags, IntPtr extra);

    static IntPtr hook;
    static string log = Path.Combine(Path.GetTempPath(), "hooktest.log");

    [StructLayout(LayoutKind.Sequential)]
    struct KKS { public int vkCode, scanCode, flags, time; public IntPtr extra; }

    static LowLevelProc proc;

    static IntPtr Callback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        File.AppendAllText(log, "cb nCode=" + nCode + " wParam=" + wParam + "\n");
        return CallNextHookEx(hook, nCode, wParam, lParam);
    }

    [STAThread]
    static void Main()
    {
        File.WriteAllText(log, "start\n");
        proc = Callback;
        hook = SetWindowsHookEx(13, proc, GetModuleHandle(null), 0);
        File.AppendAllText(log, "hook=" + hook + " err=" + Marshal.GetLastWin32Error() + "\n");

        var t = new Thread(() => { Thread.Sleep(600); keybd_event(0x48, 0, 0, IntPtr.Zero); Thread.Sleep(50); keybd_event(0x48, 0, 2, IntPtr.Zero); });
        t.IsBackground = true; t.Start();

        // 简易消息泵
        for (int i = 0; i < 200; i++)
        {
            MSG m;
            while (PeekMessage(out m, IntPtr.Zero, 0, 0, 1))
            {
                TranslateMessage(ref m); DispatchMessage(ref m);
            }
            Thread.Sleep(10);
        }
        File.AppendAllText(log, "done\n");
    }

    [StructLayout(LayoutKind.Sequential)]
    struct MSG { public IntPtr hwnd; public uint message; public IntPtr wParam, lParam; public uint time; public int x, y; }

    [DllImport("user32.dll")] static extern bool PeekMessage(out MSG m, IntPtr hwnd, uint min, uint max, uint remove);
    [DllImport("user32.dll")] static extern bool TranslateMessage(ref MSG m);
    [DllImport("user32.dll")] static extern IntPtr DispatchMessage(ref MSG m);
}
