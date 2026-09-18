"""Chemins, constantes et conventions de nommage du projet.

Tous les chemins sont relatifs a la racine du depot. Ils peuvent etre
surcharges par la variable d'environnement DRIM_DATA_DIR, ce qui evite
les chemins absolus dans le code.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("DRIM_DATA_DIR", ROOT / "data" / "raw"))
OUTPUT_DIR = Path(os.environ.get("DRIM_OUTPUT_DIR", ROOT / "outputs"))

# Fichiers sources. Les deux premiers sont fournis par Deloitte et SAS dans le
# cadre du DRiM Game, les suivants ont ete construits par l'equipe a partir de
# sources publiques (INSEE, Banque de France, CITEPA, EIA).
FILE_DEFAILLANCES = DATA_DIR / "DRiM GAME 2024_Series defaillances d'entreprises.xlsx"
FILE_EXOGENES = DATA_DIR / "exogenes.xlsx"
FILE_EXOGENES_V2 = DATA_DIR / "exogenes_v2.xlsx"
FILE_EXO_LAG = DATA_DIR / "exo_lage_V1.xlsx"
FILE_EXO_LAG_CLIMAT = DATA_DIR / "exo_lageNEW.xlsx"
FILE_EMISSIONS = DATA_DIR / "emissions_ges.xlsx"

# ---------------------------------------------------------------------------
# Colonnes et modalites
# ---------------------------------------------------------------------------

COL_SECTEUR = "Secteur d'activité"
COL_EFFECTIF = "Tranche d'effectifs"
COL_GENERATION = "Generation"
COL_TAUX = "Taux de défaillances 3 mois"

EFFECTIFS_ORDER = [
    "Moins de 2 salariés",
    "3 - 10 salariés",
    "10 - 50 salariés",
    "50 - 200 salariés",
    "Plus de 200 salariés",
]

# Tranches utilisees dans la modelisation, apres fusion 3-10 et 10-50.
EFFECTIFS_MODEL = [
    "Moins de 2 salariés",
    "3 - 50 salariés",
    "50 - 200 salariés",
    "Plus de 200 salariés",
]

# ---------------------------------------------------------------------------
# Patterns sectoriels
# ---------------------------------------------------------------------------
# Les patterns sont issus de la lecture de la heatmap de clusters : on regroupe
# les secteurs qui presentent la meme repartition de clusters de taux de defaut
# selon les tranches d'effectifs.
#
# Le script exploratoire d'origine nommait ces groupes Safe / MidSafe /
# MidRisky / Risky. La presentation les nomme A / B / C / D. On garde la
# nomenclature de la presentation et on expose la correspondance pour pouvoir
# relire l'ancien code.

PATTERN_SECTORS = {
    "A": [
        "Activités financières et d'assurance",
        "Agriculture, sylviculture et pêche",
        "Santé humaine et action sociale",
    ],
    "B": [
        "Activités spécialisées, scientifiques et techniques",
        "Commerce ; réparation d'automobiles et de motocycles",
        "Production et distribution d'eau ; assainissement, gestion des déchets et dépollution",
        "Production et distribution d'électricité, de gaz, de vapeur et d'air conditionné",
    ],
    "C": [
        "Activités de services administratifs et de soutien",
        "Industrie manufacturière",
        "Information et communication",
        "Activités immobilières",
    ],
    # D est le groupe residuel : Construction, Hebergement et restauration,
    # Transports et entreposage.
}

PATTERN_DEFAULT = "D"

LEGACY_PATTERN_NAMES = {"A": "Safe", "B": "MidSafe", "C": "MidRisky", "D": "Risky"}

# ---------------------------------------------------------------------------
# Decoupage temporel
# ---------------------------------------------------------------------------

DATE_PRE_COVID = "2020-03-01"
DATE_COVID_END = "2021-07-01"

# ---------------------------------------------------------------------------
# Notes de transition
# ---------------------------------------------------------------------------
# Notes de risque de transition par secteur, utilisees pour annoter les
# correlations croisees. Elles proviennent du referentiel de notation
# sectorielle fourni avec l'enonce du DRiM Game.

NOTES_TRANSITION = {
    "Transports et entreposage": 6.3,
    "Production et distribution d'électricité, de gaz, de vapeur et d'air conditionné": 6.4,
    "Commerce ; réparation d'automobiles et de motocycles": 6.3,
    "Industrie manufacturière": 8.8,
}

# ---------------------------------------------------------------------------
# Graphique
# ---------------------------------------------------------------------------

SEED = 42
GREEN = "#87bf20"
DARK_GREEN = "#046a38"
CLUSTER_PALETTE = {"A": "#a5d867", "B": "#54a021", "C": "#0f5c2e"}
