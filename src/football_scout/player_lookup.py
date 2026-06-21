from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Optional

import pandas as pd

from football_scout.config import DEFAULT_SCOUTING_SEASON, NAME_MATCH_THRESHOLD


def normalize_name(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def name_similarity(left: str, right: str) -> int:
    left_sorted = " ".join(sorted(left.split()))
    right_sorted = " ".join(sorted(right.split()))
    return round(SequenceMatcher(None, left_sorted, right_sorted).ratio() * 100)


def resolve_player_row(
    df: pd.DataFrame,
    player_name: str,
    *,
    season: Optional[str] = DEFAULT_SCOUTING_SEASON,
    allow_season_fallback: bool = True,
) -> pd.Series:
    if df.empty:
        raise ValueError("Dataset is empty.")

    query = normalize_name(player_name)
    if not query:
        raise ValueError("Player name cannot be empty.")

    def _find_match(frame: pd.DataFrame) -> pd.Series | None:
        working = frame.copy()
        working["_name_norm"] = working["player_name"].map(normalize_name)

        exact = working[working["_name_norm"] == query]
        if len(exact) == 1:
            return exact.iloc[0]
        if len(exact) > 1:
            return exact.sort_values("market_value_eur", ascending=False).iloc[0]

        scores = working["_name_norm"].map(lambda candidate: name_similarity(query, candidate))
        best_idx = scores.idxmax()
        best_score = int(scores.loc[best_idx])
        if best_score < NAME_MATCH_THRESHOLD:
            return None
        return working.loc[best_idx]

    if season is not None and "season" in df.columns:
        season_match = _find_match(df[df["season"] == season])
        if season_match is not None:
            return season_match
        if not allow_season_fallback:
            raise ValueError(f"Could not find player '{player_name}' for season '{season}'.")

    fallback = _find_match(df)
    if fallback is not None:
        return fallback

    raise ValueError(
        f"Could not find player '{player_name}'"
        + (f" for season '{season}'." if season else ".")
    )
