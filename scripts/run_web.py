from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

import uvicorn  # noqa: E402


if __name__ == "__main__":
    uvicorn.run("football_scout.api:app", host="0.0.0.0", port=8000, reload=True)
