from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from football_scout.config import (
    DEFAULT_SCOUTING_SEASON,
    MARKET_STATUS_RATIO,
    PLAYER_SEASONS_FILE,
    SCOUTING_FEATURES,
    SCOUTING_FILE,
    SCOUTING_SCALER_FILE,
    VALUATION_FEATURES,
    VALUATION_MODEL_FILE,
)
from football_scout.player_lookup import resolve_player_row
from football_scout.train import (
    load_player_seasons,
    load_scouting_data,
    train_all,
    train_scouting_scaler,
    train_valuation_model,
)


def _ensure_valuation_model(model_path: Path = VALUATION_MODEL_FILE):
    if model_path.exists():
        return joblib.load(model_path)
    return train_valuation_model(output_path=model_path)


def _ensure_scouting_scaler(scaler_path: Path = SCOUTING_SCALER_FILE) -> StandardScaler:
    if scaler_path.exists():
        return joblib.load(scaler_path)
    return train_scouting_scaler(output_path=scaler_path)


def _market_status(predicted: float, actual: float) -> str:
    if actual <= 0:
        return "Unknown"
    ratio = (predicted - actual) / actual
    if ratio > MARKET_STATUS_RATIO:
        return "Undervalued"
    if ratio < -MARKET_STATUS_RATIO:
        return "Overvalued"
    return "Fairly valued"


def predict_player_value(
    player_name: str,
    *,
    season: str | None = DEFAULT_SCOUTING_SEASON,
    player_seasons_path: Path = PLAYER_SEASONS_FILE,
    model_path: Path = VALUATION_MODEL_FILE,
) -> dict[str, Any]:
    df = load_player_seasons(player_seasons_path)
    row = resolve_player_row(df, player_name, season=season)
    model = _ensure_valuation_model(model_path)

    features = pd.DataFrame([row[VALUATION_FEATURES].to_dict()])
    log_prediction = float(model.predict(features)[0])
    predicted_value = float(np.expm1(log_prediction))
    actual_value = float(row["market_value_eur"])

    return {
        "player_name": row["player_name"],
        "position": row["position_group"],
        "age": int(row["age"]) if pd.notna(row["age"]) else None,
        "predicted_value_eur": int(round(predicted_value)),
        "actual_market_value_eur": int(round(actual_value)),
        "market_status": _market_status(predicted_value, actual_value),
    }


def find_similar_players(
    player_name: str,
    max_price: int | None = None,
    max_age: int | None = None,
    top_k: int = 5,
    *,
    season: str | None = DEFAULT_SCOUTING_SEASON,
    scouting_path: Path = SCOUTING_FILE,
    scaler_path: Path = SCOUTING_SCALER_FILE,
) -> dict[str, Any]:
    df = load_scouting_data(scouting_path)
    if season is not None:
        season_df = df[df["season"] == season]
        if not season_df.empty:
            df = season_df

    target = resolve_player_row(df, player_name, season=None)
    target_position = target["position_group"]

    candidates = df[df["position_group"] == target_position].copy()
    candidates = candidates[candidates["player_name"] != target["player_name"]]

    if max_price is not None:
        candidates = candidates[candidates["market_value_eur"] <= max_price]
    if max_age is not None:
        candidates = candidates[candidates["age"] <= max_age]

    if candidates.empty:
        return {
            "target_player": target["player_name"],
            "results": [],
        }

    scaler = _ensure_scouting_scaler(scaler_path)
    target_vector = scaler.transform(
        pd.DataFrame([target[SCOUTING_FEATURES].fillna(0.0).to_dict()])
    )
    candidate_matrix = scaler.transform(candidates[SCOUTING_FEATURES].fillna(0.0))
    similarities = cosine_similarity(target_vector, candidate_matrix).flatten()

    ranked = candidates.copy()
    ranked["similarity_score"] = similarities
    ranked = ranked.sort_values("similarity_score", ascending=False).head(top_k)

    results = []
    for _, row in ranked.iterrows():
        results.append(
            {
                "name": row["player_name"],
                "age": int(row["age"]) if pd.notna(row["age"]) else None,
                "position": row["position_group"],
                "club": row["squad"],
                "market_value_eur": int(round(float(row["market_value_eur"]))),
                "similarity_score": round(float(row["similarity_score"]), 2),
            }
        )

    return {
        "target_player": target["player_name"],
        "results": results,
    }


def ensure_models_trained() -> None:
    if not VALUATION_MODEL_FILE.exists() or not SCOUTING_SCALER_FILE.exists():
        train_all()
