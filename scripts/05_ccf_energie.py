"""Etape 5 : sensibilite des secteurs aux prix du petrole et des energies.

Produit les deux grilles de correlations croisees de la fin de la
presentation, ainsi qu'un tableau de synthese confrontant la note de
transition de chaque secteur a la sensibilite effectivement mesuree.

    python scripts/05_ccf_energie.py
"""

from __future__ import annotations

from drim import config as cfg
from drim.climate.ccf import panel
from drim.data import load_defaillances, load_exogenes

# Colonnes attendues dans le fichier d'exogenes energetiques.
PRICES = {
    "Prix du Brent": "Prix_brent",
    "Prix de l'énergie": "Prix_energie",
}


def main() -> None:
    cfg.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pivot = load_defaillances()
    pivot.columns = pivot.columns.to_period("M")

    exogenes = load_exogenes(cfg.FILE_EXO_LAG_CLIMAT, shift_months=-1)

    for label, column in PRICES.items():
        if column not in exogenes.columns:
            print(f"Colonne {column} absente du fichier, série ignorée")
            continue

        fig, summary = panel(pivot, exogenes[column], label)
        slug = column.lower()
        fig.savefig(cfg.OUTPUT_DIR / f"05_ccf_{slug}.png", dpi=200, bbox_inches="tight")
        summary.to_csv(cfg.OUTPUT_DIR / f"05_ccf_{slug}.csv", index=False)

        print(f"\n{label}")
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
