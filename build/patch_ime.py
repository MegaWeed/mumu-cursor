import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert old in s, "MISSING: " + old[:70]
    s = s.replace(old, new, count)


# 1) 输入法开着时，按键会被系统换成 VK_PROCESSKEY(229)：这种不能拿来绑
rep('''        if (binding)
        {
            // 什么键都收：字母、数字、方向、小键盘、符号……
            if (e.KeyCode != Keys.None) BindEgg((int)e.KeyCode);
            e.Handled = true; e.SuppressKeyPress = true;
            return;
        }''',
'''        if (binding)
        {
            // 中文输入法开着时，按键会被系统“吞”成 VK_PROCESSKEY(229)，不能拿来绑
            int kv = (int)e.KeyCode;
            if (kv != 229 && e.KeyCode != Keys.None && e.KeyCode != Keys.ProcessKey) BindEgg(kv);
            e.Handled = true; e.SuppressKeyPress = true;
            return;
        }''')

# 2) BindEgg 里再兜一层：0 / 229 / 255（VK_NONAME）直接拒绝，并提示换一个
rep('''            UnbindHook();
            C.EggKey = vk;''',
'''            if (vk == 0 || vk == 229 || vk == 255 || vk == -1)
            {
                if (eggHint != null)
                {
                    eggHint.Text = "这个键被输入法/系统占用了，换一个（比如 F6~F12）。";
                    eggHint.ForeColor = Color.FromArgb(255, 170, 120);
                }
                return;
            }
            UnbindHook();
            C.EggKey = vk;''')

# 3) 绑定期间哪怕 SyncEggWatch 被调用，也别把“按一下想绑的键”这句覆盖掉
rep('''            if (eggHint != null && !binding)
            {
                if (Nat.IsLowIntegrity())''',
'''            if (eggHint != null && binding)
            {
                eggHint.Text = "现在按一下想绑的键位，绑定后就可以按下按键触发彩蛋。";
                eggHint.ForeColor = Color.FromArgb(255, 190, 120);
                return;
            }
            if (eggHint != null)
            {
                if (Nat.IsLowIntegrity())''')

# 4) 未知键名别显示成“键229”这种，统一给人话
rep('''        return "键" + vk;''', '''        return "VK" + vk + " 键";''')

p.write_text(s, encoding="utf-8")
print("ime guard added")
