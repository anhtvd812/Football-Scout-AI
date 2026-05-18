from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    from thefuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None

try:
    from unidecode import unidecode
except ImportError:  # pragma: no cover
    unidecode = None


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FBREF_FILE = DATA_DIR / "players_data-2024_2025.csv"
TM_PLAYERS_FILE = DATA_DIR / "players.csv"
TM_VALUATIONS_FILE = DATA_DIR / "player_valuations.csv"

SEASON_START = "2024-07-01"
SEASON_END = "2025-06-30"


NON_NUMERIC_COLS = {
    "Player",
    "Nation",
    "Pos",
    "Squad",
    "Comp",
}

PER90_COLS = [
    "Gls",
    "Ast",
    "G+A",
    "G-PK",
    "PK",
    "PKatt",
    "xG",
    "npxG",
    "xAG",
    "PrgC",
    "PrgP",
    "PrgR",
    "KP",
    "PPA",
    "Tkl",
    "TklW",
    "Int",
    "Tkl+Int",
    "Clr",
    "Err",
    "Touches",
    "Carries",
    "Mis",
    "Dis",
    "Recov",
    "Sh",
    "SoT",
]


@dataclass
class MatchResult:
    player_id: Optional[int]
    method: str
    score: Optional[int]


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if unidecode is not None:
        text = unidecode(text)
    for ch in ["'", "\"", ".", ",", "-", "(", ")", "[", "]"]:
        text = text.replace(ch, " ")
    text = " ".join(text.split())
    return text


def parse_age(value: object) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "-" in text:
        text = text.split("-")[0]
    try:
        return float(text)
    except ValueError:
        return None


def parse_birth_year(value: object) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "-" in text:
        text = text.split("-")[0]
    try:
        return int(float(text))
    except ValueError:
        return None


def clean_numeric_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace({"nan": None, "": None})
        .apply(lambda x: None if x is None else x)
        .pipe(pd.to_numeric, errors="coerce")
    )


def to_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [c for c in df.columns if c not in NON_NUMERIC_COLS]
    for col in numeric_cols:
        df[col] = clean_numeric_series(df[col])
    return df


def add_per90(df: pd.DataFrame, per90_cols: Iterable[str]) -> pd.DataFrame:
    if "90s" not in df.columns:
        return df
    minutes = df["90s"].replace({0: pd.NA})
    for col in per90_cols:
        if col in df.columns:
            df[f"{col}_per90"] = df[col] / minutes
    return df


def load_fbref() -> pd.DataFrame:
    df = pd.read_csv(FBREF_FILE, low_memory=False)
    df["Age"] = df["Age"].apply(parse_age)
    df["Birth_Year"] = df["Born"].apply(parse_birth_year)
    df = to_numeric_columns(df)
    df = add_per90(df, PER90_COLS)
    df["player_name_norm"] = df["Player"].apply(normalize_text)
    df["squad_norm"] = df["Squad"].apply(normalize_text)
    return df


def load_tm_players() -> pd.DataFrame:
    df = pd.read_csv(TM_PLAYERS_FILE)
    df["birth_year"] = pd.to_datetime(df["date_of_birth"], errors="coerce").dt.year
    df["player_name_norm"] = df["name"].apply(normalize_text)
    df["club_norm"] = df["current_club_name"].apply(normalize_text)
    return df


def load_tm_valuations() -> pd.DataFrame:
    df = pd.read_csv(TM_VALUATIONS_FILE)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    season_mask = (df["date"] >= SEASON_START) & (df["date"] <= SEASON_END)
    df_season = df.loc[season_mask].copy()
    df_season = (
        df_season.sort_values("date")
        .groupby("player_id", as_index=False)
        .tail(1)
    )
    df_season = df_season[["player_id", "market_value_in_eur", "date"]]
    df_season = df_season.rename(
        columns={"market_value_in_eur": "market_value_season_eur"}
    )
    return df_season


