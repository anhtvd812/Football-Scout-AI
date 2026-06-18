# Football-Scout-AI

Hệ thống machine learning để **định giá cầu thủ** (regression) và **tìm cầu thủ tương đồng** (cosine similarity trên chỉ số per-90). Dữ liệu lấy từ bảng thống kê kiểu FBref, join với giá thị trường Transfermarkt.

## Hai pipeline chính

| Pipeline | Mục tiêu | Output chính |
|----------|----------|--------------|
| Định giá | Ước `market_value_eur` cuối mùa từ stats + metadata (cùng mùa, không forecast mùa sau) | `predict_player_value()` |
| Scouting | Tìm cầu thủ tương đồng trong cùng nhóm vị trí và **cùng mùa** | `find_similar_players()` |

Chi tiết dataset và spec model cho team AI: [docs/FEATURES.md](docs/FEATURES.md).

## Cấu trúc project

```
data/raw/              # File CSV đầu vào (không commit)
data/processed/        # File train / scouting đã merge
models/                # Model đã train (joblib)
scripts/               # Xử lý data, train, demo, chạy web
src/football_scout/    # ML + backend FastAPI
web/static/            # Giao diện dashboard
```

## Yêu cầu

- Python 3.10+
- Raw data trong `data/raw/` (xem bên dưới)

## Cài đặt

```bash
pip install -r requirements.txt
```

## Raw data

Tải từ [Google Drive](https://drive.google.com/drive/folders/1YGc01tisXaiBsYDRdMXkh4BSaamep4HB?usp=drive_link) hoặc Kaggle, rồi đặt vào `data/raw/`:

| File | Nguồn |
|------|-------|
| `players.csv` | Transfermarkt — thông tin cầu thủ |
| `player_valuations.csv` | Transfermarkt — lịch sử giá |
| `players_data-2024_2025.csv` | FBref mùa 2024/25 |
| `player_standard_stats.csv` (+ shooting, passing, defense, possession, misc) | FBref warehouse 2018/19–2023/24 |

`players_data-2025_2026.csv` chưa dùng (schema khác mùa 2024/25).

## Thứ tự chạy

### 1. Chuẩn bị dataset

Chạy từ thư mục gốc project:

```bash
python scripts/prepare_multi_season_dataset.py
```

Ghi ra `data/processed/`:

- `player_seasons_merged.csv` — train định giá multi-season (~12k dòng, 7 mùa)
- `scouting_features_multi_season.csv` — similarity multi-season
- `unmatched_players_multi_season.csv` — dòng chưa match, dùng QA thủ công

Raw data cần có:

- `players.csv`, `player_valuations.csv` — Transfermarkt
- `players_data-2024_2025.csv` — FBref mùa 2024/25
- `player_standard_stats.csv`, `player_shooting.csv`, `player_passing.csv`, `player_defense.csv`, `player_possession.csv`, `player_misc.csv` — FBref warehouse 2018/19–2023/24

### 2. Train model

```bash
python scripts/train_models.py
```

Lưu tại:

- `models/valuation_model.joblib`
- `models/scouting_scaler.joblib`
- `models/valuation_metrics.json` — metric hold-out (R², MAE, RMSE, MAPE)

### 3. Test CLI (tùy chọn)

```bash
python scripts/demo_inference.py
```

### 4. Web dashboard

```bash
python scripts/run_web.py
```

Mở http://127.0.0.1:8000

Giao diện web gọi cùng logic inference với API Python bên dưới.

## API (backend)

| Endpoint | Mô tả |
|----------|-------|
| `GET /health` | Kiểm tra server |
| `GET /api/players?q=` | Gợi ý tên (mùa mặc định `2024_2025`) |
| `GET /api/predict?player_name=&season=` | Định giá theo stats mùa chọn |
| `GET /api/similar?player_name=&max_price=&max_age=&top_k=&season=` | Cầu thủ tương đồng trong cùng mùa |

## Dùng trong Python

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

from football_scout import predict_player_value, find_similar_players

predict_player_value("Xavi Simons")  # mặc định season="2024_2025"
find_similar_players("Kevin De Bruyne", max_price=30_000_000, max_age=25, top_k=5)
```

Model load từ `models/`; nếu chưa có sẽ tự train lần gọi đầu.

## Ghi chú

- Dataset train gồm **7 mùa** Big 5: `2018_2019` … `2024_2025` (~12.164 player-season sau lọc `Min >= 450`, có giá TM).
- Warehouse FBref (2018/19–2023/24) + file wide `players_data-2024_2025.csv`; mùa `2019_2020` dùng cửa sổ giá rộng hơn vì COVID.
- Định giá và scouting mặc định **`season=2024_2025`** — so sánh phong độ/giá **cùng mùa**, không phải dự đoán mùa 2025/26.
- Model định giá: Random Forest trên **22 feature số** (gồm `xG_per90`, `xAG_per90`) + `position_group`, `foot`, `competition`.
- Scouting: cosine similarity trên **16 feature per-90**, chỉ trong cùng `position_group`.
- Thủ môn (GK) bị loại khỏi output train và inference.
- Chỉnh ngưỡng fuzzy match TM: `FUZZY_THRESHOLD` trong `scripts/prepare_2024_2025_dataset.py` (module helper cho `prepare_multi_season_dataset.py`).
