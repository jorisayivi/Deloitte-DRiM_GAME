"""Modele VAR-X du taux de defaut du pattern D, estime en SUR.

C'est le modele qui produit le tableau de la partie "Modelisation
parametrique" de la presentation : quatre equations, une par tranche
d'effectifs, chacune expliquee par les retards 1 et 2 des quatre tranches et
par deux variables exogenes en variation (prix de l'electricite et taux
d'interet long terme).

Structure, pour chaque tranche i :

    d TD_i,t = sum_j a_ij d TD_j,t-1 + sum_j b_ij d TD_j,t-2
               + c_i d PrixElec_t + d_i d TauxLT_t + e_i,t

Tout est en difference premiere, les taux de defaut en niveau n'etant pas
stationnaires sur la periode (voir models/stationarity.py).

Pourquoi un SUR et pas un VAR classique : l'echantillon est court, environ
29 trimestres, et un VAR complet a deux retards consomme beaucoup de degres
de liberte. Le SUR permet d'imposer des restrictions d'exclusion equation par
equation tout en exploitant la correlation entre les residus des quatre
equations, qui est forte puisque les tranches subissent les memes chocs.

Note de reproductibilite : cette implementation reconstruit la specification
telle qu'elle est decrite dans la presentation. Le script exploratoire
d'origine s'arretait a un SUR sans retards endogenes, les resultats presentes
ayant ete produits dans une version ulterieure qui n'a pas ete conservee. Les
coefficients obtenus en relancant ce module doivent donc etre compares au
tableau de la presentation, pas presumes identiques au signe pres.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from linearmodels.system import SUR

from .. import config as cfg

# Variables exogenes retenues dans la specification finale de la presentation.
EXOG_FINAL = ["Prix_elec_diff", "taux_interet_lt_diff"]


def build_design(
    taux: pd.DataFrame,
    exogenes: pd.DataFrame,
    max_lag: int = 2,
    exog_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, str], dict[str, str]]:
    """Construit la matrice de regression du VAR-X.

    Parameters
    ----------
    taux
        Taux de defaut du pattern D par tranche d'effectifs, en niveau,
        indexe par generation.
    exogenes
        Variables exogenes deja en difference premiere, index compatible.

    Returns
    -------
    design
        Table des variables differenciees, contemporaines et retardees.
    endog_names
        Correspondance nom de tranche -> nom de colonne contemporaine.
    lag_names
        Correspondance (tranche, retard) -> nom de colonne.
    """
    exog_cols = exog_cols or EXOG_FINAL

    diff = taux.diff().dropna()
    if not isinstance(diff.index, pd.PeriodIndex):
        diff.index = pd.to_datetime(diff.index).to_period("M")

    design = diff.copy()
    lag_names: dict[str, str] = {}
    for lag in range(1, max_lag + 1):
        for col in diff.columns:
            name = f"{col} [t-{lag}]"
            design[name] = diff[col].shift(lag)
            lag_names[(col, lag)] = name

    design = design.join(exogenes[exog_cols], how="left")
    design = design.dropna()

    endog_names = {col: col for col in diff.columns}
    return design, endog_names, lag_names


def _sanitize(design: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Renomme les colonnes en identifiants simples pour les formules.

    Les noms de tranches contiennent des espaces et des accents, que le
    parseur de formules de linearmodels ne digere pas.
    """
    alias = {col: f"v{i}" for i, col in enumerate(design.columns)}
    return design.rename(columns=alias), alias


def _iter_params(results):
    """Itere sur (equation, variable, coefficient, p-value).

    linearmodels expose les resultats d'un SUR avec un index MultiIndex
    (equation, variable) ou, selon les versions, un index plat de la forme
    "equation_variable". On gere les deux cas.
    """
    alias = getattr(results, "alias", {})
    params, pvalues = results.params, results.pvalues
    for key in params.index:
        if isinstance(key, tuple):
            equation, variable = key[0], key[-1]
        else:
            equation, _, variable = str(key).partition("_")
        yield equation, alias.get(variable, variable), params[key], pvalues[key]


