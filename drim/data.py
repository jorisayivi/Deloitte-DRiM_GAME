"""Chargement et mise en forme des donnees.

Deux familles de fichiers :

* la serie de defaillances fournie par Deloitte et SAS, au format long
  (secteur, tranche d'effectifs, generation, taux de defaillance 3 mois) ;
* les series exogenes macroeconomiques et energetiques, au format large,
  avec une colonne Generation.

Les generations sont trimestrielles mais datees au mois. On les recale
systematiquement sur la fin de trimestre pour pouvoir fusionner les sources.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config as cfg


def adjust_to_quarter(date: pd.Timestamp) -> pd.Timestamp:
    """Recale une date sur le premier jour du dernier mois de son trimestre."""
    month = date.month
    if month <= 3:
        month = 3
    elif month <= 6:
        month = 6
    elif month <= 9:
        month = 9
    else:
        month = 12
    return pd.Timestamp(year=date.year, month=month, day=1)


def load_defaillances(path: Path | str = cfg.FILE_DEFAILLANCES) -> pd.DataFrame:
    """Charge la table de defaillances et la pivote en series temporelles.

    Returns
    -------
    DataFrame indexe par (secteur, tranche d'effectifs), une colonne par
    generation, valeurs = taux de defaillance 3 mois.
    """
    df = pd.read_excel(path)
    df[cfg.COL_GENERATION] = df[cfg.COL_GENERATION].astype(str)

    pivot = df.pivot_table(
        index=[cfg.COL_SECTEUR, cfg.COL_EFFECTIF],
        columns=cfg.COL_GENERATION,
        values=cfg.COL_TAUX,
    )
    pivot.columns = pd.to_datetime(pivot.columns)
    return pivot.sort_index(axis=1)


def load_exogenes(
    path: Path | str,
    shift_months: int = 0,
    to_period: bool = True,
) -> pd.DataFrame:
    """Charge un fichier de variables exogenes et aligne son index temporel.

    Parameters
    ----------
    shift_months
        Decalage applique avant recalage trimestriel. Les fichiers de
        variables retardees sont dates au mois suivant la fin de trimestre,
        d'ou un decalage de -1 mois.
    to_period
        Si vrai, l'index est converti en PeriodIndex mensuel, ce qu'attendent
        statsmodels et linearmodels pour les fusions.
    """
    df = pd.read_excel(path)
    dates = pd.to_datetime(df[cfg.COL_GENERATION])
    if shift_months:
        dates = dates + pd.DateOffset(months=shift_months)
    df[cfg.COL_GENERATION] = dates.apply(adjust_to_quarter)

    df = df.set_index(cfg.COL_GENERATION)
    df.index = pd.to_datetime(df.index)
    if to_period:
        df.index = df.index.to_period("M")
    return df.sort_index()


def split_level_and_diff(exogenes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separe les colonnes en niveau des colonnes en difference premiere.

    La convention du fichier exogenes_v2 est un suffixe `_diff` pour les
    series deja differenciees.
    """
    diff_cols = exogenes.columns.str.endswith("diff")
    niveau = exogenes.loc[:, ~diff_cols].dropna()
    difference = exogenes.loc[:, diff_cols]
    return niveau, difference


def to_period_index(df: pd.DataFrame) -> pd.DataFrame:
    """Force l'index temporel en PeriodIndex mensuel.

    Les taux de defaut arrivent avec un index de dates, les fichiers
    exogenes avec un index de periodes. Sans harmonisation, les jointures
    renvoient silencieusement une table vide.
    """
    out = df.copy()
    if not isinstance(out.index, pd.PeriodIndex):
        out.index = pd.to_datetime(out.index).to_period("M")
    return out


def merge_3_to_50(df: pd.DataFrame) -> pd.DataFrame:
    """Fusionne les tranches 3-10 et 10-50 en une tranche 3-50 salaries.

    Les deux tranches se comportent de facon tres proche et cette fusion
    stabilise l'estimation sur un echantillon court (29 trimestres).
    Attend un DataFrame dont les colonnes sont les tranches d'effectifs.
    """
    out = df.copy()
    out["3 - 50 salariés"] = out[["3 - 10 salariés", "10 - 50 salariés"]].mean(axis=1)
    out = out.drop(columns=["3 - 10 salariés", "10 - 50 salariés"])
    return out[[c for c in cfg.EFFECTIFS_MODEL if c in out.columns]]
