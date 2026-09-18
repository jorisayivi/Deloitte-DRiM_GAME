"""Regroupement des secteurs en patterns A, B, C et D.

La heatmap de clusters donne, pour chaque secteur, une signature : la suite
des clusters obtenus sur les cinq tranches d'effectifs. Les secteurs qui
partagent la meme signature sont regroupes dans un meme pattern.

* A : taux de defaut faible et homogene selon la taille (secteurs stables,
  soutenus ou essentiels).
* B et C : situations intermediaires.
* D : taux de defaut fortement heterogene selon la taille, avec des PME tres
  exposees (construction, hebergement et restauration, transport).

Le pattern D concentre l'analyse de la suite du projet.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from . import config as cfg
from .data import merge_3_to_50


def assign_pattern(secteur: str) -> str:
    """Renvoie le pattern d'un secteur, D par defaut."""
    for pattern, secteurs in cfg.PATTERN_SECTORS.items():
        if secteur in secteurs:
            return pattern
    return cfg.PATTERN_DEFAULT


def add_pattern_column(series: pd.DataFrame) -> pd.DataFrame:
    """Ajoute une colonne Pattern a une table indexee par (secteur, tranche)."""
    out = series.copy()
    out["Pattern"] = out.index.get_level_values(cfg.COL_SECTEUR).map(assign_pattern)
    return out


def aggregate_by_pattern(series: pd.DataFrame) -> pd.DataFrame:
    """Taux de defaut moyen par pattern, en ligne, generations en colonnes."""
    tagged = add_pattern_column(series)
    aggregate = tagged.groupby("Pattern").mean()
    # L'ajout de la colonne Pattern passe l'index de colonnes en object, on
    # restaure le type date pour que les graphiques et les fusions marchent.
    aggregate.columns = pd.to_datetime(aggregate.columns)
    return aggregate


def pattern_by_effectif(series: pd.DataFrame, pattern: str = "D") -> pd.DataFrame:
    """Series de taux de defaut d'un pattern, par tranche d'effectifs.

    Returns
    -------
    DataFrame indexe par generation, une colonne par tranche d'effectifs,
    tranches 3-10 et 10-50 fusionnees en 3-50.
    """
    tagged = add_pattern_column(series)
    subset = tagged[tagged["Pattern"] == pattern].drop(columns="Pattern")
    by_effectif = subset.groupby(level=cfg.COL_EFFECTIF).mean().T
    by_effectif.index = pd.to_datetime(by_effectif.index)
    by_effectif.index.name = cfg.COL_GENERATION
    return merge_3_to_50(by_effectif)


def plot_patterns(aggregate: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Trajectoire du taux de defaut moyen de chaque pattern."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    for pattern in sorted(aggregate.index):
        ax.plot(aggregate.columns, aggregate.loc[pattern], marker="o", label=pattern)
    ax.set_title("Taux de défaut moyen par pattern")
    ax.set_xlabel("Génération")
    ax.set_ylabel("Taux de défaut moyen")
    ax.legend(title="Pattern")
    ax.grid(True, linestyle="--", alpha=0.6)
    return ax
