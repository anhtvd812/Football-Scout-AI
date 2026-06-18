from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from prepare_2024_2025_dataset import (
    FUZZY_THRESHOLD,
    MIN_MINUTES_FOR_MODEL,
    PROCESSED_DIR,
    RAW_DIR,
    SCOUTING_FEATURES,
    SCOUTING_X_FEATURES,
    find_match,
    load_tm_players,
    normalize_competition,
    normalize_text,
    parse_age,
    parse_birth_year,
    read_csv,
    to_float,
    to_int,
    write_csv,
)


TM_VALUATIONS_FILE = RAW_DIR / "player_valuations.csv"
SEASON_2024_2025_EXTENDED_START = "2024-07-01"
SEASON_2024_2025_EXTENDED_END = "2025-06-30"


@dataclass(frozen=True)
class SeasonConfig:
    season: str
    stats_file: Path
    delimiter: str
    encoding: str
    source_is_per90: bool
    goals_are_total: bool
    valuation_start: str
    valuation_end: str


SEASONS = [
    SeasonConfig(
        season="2021_2022",
        stats_file=RAW_DIR / "players_data-2021_2022.csv",
        delimiter=";",
        encoding="latin-1",
        source_is_per90=True,
        goals_are_total=False,
        valuation_start="2022-05-01",
        valuation_end="2022-07-31",
    ),
    SeasonConfig(
        season="2022_2023",
        stats_file=RAW_DIR / "players_data-2022_2023.csv",
        delimiter=";",
        encoding="latin-1",
        source_is_per90=True,
        goals_are_total=True,
        valuation_start="2023-05-01",
        valuation_end="2023-07-31",
    ),
    SeasonConfig(
        season="2024_2025",
        stats_file=RAW_DIR / "players_data-2024_2025.csv",
        delimiter=",",
        encoding="utf-8",
        source_is_per90=False,
        goals_are_total=True,
        valuation_start="2025-05-01",
        valuation_end="2025-07-31",
    ),
]


CANONICAL_TOTAL_FEATURES = [
    "MP",
    "Starts",
    "Min",
    "90s",
]

CANONICAL_PER90_FEATURES = [
    "Gls_per90",
    "Ast_per90",
    "xG_per90",
    "npxG_per90",
    "xAG_per90",
    "PrgC_per90",
    "PrgP_per90",
    "PrgR_per90",
    "Sh_per90",
    "SoT_per90",
    "KP_per90",
    "PPA_per90",
    "Tkl_per90",
    "TklW_per90",
    "Int_per90",
    "Blocks_per90",
    "Clr_per90",
    "Touches_per90",
    "Carries_per90",
    "Mis_per90",
    "Dis_per90",
    "Rec_per90",
    "Recov_per90",
    "AerWon_per90",
    "AerLost_per90",
]

RAW_TOTAL_TO_PER90 = {
    "Gls": "Gls_per90",
    "Ast": "Ast_per90",
    "xG": "xG_per90",
    "npxG": "npxG_per90",
    "xAG": "xAG_per90",
    "PrgC": "PrgC_per90",
    "PrgP": "PrgP_per90",
    "PrgR": "PrgR_per90",
    "Sh": "Sh_per90",
    "SoT": "SoT_per90",
    "KP": "KP_per90",
    "PPA": "PPA_per90",
    "Tkl": "Tkl_per90",
    "TklW": "TklW_per90",
    "Int": "Int_per90",
    "Blocks": "Blocks_per90",
    "Clr": "Clr_per90",
    "Touches": "Touches_per90",
    "Carries": "Carries_per90",
    "Mis": "Mis_per90",
    "Dis": "Dis_per90",
    "Rec": "Rec_per90",
    "Recov": "Recov_per90",
    "Won": "AerWon_per90",
    "Lost": "AerLost_per90",
}

