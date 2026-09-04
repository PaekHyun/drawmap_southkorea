# 남한 시군구 경계 지도 생성기

남한 지도를 시·군 단위로 그려 1m × 1.391m 크기의 고해상도(1000dpi) 이미지로 출력하는 도구입니다.

## 기능

- 시·군 경계선 + 시·군 이름 표기
- 광역시(서울·부산·대구·인천·광주·대전·울산)는 구 경계 유지
- 도는 시/군 단위로 병합 (구로 나뉜 시는 시 이름으로 병합)
- 시도 경계는 두껍게, 도 이름은 흐리게 2배 크기로 표기
- 북한 하단 형태 포함 (절단선 아래만)

## 실행 방법

### 1. 스크립트 실행

```bash
python draw_map.py
```

### 2. Jupyter Notebook

`draw_map.ipynb` 파일을 Jupyter Notebook / Jupyter Lab / VS Code에서 열어 셀을 순서대로 실행하세요.

## 필요한 데이터 파일

다음 데이터 파일을 스크립트와 같은 폴더에 두어야 합니다.

| 파일 | 설명 | 출처 |
|------|------|------|
| `skorea-municipalities-2018-geo.json` | 남한 시군구 경계 | [southkorea-maps](https://github.com/southkorea/southkorea-maps) |
| `north_korea.geojson` | 북한 형태 | [geo-countries](https://github.com/datasets/geo-countries) |

## 필요한 패키지

```bash
pip install matplotlib shapely numpy
```

## 출력

- 파일: `south_korea_map.png`
- 크기: 39370 × 54763 px (1000dpi, 1m × 1.391m)
- 파일 크기: 약 39MB

## 설정 변경

`draw_map.py` 상단 또는 노트북 2번 셀에서 다음 값을 변경할 수 있습니다.

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DPI` | 해상도 | 1000 |
| `W_INCH` | 가로 크기 (인치) | 39.37 (1m) |
| `NK_CUT` | 북한 절단 위도 | 38.7174 |
| `SIDO_NAMES` | 시도 이름 | - |

### 색상

| 항목 | 기본값 |
|------|--------|
| 바다 | `#cfe8f7` |
| 육지 | `#e8f4e8` |
| 시군구 경계선 | `#333333` |
| 시도 경계선 | `#111111` |


<img width="697" height="969" alt="image" src="https://github.com/user-attachments/assets/d21bddb0-b33b-4d2d-8fff-239f4b4f96c7" />
