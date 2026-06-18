# Football-Scout-AI

Machine learning system for football player **valuation** (regression) and **similarity scouting** (cosine similarity on per-90 stats). Data comes from FBref-style performance tables joined with Transfermarkt market values.

## Pipelines

| Pipeline | Goal | Main output |
|----------|------|-------------|
| Valuation | Predict `market_value_eur` from performance + metadata | `predict_player_value()` |
| Scouting | Find similar players in the same position group | `find_similar_players()` |

Processed datasets and model specs for the AI team: [docs/FEATURES.md](docs/FEATURES.md).

## Project layout

```
data/raw/              # Input CSVs (not committed)
data/processed/        # Merged training / scouting files
models/                # Trained joblib artifacts (regenerate via train script)
scripts/               # Data prep, train, demo, web launcher
src/football_scout/    # ML + FastAPI backend
web/static/            # Dashboard frontend
```

## Prerequisites

- Python 3.10+
- Raw data in `data/raw/` (see below)

## Setup

```bash
pip install -r requirements.txt
```

## Raw data

Download from [Google Drive](https://drive.google.com/drive/folders/1YGc01tisXaiBsYDRdMXkh4BSaamep4HB?usp=drive_link) or Kaggle, then place files under `data/raw/`:

| File | Source |
|------|--------|
| `players.csv` | Transfermarkt players |
| `player_valuations.csv` | Transfermarkt valuations |
| `players_data-2024_2025.csv` | FBref 2024/25 |
| `2021-2022 Football Player Stats.csv` | Kaggle / vivovinco (multi-season) |
| `2022-2023 Football Player Stats.csv` | Kaggle / vivovinco (multi-season) |

`players_data-2025_2026.csv` is not used yet (schema mismatch).

## Run order

### 1. Prepare datasets

From the project root:

```bash
python scripts/prepare_multi_season_dataset.py
python scripts/prepare_2024_2025_dataset.py
```

Writes to `data/processed/`:

- `player_seasons_merged.csv` — valuation training (multi-season, preferred)
- `scouting_features_multi_season.csv` — similarity (multi-season)
- `players_merged_2024_2025.csv` — single-season valuation
- `scouting_features_2024_2025.csv` — single-season scouting
- `unmatched_players_*.csv` — rows for manual QA

### 2. Train models

```bash
python scripts/train_models.py
```

Saves:

- `models/valuation_model.joblib`
- `models/scouting_scaler.joblib`

### 3. CLI smoke test (optional)

```bash
python scripts/demo_inference.py
```

### 4. Web dashboard

```bash
python scripts/run_web.py
```

Open http://127.0.0.1:8000

The UI calls the same inference functions as the Python API below.

## API (backend)

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/players?q=` | Player name autocomplete |
| `GET /api/predict?player_name=` | Valuation |
| `GET /api/similar?player_name=&max_price=&max_age=&top_k=` | Similar players |

## Python usage

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

from football_scout import predict_player_value, find_similar_players

predict_player_value("Xavi Simons")
find_similar_players("Kevin De Bruyne", max_price=30_000_000, max_age=25, top_k=5)
```

Models are loaded from `models/`; if missing, they are trained on first call.

## Notes

- Multi-season valuation uses features available across 2021/22, 2022/23, and 2024/25 (no `xG` in older seasons).
- Scouting defaults to season `2024_2025`; comparisons are within the same `position_group`.
- Goalkeepers are excluded from valuation and scouting outputs.
- Tune fuzzy matching in `scripts/prepare_2024_2025_dataset.py` (`FUZZY_THRESHOLD`).
