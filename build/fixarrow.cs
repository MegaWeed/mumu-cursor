using System;
using System.Runtime.InteropServices;
class P {
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern IntPtr LoadImageW(IntPtr i, string n, int t, int cx, int cy, int f);
  [DllImport("user32.dll", SetLastError=true)] static extern bool SetSystemCursor(IntPtr h, int id);
  [DllImport("user32.dll")] static extern int GetSystemMetrics(int i);
  [DllImport("user32.dll")] static extern bool SystemParametersInfoW(int a,int p,IntPtr v,int w);
  static void Try(string path, int flags, int cx, int cy) {
    IntPtr h = LoadImageW(IntPtr.Zero, path, 2, cx, cy, flags);
    int e1 = Marshal.GetLastWin32Error();
    bool ok = false; int e2 = 0;
    if (h != IntPtr.Zero) { ok = SetSystemCursor(h, 32512); e2 = Marshal.GetLastWin32Error(); }
    Console.WriteLine(path + " flags=" + flags + " cx=" + cx + " h=" + h + " err=" + e1 + " set=" + ok + " err2=" + e2);
  }
  static void Main() {
    int cx = GetSystemMetrics(13), cy = GetSystemMetrics(14);
    Console.WriteLine("metrics " + cx + "x" + cy);
    Try(@"C:\Windows\Cursors\aero_arrow.cur", 0x10, 0, 0);
    Try(@"C:\Windows\Cursors\aero_arrow.cur", 0x10 | 0x40, cx, cy);
    Try(@"C:\Windows\Cursors\aero_arrow.cur", 0x10, cx, cy);
    SystemParametersInfoW(0x57, 0, IntPtr.Zero, 2);
  }
}
