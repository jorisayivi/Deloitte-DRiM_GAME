"""Genere un jeu de donnees synthetique au format attendu.

Les fichiers sources du concours ne sont pas redistribuables. Ce script
fabrique des fichiers de meme structure, avec des valeurs aleatoires, pour
que le pipeline soit executable de bout en bout par un lecteur qui n'a pas
acces aux donnees. Les resultats obtenus n'ont evidemment aucune
interpretation economique.

    python scripts/00_donnees_synthetiques.py --dossier data/raw
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from drim import config as cfg

SECTEURS = [
    "Activités de services administratifs et de soutien",
    "Activités financières et d'assurance",
    "Activités immobilières",
    "Activités spécialisées, scientifiques et techniques",
    "Agriculture, sylviculture et pêche",
    "Commerce ; réparation d'automobiles et de motocycles",
    "Construction",
    "Hébergement et restauration",
    "Industrie manufacturière",
    "Information et communication",
    "Production et distribution d'eau ; assainissement, gestion des déchets et dépollution",
    "Production et distribution d'électricité, de gaz, de vapeur et d'air conditionné",
    "Santé humaine et action sociale",
    "Transports et entreposage",
]

MACRO = [
    "PIB",
    "IPC",
    "Taux_chomage",
    "Prix_Gazole",
    "Climat_affaires",
    "Prix_elec",
    "CAC",
    "taux_interet_lt",
]

ENERGIE = [
    "Prix_brent",
    "Prix_energie",
    "Vapeur",
    "Combustibles_minéraux_solides",
    "Produits_pétroliers",
    "Ensemble",
]

RETARDS = ["IPC", "IPC_lag1", "IPC_lag2", "IPC_lag3", "CAC_lag3", "CAC_diff_lag4"]


def main(dossier: Path, seed: int = 0) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    generations = pd.date_range("2016-12-01", periods=29, freq="3MS")

    # --- Taux de defaillance ------------------------------------------------
    # Niveau de base par serie, plus une tendance haussiere qui imite la
    # rupture post-Covid, plus un bruit.
    lignes = []
    for secteur in SECTEURS:
        for effectif in cfg.EFFECTIFS_ORDER:
            base = rng.uniform(0.0005, 0.002)
            tendance = np.linspace(0, rng.uniform(0, 0.004), len(generations))
            serie = base + tendance + rng.normal(0, 0.0002, len(generations))
            for date, valeur in zip(generations, serie):
                lignes.append(
                    {
                        cfg.COL_SECTEUR: secteur,
                        cfg.COL_EFFECTIF: effectif,
                        cfg.COL_GENERATION: date,
                        cfg.COL_TAUX: max(valeur, 0.0),
                    }
                )
    pd.DataFrame(lignes).to_excel(dossier / cfg.FILE_DEFAILLANCES.name, index=False)

    # --- Exogenes macro en niveau et en difference --------------------------
    exogenes = pd.DataFrame({cfg.COL_GENERATION: generations})
    for col in MACRO:
        exogenes[col] = rng.normal(0, 1, len(generations)).cumsum() + 100
    exogenes.to_excel(dossier / cfg.FILE_EXOGENES.name, index=False)

    exogenes_v2 = exogenes.copy()
    for col in MACRO:
        exogenes_v2[f"{col}_diff"] = exogenes_v2[col].diff()
    exogenes_v2.to_excel(dossier / cfg.FILE_EXOGENES_V2.name, index=False)

    # --- Exogenes deja retardes, dates au mois suivant la fin de trimestre ---
    retards = pd.DataFrame({cfg.COL_GENERATION: generations + pd.DateOffset(months=1)})
    for col in RETARDS:
        retards[col] = rng.normal(0, 1, len(generations))
    retards.to_excel(dossier / cfg.FILE_EXO_LAG.name, index=False)

    climat = retards.copy()
    for col in ENERGIE:
        climat[col] = rng.normal(0, 1, len(generations)).cumsum()
    climat.to_excel(dossier / cfg.FILE_EXO_LAG_CLIMAT.name, index=False)

    print(f"Cinq fichiers synthétiques écrits dans {dossier}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier", default=str(cfg.DATA_DIR), type=Path)
    args = parser.parse_args()
    main(args.dossier)
