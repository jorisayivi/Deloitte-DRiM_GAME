"""Random Forest sur les taux de defaut du pattern D.

Le modele parametrique impose une forme lineaire et une specification fixe.
La foret aleatoire sert de contre-epreuve : elle selectionne seule les
variables pertinentes et capte d'eventuelles non-linearites, au prix d'une
capacite d'inference tres reduite. On ne lui demande donc pas des
coefficients mais deux choses : la trajectoire predite et le classement des
variables par importance.

Trois jeux de variables explicatives sont testes en cascade :

1. les seuls retards de la serie cible ;
2. plus les retards des autres tranches d'effectifs ;
3. plus les variables exogenes macroeconomiques, energetiques et
   d'emissions.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

from .. import config as cfg
from .features import block_bootstrap


def fit_forest(
    X: pd.DataFrame,
    y: pd.Series,
    block_size: int,
    n_blocks: int,
    n_estimators: int = 100,
    max_depth: int | None = None,
    seed: int = cfg.SEED,
) -> RandomForestRegressor:
    """Entraine une foret sur un echantillon reechantillonne par blocs.

    Le meme tirage est applique a X et a y pour conserver l'appariement.
    """
    rng = np.random.default_rng(seed)
    n = len(X)
    starts = rng.integers(0, n - block_size + 1, size=n_blocks)
    index = np.concatenate([np.arange(s, s + block_size) for s in starts])

    model = RandomForestRegressor(
        n_estimators=n_estimators, max_depth=max_depth, random_state=seed
    )
    model.fit(X.iloc[index], y.iloc[index])
    return model


def tune(
    X: pd.DataFrame,
    y: pd.Series,
    block_sizes: list[int],
    n_blocks_options: list[int],
    n_estimators_options: list[int] = (100, 300),
    max_depth_options: list[int | None] = (None, 5, 10),
    train_size: float = 0.8,
    seed: int = cfg.SEED,
) -> tuple[RandomForestRegressor, dict, float]:
    """Calibration sur un decoupage temporel unique.

    Pas de validation croisee par k blocs : avec moins de trente
    observations, melanger les periodes ferait fuir de l'information du futur
    vers le passe. On coupe donc une seule fois, en respectant l'ordre
    chronologique.
    """
    if len(X) == 0:
        raise ValueError(
            "Matrice explicative vide : vérifier l'alignement temporel entre "
            "les taux de défaut et le fichier d'exogènes."
        )

    split = int(len(X) * train_size)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    best_model, best_params, best_mse = None, {}, np.inf

    for block_size in block_sizes:
        if block_size > len(X_train):
            continue
        for n_blocks in n_blocks_options:
            for n_estimators in n_estimators_options:
                for max_depth in max_depth_options:
                    model = fit_forest(
                        X_train,
                        y_train,
                        block_size=block_size,
                        n_blocks=n_blocks,
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        seed=seed,
                    )
                    mse = mean_squared_error(y_test, model.predict(X_test))
                    if mse < best_mse:
                        best_model, best_mse = model, mse
                        best_params = {
                            "block_size": block_size,
                            "n_blocks": n_blocks,
                            "n_estimators": n_estimators,
                            "max_depth": max_depth,
                        }

    if best_model is None:
        raise ValueError(
            "Aucun modèle estimé : les tailles de blocs demandées dépassent "
            f"la longueur de l'échantillon d'entraînement ({len(X_train)})."
        )

    return best_model, best_params, best_mse


def plot_predictions(
    y_true: pd.Series,
    y_pred: np.ndarray,
    target_col: str,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Reproduit le graphique observe contre predit de la presentation."""
    labels = y_true.index.strftime("%Y-%m")
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    ax.plot(labels, y_true.values, label="Observé", color="black", alpha=0.8)
    ax.plot(labels, y_pred, label="Prédit", color=cfg.GREEN, alpha=0.8)
    ax.set_title(f"Prédictions du taux de défaut des {target_col} du pattern D")
    ax.legend()
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    return ax


def importance_table(model: RandomForestRegressor, features: pd.Index) -> pd.DataFrame:
    """Importances des variables, triees par ordre decroissant."""
    return (
        pd.DataFrame({"Feature": features, "Importance": model.feature_importances_})
        .sort_values("Importance", ascending=False)
        .reset_index(drop=True)
    )


def plot_importances(
    importances: pd.DataFrame,
    target_col: str,
    top: int = 8,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    """Reproduit le graphique d'importance des variables de la presentation."""
    subset = importances.head(top)
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    ax.barh(subset["Feature"], subset["Importance"], align="center", color=cfg.GREEN)
    ax.set_title(f"Importance des variables du RF {target_col} du pattern D")
    ax.set_xlabel("Importance")
    ax.set_ylabel("Variables")
    ax.invert_yaxis()
    return ax
