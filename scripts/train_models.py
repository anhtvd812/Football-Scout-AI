from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from football_scout.train import train_all  # noqa: E402


def main() -> None:
    print("Training valuation model and scouting scaler...")
    artifacts = train_all()
    print(f"Saved valuation model to {artifacts['valuation_model']}")
    print(f"Saved scouting scaler to {artifacts['scouting_scaler']}")
    print(f"Training rows: {artifacts['valuation_rows']} player-seasons")
    print(f"Scouting rows: {artifacts['scouting_rows']}")


if __name__ == "__main__":
    main()
