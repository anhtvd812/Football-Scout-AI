from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from football_scout import find_similar_players, predict_player_value  # noqa: E402
from football_scout.inference import ensure_models_trained  # noqa: E402


def main() -> None:
    ensure_models_trained()

    valuation = predict_player_value("Xavi Simons")
    similar = find_similar_players("Kevin De Bruyne", max_price=30_000_000, max_age=25, top_k=5)

    print("=== predict_player_value ===")
    print(json.dumps(valuation, indent=2, ensure_ascii=False))
    print("\n=== find_similar_players ===")
    print(json.dumps(similar, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
