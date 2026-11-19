import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

if "ElevateRestart" in s:
    print("already patched")
    raise SystemExit

old = "        settings.Controls.Add(eggHint);"
new = (
    "        eggHint.Click += (a, b) => { if (Nat.IsLowIntegrity()) ElevateRestart(); };\n"
    "        settings.Controls.Add(eggHint);"
)
assert old in s, "anchor eggHint add not found"
s = s.replace(old, new, 1)

anchor = "    public void SyncEggWatch()"
assert anchor in s, "anchor SyncEggWatch not found"
method = (
    "    void ElevateRestart()\n"
    "    {\n"
    "        try\n"
    "        {\n"
    "            Program.DropInstance();          // 先放开单实例锁，否则新进程会以为已有实例在跑\n"
    "            var psi = new System.Diagnostics.ProcessStartInfo(Application.ExecutablePath);\n"
    "            psi.UseShellExecute = true;\n"
    "            psi.Verb = \"runas\";              // 触发 UAC：用户点「是」＝管理员权限\n"
    "            System.Diagnostics.Process.Start(psi);\n"
    "            Close();\n"
    "        }\n"
    "        catch (Exception ex)\n"
    "        {\n"
    "            MessageBox.Show(\"没能用管理员权限重启：\\n\" + ex.Message, \"MUMU 光标\");\n"
    "        }\n"
    "    }\n"
    "\n"
)
s = s.replace(anchor, method + anchor, 1)

old2 = "    static Mutex instanceMutex;"
assert old2 in s, "mutex field not found"
new2 = (
    "    static Mutex instanceMutex;\n"
    "    public static void DropInstance()\n"
    "    {\n"
    "        try { if (instanceMutex != null) instanceMutex.ReleaseMutex(); } catch { }\n"
    "    }"
)
s = s.replace(old2, new2, 1)

p.write_text(s, encoding="utf-8")
print("elevate patched")
