# -*- coding: utf-8 -*-
"""把地图边界数据和景点数据注入模板，生成站点根目录的 index.html。

用法：
    cd source
    python build.py

改完之后刷新浏览器即可看到效果（index.html 是纯静态文件，不需要服务器）。
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)


def read(name):
    path = os.path.join(BASE, name)
    with open(path, encoding="utf-8") as f:
        return f.read()


tpl = read("template.html")
map_data = read("map_paths.js")
spots = read("spots.js")

# 占位符必须存在，否则说明模板被改坏了
for token, label in (("/*__MAP_DATA__*/", "地图数据"), ("/*__SPOTS__*/", "景点数据")):
    if token not in tpl:
        raise SystemExit("模板 template.html 里找不到%s占位符 %s" % (label, token))

html = tpl.replace("/*__MAP_DATA__*/", map_data.strip())
html = html.replace("/*__SPOTS__*/", spots.strip())

out = os.path.join(ROOT, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print("已生成: %s" % out)
print("大小: %.1f KB" % (os.path.getsize(out) / 1024))
print("景点数: %d 条" % spots.count("\n{u:"))
