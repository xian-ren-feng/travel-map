# -*- coding: utf-8 -*-
"""把四川省 21 市州的 GeoJSON 转成 SVG path，供单文件网页内嵌使用。"""
import json, math, os

SRC = r"C:/Users/Werobot/WorkBuddy/2026-11-20-14-55-48/四川旅游规划/assets/sc_raw.json"
OUT = r"C:/Users/Werobot/WorkBuddy/2026-11-20-14-55-48/四川旅游规划/assets/map_paths.js"

W, H, PAD = 1000, 860, 30

REGION = {
    "成都市": "成都平原", "德阳市": "成都平原", "绵阳市": "成都平原", "眉山市": "成都平原",
    "资阳市": "成都平原", "遂宁市": "成都平原", "乐山市": "成都平原", "雅安市": "成都平原",
    "自贡市": "川南", "泸州市": "川南", "内江市": "川南", "宜宾市": "川南",
    "南充市": "川东北", "达州市": "川东北", "广安市": "川东北", "巴中市": "川东北", "广元市": "川东北",
    "攀枝花市": "攀西", "凉山彝族自治州": "攀西",
    "阿坝藏族羌族自治州": "川西北", "甘孜藏族自治州": "川西北",
}
SHORT = {"凉山彝族自治州": "凉山州", "阿坝藏族羌族自治州": "阿坝州", "甘孜藏族自治州": "甘孜州"}


def rdp(pts, eps):
    """Douglas-Peucker 折线简化"""
    if len(pts) < 3:
        return pts
    dmax, idx = 0.0, 0
    x1, y1 = pts[0]
    x2, y2 = pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy)
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        if norm == 0:
            d = math.hypot(x - x1, y - y1)
        else:
            d = abs(dy * (x - x1) - dx * (y - y1)) / norm
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = rdp(pts[:idx + 1], eps)
        right = rdp(pts[idx:], eps)
        return left[:-1] + right
    return [pts[0], pts[-1]]


def poly_area_centroid(ring):
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        cr = x1 * y2 - x2 * y1
        a += cr
        cx += (x1 + x2) * cr
        cy += (y1 + y2) * cr
    a *= 0.5
    if abs(a) < 1e-9:
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        return sum(xs) / len(xs), sum(ys) / len(ys), 0
    return cx / (6 * a), cy / (6 * a), abs(a)


data = json.load(open(SRC, encoding="utf-8"))
feats = data["features"]

lons, lats = [], []
for f in feats:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        for ring in poly:
            for lon, lat in ring:
                lons.append(lon); lats.append(lat)

lon0, lon1 = min(lons), max(lons)
lat0, lat1 = min(lats), max(lats)
COS = math.cos(math.radians((lat0 + lat1) / 2))
wM = (lon1 - lon0) * COS
hM = lat1 - lat0
scale = min((W - 2 * PAD) / wM, (H - 2 * PAD) / hM)
offX = (W - wM * scale) / 2
offY = (H - hM * scale) / 2


def project(lon, lat):
    return (round((lon - lon0) * COS * scale + offX, 1),
            round((lat1 - lat) * scale + offY, 1))


out = []
total_pts = 0
for f in feats:
    name = f["properties"]["name"]
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    ds = []
    biggest = None
    for poly in polys:
        for ring in poly:
            pts = [project(lon, lat) for lon, lat in ring]
            if len(pts) < 4:
                continue
            simp = rdp(pts, 0.6)
            total_pts += len(simp)
            d = "M" + " ".join(f"{p[0]} {p[1]}" if i else f"{p[0]} {p[1]}" for i, p in enumerate(simp)) + "Z"
            # 去掉重复空格，更紧凑
            ds.append(d)
            c = poly_area_centroid(simp)
            if biggest is None or c[2] > biggest[2]:
                biggest = c
    # 该市州在 SVG 坐标里的边界框，用于单市视图放大
    # 只按面积最大的那块主体算，避免飞地/小岛把框拉大导致画面偏移
    main_pts, main_area = None, -1
    for poly in polys:
        pts = [project(lon, lat) for lon, lat in poly[0]]
        if len(pts) < 4:
            continue
        a = abs(poly_area_centroid(pts)[2])
        if a > main_area:
            main_area, main_pts = a, pts
    if not main_pts:
        main_pts = [project(lon, lat) for poly in polys for ring in poly for lon, lat in ring]
    xs = [p[0] for p in main_pts]
    ys = [p[1] for p in main_pts]
    bb = [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)]

    out.append({
        "name": name,
        "short": SHORT.get(name, name.replace("市", "")),
        "region": REGION[name],
        "d": " ".join(ds),
        "cx": round(biggest[0], 1),
        "cy": round(biggest[1], 1),
        "bb": bb,
    })

order = ["成都平原", "川南", "川东北", "攀西", "川西北"]
out.sort(key=lambda x: order.index(x["region"]))

body = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
proj = json.dumps({"lon0": round(lon0, 6), "lat1": round(lat1, 6),
                   "cos": round(COS, 8), "scale": round(scale, 6),
                   "offX": round(offX, 4), "offY": round(offY, 4)},
                  ensure_ascii=False, separators=(",", ":"))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("/* 四川省 21 个市州边界（教学示意，不作地理依据） */\n")
    fh.write("const SC_MAP=" + body + ";\n")
    fh.write("const PROJ=" + proj + ";\n")

print("viewBox: 0 0 %d %d" % (W, H))
print("保留点数:", total_pts)
print("输出大小: %.1f KB" % (os.path.getsize(OUT) / 1024))
for o in out:
    print("  %-6s %-5s (%s, %s)" % (o["short"], o["region"], o["cx"], o["cy"]))
