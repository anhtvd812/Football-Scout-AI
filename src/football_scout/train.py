from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from football_scout.config import (
    CATEGORICAL_FEATURES,
    MODELS_DIR,
    MULTI_SEASON_NUMERIC_FEATURES,
    PLAYER_SEASONS_FILE,
    SCOUTING_FEATURES,
    SCOUTING_FILE,
    SCOUTING_SCALER_FILE,
    TARGET_COLUMN,
    VALUATION_FEATURES,
    VALUATION_METRICS_FILE,
    VALUATION_MODEL_FILE,
    VALUATION_RANDOM_STATE,
    VALUATION_TEST_SIZE,
)


def load_player_seasons(path: Path = PLAYER_SEASONS_FILE) -> pd.DataFrame:
    return pd.read_csv(path)


def load_scouting_data(path: Path = SCOUTING_FILE) -> pd.DataFrame:
    return pd.read_csv(path)


def build_valuation_pipeline() -> Pipeline:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, MULTI_SEASON_NUMERIC_FEATURES),
            ("categorical", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )
    model = RandomForestRegressor(
        n_estimators=300,
        random_state=VALUATION_RANDOM_STATE,
        n_jobs=-1,
        min_samples_leaf=3,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def _valuation_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    train_df = df.dropna(subset=[TARGET_COLUMN]).copy()
    x = train_df[VALUATION_FEATURES]
    y_log = np.log1p(train_df[TARGET_COLUMN].astype(float))
    y_eur = train_df[TARGET_COLUMN].astype(float)
    return x, y_log, y_eur


def evaluate_valuation_model(
    df: pd.DataFrame | None = None,
    *,
    test_size: float = VALUATION_TEST_SIZE,
    random_state: int = VALUATION_RANDOM_STATE,
) -> dict[str, Any]:
    if df is None:
        df = load_player_seasons()

    x, y_log, y_eur = _valuation_target(df)
    x_train, x_test, y_train_log, y_test_log, _, y_test_eur = train_test_split(
        x,
        y_log,
        y_eur,
        test_size=test_size,
        random_state=random_state,
    )

    pipeline = build_valuation_pipeline()
    pipeline.fit(x_train, y_train_log)

    pred_log = pipeline.predict(x_test)
    pred_eur = np.expm1(pred_log)
    y_test_eur_arr = y_test_eur.to_numpy()
    pct_error = np.abs((y_test_eur_arr - pred_eur) / y_test_eur_arr)

    return {
        "feature_count": len(VALUATION_FEATURES),
        "numeric_features": len(MULTI_SEASON_NUMERIC_FEATURES),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "test_size": test_size,
        "r2_log": float(r2_score(y_test_log, pred_log)),
        "mae_log": float(mean_absolute_error(y_test_log, pred_log)),
        "rmse_log": float(np.sqrt(mean_squared_error(y_test_log, pred_log))),
        "r2_eur": float(r2_score(y_test_eur_arr, pred_eur)),
        "mae_eur": float(mean_absolute_error(y_test_eur_arr, pred_eur)),
        "rmse_eur": float(np.sqrt(mean_squared_error(y_test_eur_arr, pred_eur))),
        "mape_pct": float(np.mean(pct_error) * 100),
        "median_ape_pct": float(np.median(pct_error) * 100),
    }


def save_valuation_metrics(
    metrics: dict[str, Any],
    output_path: Path = VALUATION_METRICS_FILE,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return output_path


def train_valuation_model(
    df: pd.DataFrame | None = None,
    *,
    output_path: Path = VALUATION_MODEL_FILE,
) -> Pipeline:
    if df is None:
        df = load_player_seasons()

    x, y_log, _ = _valuation_target(df)
    pipeline = build_valuation_pipeline()
    pipeline.fit(x, y_log)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path)
    return pipeline


def train_scouting_scaler(
    df: pd.DataFrame | None = None,
    *,
    output_path: Path = SCOUTING_SCALER_FILE,
) -> StandardScaler:
    if df is None:
        df = load_scouting_data()

    scaler = StandardScaler()
    scaler.fit(df[SCOUTING_FEATURES].fillna(0.0))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, output_path)
    return scaler


def train_all(
    *,
    evaluate: bool = True,
    metrics_path: Path = VALUATION_METRICS_FILE,
) -> dict[str, object]:
    train_df = load_player_seasons()
    scouting_df = load_scouting_data()

    metrics: dict[str, Any] | None = None
    if evaluate:
        metrics = evaluate_valuation_model(train_df)
        save_valuation_metrics(metrics, metrics_path)

    train_valuation_model(train_df)
    train_scouting_scaler(scouting_df)

    result: dict[str, object] = {
        "valuation_model": VALUATION_MODEL_FILE,
        "scouting_scaler": SCOUTING_SCALER_FILE,
        "valuation_rows": len(train_df),
        "scouting_rows": len(scouting_df),
    }
    if metrics is not None:
        result["valuation_metrics"] = metrics
        result["valuation_metrics_file"] = metrics_path
    return result
