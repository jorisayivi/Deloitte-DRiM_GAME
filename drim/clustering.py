"""Clusterisation temporelle des couples (secteur, tranche d'effectifs).

Objectif : identifier quelles series de taux de defaut sont les plus et les
moins risquees, en tenant compte de la forme de la trajectoire et pas
seulement de son niveau moyen. D'ou le K-Means avec distance DTW, qui
tolere de legers decalages de phase entre series.

Les clusters sont ensuite renommes A, B, C par niveau de risque croissant
pour que la lecture ne depende pas de l'ordre arbitraire de sortie de
l'algorithme.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from tslearn.clustering import TimeSeriesKMeans

from . import config as cfg


def fit_clusters(
    series: pd.DataFrame,
    n_clusters: int = 3,
    seed: int = cfg.SEED,
) -> pd.Series:
    """Ajuste un K-Means DTW et renvoie le cluster de chaque serie.

    Parameters
    ----------
    series
        DataFrame indexe par (secteur, tranche d'effectifs), une colonne par
        generation.

    Returns
    -------
    Series de labels 'A', 'B' ou 'C', indexee comme `series`, ordonnee par
    taux de defaut moyen croissant.
    """
    model = TimeSeriesKMeans(
        n_clusters=n_clusters, metric="dtw", random_state=seed, verbose=False
    )
    labels = pd.Series(model.fit_predict(series.values), index=series.index)

    # Renommage par niveau de risque : le cluster de plus faible taux moyen
    # devient A. Sans cela, les lettres changent d'un run a l'autre.
    mean_by_label = series.mean(axis=1).groupby(labels).mean().sort_values()
    mapping = {old: new for old, new in zip(mean_by_label.index, "ABCDEFG")}
    return labels.map(mapping).rename("Cluster")


def cluster_heatmap(
    labels: pd.Series,
    title: str = "Répartition Globale des Clusters par Secteur et Tranche d'Effectifs",
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Heatmap secteur x tranche d'effectifs coloree par cluster."""
    table = labels.reset_index().pivot(
        index=cfg.COL_EFFECTIF, columns=cfg.COL_SECTEUR, values="Cluster"
    )
    table = table.reindex(index=cfg.EFFECTIFS_ORDER)

    letters = sorted(cfg.CLUSTER_PALETTE)
    numeric = table.replace({letter: i for i, letter in enumerate(letters)})

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(
        numeric.astype(float),
        annot=table.values,
        fmt="",
        cmap=sns.color_palette([cfg.CLUSTER_PALETTE[l] for l in letters]),
        cbar=False,
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("Secteur d'Activité")
    ax.set_ylabel("Tranche d'Effectifs")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    return ax


def plot_mean_by_cluster(
    series: pd.DataFrame,
    labels: pd.Series,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Trajectoire du taux de defaut moyen de chaque cluster."""
    aggregate = series.groupby(labels).mean()

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    for cluster in sorted(aggregate.index):
        ax.plot(
            aggregate.columns,
            aggregate.loc[cluster],
            marker="o",
            label=cluster,
            color=cfg.CLUSTER_PALETTE.get(cluster, "black"),
        )

    ax.axvspan(
        pd.to_datetime(cfg.DATE_COVID_END),
        aggregate.columns.max(),
        color="gray",
        alpha=0.2,
    )
    ax.set_title("Taux de défaut moyen par cluster")
    ax.set_xlabel("Génération")
    ax.set_ylabel("Taux de défaut moyen")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(title="Cluster")
    ax.grid(True, linestyle="--", alpha=0.6)
    return ax