def estimate(
    design: pd.DataFrame,
    targets: list[str] | None = None,
    restrictions: dict[str, list[str]] | None = None,
):
    """Estime le systeme SUR.

    Parameters
    ----------
    targets
        Variables expliquees, par defaut les quatre tranches d'effectifs.
    restrictions
        Pour chaque equation, liste des regresseurs a conserver. Par defaut
        toutes les variables retardees et exogenes entrent dans chaque
        equation.
    """
    targets = targets or [c for c in cfg.EFFECTIFS_MODEL if c in design.columns]
    regressors_all = [c for c in design.columns if c not in targets]

    renamed, alias = _sanitize(design)

    system = {}
    for target in targets:
        regressors = restrictions[target] if restrictions else regressors_all
        formula = " + ".join(alias[r] for r in regressors)
        system[target] = f"{alias[target]} ~ {formula}"

    results = SUR.from_formula(system, renamed).fit(cov_type="robust")
    try:
        results.alias = {v: k for k, v in alias.items()}
    except AttributeError:  # objet non extensible selon la version
        object.__setattr__(results, "alias", {v: k for k, v in alias.items()})
    return results


def backward_selection(
    design: pd.DataFrame,
    targets: list[str] | None = None,
    alpha: float = 0.10,
    min_regressors: int = 1,
) -> dict[str, list[str]]:
    """Selection descendante equation par equation.

    On retire iterativement le regresseur le moins significatif tant que sa
    p-value depasse `alpha`. C'est la procedure qui produit les cases a zero
    du tableau de la presentation : une case vide signifie que la variable a
    ete exclue de l'equation, pas que son coefficient est nul.
    """
    targets = targets or [c for c in cfg.EFFECTIFS_MODEL if c in design.columns]
    regressors_all = [c for c in design.columns if c not in targets]
    kept = {target: list(regressors_all) for target in targets}

    for target in targets:
        while len(kept[target]) > min_regressors:
            results = estimate(design, targets=[target], restrictions=kept)
            worst_var, worst_p = None, -np.inf
            for _, variable, _, pvalue in _iter_params(results):
                if variable in kept[target] and pvalue > worst_p:
                    worst_var, worst_p = variable, pvalue
            if worst_var is None or worst_p <= alpha:
                break
            kept[target].remove(worst_var)

    return kept


def coefficient_table(
    results,
    lag_names: dict,
    targets: list[str] | None = None,
    exog_cols: list[str] | None = None,
    alpha: float = 0.10,
    decimals: int = 2,
) -> pd.DataFrame:
    """Met en forme les coefficients comme le tableau de la presentation.

    Les coefficients dont la p-value depasse `alpha` sont remplaces par zero,
    ce qui correspond a la lecture retenue dans la presentation : seules les
    relations significatives a 5 ou 10 pour cent sont commentees.
    """
    targets = targets or cfg.EFFECTIFS_MODEL
    exog_cols = exog_cols or EXOG_FINAL

    columns = [lag_names[(t, 1)] for t in targets]
    columns += [lag_names[(t, 2)] for t in targets]
    columns += exog_cols

    table = pd.DataFrame(0.0, index=targets, columns=columns)

    for equation, variable, value, pvalue in _iter_params(results):
        if equation in table.index and variable in table.columns and pvalue <= alpha:
            table.loc[equation, variable] = round(value, decimals)

    return table


def significance_mask(
    results,
    lag_names: dict,
    targets: list[str] | None = None,
    exog_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Renvoie le seuil de significativite de chaque cellule : 5, 10 ou NaN.

    Sert a reproduire le code couleur du tableau, vert pour moins de 5 pour
    cent et bleu pour moins de 10 pour cent.
    """
    targets = targets or cfg.EFFECTIFS_MODEL
    exog_cols = exog_cols or EXOG_FINAL

    columns = [lag_names[(t, 1)] for t in targets]
    columns += [lag_names[(t, 2)] for t in targets]
    columns += exog_cols

    mask = pd.DataFrame(np.nan, index=targets, columns=columns)
    for equation, variable, _, pvalue in _iter_params(results):
        if equation in mask.index and variable in mask.columns:
            if pvalue <= 0.05:
                mask.loc[equation, variable] = 5
            elif pvalue <= 0.10:
                mask.loc[equation, variable] = 10
    return mask
