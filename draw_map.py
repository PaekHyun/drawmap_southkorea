# -*- coding: utf-8 -*-
"""
남한 지도 생성기 (레고 픽셀아트 소스용)
- 바다: 파랑 / 육지: 흰색
- 도(시도) 경계: 진하게 / 시·군 경계: 연하게 / 구 경계: 없음
- 섬 크기 필터: ISLAND_MIN_AREA 이하 섬 제거
- 북한 하단 윤곽 표시
- 1m × 1.5m 초고해상도 출력
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import shape, box, LineString
from shapely.ops import unary_union

# 한글 폰트
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# ── 파일 경로 ──
DATA = r"D:\SEMCoWork\Session25_map\skorea-municipalities-2018-geo.json"
NK = r"D:\SEMCoWork\Session25_map\north_korea.geojson"
OUT = r"D:\SEMCoWork\Session25_map\south_korea_map.png"

# ── 출력 설정 ──
W_INCH = 39.37            # 가로 1m
H_INCH = W_INCH * 1.5     # 세로 1.5m
DPI = 1000                # 인화용 초고해상도

# ── 섬 필터 ──
# 폴리곤 면적(제곱도) 기준. 1제곱도 ≈ 9,845 km² (한반도 위도 보정 0.799)
# 0.02 ≈ 197 km², 0.01 ≈ 98 km², 0.005 ≈ 49 km²
ISLAND_MIN_AREA = 0.02

# ── 색상 ──
SEA_COLOR = "#4A90D9"        # 바다 (파랑)
LAND_COLOR = "#FFFFFF"        # 육지 (흰색)
NK_COLOR = "#E8E8E8"          # 북한 (연회색)
SIDO_EDGE = "#222222"         # 도 경계 (진하게)
CITY_EDGE = "#888888"         # 시/군 경계 (연하게)
NK_EDGE = "#555555"           # 북한 윤곽선

# ── 코드 ──
METRO_CODES = {"11", "21", "22", "23", "24", "25", "26"}
SIDO_NAMES = {
    "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
    "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
    "31": "경기도", "32": "강원도", "33": "충청북도", "34": "충청남도",
    "35": "전라북도", "36": "전라남도", "37": "경상북도", "38": "경상남도",
    "39": "제주특별자치도",
}

# 북한 절단 위도 (이 위도 아래만 표시)
NK_CUT = 38.71740371170524


def filter_islands(geom, min_area):
    """MultiPolygon/Polygon에서 min_area 미만 폴리곤(섬) 제거"""
    if geom.is_empty:
        return geom
    if geom.geom_type == "Polygon":
        if geom.area < min_area:
            return None
        return geom
    polys = [p for p in geom.geoms if p.area >= min_area]
    if not polys:
        return None
    return unary_union(polys)


def get_polys(geom):
    """Polygon/MultiPolygon → list[Polygon]"""
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return list(geom.geoms)


def main():
    # ── 1. 데이터 로드 ──
    with open(DATA, encoding="utf-8") as f:
        gj = json.load(f)
    features = gj["features"]

    # 시도별 폴리곤 (도 경계용)
    sido_groups = {}
    # 시/군별 폴리곤 (시/군 경계용, 구 경계 제거 → 시 단위 병합)
    city_groups = {}

    for ft in features:
        name = ft["properties"]["name"]
        code = ft["properties"]["code"]
        if name == "울릉군":
            continue  # 울릉도/독도 제외
        geom = shape(ft["geometry"])
        sido_groups.setdefault(code[:2], []).append(geom)
        if code[:2] in METRO_CODES:
            # 광역시/특별시: 시 단위로 병합 (구 경계 제거)
            city = SIDO_NAMES[code[:2]]
        else:
            # 도: 시/군 단위로 병합 (구가 있는 시는 시 이름으로 병합)
            city = name[:name.index("시") + 1] if "시" in name else name
        city_groups.setdefault(city, []).append(geom)

    # ── 2. 병합 + 섬 필터 ──
    # 시도별 병합
    sido_polys = {}  # code → merged geom
    for code, geoms in sido_groups.items():
        merged = unary_union(geoms)
        filtered = filter_islands(merged, ISLAND_MIN_AREA)
        if filtered is not None:
            sido_polys[code] = filtered

    # 시/군별 병합
    city_polys = {}  # name → merged geom
    for city, geoms in city_groups.items():
        merged = unary_union(geoms)
        filtered = filter_islands(merged, ISLAND_MIN_AREA)
        if filtered is not None:
            city_polys[city] = filtered

    # 전체 남한 육지 (해안선 1회 그리기용)
    all_land = unary_union(list(sido_polys.values()))

    # ── 3. 북한 데이터 로드 ──
    with open(NK, encoding="utf-8") as f:
        nk_gj = json.load(f)
    nk_geom = shape(nk_gj["geometry"])
    nk_clip = nk_geom.intersection(box(-180, -90, 180, NK_CUT))

    # ── 4. 전체 범위 계산 ──
    xs, ys = [], []
    for g in sido_polys.values():
        minx, miny, maxx, maxy = g.bounds
        xs += [minx, maxx]
        ys += [miny, maxy]
    nk_b = nk_clip.bounds
    xs += [nk_b[0], nk_b[2]]
    ys += [nk_b[1], nk_b[3]]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    # 포항 동쪽 여백
    xpad = (xmax - xmin) * 0.03
    xmax += xpad

    # ── 5. 그리기 ──
    fig, ax = plt.subplots(figsize=(W_INCH, H_INCH), dpi=DPI)
    ax.set_aspect(1.391 / 1.127)  # 실제 지리 비율 보정

    # 배경 (바다)
    ax.set_facecolor(SEA_COLOR)
    fig.set_facecolor(SEA_COLOR)

    # 북한 하단 (연회색 채우기)
    for poly in get_polys(nk_clip):
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor=NK_COLOR, edgecolor="none", zorder=1)

    # 육지 채우기 (흰색) — 해안선은 exterior 1회만
    for poly in get_polys(all_land):
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor=LAND_COLOR, edgecolor="none", zorder=2)

    # 시/군 경계 (연하게) — 인접 시/군과 접하는 내륙 경계만
    city_list = list(city_polys.values())
    for i, g in enumerate(city_list):
        for j in range(i + 1, len(city_list)):
            inter = g.boundary.intersection(city_list[j].boundary)
            if not inter.is_empty:
                if inter.geom_type == "LineString":
                    x, y = inter.xy
                    ax.plot(x, y, color=CITY_EDGE, linewidth=0.4, zorder=3)
                else:
                    for line in inter.geoms:
                        x, y = line.xy
                        ax.plot(x, y, color=CITY_EDGE, linewidth=0.4, zorder=3)

    # 도(시도) 경계 (진하게) — 인접 시도와 접하는 내륙 경계만
    sido_list = list(sido_polys.values())
    for i, g in enumerate(sido_list):
        for j in range(i + 1, len(sido_list)):
            inter = g.boundary.intersection(sido_list[j].boundary)
            if not inter.is_empty:
                if inter.geom_type == "LineString":
                    x, y = inter.xy
                    ax.plot(x, y, color=SIDO_EDGE, linewidth=1.5, zorder=4)
                else:
                    for line in inter.geoms:
                        x, y = line.xy
                        ax.plot(x, y, color=SIDO_EDGE, linewidth=1.5, zorder=4)

    # 북한 윤곽선
    for poly in get_polys(nk_clip):
        x, y = poly.exterior.xy
        ax.plot(x, y, color=NK_EDGE, linewidth=0.8, zorder=4)

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.axis("off")

    plt.tight_layout(pad=0)
    plt.savefig(OUT, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("saved:", OUT)
    print(f"출력 크기: {int(W_INCH*DPI)} x {int(H_INCH*DPI)} px")
    print(f"물리 크기: {W_INCH/39.37:.2f}m x {H_INCH/39.37:.2f}m")
    print(f"섬 필터: {ISLAND_MIN_AREA} 제곱도 (≈{ISLAND_MIN_AREA*9845:.0f} km² 이하 제거)")


if __name__ == "__main__":
    main()
