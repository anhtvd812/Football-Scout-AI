from __future__ import annotations

import csv
import math
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

FBREF_FILE = RAW_DIR / "players_data-2024_2025.csv"
TM_PLAYERS_FILE = RAW_DIR / "players.csv"
TM_VALUATIONS_FILE = RAW_DIR / "player_valuations.csv"

SEASON_START = "2024-07-01"
SEASON_END = "2025-06-30"
FUZZY_THRESHOLD = 90
MIN_MINUTES_FOR_MODEL = 450.0

IDENTITY_COLUMNS = [
    "player_id",
    "player_name",
    "fbref_player",
    "age",
    "birth_year",
    "nation",
    "position",
    "position_group",
    "squad",
    "competition",
    "foot",
    "height_in_cm",
    "market_value_eur",
    "highest_market_value_in_eur",
    "valuation_date",
    "tm_match_method",
    "tm_match_score",
]

BASE_FEATURES = [
    "MP",
    "Starts",
    "Min",
    "90s",
    "Gls",
    "Ast",
    "G+A",
    "G-PK",
    "PK",
    "PKatt",
    "CrdY",
    "CrdR",
    "xG",
    "npxG",
    "xAG",
    "npxG+xAG",
    "PrgC",
    "PrgP",
    "PrgR",
    "Sh",
    "SoT",
    "KP",
    "PPA",
    "Tkl",
    "TklW",
    "Int",
    "Tkl+Int",
    "Blocks",
    "Clr",
    "Err",
    "Touches",
    "Carries",
    "Mis",
    "Dis",
    "Rec",
    "Recov",
    "Won",
    "Lost",
]

PER90_FEATURES = [
    "Gls",
    "Ast",
    "G+A",
    "G-PK",
    "xG",
    "npxG",
    "xAG",
    "npxG+xAG",
    "PrgC",
    "PrgP",
    "PrgR",
    "Sh",
    "SoT",
    "KP",
    "PPA",
    "Tkl",
    "TklW",
    "Int",
    "Tkl+Int",
    "Blocks",
    "Clr",
    "Touches",
    "Carries",
    "Mis",
    "Dis",
    "Rec",
    "Recov",
]

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

SCOUTING_X_FEATURES = ["xG_per90", "xAG_per90"]


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


def position_group(position: str) -> str:
    first = (position or "").split(",", 1)[0].strip().upper()
    if first == "GK":
        return "GK"
    if first == "DF":
        return "DF"
    if first == "MF":
        return "MF"
    if first == "FW":
        return "FW"
    return "UNK"


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


def load_latest_season_valuations() -> Dict[int, Dict[str, Any]]:
    latest: Dict[int, Dict[str, Any]] = {}
    for row in read_csv(TM_VALUATIONS_FILE):
        date = row.get("date", "")
        if date < SEASON_START or date > SEASON_END:
            continue

        player_id = to_int(row.get("player_id"))
        value = to_int(row.get("market_value_in_eur"))
        if player_id is None or value is None:
            continue

        if player_id not in latest or date > latest[player_id]["valuation_date"]:
            latest[player_id] = {
                "market_value_eur": value,
                "valuation_date": date,
            }
    return latest


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


def clean_fbref_row(row: Dict[str, str]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {
        "fbref_player": row.get("Player", ""),
        "player_name": row.get("Player", ""),
        "age": parse_age(row.get("Age")),
        "birth_year": parse_birth_year(row.get("Born")),
        "nation": row.get("Nation", ""),
        "position": row.get("Pos", ""),
        "position_group": position_group(row.get("Pos", "")),
        "squad": row.get("Squad", ""),
        "competition": normalize_competition(row.get("Comp", "")),
        "player_name_norm": normalize_text(row.get("Player")),
        "squad_norm": normalize_text(row.get("Squad")),
    }

    for feature in BASE_FEATURES:
        cleaned[feature] = to_float(row.get(feature))
    return cleaned


def add_tm_fields(
    row: Dict[str, Any],
    tm_player: Dict[str, Any],
    valuation: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    market_value = None
    valuation_date = ""
    if valuation:
        market_value = valuation.get("market_value_eur")
        valuation_date = valuation.get("valuation_date", "")
    if market_value is None:
        market_value = tm_player.get("market_value_in_eur")

    row["player_id"] = tm_player.get("player_id")
    row["player_name"] = tm_player.get("name") or row.get("fbref_player")
    row["foot"] = tm_player.get("foot", "")
    row["height_in_cm"] = tm_player.get("height_in_cm")
    row["market_value_eur"] = market_value
    row["highest_market_value_in_eur"] = tm_player.get("highest_market_value_in_eur")
    row["valuation_date"] = valuation_date
    return row


def add_per90_features(row: Dict[str, Any]) -> None:
    nineties = row.get("90s")
    if not nineties:
        for feature in PER90_FEATURES:
            row[f"{feature}_per90"] = None
        return

    for feature in PER90_FEATURES:
        value = row.get(feature)
        row[f"{feature}_per90"] = None if value is None else value / nineties


def aggregate_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["player_id"])].append(row)

    aggregated: List[Dict[str, Any]] = []
    for _, player_rows in grouped.items():
        primary = max(player_rows, key=lambda item: item.get("Min") or 0)
        output = {key: primary.get(key) for key in IDENTITY_COLUMNS}
        output["squad"] = " / ".join(dict.fromkeys(row.get("squad", "") for row in player_rows if row.get("squad")))
        output["competition"] = " / ".join(
            dict.fromkeys(
                normalize_competition(row.get("competition", ""))
                for row in player_rows
                if row.get("competition")
            )
        )

        for feature in BASE_FEATURES:
            values = [row.get(feature) for row in player_rows if row.get(feature) is not None]
            output[feature] = sum(values) if values else None

        add_per90_features(output)
        aggregated.append(output)

    return sorted(aggregated, key=lambda item: item.get("player_name", ""))


