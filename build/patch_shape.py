import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# ---------- Cfg: 造型 / 颜色 拆成两个字段 ----------
s = s.replace('public string Pointer = "arrow";',
              'public string PointerShape = "chevron";   // chevron|arrow|cross|ring|diamond|move\n'
              '    public string PointerColor = "silver";    // silver|gold|neon|ink|bubble')

s = s.replace('case "Pointer": c.Pointer = v; break;',
              'case "Pointer":\n'
              '                            // 老配置只有颜色名：当成「雪佛龙 + 那个颜色」\n'
              '                            if (Array.IndexOf(new[] { "silver", "gold", "neon", "ink", "bubble" }, v) >= 0) { c.PointerShape = "chevron"; c.PointerColor = v; }\n'
              '                            else if (Array.IndexOf(new[] { "arrow", "cross", "ring", "diamond", "move" }, v) >= 0) { c.PointerShape = v; }\n'
              '                            break;\n'
              '                        case "PointerShape": c.PointerShape = v; break;\n'
              '                        case "PointerColor": c.PointerColor = v; break;')

s = s.replace('''        // 老版本的 5 个「换色雪佛龙」已换成 5 个不同造型，旧名字统一落到箭头
        if (Array.IndexOf(new[] { "arrow", "cross", "ring", "diamond", "move" }, c.Pointer) < 0) c.Pointer = "arrow";''',
'''        // 造型 / 颜色 各留一个兜底，配置写坏了也不至于空白
        if (Array.IndexOf(new[] { "chevron", "arrow", "cross", "ring", "diamond", "move" }, c.PointerShape) < 0) c.PointerShape = "chevron";
        if (Array.IndexOf(new[] { "silver", "gold", "neon", "ink", "bubble" }, c.PointerColor) < 0) c.PointerColor = "silver";''')

s = s.replace('lines.Add("Pointer=" + Pointer);',
              'lines.Add("PointerShape=" + PointerShape);\n            lines.Add("PointerColor=" + PointerColor);')

# ---------- Art.Build ----------
s = s.replace('l.Pointer = Res("pointer_" + c.Pointer + ".png");',
              'l.Pointer = Res("pointer_" + c.PointerShape + "_" + c.PointerColor + ".png");')
s = s.replace('if (c.Pointer == "arrow") { l.HotX = 9f; l.HotY = 6f; }',
              'if (c.PointerShape == "chevron") { l.HotX = 10f; l.HotY = 10f; }\n'
              '        else if (c.PointerShape == "arrow") { l.HotX = 9f; l.HotY = 6f; }')

print("cfg/build patched:", s.count("PointerShape"))
p.write_text(s, encoding="utf-8")
