# Bàn giao dữ liệu cho Core AI

Tài liệu này dành cho Kiệt hoặc người phụ trách phần model. Mục tiêu là giúp team AI biết chính xác file nào cần dùng, target là gì, feature nào nên lấy và function đầu ra cần trả về theo format nào.

## Các file cần dùng

- `data/processed/player_seasons_merged.csv`
  - File chính nên ưu tiên cho mô hình định giá multi-season.
  - Mỗi dòng là một cặp `cầu thủ - mùa giải`.
  - Hiện gồm 7 mùa: `2018_2019`, `2019_2020`, `2020_2021`, `2021_2022`, `2022_2023`, `2023_2024`, `2024_2025` (~12.164 dòng sau lọc).
  - Target `market_value_eur` đã lấy theo valuation gần cuối mùa tương ứng, không dùng giá trị tương lai quá xa.
  - File này đã lọc sẵn:
    - Chỉ lấy cầu thủ không phải thủ môn.
    - `Min >= 450`.
    - Có `market_value_eur`.

- `data/processed/scouting_features_multi_season.csv`
  - File chính nên ưu tiên cho bài toán tìm cầu thủ tương đồng khi muốn dùng nhiều mùa.
  - Có thể lọc theo `season == "2024_2025"` nếu chỉ muốn tìm theo phong độ mới nhất.
  - Có thể dùng toàn bộ nhiều mùa nếu muốn xây profile ổn định hơn theo thời gian.

- `data/processed/unmatched_players_multi_season.csv`
  - Danh sách các dòng chưa match hoặc thiếu valuation theo mùa.
  - Dùng để QA nếu thiếu cầu thủ quan trọng trong demo.

## Target cho mô hình định giá

Target chính:

```python
target = "market_value_eur"
```

Nên train bằng log value:

```python
y = np.log1p(df["market_value_eur"])
```

Khi predict thì đổi ngược lại:

```python
predicted_value_eur = np.expm1(prediction)
```

Lý do: giá cầu thủ bị lệch rất mạnh. Một số cầu thủ chỉ vài trăm nghìn euro, trong khi nhóm siêu sao có thể hơn 100 triệu euro. Nếu train trực tiếp bằng giá gốc, model dễ bị kéo lệch bởi các cầu thủ quá đắt.

## Lưu ý về dữ liệu nhiều mùa

Với file `player_seasons_merged.csv`, các mùa `2018_2019`–`2023_2024` đến từ FBref warehouse (merge standard + shooting + passing + defense + possession + misc). Mùa `2024_2025` đến từ file FBref wide `players_data-2024_2025.csv`. Mùa `2019_2020` dùng cửa sổ giá rộng hơn (`2019-12` → `2020-12`) vì COVID làm giảm cập nhật giá giữa mùa 2020.

Feature nên ưu tiên cho baseline multi-season:

```python
multi_season_features = [
    "age",
    "height_in_cm",
    "Min",
    "90s",
    "Gls_per90",
    "Ast_per90",
    "xG_per90",
    "xAG_per90",
    "Sh_per90",
    "SoT_per90",
    "PrgC_per90",
    "PrgP_per90",
    "PrgR_per90",
    "KP_per90",
    "PPA_per90",
    "Tkl_per90",
    "Int_per90",
    "Blocks_per90",
    "Clr_per90",
    "Touches_per90",
    "Carries_per90",
    "Recov_per90",
]
```

Model production hiện dùng đúng bộ feature trên (cộng thêm `position_group`, `foot`, `competition`).

## Feature đề xuất cho mô hình định giá

Model production (`src/football_scout/config.py`) dùng **22 feature số** + 3 categorical:

```python
valuation_numeric = [
    "age", "height_in_cm", "Min", "90s",
    "Gls_per90", "Ast_per90", "xG_per90", "xAG_per90",
    "Sh_per90", "SoT_per90",
    "PrgC_per90", "PrgP_per90", "PrgR_per90",
    "KP_per90", "PPA_per90",
    "Tkl_per90", "Int_per90", "Blocks_per90", "Clr_per90",
    "Touches_per90", "Carries_per90", "Recov_per90",
]

categorical_features = ["position_group", "foot", "competition"]
```

