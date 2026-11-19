import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

s = s.replace("""        kbdHook = Nat.SetWindowsHookEx(Nat.WH_KEYBOARD_LL, kbdProc, Nat.GetModuleHandle(null), 0);
        if (kbdHook == IntPtr.Zero && eggHint != null)""",
"""        kbdHook = Nat.SetWindowsHookEx(Nat.WH_KEYBOARD_LL, kbdProc, Nat.GetModuleHandle(null), 0);
        try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " set hook=" + kbdHook + " err=" + Marshal.GetLastWin32Error() + "\\n"); } catch { }
        if (kbdHook == IntPtr.Zero && eggHint != null)""")

s = s.replace("""            if (nCode >= 0 && C.EggOn && !binding &&
                (wParam == (IntPtr)Nat.WM_KEYDOWN || wParam == (IntPtr)Nat.WM_SYSKEYDOWN))
            {
                var info = (Nat.KBDLLHOOKSTRUCT)Marshal.PtrToStructure(lParam, typeof(Nat.KBDLLHOOKSTRUCT));""",
"""            if (nCode >= 0 && (wParam == (IntPtr)Nat.WM_KEYDOWN || wParam == (IntPtr)Nat.WM_SYSKEYDOWN))
            {
                var info = (Nat.KBDLLHOOKSTRUCT)Marshal.PtrToStructure(lParam, typeof(Nat.KBDLLHOOKSTRUCT));
                try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "mumu_hook.log"), DateTime.Now.ToString("HH:mm:ss.fff") + " key vk=" + info.vkCode + " on=" + C.EggOn + " bind=" + binding + " want=" + C.EggKey + "\\n"); } catch { }""")

p.write_text(s, encoding="utf-8")
print("debug hook logging added")