KAGGLE_PER90_TO_CANONICAL = {
    "Assists": "Ast_per90",
    "Shots": "Sh_per90",
    "SoT": "SoT_per90",
    "CarProg": "PrgC_per90",
    "PasProg": "PrgP_per90",
    "RecProg": "PrgR_per90",
    "PasAss": "KP_per90",
    "PPA": "PPA_per90",
    "Tkl": "Tkl_per90",
    "TklW": "TklW_per90",
    "Int": "Int_per90",
    "Blocks": "Blocks_per90",
    "Clr": "Clr_per90",
    "Touches": "Touches_per90",
    "Carries": "Carries_per90",
    "CarMis": "Mis_per90",
    "CarDis": "Dis_per90",
    "Rec": "Rec_per90",
    "Recov": "Recov_per90",
    "AerWon": "AerWon_per90",
    "AerLost": "AerLost_per90",
}

IDENTITY_COLUMNS = [
    "player_id",
    "player_name",
    "season",
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
    "source_file",
]


def read_stats_csv(config: SeasonConfig) -> List[Dict[str, str]]:
    with config.stats_file.open(newline="", encoding=config.encoding) as handle:
        return list(csv.DictReader(handle, delimiter=config.delimiter))


def position_group(value: str) -> str:
    text = (value or "").upper().replace(",", "")
    for group in ("GK", "DF", "MF", "FW"):
        if text.startswith(group) or group in text:
            return group
    return "UNK"


def load_valuations_by_season() -> Dict[str, Dict[int, Dict[str, Any]]]:
    valuations_by_season: Dict[str, Dict[int, Dict[str, Any]]] = {
        config.season: {} for config in SEASONS
    }
    with TM_VALUATIONS_FILE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            player_id = to_int(row.get("player_id"))
            value = to_int(row.get("market_value_in_eur"))
            date = row.get("date", "")
            if player_id is None or value is None or not date:
                continue

            for config in SEASONS:
                if not (config.valuation_start <= date <= config.valuation_end):
                    continue

                season_values = valuations_by_season[config.season]
                if player_id not in season_values or date > season_values[player_id]["valuation_date"]:
                    season_values[player_id] = {
                        "market_value_eur": value,
                        "valuation_date": date,
                    }

    return valuations_by_season


def load_extended_valuations_2024_2025() -> Dict[int, Dict[str, Any]]:
    extended: Dict[int, Dict[str, Any]] = {}
    with TM_VALUATIONS_FILE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            player_id = to_int(row.get("player_id"))
            value = to_int(row.get("market_value_in_eur"))
            date = row.get("date", "")
            if player_id is None or value is None or not date:
                continue
            if not (SEASON_2024_2025_EXTENDED_START <= date <= SEASON_2024_2025_EXTENDED_END):
                continue
            if player_id not in extended or date > extended[player_id]["valuation_date"]:
                extended[player_id] = {
                    "market_value_eur": value,
                    "valuation_date": date,
                }
    return extended


def resolve_season_valuation(
    player_id: int,
    season_values: Dict[int, Dict[str, Any]],
    extended_values: Optional[Dict[int, Dict[str, Any]]],
    tm_player: Dict[str, Any],
    *,
    allow_current_fallback: bool = False,
) -> Tuple[Optional[Dict[str, Any]], str]:
    valuation = season_values.get(player_id)
    if valuation is not None:
        return valuation, "season_window"

    if extended_values is not None:
        valuation = extended_values.get(player_id)
        if valuation is not None:
            return valuation, "extended_season_window"

    if allow_current_fallback:
        current_value = tm_player.get("market_value_in_eur")
        if current_value is not None:
            return {
                "market_value_eur": current_value,
                "valuation_date": "",
            }, "current_market_value"

    return None, "none"


def finalize_scouting_metrics(row: Dict[str, Any], config: SeasonConfig) -> None:
    if not config.source_is_per90:
        return
    for feature in SCOUTING_X_FEATURES:
        if row.get(feature) is None:
            row[feature] = 0.0


