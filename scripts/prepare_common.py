"""Shared helpers for merging FBref stats with Transfermarkt metadata."""

from __future__ import annotations

import csv
import math
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

TM_PLAYERS_FILE = RAW_DIR / "players.csv"

FUZZY_THRESHOLD = 90
MIN_MINUTES_FOR_MODEL = 450.0

SCOUTING_FEATURES = [
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


def normalize_competition(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return text

    parts = text.split(None, 1)
    if len(parts) == 2 and len(parts[0]) <= 3 and parts[0].isalpha():
        return parts[1]
    return text


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def token_sort_ratio(left: str, right: str) -> int:
    left_sorted = " ".join(sorted(left.split()))
    right_sorted = " ".join(sorted(right.split()))
    return round(SequenceMatcher(None, left_sorted, right_sorted).ratio() * 100)


def to_float(value: Any) -> Optional[float]:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    text = text.replace(",", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None


def to_int(value: Any) -> Optional[int]:
    number = to_float(value)
    if number is None or math.isnan(number):
        return None
    return int(number)


def parse_age(value: Any) -> Optional[float]:
    text = "" if value is None else str(value).strip()
    if "-" in text:
        text = text.split("-", 1)[0]
    return to_float(text)


def parse_birth_year(value: Any) -> Optional[int]:
    text = "" if value is None else str(value).strip()
    if "-" in text:
        text = text.split("-", 1)[0]
    return to_int(text)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_tm_players() -> Tuple[Dict[int, Dict[str, Any]], Dict[Tuple[str, int], List[int]], Dict[int, List[int]]]:
    players_by_id: Dict[int, Dict[str, Any]] = {}
    exact_index: Dict[Tuple[str, int], List[int]] = defaultdict(list)
    year_index: Dict[int, List[int]] = defaultdict(list)

    for row in read_csv(TM_PLAYERS_FILE):
        player_id = to_int(row.get("player_id"))
        if player_id is None:
            continue

        birth_year = parse_birth_year(str(row.get("date_of_birth", ""))[:4])
        clean_row: Dict[str, Any] = {
            **row,
            "player_id": player_id,
            "birth_year": birth_year,
            "player_name_norm": normalize_text(row.get("name")),
            "club_norm": normalize_text(row.get("current_club_name")),
            "market_value_in_eur": to_int(row.get("market_value_in_eur")),
            "highest_market_value_in_eur": to_int(row.get("highest_market_value_in_eur")),
            "height_in_cm": to_float(row.get("height_in_cm")),
        }
        players_by_id[player_id] = clean_row

        if birth_year is not None and clean_row["player_name_norm"]:
            exact_index[(clean_row["player_name_norm"], birth_year)].append(player_id)
            year_index[birth_year].append(player_id)

    return players_by_id, exact_index, year_index


def choose_best_exact_match(player_ids: List[int], players_by_id: Dict[int, Dict[str, Any]], squad_norm: str) -> int:
    club_matches = [
        player_id
        for player_id in player_ids
        if squad_norm and players_by_id[player_id].get("club_norm") == squad_norm
    ]
    candidates = club_matches or player_ids
    return max(
        candidates,
        key=lambda player_id: players_by_id[player_id].get("highest_market_value_in_eur") or 0,
    )


def find_match(
    fbref_name_norm: str,
    birth_year: Optional[int],
    squad_norm: str,
    players_by_id: Dict[int, Dict[str, Any]],
    exact_index: Dict[Tuple[str, int], List[int]],
    year_index: Dict[int, List[int]],
) -> Tuple[Optional[int], str, Optional[int]]:
    if not fbref_name_norm or birth_year is None:
        return None, "none", None

    exact_candidates = exact_index.get((fbref_name_norm, birth_year), [])
    if exact_candidates:
        player_id = choose_best_exact_match(exact_candidates, players_by_id, squad_norm)
        return player_id, "exact_name_birth_year", 100

    best_id: Optional[int] = None
    best_score = -1
    for player_id in year_index.get(birth_year, []):
        candidate = players_by_id[player_id]
        score = token_sort_ratio(fbref_name_norm, candidate.get("player_name_norm", ""))
        if squad_norm and candidate.get("club_norm") == squad_norm:
            score += 3
        if score > best_score:
            best_id = player_id
            best_score = score

    if best_id is not None and best_score >= FUZZY_THRESHOLD:
        return best_id, "fuzzy_name_birth_year", min(best_score, 100)

    return None, "none", best_score if best_score >= 0 else None