Model baseline (đang deploy):

```python
RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
    min_samples_leaf=3,
)
```

Nếu máy có XGBoost thì có thể thử sau khi baseline Random Forest đã chạy ổn.

## Đánh giá chất lượng model định giá

`python scripts/train_models.py` sẽ:

1. Chia hold-out **20%** để đo chất lượng (train/test `random_state=42`).
2. Train model cuối cùng trên **100%** dữ liệu để deploy.
3. Ghi metric ra `models/valuation_metrics.json`.

Các metric chính:

- `r2_log`, `mae_log`, `rmse_log` — trên `log1p(market_value_eur)` (thang train).
- `r2_eur`, `mae_eur`, `rmse_eur` — đổi ngược `expm1` về euro.
- `mape_pct`, `median_ape_pct` — sai số phần trăm (MAPE dễ bị kéo bởi cầu thủ rẻ).

## Feature đề xuất cho bài toán scouting

Với bài toán tìm cầu thủ tương đồng, nên dùng các chỉ số kỹ năng dạng per 90:

```python
scouting_features = [
    "Gls_per90",
    "Ast_per90",
    "xG_per90",
    "xAG_per90",
    "PrgC_per90",
    "PrgP_per90",
    "PrgR_per90",
    "Sh_per90",
    "SoT_per90",
    "KP_per90",
    "PPA_per90",
    "Tkl_per90",
    "Int_per90",
    "Blocks_per90",
    "Touches_per90",
    "Carries_per90",
]
```

Flow đề xuất:

```python
X = df[scouting_features].fillna(0)
X_scaled = StandardScaler().fit_transform(X)
similarity = cosine_similarity(X_scaled)
```

Để kết quả hợp lý hơn về mặt bóng đá, nên so sánh trong cùng nhóm vị trí và **cùng mùa** trước (mặc định `season="2024_2025"`):

- `FW` so với `FW`
- `MF` so với `MF`
- `DF` so với `DF`
- `GK` bị loại khỏi dataset train hiện tại

`StandardScaler` cho scouting được fit trên toàn bộ multi-season; cosine similarity chạy trong pool đã lọc theo mùa.

## Function Python team AI cần bàn giao

Backend cần gọi được function này để định giá cầu thủ:

```python
def predict_player_value(player_name: str, season: str | None = "2024_2025") -> dict:
    ...
```

- `predicted_value_eur`: giá model ước tính từ stats **cùng mùa**
- `actual_market_value_eur`: giá TM thật cuối mùa đó trong dataset
- Không phải forecast giá mùa kế tiếp (vd. 2025/26)

Output kỳ vọng:

```json
{
  "player_name": "Xavi Simons",
  "position": "MF",
  "age": 22,
  "predicted_value_eur": 55000000,
  "actual_market_value_eur": 40000000,
  "market_status": "Undervalued"
}
```

Backend cần gọi được function này để tìm cầu thủ tương đồng:

```python
def find_similar_players(
    player_name: str,
    max_price: int | None = None,
    max_age: int | None = None,
    top_k: int = 5,
    season: str | None = "2024_2025",
) -> dict:
    ...
```

Output kỳ vọng:

```json
{
  "target_player": "Kevin De Bruyne",
  "results": [
    {
      "name": "Oscar Gloukh",
      "age": 21,
      "position": "MF",
      "club": "Red Bull Salzburg",
      "market_value_eur": 18000000,
      "similarity_score": 0.89
    }
  ]
}
```

## Ghi chú cho Kiệt

- Chuẩn bị data: `python scripts/prepare_multi_season_dataset.py` (đọc warehouse + `players_data-2024_2025.csv`).
- Train + metric hold-out: `python scripts/train_models.py` → `models/valuation_metrics.json`.
- Web/API mặc định mùa `2024_2025`; cầu thủ chỉ có ở mùa cũ (vd. Messi sau khi rời Big 5) không xuất hiện trong autocomplete nhưng vẫn tra được nếu truyền `season` phù hợp.
- Nếu kết quả scouting hơi lạ, kiểm tra nhóm vị trí, mùa giải và số phút thi đấu.
- Nếu định giá lệch mạnh, kiểm tra log-transform của target và outlier giá TM.