def base_row(raw: Dict[str, str], config: SeasonConfig) -> Dict[str, Any]:
    player = raw.get("Player", "")
    squad = raw.get("Squad", "")
    position = raw.get("Pos", "")
    row: Dict[str, Any] = {
        "season": config.season,
        "fbref_player": player,
        "player_name": player,
        "age": parse_age(raw.get("Age")),
        "birth_year": parse_birth_year(raw.get("Born")),
        "nation": raw.get("Nation", ""),
        "position": position,
        "position_group": position_group(position),
        "squad": squad,
        "competition": normalize_competition(raw.get("Comp", "")),
        "source_file": config.stats_file.name,
        "player_name_norm": normalize_text(player),
        "squad_norm": normalize_text(squad),
    }
    for feature in CANONICAL_TOTAL_FEATURES:
        row[feature] = to_float(raw.get(feature))
    for feature in CANONICAL_PER90_FEATURES:
        row[feature] = None
    return row


def normalize_stats_row(raw: Dict[str, str], config: SeasonConfig) -> Dict[str, Any]:
    row = base_row(raw, config)

    if config.source_is_per90:
        for source, target in KAGGLE_PER90_TO_CANONICAL.items():
            row[target] = to_float(raw.get(source))
        goals = to_float(raw.get("Goals"))
        if config.goals_are_total:
            nineties = row.get("90s")
            row["Gls_per90"] = None if goals is None or not nineties else goals / nineties
        else:
            row["Gls_per90"] = goals
        return row

    nineties = row.get("90s")
    for source, target in RAW_TOTAL_TO_PER90.items():
        value = to_float(raw.get(source))
        if value is None or not nineties:
            row[target] = None
        else:
            row[target] = value / nineties
    return row


def attach_transfermarkt(
    row: Dict[str, Any],
    tm_player: Dict[str, Any],
    valuation: Dict[str, Any],
    method: str,
    score: Optional[int],
    valuation_source: str = "season_window",
) -> Dict[str, Any]:
    row["player_id"] = tm_player.get("player_id")
    row["player_name"] = tm_player.get("name") or row.get("fbref_player")
    row["foot"] = tm_player.get("foot", "")
    row["height_in_cm"] = tm_player.get("height_in_cm")
    row["highest_market_value_in_eur"] = tm_player.get("highest_market_value_in_eur")
    row["market_value_eur"] = valuation.get("market_value_eur")
    row["valuation_date"] = valuation.get("valuation_date", "")
    if valuation_source == "season_window":
        row["tm_match_method"] = method
    else:
        row["tm_match_method"] = f"{method}+{valuation_source}"
    row["tm_match_score"] = score
    return row


def weighted_average(values: Iterable[Tuple[Optional[float], float]]) -> Optional[float]:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values:
        if value is None or weight <= 0:
            continue
        numerator += value * weight
        denominator += weight
    if denominator == 0:
        return None
    return numerator / denominator


def aggregate_player_seasons(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[int, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["player_id"]), row["season"])].append(row)

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

        for feature in CANONICAL_TOTAL_FEATURES:
            values = [row.get(feature) for row in player_rows if row.get(feature) is not None]
            output[feature] = sum(values) if values else None

        weights = [row.get("90s") or 0.0 for row in player_rows]
        for feature in CANONICAL_PER90_FEATURES:
            output[feature] = weighted_average(
                (row.get(feature), weight) for row, weight in zip(player_rows, weights)
            )

        aggregated.append(output)

    return sorted(aggregated, key=lambda item: (item.get("season", ""), item.get("player_name", "")))


