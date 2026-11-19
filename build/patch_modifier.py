import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

old = '''            if (vk == 0 || vk == 229 || vk == 255 || vk == -1)'''
new = '''            // 单独的 Shift / Ctrl / Alt / Win 绑了也用不了（要一直按着），直接拦掉
            if (vk == 0x10 || vk == 0x11 || vk == 0x12 || vk == 0x5B || vk == 0x5C)
            {
                if (eggHint != null)
                {
                    eggHint.Text = "别绑单独的 Shift / Ctrl / Alt，换一个（比如 F6~F12）。";
                    eggHint.ForeColor = Color.FromArgb(255, 170, 120);
                }
                return;
            }
            if (vk == 0 || vk == 229 || vk == 255 || vk == -1)'''
assert old in s
s = s.replace(old, new)

old2 = '''        if (c.EggKey == 229 || c.EggKey == 255 || c.EggKey < 0) c.EggKey = 0;'''
new2 = '''        if (c.EggKey == 229 || c.EggKey == 255 || c.EggKey < 0) c.EggKey = 0;
        if (c.EggKey == 0x10 || c.EggKey == 0x11 || c.EggKey == 0x12 || c.EggKey == 0x5B || c.EggKey == 0x5C) c.EggKey = 0;'''
assert old2 in s
s = s.replace(old2, new2)

p.write_text(s, encoding="utf-8")
print("modifier guard ok")