def build_tm_index(tm_players: pd.DataFrame) -> Dict[Tuple[str, int], List[int]]:
    index: Dict[Tuple[str, int], List[int]] = {}
    for idx, row in tm_players.iterrows():
        name = row.get("player_name_norm", "")
        year = row.get("birth_year")
        if not name or pd.isna(year):
            continue
        key = (name, int(year))
        index.setdefault(key, []).append(idx)
    return index


def pick_best_by_club(tm_players: pd.DataFrame, indices: List[int], squad_norm: str) -> int:
    if not squad_norm:
        return indices[0]
    club_matches = [i for i in indices if tm_players.at[i, "club_norm"] == squad_norm]
    if len(club_matches) == 1:
        return club_matches[0]
    if club_matches:
        indices = club_matches
    return tm_players.loc[indices].sort_values(
        "highest_market_value_in_eur", ascending=False
    ).index[0]


def fuzzy_match(
    name_norm: str,
    birth_year: Optional[int],
    tm_players: pd.DataFrame,
    squad_norm: str,
) -> MatchResult:
    if fuzz is None or not name_norm or birth_year is None:
        return MatchResult(None, "none", None)

    candidates = tm_players[tm_players["birth_year"] == birth_year]
    if candidates.empty:
        return MatchResult(None, "none", None)

    best_score = -1
    best_idx = None
    for idx, row in candidates.iterrows():
        score = fuzz.token_sort_ratio(name_norm, row["player_name_norm"])
        if squad_norm and row["club_norm"] == squad_norm:
            score += 3
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_score >= 90 and best_idx is not None:
        return MatchResult(int(tm_players.at[best_idx, "player_id"]), "fuzzy", best_score)

    return MatchResult(None, "none", best_score if best_score >= 0 else None)


def match_players(fbref: pd.DataFrame, tm_players: pd.DataFrame) -> pd.DataFrame:
    tm_index = build_tm_index(tm_players)

    matched_ids: List[Optional[int]] = []
    matched_method: List[str] = []
    matched_score: List[Optional[int]] = []

    for _, row in fbref.iterrows():
        name_norm = row.get("player_name_norm", "")
        birth_year = row.get("Birth_Year")
        squad_norm = row.get("squad_norm", "")

        player_id = None
        method = "none"
        score = None

        if name_norm and pd.notna(birth_year):
            key = (name_norm, int(birth_year))
            indices = tm_index.get(key, [])
            if indices:
                best_idx = pick_best_by_club(tm_players, indices, squad_norm)
                player_id = int(tm_players.at[best_idx, "player_id"])
                method = "exact"
        if player_id is None:
            result = fuzzy_match(name_norm, birth_year, tm_players, squad_norm)
            player_id, method, score = result.player_id, result.method, result.score

        matched_ids.append(player_id)
        matched_method.append(method)
        matched_score.append(score)

    fbref = fbref.copy()
    fbref["tm_player_id"] = matched_ids
    fbref["tm_match_method"] = matched_method
    fbref["tm_match_score"] = matched_score
    return fbref


def main() -> None:
    fbref = load_fbref()
    tm_players = load_tm_players()
    tm_vals = load_tm_valuations()

    fbref = match_players(fbref, tm_players)

    merged = fbref.merge(
        tm_players,
        left_on="tm_player_id",
        right_on="player_id",
        how="left",
        suffixes=("_fbref", "_tm"),
    )
    merged = merged.merge(tm_vals, on="player_id", how="left")
    merged["market_value_eur_final"] = merged["market_value_season_eur"].fillna(
        merged["market_value_in_eur"]
    )

    out_file = DATA_DIR / "players_2024_2025_joined.csv"
    unmatched_file = DATA_DIR / "players_2024_2025_unmatched.csv"

    merged.to_csv(out_file, index=False)
    merged.loc[merged["tm_player_id"].isna()].to_csv(unmatched_file, index=False)

    print(f"Saved joined dataset to: {out_file}")
    print(f"Saved unmatched rows to: {unmatched_file}")


if __name__ == "__main__":
    main()