def build_multi_season_rows() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Counter]:
    players_by_id, exact_index, year_index = load_tm_players()
    valuations_by_season = load_valuations_by_season()
    extended_2024_2025 = load_extended_valuations_2024_2025()
    matched_rows: List[Dict[str, Any]] = []
    unmatched_rows: List[Dict[str, Any]] = []
    stats: Counter = Counter()

    for config in SEASONS:
        season_values = valuations_by_season[config.season]
        extended_values = extended_2024_2025 if config.season == "2024_2025" else None
        for raw in read_stats_csv(config):
            row = normalize_stats_row(raw, config)
            finalize_scouting_metrics(row, config)
            stats[f"{config.season}_raw_rows"] += 1

            player_id, method, score = find_match(
                row["player_name_norm"],
                row["birth_year"],
                row["squad_norm"],
                players_by_id,
                exact_index,
                year_index,
            )
            if player_id is None:
                row["tm_match_method"] = "none"
                row["tm_match_score"] = score
                unmatched_rows.append(row)
                stats[f"{config.season}_unmatched"] += 1
                continue

            tm_player = players_by_id[player_id]
            valuation, valuation_source = resolve_season_valuation(
                player_id,
                season_values,
                extended_values,
                tm_player,
                allow_current_fallback=config.season == "2024_2025",
            )
            if valuation is None:
                row["player_id"] = player_id
                row["tm_match_method"] = method
                row["tm_match_score"] = score
                unmatched_rows.append(row)
                stats[f"{config.season}_missing_valuation"] += 1
                continue

            attach_transfermarkt(
                row,
                tm_player,
                valuation,
                method,
                score,
                valuation_source=valuation_source,
            )
            matched_rows.append(row)
            stats[f"{config.season}_{method}"] += 1
            if valuation_source != "season_window":
                stats[f"{config.season}_{valuation_source}"] += 1

    return aggregate_player_seasons(matched_rows), unmatched_rows, stats


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
    all_rows, unmatched_rows, stats = build_multi_season_rows()
    model_rows = [row for row in all_rows if model_ready_filter(row)]
    scouting_rows = [row for row in all_rows if scouting_filter(row)]

    model_columns = IDENTITY_COLUMNS + CANONICAL_TOTAL_FEATURES + CANONICAL_PER90_FEATURES
    scouting_columns = [
        "player_id",
        "player_name",
        "season",
        "age",
        "birth_year",
        "nation",
        "position",
        "position_group",
        "squad",
        "competition",
        "market_value_eur",
        "valuation_date",
        "Min",
        "90s",
    ] + SCOUTING_FEATURES
    unmatched_columns = [
        "season",
        "fbref_player",
        "age",
        "birth_year",
        "nation",
        "position",
        "squad",
        "competition",
        "player_id",
        "tm_match_method",
        "tm_match_score",
        "source_file",
    ]

    write_csv(PROCESSED_DIR / "player_seasons_merged.csv", model_rows, model_columns)
    write_csv(PROCESSED_DIR / "scouting_features_multi_season.csv", scouting_rows, scouting_columns)
    write_csv(PROCESSED_DIR / "unmatched_players_multi_season.csv", unmatched_rows, unmatched_columns)

    print("Prepared multi-season datasets")
    for config in SEASONS:
        season = config.season
        matched = (
            stats[f"{season}_exact_name_birth_year"]
            + stats[f"{season}_fuzzy_name_birth_year"]
        )
        print(
            f"{season}: raw={stats[f'{season}_raw_rows']}, matched_with_value={matched}, "
            f"unmatched={stats[f'{season}_unmatched']}, missing_valuation={stats[f'{season}_missing_valuation']}, "
            f"extended_window={stats[f'{season}_extended_season_window']}, "
            f"current_value_fallback={stats[f'{season}_current_market_value']}"
        )
    print(f"Valuation training rows: {len(model_rows)}")
    print(f"Scouting rows: {len(scouting_rows)}")
    print(f"Saved: {PROCESSED_DIR / 'player_seasons_merged.csv'}")
    print(f"Saved: {PROCESSED_DIR / 'scouting_features_multi_season.csv'}")
    print(f"Saved: {PROCESSED_DIR / 'unmatched_players_multi_season.csv'}")


if __name__ == "__main__":
    main()
