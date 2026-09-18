"""Sensibilite des secteurs aux prix du petrole et des energies.

Derniere brique de l'analyse : verifier si les secteurs les plus exposes au
risque de transition sont aussi ceux dont le taux de defaut reagit aux prix
de l'energie. La reponse de la presentation est negative sur la periode
etudiee, ce qui justifie la conclusion sur la significativite encore limitee
des variables liees aux emissions.

Methode : correlation croisee entre la variation du prix considere et la
variation du taux de defaut sectoriel, pour des retards de 0 a 10
trimestres. Une correlation est jugee non significative si elle reste dans
la bande de plus ou moins 2 sur racine de n, approximation usuelle de
l'intervalle de confiance a 95 pour cent sous hypothese de bruit blanc.

Chaque secteur est annote de sa note de transition, ce qui permet de
confronter exposition theorique et sensibilite mesuree.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import ccf

from .. import config as cfg


def sector_series(pivot: pd.DataFrame, secteur: str) -> pd.Series:
    """Taux de defaut moyen d'un secteur, toutes tranches d'effectifs."""
    subset = pivot.xs(secteur, level=cfg.COL_SECTEUR)
    return subset.mean(axis=0)


def cross_correlation(
    price: pd.Series,
    default_rate: pd.Series,
    max_lag: int = 10,
    difference: bool = True,
) -> tuple[pd.Series, float]:
    """Correlation croisee entre un prix et un taux de defaut.

    Parameters
    ----------
    difference
        Si vrai, les deux series sont differenciees avant calcul. Les niveaux
        etant non stationnaires, une correlation calculee en niveau serait
        essentiellement une correlation de tendances.

    Returns
    -------
    values
        Correlations indexees par retard, de 0 a max_lag. Un retard k se lit
        comme l'effet du prix a la date t sur le taux de defaut a t+k.
    bound
        Demi-largeur de l'intervalle de confiance a 95 pour cent.
    """
    aligned = pd.concat([price, default_rate], axis=1, join="inner").dropna()
    if difference:
        aligned = aligned.diff().dropna()

    x = aligned.iloc[:, 0].to_numpy()
    y = aligned.iloc[:, 1].to_numpy()
    values = ccf(y, x, adjusted=False)[: max_lag + 1]

    bound = 2 / np.sqrt(len(aligned))
    return pd.Series(values, index=range(max_lag + 1), name="ccf"), bound


def is_invariant(values: pd.Series, bound: float) -> bool:
    """Vrai si aucune correlation ne sort de l'intervalle de confiance."""
    return bool((values.abs() < bound).all())


def plot_ccf(
    values: pd.Series,
    bound: float,
    price_label: str,
    secteur: str,
    note_transition: float | None = None,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Graphique en batons de la correlation croisee, format presentation."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4))

    markerline, stemlines, baseline = ax.stem(
        values.index, values.values, basefmt=" "
    )
    plt.setp(markerline, markersize=5, color=cfg.DARK_GREEN)
    plt.setp(stemlines, color=cfg.DARK_GREEN, linewidth=1)

    ax.axhline(bound, color="red", linestyle="--", linewidth=1, label="IC 95 %")
    ax.axhline(-bound, color="red", linestyle="--", linewidth=1)
    ax.axhline(0, color="black", linewidth=1)

    ax.set_ylim(-1, 1)
    ax.set_xticks(list(values.index))
    ax.set_title(f"CCF: {price_label} vs {secteur}", fontsize=9)
    ax.set_xlabel("Retard")
    ax.set_ylabel("Coefficient de corrélation croisée")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, color="#dcefc4", linewidth=0.5)

    if note_transition is not None:
        ax.set_xlabel(f"Retard\nNote de transition : {note_transition}")
    return ax


def panel(
    pivot: pd.DataFrame,
    price: pd.Series,
    price_label: str,
    secteurs: list[str] | None = None,
    max_lag: int = 10,
) -> tuple[plt.Figure, pd.DataFrame]:
    """Grille de correlations croisees pour plusieurs secteurs.

    Returns
    -------
    fig
        La figure, disposee en deux colonnes comme dans la presentation.
    summary
        Un tableau recapitulant, par secteur, la note de transition, la
        correlation maximale en valeur absolue et le verdict d'invariance.
    """
    secteurs = secteurs or list(cfg.NOTES_TRANSITION)
    n_rows = (len(secteurs) + 1) // 2
    fig, axes = plt.subplots(n_rows, 2, figsize=(14, 4 * n_rows))
    axes = np.atleast_1d(axes).ravel()

    rows = []
    for ax, secteur in zip(axes, secteurs):
        values, bound = cross_correlation(price, sector_series(pivot, secteur), max_lag)
        note = cfg.NOTES_TRANSITION.get(secteur)
        plot_ccf(values, bound, price_label, secteur, note_transition=note, ax=ax)
        rows.append(
            {
                "Secteur": secteur,
                "Note de transition": note,
                "|CCF| max": values.abs().max(),
                "Seuil IC 95 %": bound,
                "Invariant": is_invariant(values, bound),
            }
        )

    for ax in axes[len(secteurs) :]:
        ax.axis("off")

    fig.tight_layout()
    return fig, pd.DataFrame(rows)
