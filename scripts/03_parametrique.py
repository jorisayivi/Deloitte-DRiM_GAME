"""Etape 3 : modelisation parametrique du pattern D.

Enchaine trois choses :

1. les tests de stationnarite qui justifient le passage en difference
   premiere ;
2. le SUR sur variables macroeconomiques seules, avec selection par AIC ;
3. le VAR-X a deux retards, dont le tableau de coefficients est celui
   presente lors de la soutenance.

    python scripts/03_parametrique.py [--aic]

L'option --aic relance la recherche exhaustive de combinaisons, qui prend
plusieurs minutes.
"""

from __future__ import annotations

import argparse

import pandas as pd

from drim import config as cfg
from drim.data import load_defaillances, load_exogenes, split_level_and_diff
from drim.models import sur, varx
from drim.models.stationarity import adf_table
from drim.patterns import pattern_by_effectif


def main(run_aic: bool = False) -> None:
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pivot = load_defaillances()
    taux = pattern_by_effectif(pivot, pattern="D")

    exogenes = load_exogenes(cfg.FILE_EXOGENES_V2)
    _, exog_diff = split_level_and_diff(exogenes)

    # --- 1. Stationnarite ---------------------------------------------------
    print("Test ADF en niveau")
    print(adf_table(taux).to_string(), "\n")
    print("Test ADF en différence première")
    print(adf_table(taux.diff().dropna()).to_string(), "\n")

    # --- 2. SUR sur exogenes seules ----------------------------------------
    design, endog, lag_names = varx.build_design(taux, exog_diff, max_lag=2)

    if run_aic:
        candidates = list(exog_diff.columns)
        targets = {name: name for name in cfg.EFFECTIFS_MODEL if name in taux.columns}
        data = taux.diff().dropna().join(exog_diff, how="left").dropna()
        combo, score = sur.best_combination(targets, candidates, data, max_size=4, verbose=True)
        print(f"\nMeilleure combinaison AIC : {combo} (AIC {score:.2f})\n")

    # --- 3. VAR-X -----------------------------------------------------------
    results = varx.estimate(design)
    print(results)

    table = varx.coefficient_table(results, lag_names, alpha=0.10)
    mask = varx.significance_mask(results, lag_names)

    print("\nTableau des coefficients, zéro si non significatif à 10 %")
    print(table.to_string())

    table.to_csv(cfg.OUTPUT_DIR / "03_varx_coefficients.csv")
    mask.to_csv(cfg.OUTPUT_DIR / "03_varx_significativite.csv")

    with pd.option_context("display.float_format", "{:.5f}".format):
        print(f"\nSorties écrites dans {cfg.OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--aic", action="store_true", help="relancer la sélection AIC")
    args = parser.parse_args()
    main(run_aic=args.aic)
