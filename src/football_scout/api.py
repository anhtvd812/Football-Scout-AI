from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from football_scout.config import DEFAULT_SCOUTING_SEASON, SCOUTING_FILE
from football_scout.inference import (
    ensure_models_trained,
    find_similar_players,
    predict_player_value,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_STATIC_DIR = ROOT_DIR / "web" / "static"

app = FastAPI(title="Football Scout AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=WEB_STATIC_DIR), name="static")


@lru_cache(maxsize=1)
def _player_names() -> list[str]:
    df = pd.read_csv(SCOUTING_FILE)
    season_df = df[df["season"] == DEFAULT_SCOUTING_SEASON]
    if season_df.empty:
        season_df = df
    names = sorted(season_df["player_name"].dropna().astype(str).unique().tolist())
    return names


@app.on_event("startup")
def startup() -> None:
    ensure_models_trained()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/players")
def players(q: str = Query("", min_length=0, max_length=100)) -> dict[str, list[str]]:
    query = q.strip().lower()
    names = _player_names()
    if not query:
        return {"players": names[:50]}
    matched = [name for name in names if query in name.lower()]
    return {"players": matched[:50]}


@app.get("/api/predict")
def api_predict(
    player_name: str = Query(..., min_length=1),
    season: str | None = Query(DEFAULT_SCOUTING_SEASON),
) -> dict:
    try:
        return predict_player_value(player_name=player_name, season=season)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/similar")
def api_similar(
    player_name: str = Query(..., min_length=1),
    max_price: int | None = Query(default=None, ge=0),
    max_age: int | None = Query(default=None, ge=0, le=50),
    top_k: int = Query(default=5, ge=1, le=20),
    season: str | None = Query(DEFAULT_SCOUTING_SEASON),
) -> dict:
    try:
        return find_similar_players(
            player_name=player_name,
            max_price=max_price,
            max_age=max_age,
            top_k=top_k,
            season=season,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc
