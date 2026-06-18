from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
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
    VALUATION_MODEL_FILE,
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
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=3,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def train_valuation_model(
    df: pd.DataFrame | None = None,
    *,
    output_path: Path = VALUATION_MODEL_FILE,
) -> Pipeline:
    if df is None:
        df = load_player_seasons()

    train_df = df.dropna(subset=[TARGET_COLUMN]).copy()
    x_train = train_df[VALUATION_FEATURES]
    y_train = np.log1p(train_df[TARGET_COLUMN].astype(float))

    pipeline = build_valuation_pipeline()
    pipeline.fit(x_train, y_train)

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


def train_all() -> dict[str, object]:
    train_df = load_player_seasons()
    scouting_df = load_scouting_data()
    train_valuation_model(train_df)
    train_scouting_scaler(scouting_df)
    return {
        "valuation_model": VALUATION_MODEL_FILE,
        "scouting_scaler": SCOUTING_SCALER_FILE,
        "valuation_rows": len(train_df),
        "scouting_rows": len(scouting_df),
    }
