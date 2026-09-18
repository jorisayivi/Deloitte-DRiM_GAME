"""Construction des variables explicatives et reechantillonnage temporel.

Le probleme central du volet machine learning est la taille de
l'echantillon : environ vingt-neuf trimestres par serie. Un bootstrap
classique detruirait la structure temporelle, d'ou un bootstrap par blocs,
qui tire des segments consecutifs et preserve l'autocorrelation locale.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def create_features_targets(series: pd.Series, lags: int) -> tuple[pd.DataFrame, pd.Series]:
    """Transforme une serie en table (retards, cible).

    Returns
    -------
    X
        Une colonne par retard, nommee lag_1 a lag_n.
    y
        La serie contemporaine, alignee sur X.
    """
    frame = pd.DataFrame({f"lag_{lag}": series.shift(lag) for lag in range(1, lags + 1)})
    frame["target"] = series
    frame = frame.dropna()
    return frame.drop(columns="target"), frame["target"]


def create_lags(df: pd.DataFrame, max_lag: int = 4) -> pd.DataFrame:
    """Ajoute les retards 1 a max_lag de chaque colonne d'une table."""
    lagged = {
        f"{col}_lag{lag}": df[col].shift(lag)
        for col in df.columns
        for lag in range(1, max_lag + 1)
    }
    return pd.DataFrame(lagged, index=df.index).dropna()


def block_bootstrap(
    data: pd.DataFrame | pd.Series,
    block_size: int,
    n_blocks: int,
    rng: np.random.Generator | None = None,
):
    """Tire n_blocks segments consecutifs de longueur block_size, avec remise.

    Les blocs sont concatenes dans l'ordre du tirage. La taille de bloc et le
    nombre de blocs sont calibres conjointement aux hyperparametres de la
    foret (voir ml/random_forest.tune).
    """
    rng = rng or np.random.default_rng()
    n = len(data)
    if block_size > n:
        raise ValueError(f"block_size={block_size} depasse la longueur {n}")

    starts = rng.integers(0, n - block_size + 1, size=n_blocks)
    blocks = [data.iloc[start : start + block_size] for start in starts]
    return pd.concat(blocks)