def build_datasets() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Counter]:
    players_by_id, exact_index, year_index = load_tm_players()
    latest_valuations = load_latest_season_valuations()

    matched_rows: List[Dict[str, Any]] = []
    unmatched_rows: List[Dict[str, Any]] = []
    stats: Counter = Counter()

    for raw_row in read_csv(FBREF_FILE):
        row = clean_fbref_row(raw_row)
        player_id, method, score = find_match(
            row["player_name_norm"],
            row["birth_year"],
            row["squad_norm"],
            players_by_id,
            exact_index,
            year_index,
        )
        row["tm_match_method"] = method
        row["tm_match_score"] = score

        if player_id is None:
            unmatched_rows.append(row)
            stats["unmatched"] += 1
            continue

        tm_player = players_by_id[player_id]
        add_tm_fields(row, tm_player, latest_valuations.get(player_id))
        matched_rows.append(row)
        stats[method] += 1

    return aggregate_rows(matched_rows), unmatched_rows, stats


def model_ready_filter(row: Dict[str, Any]) -> bool:
    if row.get("market_value_eur") is None:
        return False
    if row.get("Min") is None or row["Min"] < MIN_MINUTES_FOR_MODEL:
        return False
    if row.get("position_group") in {"GK", "UNK"}:
        return False
    return True


def scouting_filter(row: Dict[str, Any]) -> bool:
    if row.get("market_value_eur") is None:
        return False
    if row.get("Min") is None or row["Min"] < MIN_MINUTES_FOR_MODEL:
        return False
    return row.get("position_group") not in {"UNK", "GK"}


def main() -> None:
    merged_rows, unmatched_rows, stats = build_datasets()
    model_rows = [row for row in merged_rows if model_ready_filter(row)]
    scouting_rows = [row for row in merged_rows if scouting_filter(row)]

    feature_columns = BASE_FEATURES + [f"{feature}_per90" for feature in PER90_FEATURES]
    merged_columns = IDENTITY_COLUMNS + feature_columns
    scouting_columns = [
        "player_id",
        "player_name",
        "age",
        "birth_year",
        "nation",
        "position",
        "position_group",
        "squad",
        "competition",
        "market_value_eur",
        "Min",
        "90s",
    ] + SCOUTING_FEATURES

    write_csv(PROCESSED_DIR / "players_merged_2024_2025.csv", model_rows, merged_columns)
    write_csv(PROCESSED_DIR / "scouting_features_2024_2025.csv", scouting_rows, scouting_columns)
    write_csv(
        PROCESSED_DIR / "unmatched_players_2024_2025.csv",
        unmatched_rows,
        [
            "fbref_player",
            "age",
            "birth_year",
            "nation",
            "position",
            "squad",
            "competition",
            "tm_match_method",
            "tm_match_score",
        ],
    )

    print("Prepared 2024/25 datasets")
    print(f"Matched player rows before aggregation: {sum(stats.values()) - stats['unmatched']}")
    print(f"Unmatched FBref rows: {stats['unmatched']}")
    print(f"Exact matches: {stats['exact_name_birth_year']}")
    print(f"Fuzzy matches: {stats['fuzzy_name_birth_year']}")
    print(f"Valuation training rows: {len(model_rows)}")
    print(f"Scouting rows: {len(scouting_rows)}")
    print(f"Saved: {PROCESSED_DIR / 'players_merged_2024_2025.csv'}")
    print(f"Saved: {PROCESSED_DIR / 'scouting_features_2024_2025.csv'}")
    print(f"Saved: {PROCESSED_DIR / 'unmatched_players_2024_2025.csv'}")


if __name__ == "__main__":
    main()
