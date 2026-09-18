# Fichiers de données attendus

Aucun fichier de données n'est versionné. Déposer ici les fichiers suivants, ou pointer `DRIM_DATA_DIR` vers le dossier qui les contient.

## `DRiM GAME 2024_Series defaillances d'entreprises.xlsx`

Source : fournie aux équipes par Deloitte et SAS dans le cadre du concours. Format long, une ligne par croisement.

| Colonne | Contenu |
| --- | --- |
| `Secteur d'activité` | 14 secteurs, nomenclature agrégée type NAF A17 |
| `Tranche d'effectifs` | Moins de 2, 3-10, 10-50, 50-200, Plus de 200 salariés |
| `Generation` | fin de trimestre, du T4 2016 au T4 2023 |
| `Taux de défaillances 3 mois` | taux de défaillance sur 3 mois, en décimal |

## `exogenes.xlsx`

Variables macroéconomiques en niveau, une colonne `Generation` plus les séries : `PIB`, `IPC`, `Taux_chomage`, `Prix_Gazole`, `Climat des affaires en France`, `Prix_elec`, `CAC`, `taux_interet_lt`.

## `exogenes_v2.xlsx`

Même contenu, avec pour chaque série sa version en différence première, suffixée `_diff` : `PIB_diff`, `IPC_diff`, `Taux_chomage_diff`, `Prix_Gazole_diff`, `Climat_affaires_diff`, `Prix_elec_diff`, `CAC_diff`, `taux_interet_lt_diff`. C'est ce fichier qu'utilisent le SUR et le VAR-X.

## `exo_lage_V1.xlsx`

Variables macroéconomiques déjà retardées, préparées pour la forêt aléatoire : `IPC`, `IPC_lag1` à `IPC_lag3`, `CAC_lag3`, `IPC_diff_lag1`, `CAC_diff_lag4`, entre autres. Les dates sont exprimées au mois suivant la fin de trimestre, d'où le décalage de moins un mois appliqué au chargement.

## `exo_lageNEW.xlsx`

Même logique, enrichie des variables énergétiques et d'émissions : `Prix_brent`, `Prix_energie`, `Vapeur`, `Combustibles_minéraux_solides`, `Produits_pétroliers`, `Ensemble`, plus leurs retards. C'est ce fichier qui alimente le modèle avec émissions et les corrélations croisées.

## Remarque sur les générations

Toutes les sources sont recalées sur le premier jour du dernier mois du trimestre par `drim.data.adjust_to_quarter`. Sans ce recalage, les fusions produisent des lignes vides silencieuses, les fichiers ne datant pas les trimestres de la même façon.
