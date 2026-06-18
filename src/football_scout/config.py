from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"

PLAYER_SEASONS_FILE = DATA_DIR / "player_seasons_merged.csv"
SCOUTING_FILE = DATA_DIR / "scouting_features_multi_season.csv"

VALUATION_MODEL_FILE = MODELS_DIR / "valuation_model.joblib"
SCOUTING_SCALER_FILE = MODELS_DIR / "scouting_scaler.joblib"

DEFAULT_SCOUTING_SEASON = "2024_2025"
NAME_MATCH_THRESHOLD = 85
MARKET_STATUS_RATIO = 0.15

VALUATION_TEST_SIZE = 0.2
VALUATION_RANDOM_STATE = 42
VALUATION_METRICS_FILE = MODELS_DIR / "valuation_metrics.json"

MULTI_SEASON_NUMERIC_FEATURES = [
    "age",
    "height_in_cm",
    "Min",
    "90s",
    "Gls_per90",
    "Ast_per90",
    "xG_per90",
    "xAG_per90",
    "Sh_per90",
    "SoT_per90",
    "PrgC_per90",
    "PrgP_per90",
    "PrgR_per90",
    "KP_per90",
    "PPA_per90",
    "Tkl_per90",
    "Int_per90",
    "Blocks_per90",
    "Clr_per90",
    "Touches_per90",
    "Carries_per90",
    "Recov_per90",
]

CATEGORICAL_FEATURES = ["position_group", "foot", "competition"]

VALUATION_FEATURES = MULTI_SEASON_NUMERIC_FEATURES + CATEGORICAL_FEATURES

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

TARGET_COLUMN = "market_value_eur"
