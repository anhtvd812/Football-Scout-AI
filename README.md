# Football-Scout-AI

## Tong quan du an
Football-Scout-AI la he thong khoa hoc du lieu va machine learning de danh gia gia tri cau thu va tim "hidden gems". Du an co 2 pipeline chinh:

- Dinh gia cau thu (Regression): du doan `market_value_eur` tu thong so hieu suat per 90.
- Scout tuong dong (Similarity): tim cau thu tre, gia thap co phong cach giong sao muc tieu.

Tap du lieu chinh cho hien tai: FBref 2024-2025 ket hop Transfermarkt (players + valuations).

## Toi da lam gi
Da hoan thanh 2 buoc xu ly du lieu de tao tap train dau vao:

1) Lam sach va chuan hoa du lieu mua 2024-2025
- Chuyen doi cac cot so, loai ky tu % va dau phay.
- Parse `Age` va `Born` thanh gia tri so.
- Tao cot `*_per90` cho cac chi so quan trong (chia tren `90s`, co chan chia 0).

2) Join Transfermarkt
- Map cau thu tu FBref sang Transfermarkt bang `name + birth_year`.
- Co fuzzy match khi khop chinh xac khong thanh cong.
- Lay market value theo mua 2024-2025, neu thieu thi fallback ve market value hien tai.

Script thuc hien hai buoc nay:
- [scripts/prepare_2024_2025_dataset.py](scripts/prepare_2024_2025_dataset.py)

Ket qua sinh ra:
- [data/players_2024_2025_joined.csv](data/players_2024_2025_joined.csv)
- [data/players_2024_2025_unmatched.csv](data/players_2024_2025_unmatched.csv)

## Huong dan chay

### 1) Cai thu vien (neu chua co)
```bash
pip install pandas thefuzz unidecode
```

### 2) Chay xu ly du lieu
```bash
python scripts/prepare_2024_2025_dataset.py
```

## Data dau vao su dung
- Link tai data: https://drive.google.com/drive/folders/1YGc01tisXaiBsYDRdMXkh4BSaamep4HB?usp=drive_link
- [data/players_data-2024_2025.csv](data/players_data-2024_2025.csv) (FBref 2024-2025)
- [data/players.csv](data/players.csv) (Transfermarkt players)
- [data/player_valuations.csv](data/player_valuations.csv) (Transfermarkt valuations)

## Ghi chu
- Mua 2025-2026 hien tai khong dong nhat schema so voi 2024-2025, vi vay chua duoc dua vao tap train.
- Co the dieu chinh nguong fuzzy match va bo sung quy tac chuan hoa ten neu can.