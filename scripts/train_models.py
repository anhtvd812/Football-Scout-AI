from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from football_scout.train import train_all  # noqa: E402


def _format_eur(value: float) -> str:
    return f"EUR {value:,.0f}"


def main() -> None:
    print("Training valuation model and scouting scaler...")
    artifacts = train_all()

    print(f"Saved valuation model to {artifacts['valuation_model']}")
    print(f"Saved scouting scaler to {artifacts['scouting_scaler']}")
    print(f"Training rows: {artifacts['valuation_rows']} player-seasons")
    print(f"Scouting rows: {artifacts['scouting_rows']}")

    metrics = artifacts.get("valuation_metrics")
    if metrics:
        print()
        print("Valuation hold-out metrics (20% test split, final model trained on 100% data):")
        print(
            f"  Split: train={metrics['train_rows']}, test={metrics['test_rows']} "
            f"({metrics['feature_count']} features)"
        )
        print(f"  R2 (log scale):   {metrics['r2_log']:.4f}")
        print(f"  MAE (log scale):  {metrics['mae_log']:.4f}")
        print(f"  RMSE (log scale): {metrics['rmse_log']:.4f}")
        print(f"  R2 (EUR):         {metrics['r2_eur']:.4f}")
        print(f"  MAE (EUR):        {_format_eur(metrics['mae_eur'])}")
        print(f"  RMSE (EUR):       {_format_eur(metrics['rmse_eur'])}")
        print(f"  MAPE:             {metrics['mape_pct']:.1f}%")
        print(f"  Median APE:       {metrics['median_ape_pct']:.1f}%")
        print(f"Saved metrics to {artifacts['valuation_metrics_file']}")


if __name__ == "__main__":
    main()
