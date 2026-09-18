"""Etape 4 : Random Forest sur une tranche d'effectifs du pattern D.

Remplace les quatre blocs copies-colles du script exploratoire d'origine :
la tranche cible et le jeu de variables exogenes sont des arguments.

    python scripts/04_random_forest.py --tranche "3 - 50 salariés"
    python scripts/04_random_forest.py --tranche "Plus de 200 salariés" --exogenes climat

Le jeu `macro` correspond aux variables macroeconomiques, le jeu `climat`
ajoute les prix de l'energie et les emissions sectorielles, ce qui produit
le graphique d'importance de la slide "Modèle avec les émissions".
"""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_squared_error

from drim import config as cfg
from drim.data import load_defaillances, load_exogenes, to_period_index
from drim.ml.features import create_features_targets, create_lags
from drim.ml.random_forest import importance_table, plot_importances, plot_predictions, tune
from drim.patterns import pattern_by_effectif

EXO_FILES = {"macro": cfg.FILE_EXO_LAG, "climat": cfg.FILE_EXO_LAG_CLIMAT}


def build_matrix(taux: pd.DataFrame, target_col: str, exo_key: str, lags: int = 4):
    """Assemble retards de la cible, retards des autres tranches et exogenes."""
    taux = to_period_index(taux)
    X_target, y_target = create_features_targets(taux[target_col], lags)

    others = create_lags(taux.drop(columns=target_col), max_lag=lags)
    X = X_target.join(others, how="inner")

    exogenes = load_exogenes(EXO_FILES[exo_key], shift_months=-1)
    X = X.join(exogenes, how="inner")

    y = y_target.loc[X.index]
    return X, y


def main(target_col: str, exo_key: str) -> None:
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pivot = load_defaillances()
    taux = pattern_by_effectif(pivot, pattern="D")

    X, y = build_matrix(taux, target_col, exo_key)
    print(f"{X.shape[0]} observations, {X.shape[1]} variables explicatives")

    model, params, mse_test = tune(
        X,
        y,
        block_sizes=[12, 16, 18, 20],
        n_blocks_options=[50, 100],
    )
    print(f"Hyperparamètres retenus : {params}")
    print(f"MSE sur l'échantillon de test : {mse_test:.3e}")

    y_pred = model.predict(X)
    print(f"MSE sur l'échantillon complet : {mean_squared_error(y, y_pred):.3e}")

    slug = target_col.replace(" ", "").replace("-", "_")

    plot_predictions(y, y_pred, target_col)
    plt.savefig(cfg.OUTPUT_DIR / f"04_predictions_{slug}_{exo_key}.png", dpi=200, bbox_inches="tight")

    importances = importance_table(model, X.columns)
    print("\nDix variables les plus importantes")
    print(importances.head(10).to_string(index=False))

    plot_importances(importances, target_col)
    plt.savefig(cfg.OUTPUT_DIR / f"04_importances_{slug}_{exo_key}.png", dpi=200, bbox_inches="tight")
    importances.to_csv(cfg.OUTPUT_DIR / f"04_importances_{slug}_{exo_key}.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tranche", default="3 - 50 salariés", choices=cfg.EFFECTIFS_MODEL)
    parser.add_argument("--exogenes", default="macro", choices=list(EXO_FILES))
    args = parser.parse_args()
    main(args.tranche, args.exogenes)
