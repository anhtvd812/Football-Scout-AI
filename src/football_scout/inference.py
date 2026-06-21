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


def _number(row: pd.Series, column: str, default: float = 0.0) -> float:
    value = row.get(column)
    if pd.isna(value):
        return default
    return float(value)


def _valuation_explanation(row: pd.Series, predicted: float, actual: float) -> dict[str, Any]:
    positives: list[str] = []
    cautions: list[str] = []
    notes: list[str] = []

    age = _number(row, "age")
    position = str(row.get("position_group", ""))
    competition = str(row.get("competition", ""))
    minutes = _number(row, "Min")
    goals = _number(row, "Gls_per90")
    assists = _number(row, "Ast_per90")
    xg = _number(row, "xG_per90")
    xag = _number(row, "xAG_per90")
    carries = _number(row, "PrgC_per90")
    passes = _number(row, "PrgP_per90")
    key_passes = _number(row, "KP_per90")
    tackles = _number(row, "Tkl_per90")
    interceptions = _number(row, "Int_per90")

    if age and age <= 23:
        positives.append(f"Còn trẻ ({int(age)} tuổi), nên model cộng thêm kỳ vọng phát triển.")
    elif age and age >= 30:
        cautions.append(f"Tuổi {int(age)} khiến model thận trọng hơn so với nhóm cầu thủ trẻ.")

    if minutes >= 2400:
        positives.append("Số phút thi đấu cao, cho thấy vai trò ổn định trong đội.")
    elif minutes < 1200:
        cautions.append("Số phút thi đấu chưa cao, nên tín hiệu hiệu suất kém chắc chắn hơn.")

    if position == "FW":
        if goals >= 0.45:
            positives.append(f"Hiệu suất ghi bàn tốt cho tiền đạo ({goals:.2f} bàn/90).")
        elif goals < 0.25:
            cautions.append(f"Sản lượng bàn thắng chưa nổi bật với tiền đạo ({goals:.2f} bàn/90).")
    elif position == "MF":
        if goals >= 0.25:
            positives.append(f"Ghi bàn tốt so với mặt bằng tiền vệ ({goals:.2f} bàn/90).")
        if assists >= 0.20:
            positives.append(f"Kiến tạo tốt so với mặt bằng tiền vệ ({assists:.2f} kiến tạo/90).")
        if xg and xg < 0.20 and xag and xag < 0.20:
            cautions.append("xG/xAG chưa ở nhóm elite, nên model không đẩy giá lên quá cao.")
    elif position == "DF":
        if tackles >= 1.8 or interceptions >= 1.2:
            positives.append("Chỉ số phòng ngự nổi bật so với nhóm hậu vệ.")
        if goals < 0.05 and assists < 0.05:
            cautions.append("Đóng góp bàn thắng/kiến tạo thấp, điều này thường giới hạn valuation của hậu vệ.")

    if carries >= 3.0:
        positives.append(f"Kéo bóng tịnh tiến tốt ({carries:.2f} progressive carries/90).")
    if passes >= 5.0:
        positives.append(f"Chuyền tịnh tiến tốt ({passes:.2f} progressive passes/90).")
    if key_passes >= 2.0:
        positives.append(f"Tạo cơ hội tốt ({key_passes:.2f} key passes/90).")

    if "Premier League" in competition:
        positives.append("Thi đấu ở Premier League, giải đấu thường có mặt bằng valuation cao.")
    elif competition:
        notes.append(f"Competition trong dữ liệu: {competition}.")

    if actual > 0:
        gap = (actual - predicted) / actual
        if gap > MARKET_STATUS_RATIO:
            cautions.append(
                "Market value thực tế cao hơn đáng kể so với mức model kỳ vọng từ hiệu suất sân cỏ."
            )
        elif gap < -MARKET_STATUS_RATIO:
            positives.append(
                "Hiệu suất sân cỏ cao hơn mức market value hiện tại, nên model xem là có thể undervalued."
            )

    match_method = str(row.get("tm_match_method", ""))
    valuation_date = row.get("valuation_date")
    if "current_market_value" in match_method or pd.isna(valuation_date) or not str(valuation_date).strip():
        notes.append(
            "Market value dùng trong dòng này là fallback từ hồ sơ Transfermarkt, không phải valuation window cuối mùa."
        )

    notes.append(
        "Đây là giải thích rule-based cho demo: model chủ yếu nhìn hiệu suất sân cỏ, tuổi, vị trí và giải đấu; không biết hợp đồng, hype, thương hiệu hay bối cảnh chuyển nhượng."
    )

    return {
        "summary": (
            "Model định giá dựa trên profile hiệu suất cùng mùa rồi so với market value trong dữ liệu."
        ),
        "positive_factors": positives[:5],
        "caution_factors": cautions[:5],
        "notes": notes[:4],
    }


def predict_player_value(
    player_name: str,
    *,
    season: str | None = DEFAULT_SCOUTING_SEASON,
    player_seasons_path: Path = PLAYER_SEASONS_FILE,
    model_path: Path = VALUATION_MODEL_FILE,
) -> dict[str, Any]:
    df = load_player_seasons(player_seasons_path)
    row = resolve_player_row(df, player_name, season=season, allow_season_fallback=False)
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
        "explanation": _valuation_explanation(row, predicted_value, actual_value),
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

    target = resolve_player_row(df, player_name, season=None, allow_season_fallback=False)
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
