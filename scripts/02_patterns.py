"""Etape 2 : regroupement des secteurs en patterns et extraction du pattern D.

Produit la trajectoire moyenne de chaque pattern et le fichier de series par
tranche d'effectifs du pattern D, qui alimente les etapes 3 et 4.

    python scripts/02_patterns.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from drim import config as cfg
from drim.data import load_defaillances
from drim.patterns import aggregate_by_pattern, assign_pattern, pattern_by_effectif, plot_patterns


def main() -> None:
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pivot = load_defaillances()

    secteurs = pivot.index.get_level_values(cfg.COL_SECTEUR).unique()
    for pattern in ["A", "B", "C", "D"]:
        membres = [s for s in secteurs if assign_pattern(s) == pattern]
        print(f"Pattern {pattern} : {len(membres)} secteurs")
        for secteur in membres:
            print(f"    {secteur}")

    aggregate = aggregate_by_pattern(pivot)
    plot_patterns(aggregate)
    plt.savefig(cfg.OUTPUT_DIR / "02_taux_par_pattern.png", dpi=200, bbox_inches="tight")

    taux_d = pattern_by_effectif(pivot, pattern="D")
    taux_d.to_csv(cfg.OUTPUT_DIR / "02_pattern_D_par_effectif.csv")
    print(f"\nPattern D : {taux_d.shape[0]} générations, {taux_d.shape[1]} tranches")


if __name__ == "__main__":
    main()
