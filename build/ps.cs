using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

class PS
{
    [DllImport("winmm.dll", CharSet = CharSet.Unicode, EntryPoint = "PlaySoundW")]
    static extern bool PlaySound(string f, IntPtr m, int flags);
    [DllImport("winmm.dll")] static extern int waveOutGetNumDevs();

    static void Main(string[] a)
    {
        string path = a.Length > 0 ? a[0] : Path.Combine(Path.GetTempPath(), "MUMUCursor", "egg.wav");
        Console.WriteLine("file=" + path + " exists=" + File.Exists(path) + " size=" + (File.Exists(path) ? new FileInfo(path).Length.ToString() : "-"));
        Console.WriteLine("waveOutDevs=" + waveOutGetNumDevs());
        var sw = Stopwatch.StartNew();
        int flags = 0x20000 | 0x2;            // FILENAME | NODEFAULT (sync)
        bool ok = PlaySound(path, IntPtr.Zero, flags);
        sw.Stop();
        Console.WriteLine("sync play ok=" + ok + " err=" + Marshal.GetLastWin32Error() + " elapsed=" + sw.ElapsedMilliseconds + "ms");
    }
}
