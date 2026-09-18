"""Etape 1 : clusterisation des series de taux de defaut.

Produit la heatmap de repartition des clusters par secteur et tranche
d'effectifs, ainsi que la trajectoire moyenne de chaque cluster.

    python scripts/01_clustering.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from drim import config as cfg
from drim.clustering import cluster_heatmap, fit_clusters, plot_mean_by_cluster
from drim.data import load_defaillances


def main() -> None:
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pivot = load_defaillances()
    print(f"{pivot.shape[0]} séries, {pivot.shape[1]} générations")

    labels = fit_clusters(pivot, n_clusters=3)
    print(labels.value_counts().sort_index().to_string())

    cluster_heatmap(labels)
    plt.savefig(cfg.OUTPUT_DIR / "01_heatmap_clusters.png", dpi=200, bbox_inches="tight")

    plot_mean_by_cluster(pivot, labels)
    plt.savefig(cfg.OUTPUT_DIR / "01_taux_moyen_par_cluster.png", dpi=200, bbox_inches="tight")

    labels.to_csv(cfg.OUTPUT_DIR / "01_clusters.csv")
    print(f"Sorties écrites dans {cfg.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
