import pathlib
p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 1) render thread must NOT call SetSystemCursor (it blocks); only signal readiness
old = "                if (ok) { fails = 0; if (HideSystem && !stopped && !CursorSwitch.Applied) CursorSwitch.Apply(); }"
new = "                if (ok) { fails = 0; HideReady = true; }"
assert old in s
s = s.replace(old, new, 1)

old = "    public volatile bool HideSystem = true;"
new = "    public volatile bool HideSystem = true;\n    public volatile bool HideReady;"
assert old in s
s = s.replace(old, new, 1)

# 2) MainForm: apply cursor on the UI thread once the overlay is actually painting
old = "    Overlay overlay; Thread overlayThread;"
new = "    Overlay overlay; Thread overlayThread; Timer hideTimer;"
assert old in s
s = s.replace(old, new, 1)

old = """            overlay = new Overlay(look);
            overlayThread = new Thread(overlay.Run) { IsBackground = true };
            overlayThread.Start();
            RefreshStatus();"""
new = """            overlay = new Overlay(look);
            overlayThread = new Thread(overlay.Run) { IsBackground = true };
            overlayThread.Start();
            // 等渲染线程真的推上去一帧，再在 UI 线程换光标（SetSystemCursor 可能在非消息泵线程上卡死）
            hideTimer = new Timer { Interval = 80 };
            hideTimer.Tick += (a1, a2) =>
            {
                if (overlay == null) { hideTimer.Stop(); return; }
                if (!overlay.HideReady) return;
                hideTimer.Stop();
                try { CursorSwitch.Apply(); } catch { }
            };
            hideTimer.Start();
            RefreshStatus();"""
assert old in s
s = s.replace(old, new, 1)

# 3) --test: apply from the main thread after the overlay signals ready
old = """            var th = new Thread(ov.Run) { IsBackground = true };
            th.Start();
            var sw2 = System.Diagnostics.Stopwatch.StartNew();
            bool applied = false;"""
new = """            var th = new Thread(ov.Run) { IsBackground = true };
            th.Start();
            var sw2 = System.Diagnostics.Stopwatch.StartNew();
            for (int i = 0; i < 100 && !ov.HideReady; i++) Thread.Sleep(20);
            try { CursorSwitch.Apply(); } catch (Exception ex) { Console.WriteLine("apply err " + ex.GetType().Name); }
            bool applied = false;"""
assert old in s
s = s.replace(old, new, 1)

# 4) stop the timer when restoring
old = "            if (overlay != null) { overlay.Stop(); overlay = null; Thread.Sleep(220); }\n            CursorSwitch.Restore();"
new = "            if (hideTimer != null) { hideTimer.Stop(); hideTimer.Dispose(); hideTimer = null; }\n            if (overlay != null) { overlay.Stop(); overlay = null; Thread.Sleep(220); }\n            CursorSwitch.Restore();"
assert old in s
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("patched: apply moved to UI thread")
