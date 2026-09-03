# -*- coding: utf-8 -*-
"""
남한 시군구 경계 지도 생성기
- 시·군·구 경계선 + 시 이름 표기 (광역시 구는 이름 제외)
- 광역시/도 경계는 두껍게
- 북한 하단 형태 추가
- 1m x 1.359m 인화용 초고해상도 출력
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely.ops import unary_union

# 한글 폰트
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

DATA = r"D:\SEMCoWork\Session25_map\skorea-municipalities-2018-geo.json"
NK = r"D:\SEMCoWork\Session25_map\north_korea.geojson"
OUT = r"D:\SEMCoWork\Session25_map\south_korea_map.png"

# 광역시/특별시 코드 (구 경계 유지)
METRO_CODES = {"11", "21", "22", "23", "24", "25", "26"}
# 시도 전체 이름
SIDO_NAMES = {
    "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
    "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
    "31": "경기도", "32": "강원도", "33": "충청북도", "34": "충청남도",
    "35": "전라북도", "36": "전라남도", "37": "경상북도", "38": "경상남도",
    "39": "제주특별자치도",
}

# 출력 크기 (인치) : 가로 1m, 세로는 실제 지리 비율(1.391)에 맞춤 (북한 일부)
W_INCH = 39.37          # 1m
H_INCH = W_INCH * 1.391 # 1.391m (실제 지리 비율, 왜곡 없음)
DPI = 1000  # 인화용 초고해상도

# 북한 절단 위도 (이 위도 아래만 표시)
NK_CUT = 38.71740371170524

def main():
    with open(DATA, encoding="utf-8") as f:
        gj = json.load(f)

    features = gj["features"]

    # 남한 시군구 (울릉도/독도 제외)
    polys = []          # 채우기용 폴리곤 (광역시 구 + 도 시/군)
    names = {}          # 이름 표기 대상 (시/군 이름)
    sido_groups = {}    # 시도 코드 -> 폴리곤 리스트 (시도 경계용)
    city_groups = {}    # 도: 시/군 이름 -> 폴리곤 리스트 (병합용)
    for ft in features:
        name = ft["properties"]["name"]
        code = ft["properties"]["code"]
        if name == "울릉군":
            continue  # 울릉도/독도 제외
        geom = shape(ft["geometry"])
        sido_groups.setdefault(code[:2], []).append(geom)
        if code[:2] in METRO_CODES:
            # 광역시/특별시: 구 경계 유지 (이름은 아래에서 병합 후 표기)
            polys.append(geom)
        else:
            # 도: 시/군 단위로 병합 (구로 나뉜 시는 시 이름으로 병합)
            city = name[:name.index("시") + 1] if "시" in name else name
            city_groups.setdefault(city, []).append(geom)

    # 도 시/군 병합
    for city, geoms in city_groups.items():
        merged = unary_union(geoms)
        polys.append(merged)
        names[city] = merged

    # 시도 이름 (전체 병합 후 가운데 위치)
    sido_names = {}   # 시도 코드 -> (이름, 병합 폴리곤)
    for code, geoms in sido_groups.items():
        if code in SIDO_NAMES:
            sido_names[code] = (SIDO_NAMES[code], unary_union(geoms))

    # 시도 경계 (unary_union으로 합쳐 외곽선 추출)
    sido_boundaries = []
    for code, geoms in sido_groups.items():
        merged = unary_union(geoms)
        sido_boundaries.append(merged)

    # 전체 범위 (남한 + 북한)
    xs, ys = [], []
    for g in polys:
        minx, miny, maxx, maxy = g.bounds
        xs += [minx, maxx]
        ys += [miny, maxy]
    # 북한 범위 포함 (절단선 아래만)
    with open(NK, encoding="utf-8") as f:
        nk_gj = json.load(f)
    nk_geom = shape(nk_gj["geometry"])
    # 절단선 아래로 클립
    from shapely.geometry import box
    nk_clip = nk_geom.intersection(box(-180, -90, 180, NK_CUT))
    nk_b = nk_clip.bounds
    xs += [nk_b[0], nk_b[2]]
    ys += [nk_b[1], nk_b[3]]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    # 포항 동쪽 여백 추가 (오른쪽 끝에 공간)
    xpad = (xmax - xmin) * 0.03
    xmax += xpad

    fig, ax = plt.subplots(figsize=(W_INCH, H_INCH), dpi=DPI)
    # 실제 지리 비율(1.391)로 왜곡 없이 그리기 위해 aspect 조정
    # aspect = 실제비율 / 좌표비율 = 1.391 / 1.127 = 1.234
    ax.set_aspect(1.391 / 1.127)

    # 배경 (바다)
    ax.set_facecolor("#cfe8f7")
    fig.set_facecolor("#cfe8f7")

    # 북한 하단 형태 (연한색, 경계선 없음) - 절단선 아래만
    g = nk_clip
    if g.geom_type == "Polygon":
        polys_list = [g]
    else:
        polys_list = list(g.geoms)
    for poly in polys_list:
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor="#e8f4e8", edgecolor="none", zorder=1)

    # 시군구 경계 채우기 (연한색) + 경계선
    for g in polys:
        if g.geom_type == "Polygon":
            polys_list = [g]
        else:
            polys_list = list(g.geoms)
        for poly in polys_list:
            x, y = poly.exterior.xy
            ax.fill(x, y, facecolor="#e8f4e8", edgecolor="#333333",
                    linewidth=0.5, zorder=2)
            ax.plot(x, y, color="#333333", linewidth=0.5, zorder=3)

    # 시도 경계 두껍게
    for g in sido_boundaries:
        if g.geom_type == "Polygon":
            polys_list = [g]
        else:
            polys_list = list(g.geoms)
        for poly in polys_list:
            x, y = poly.exterior.xy
            ax.plot(x, y, color="#111111", linewidth=3.0, zorder=4)

    # 시/군 이름 표기
    for name, g in names.items():
        pt = g.representative_point()
        ax.text(pt.x, pt.y, name, fontsize=24, ha="center", va="center",
                color="#222222", zorder=5)

    # 시도 이름 표기 (특별시/광역시: 병하게, 도: 흐리게 2배)
    for code, (sname, g) in sido_names.items():
        pt = g.centroid
        if code in METRO_CODES:
            ax.text(pt.x, pt.y, sname, fontsize=24, ha="center", va="center",
                    color="#222222", zorder=5)
        else:
            ax.text(pt.x, pt.y, sname, fontsize=48, ha="center", va="center",
                    color="#bbbbbb", zorder=4)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.axis("off")

    plt.tight_layout(pad=0)
    plt.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    print("saved:", OUT)

if __name__ == "__main__":
    main()