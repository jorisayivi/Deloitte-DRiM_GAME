# DRiM Game 2024 : défaillances d'entreprises, taille et transition

Travail réalisé pour le DRiM Game 2024, concours de gestion des risques organisé par Deloitte et SAS, par une équipe de quatre étudiants du Master ESA de l'Université d'Orléans : Joris AYIVI-TOGBASSA, Gaëtan BLECON, Marin LANGER et Mathis VIE.

**Problématique.** Analyser les relations entre la défaillance d'entreprises de taille différente au sein d'un même secteur, et déterminer dans quelle mesure ces relations dépendent de la conjoncture et du niveau d'émission de gaz à effet de serre des différents secteurs.

La présentation soutenue devant le jury est disponible dans [`docs/DRiM_Game_Deloitte.pdf`](docs/).

## Résultats principaux

1. **Rupture post-Covid.** Le taux de défaut s'effondre pendant la crise sanitaire, sous l'effet des prêts garantis par l'État et de la fermeture des tribunaux de commerce, puis explose à partir de 2022 avec une forte hétérogénéité entre secteurs et entre tailles d'entreprises.
2. **La taille compte plus que le secteur.** Les tranches 3 à 50 salariés portent l'essentiel de la hausse. Les entreprises de moins de 2 salariés et celles de plus de 200 salariés restent relativement épargnées, pour des raisons opposées : faible exposition au crédit pour les premières, trésorerie et accès au financement pour les secondes.
3. **Quatre patterns sectoriels.** Une clusterisation temporelle des 70 couples secteur x tranche d'effectifs fait apparaître quatre signatures. Le pattern A regroupe des secteurs stables et homogènes selon la taille (finance, agriculture, santé). Le pattern D regroupe des secteurs très hétérogènes et cycliques (construction, hébergement et restauration, transport), et concentre la suite de l'analyse.
4. **Effet domino.** Le modèle VAR-X met en évidence une autodépendance forte de la tranche 3 à 50 salariés, ainsi qu'un effet des défaillances de grandes entreprises sur les tranches inférieures avec deux trimestres de retard. Les grandes entreprises se comportent comme un indicateur avancé de la conjoncture.
5. **Inflation oui, émissions pas encore.** L'inflation ressort comme un déterminant significatif du défaut, y compris dans la forêt aléatoire où les retards de l'IPC dominent les importances. Les variables d'émissions et les prix de l'énergie ne montrent pas de sensibilité significative sur la période, ce qui relativise la capacité actuelle des modèles de risque à capter le risque de transition.

## Structure du dépôt

```
drim/                     bibliothèque
  config.py               chemins, patterns sectoriels, constantes
  data.py                 chargement et alignement temporel des sources
  clustering.py           K-Means DTW et heatmap de clusters
  patterns.py             regroupement des secteurs en patterns A à D
  models/
    stationarity.py       tests ADF
    sur.py                SUR sur exogènes, sélection par AIC
    varx.py               VAR-X à deux retards, tableau de coefficients
  ml/
    features.py           retards et bootstrap par blocs
    random_forest.py      entraînement, calibration, graphiques
  climate/
    ccf.py                corrélations croisées énergies et secteurs
scripts/                  points d'entrée numérotés, à exécuter dans l'ordre
  00_donnees_synthetiques.py  jeu de test au format des sources
  01_clustering.py
  02_patterns.py
  03_parametrique.py
  04_random_forest.py
  05_ccf_energie.py
legacy/                   script exploratoire d'origine, conservé tel quel
data/raw/                 emplacement attendu des fichiers sources
outputs/                  graphiques et tables produits
```

## Installation et exécution

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Sans les fichiers sources, générer un jeu synthétique de même structure
python scripts/00_donnees_synthetiques.py

python scripts/01_clustering.py
python scripts/02_patterns.py
python scripts/03_parametrique.py
python scripts/04_random_forest.py --tranche "3 - 50 salariés"
python scripts/04_random_forest.py --tranche "Plus de 200 salariés" --exogenes climat
python scripts/05_ccf_energie.py
```

Les chemins de données peuvent être redirigés sans toucher au code :

```bash
export DRIM_DATA_DIR=/chemin/vers/mes/donnees
```

## Données

Les fichiers sources ne sont pas versionnés. Le script `00_donnees_synthetiques.py` fabrique des fichiers de même structure, avec des valeurs aléatoires, pour rendre le dépôt exécutable sans eux. Voir [`data/raw/README.md`](data/raw/README.md) pour la liste des fichiers attendus et leurs colonnes.

La série de défaillances provient du dispositif de suivi fourni aux équipes par Deloitte et SAS dans le cadre du concours : 14 secteurs d'activité, 5 tranches d'effectifs, taux de défaillance à 3 mois, du 4e trimestre 2016 au 4e trimestre 2023. Les séries exogènes ont été construites par l'équipe à partir de sources publiques (INSEE, Banque de France, CITEPA, EIA).

## Périmètre du code

Les visualisations descriptives des premières slides (taux de défaillance par secteur, nombre de défaillances par tranche d'effectifs, nombre d'entreprises saines) ont été réalisées dans **SAS Viya** et n'ont pas d'équivalent Python dans ce dépôt. Tout le reste, clusterisation, patterns, modélisation paramétrique, forêt aléatoire et corrélations croisées, est reproduit ici.

## Honnêteté sur la reproduction

Ce dépôt est une réécriture du script de travail utilisé pendant le concours, conservé dans [`legacy/`](legacy/). La réécriture corrige des chemins absolus, factorise quatre blocs de forêt aléatoire quasi identiques et remplace le vocabulaire interne Safe, MidSafe, MidRisky, Risky par la nomenclature A, B, C, D de la présentation.

Deux sections ont dû être reconstruites à partir de la présentation, le code correspondant n'ayant pas été conservé :

- le **VAR-X** de `models/varx.py`, dont la spécification est celle décrite dans la présentation : quatre équations, retards 1 et 2 des quatre tranches, variation du prix de l'électricité et du taux d'intérêt long terme, estimation en SUR ;
- les **corrélations croisées par secteur** de `climate/ccf.py`, avec annotation des notes de transition.

Ces deux modules sont fonctionnels et fidèles à la méthode décrite, mais les coefficients obtenus en les relançant peuvent différer à la marge de ceux affichés dans la présentation.

## Limites

L'échantillon est court, 29 trimestres, ce qui contraint fortement la modélisation : agrégation des tranches 3-10 et 10-50, bootstrap par blocs plutôt que validation croisée, sélection descendante plutôt que modèle complet. Les résultats sur les variables d'émissions sont à lire comme une absence de signal détectable sur cette profondeur d'historique, pas comme une absence d'effet.

## Licence

MIT. Les données sources ne sont pas couvertes par cette licence et ne sont pas redistribuées.
