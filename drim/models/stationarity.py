"""Tests de racine unitaire.

Les taux de defaut en niveau ne sont pas stationnaires sur la periode 2016
a 2024 : la rupture post-Covid produit une tendance marquee. Toute la
modelisation parametrique est donc menee en difference premiere.
"""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import adfuller


def adf_test(series: pd.Series, alpha: float = 0.05) -> dict:
    """Test de Dickey-Fuller augmente sur une serie."""
    clean = series.dropna()
    stat, pvalue, _, _, critical, _ = adfuller(clean, autolag="AIC")
    return {
        "ADF Statistic": stat,
        "p-value": pvalue,
        "Critical 5%": critical["5%"],
        "Stationnaire": pvalue < alpha,
    }


def adf_table(df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Applique le test ADF a chaque colonne et renvoie un tableau de synthese."""
    results = {col: adf_test(df[col], alpha=alpha) for col in df.columns}
    table = pd.DataFrame(results).T
    table.index.name = "Variable"
    return table
