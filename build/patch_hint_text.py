import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "MISSING:\n" + old[:160]
    s = s.replace(old, new, 1)


# 1) 低权限提示：改成普通用户也看得懂、不点破"聊天窗口"
rep('''eggHint.Text = "⚠ 程序是「低权限」启动的（多半是从聊天窗口点开的），读不到全局按键。请到资源管理器里双击 MUMU光标.exe。";''',
'''eggHint.Text = "⚠ 权限受限，读不到键盘按键。请关掉本程序，再到文件夹里双击 MUMU光标.exe 打开。";''')

# 2) 提示行给两行高度，避免第二行被裁掉
rep('''            AutoSize = false,
            Size = new Size(390, 30),
            Location = new Point(16, y),''',
'''            AutoSize = false,
            Size = new Size(390, 38),      // 两行高度，长提示不会被裁
            Location = new Point(16, y),''')

p.write_text(s, encoding="utf-8")
print("hint rewritten")
