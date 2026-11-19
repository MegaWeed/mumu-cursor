import pathlib

p = pathlib.Path(r"C:\Users\16195\Documents\deepseek-harness\default-workspace\mumu-cursor\MumuCursor.cs")
s = p.read_text(encoding="utf-8")

# 去掉诊断输出
s = s.replace('        try { Console.WriteLine("LAYOUT need=" + NeedH + " stable=" + StableNeedH + " mode=" + C.Mode); } catch { }\n', "", 1)

# 常量换成运行时量出来的「动态模式高度」
s = s.replace(
    "    const int StableNeedH = 887;    // 动态模式的内容高度；静态模式内容更少，但窗口不准变矮\n",
    "    int NeedHDynamic;               // 动态模式的内容高度（启动时量一次），静态模式也按它撑高窗口\n", 1)
s = s.replace("        int need = Math.Max(NeedH, StableNeedH);",
              "        int need = Math.Max(NeedH, NeedHDynamic);", 1)

# 启动时量动态高度：静态启动时临时切一次再切回来
old = "        FillSettings();\n    }\n\n    // 切换「动态 / 静态」"
new = ("        FillSettings();\n"
       "        if (C.Mode == \"static\")      // 先量一次动态模式的自然高度，两种模式窗口才一样高\n"
       "        {\n"
       "            C.Mode = \"pendant\"; FillSettings(); NeedHDynamic = NeedH;\n"
       "            C.Mode = \"static\"; FillSettings();\n"
       "        }\n"
       "        else NeedHDynamic = NeedH;\n"
       "    }\n\n    // 切换「动态 / 静态」")
assert old in s, "ctor tail"
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("stable height measured at runtime")
