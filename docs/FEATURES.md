# Bàn giao dữ liệu cho Core AI

Tài liệu này dành cho Kiệt hoặc người phụ trách phần model. Mục tiêu là giúp team AI biết chính xác file nào cần dùng, target là gì, feature nào nên lấy và function đầu ra cần trả về theo format nào.

## Các file cần dùng

- `data/processed/player_seasons_merged.csv`
  - File chính nên ưu tiên cho mô hình định giá multi-season.
  - Mỗi dòng là một cặp `cầu thủ - mùa giải`.
  - Hiện gồm 3 mùa: `2021_2022`, `2022_2023`, `2024_2025`.
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

- `data/processed/players_merged_2024_2025.csv`
  - File một mùa 2024/25, dùng làm fallback hoặc so sánh baseline.
  - Mỗi dòng là một cầu thủ đã match được giữa dữ liệu FBref-like và Transfermarkt.
  - Các cầu thủ chuyển CLB trong mùa đã được gộp thành một dòng.
  - File này đã lọc sẵn:
    - Chỉ lấy cầu thủ không phải thủ môn.
    - `Min >= 450`.
    - Có `market_value_eur`.

- `data/processed/scouting_features_2024_2025.csv`
  - File scouting một mùa 2024/25.
  - Có thể dùng trực tiếp với `StandardScaler` + `cosine_similarity` hoặc KNN.
  - File này đã lọc sẵn:
    - `Min >= 450`.
    - Có `market_value_eur`.
    - Có nhóm vị trí hợp lệ.

- `data/processed/unmatched_players_2024_2025.csv`
  - Danh sách các dòng FBref-like chưa match chắc chắn được với Transfermarkt.
  - Chỉ cần dùng file này để QA thủ công nếu thiếu cầu thủ quan trọng trong demo.

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

Với file `player_seasons_merged.csv`, các mùa không có schema giống nhau hoàn toàn:

- `2021_2022` và `2022_2023` đến từ Kaggle/FBref per-90, có nhiều chỉ số passing/defense/possession nhưng không có `xG`, `npxG`, `xAG`.
- `2024_2025` có schema giàu hơn, gồm cả `xG`, `npxG`, `xAG`.
- Vì vậy khi train baseline multi-season, nên bắt đầu bằng các feature có mặt ở cả 3 mùa.

Feature nên ưu tiên cho baseline multi-season:

```python
multi_season_features = [
    "age",
    "height_in_cm",
    "Min",
    "90s",
    "Gls_per90",
    "Ast_per90",
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

`xG_per90`, `xAG_per90`, `npxG_per90` có thể thêm ở model thứ hai, nhưng phải xử lý missing value cẩn thận.

## Feature đề xuất cho mô hình định giá

Nên bắt đầu bằng bộ feature nhỏ và ổn định trước. Khi baseline chạy được rồi mới mở rộng thêm feature.

```python
basic_features = [
    "age",
    "height_in_cm",
    "Min",
    "90s",
]

attacking_features = [
    "Gls_per90",
    "Ast_per90",
    "xG_per90",
    "xAG_per90",
    "Sh_per90",
    "SoT_per90",
]

progression_features = [
    "PrgC_per90",
    "PrgP_per90",
    "PrgR_per90",
    "KP_per90",
    "PPA_per90",
]

defensive_features = [
    "Tkl_per90",
    "Int_per90",
    "Blocks_per90",
    "Clr_per90",
]

categorical_features = [
    "position_group",
    "foot",
    "competition",
]
```

Model baseline đề xuất:

```python
RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
    min_samples_leaf=3,
)
```

Nếu máy có XGBoost thì có thể thử sau khi baseline Random Forest đã chạy ổn.

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

Để kết quả hợp lý hơn về mặt bóng đá, nên so sánh trong cùng nhóm vị trí trước:

- `FW` so với `FW`
- `MF` so với `MF`
- `DF` so với `DF`
- `GK` nên xử lý riêng hoặc loại khỏi MVP đầu tiên

## Function Python team AI cần bàn giao

Backend cần gọi được function này để định giá cầu thủ:

```python
def predict_player_value(player_name: str) -> dict:
    ...
```

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

- Không cần xử lý lại raw data từ đầu nếu không thật sự cần.
- Ưu tiên làm model chạy được trước, sau đó mới tối ưu.
- Nếu kết quả scouting hơi lạ, hãy kiểm tra lại nhóm vị trí và số phút thi đấu.
- Nếu model định giá dự đoán quá cao hoặc quá thấp, hãy kiểm tra log-transform của target và các cầu thủ outlier.
