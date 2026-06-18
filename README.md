# Football-Scout-AI

Hệ thống machine learning để **định giá cầu thủ** (regression) và **tìm cầu thủ tương đồng** (cosine similarity trên chỉ số per-90). Dữ liệu lấy từ bảng thống kê kiểu FBref, join với giá thị trường Transfermarkt.

## Hai pipeline chính

| Pipeline | Mục tiêu | Output chính |
|----------|----------|--------------|
| Định giá | Dự đoán `market_value_eur` từ hiệu suất + metadata | `predict_player_value()` |
| Scouting | Tìm cầu thủ tương đồng trong cùng nhóm vị trí | `find_similar_players()` |

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
| `players_data-2021_2022.csv` | Kaggle / vivovinco (multi-season) |
| `players_data-2022_2023.csv` | Kaggle / vivovinco (multi-season) |

`players_data-2025_2026.csv` chưa dùng (schema khác mùa 2024/25).

## Thứ tự chạy

### 1. Chuẩn bị dataset

Chạy từ thư mục gốc project:

```bash
python scripts/prepare_multi_season_dataset.py
python scripts/prepare_2024_2025_dataset.py
```

Ghi ra `data/processed/`:

- `player_seasons_merged.csv` — train định giá multi-season (ưu tiên)
- `scouting_features_multi_season.csv` — similarity multi-season
- `players_merged_2024_2025.csv` — định giá một mùa
- `scouting_features_2024_2025.csv` — scouting một mùa
- `unmatched_players_*.csv` — dòng chưa match, dùng QA thủ công

### 2. Train model

```bash
python scripts/train_models.py
```

Lưu tại:

- `models/valuation_model.joblib`
- `models/scouting_scaler.joblib`

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
| `GET /api/players?q=` | Gợi ý tên cầu thủ |
| `GET /api/predict?player_name=` | Định giá |
| `GET /api/similar?player_name=&max_price=&max_age=&top_k=` | Cầu thủ tương đồng |

## Dùng trong Python

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

from football_scout import predict_player_value, find_similar_players

predict_player_value("Xavi Simons")
find_similar_players("Kevin De Bruyne", max_price=30_000_000, max_age=25, top_k=5)
```

Model load từ `models/`; nếu chưa có sẽ tự train lần gọi đầu.

## Ghi chú

- Model định giá multi-season dùng feature có ở cả 3 mùa 2021/22, 2022/23, 2024/25 (mùa cũ không có `xG`).
- Scouting mặc định mùa `2024_2025`; chỉ so sánh trong cùng `position_group`.
- Thủ môn (GK) bị loại khỏi output định giá và scouting.
- Chỉnh ngưỡng fuzzy match trong `scripts/prepare_2024_2025_dataset.py` (`FUZZY_THRESHOLD`).
