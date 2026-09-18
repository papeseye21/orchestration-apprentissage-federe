# Chiffres et ajouts alignés sur les CSV (v3)

Source de vérité : `resultats.csv`, `resultats_bruts.csv`, `resultats_approfondissement.csv`.
Reproduction : `make all` ou `python3 experiment.py && python3 approfondissement.py && python3 plot_figures.py`.

## Tableau §8.2 (moyenne ± σ, 3 graines)

| Combinaison | Durée moy. ± σ (s) | p95 | Contrib. | Gini ± σ | Jamais contribué |
|---|---|---|---|---|---|
| S0+M1 | 0,632 ± 0,098 | 1,456 | 9,23 | 0,225 ± 0,012 | 0,7 % |
| S0+M2 | 0,239 ± 0,001 | 0,463 | 7,37 | 0,244 ± 0,013 | 10,0 % |
| S0+M3 | 0,548 ± 0,101 | 1,002 | 9,05 | 0,238 ± 0,002 | 1,7 % |
| S1+M1 | 0,761 ± 0,044 | 1,386 | 9,26 | 0,427 ± 0,038 | 12,3 % |
| S1+M2 | 0,294 ± 0,031 | 0,530 | 7,45 | 0,395 ± 0,016 | 16,7 % |
| S1+M3 | 0,676 ± 0,095 | 1,232 | 8,97 | 0,396 ± 0,027 | 11,3 % |
| S2+M1 | 0,156 ± 0,018 | 0,210 | 9,08 | 0,900 ± 0 | 90,0 % |
| S2+M2 | 0,113 ± 0,010 | 0,141 | 7,39 | 0,900 ± 0 | 90,0 % |
| S2+M3 | 0,156 ± 0,018 | 0,210 | 9,08 | 0,900 ± 0 | 90,0 % |
| S3+M1 | 0,499 ± 0,086 | 1,052 | 9,24 | 0,601 ± 0,028 | 8,0 % |
| S3+M2 | 0,151 ± 0,008 | 0,253 | 7,43 | 0,605 ± 0,005 | 30,3 % |
| S3+M3 | 0,453 ± 0,064 | 1,156 | 9,26 | 0,603 ± 0,005 | 8,3 % |

Note : **S2+M1 = S2+M3** car les 10 clients les plus rapides finissent avant le délai M3 simulé (0,5 s).

## Approfondissement S0 vs S4 (M1)

| Métrique | S0 | S4 |
|---|---|---|
| Durée | 0,641 ± 0,129 s | 0,461 ± 0,143 s |
| Contributions | 9,29 | 9,89 (+6,5 %) |
| Gini | 0,233 ± 0,020 | 0,900 ± 0 |
| Pearson(reliability, capacity) | ≈ 0,02 | |
| t-test contrib. | t≈−4,21, p≈0,049 | |
| t-test Gini | t≈−58,7, p≈0,0003 | |

## Pareto (recommandations)

- **Vitesse** : S2+M2 (0,113 s) — Gini 0,90 acceptable seulement si l'équité n'est pas un critère.
- **Compromis** : S3+M1 (0,499 s, Gini 0,60, 9,24 contrib.).
- **Équité** : S0+M1 (Gini 0,225).

Figures : `figures/pareto_duree_gini.png`, `figures/pareto_duree_contributions.png`.

## Rapport Word

Le fichier `../rapport_projet_federe_v3.docx` incorpore ces chiffres et les ajouts du plan (glossaire, 409, H3, limites, journal IA, etc.).
