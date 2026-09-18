"""Systeme SUR sur les seules variables macroeconomiques.

Cette specification precede le VAR-X : on explique la variation du taux de
defaut de chaque tranche d'effectifs par les seules variables
macroeconomiques, sans retard des taux de defaut eux-memes. Elle sert de
point de comparaison et permet de mesurer l'apport des retards endogenes.

La recherche exhaustive de la meilleure combinaison de regresseurs par AIC
est conservee telle qu'elle a ete utilisee pendant le concours. Elle est
couteuse, deux puissance seize systemes pour seize regresseurs candidats,
d'ou la possibilite de plafonner la taille des combinaisons testees.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from linearmodels.system import SUR


def build_system(targets: dict[str, str], regressors: list[str]) -> dict[str, str]:
    """Construit un systeme d'equations partageant les memes regresseurs."""
    formula = " + ".join(regressors)
    return {name: f"{col} ~ {formula}" for name, col in targets.items()}


def fit(system: dict[str, str], data: pd.DataFrame):
    """Estime le systeme SUR."""
    return SUR.from_formula(system, data).fit()


def aic(results) -> float:
    """AIC systeme, calcule sur la somme des carres des residus empiles."""
    rss = sum(results.resids[eq].pow(2).sum() for eq in results.equations)
    n = results.nobs
    k = results.df_model
    return n * np.log(rss / n) + 2 * k


def best_combination(
    targets: dict[str, str],
    candidates: list[str],
    data: pd.DataFrame,
    max_size: int | None = None,
    verbose: bool = False,
) -> tuple[tuple[str, ...], float]:
    """Recherche exhaustive de la combinaison de regresseurs minimisant l'AIC."""
    max_size = max_size or len(candidates)
    best_score, best_combo = np.inf, ()

    for size in range(1, max_size + 1):
        for combo in combinations(candidates, size):
            system = build_system(targets, list(combo))
            try:
                score = aic(fit(system, data))
            except Exception as error:  # systeme singulier ou colineaire
                if verbose:
                    print(f"Echec pour {combo}: {error}")
                continue
            if verbose:
                print(f"{combo} -> AIC {score:.2f}")
            if score < best_score:
                best_score, best_combo = score, combo

    return best_combo, best_score
