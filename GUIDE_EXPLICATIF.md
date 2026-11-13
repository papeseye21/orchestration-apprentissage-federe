# Guide explicatif (hors rapport)

Document destiné à **Pape Macodou Seye** (et à quiconque reprend le dépôt).  
Ce n’est **pas** le rapport de cours : c’est le mode d’emploi de tout ce qui a été ajouté / corrigé autour du code.

---

## 1. En une phrase

Le projet est un **plan de contrôle** d’apprentissage fédéré : on choisit qui participe (S0–S4), on décide quand arrêter d’attendre les lents (M1–M3), on mesure durée / contributions / équité (Gini).  
On **n’entraîne pas** un vrai réseau : le « modèle » est un vecteur de 8 nombres (`federated_simulator.py`, fourni).

---

## 2. Deux chemins différents (important)

| Chemin | Fichier | Rôle |
|---|---|---|
| **API HTTP** | `coordinator.py` | Serveur FastAPI : inscription, tour, contributions, clôture, FedAvg, métriques |
| **Expérience** | `experiment.py` | Boucle locale qui simule 12 combinaisons **sans appeler l’API** |

Pourquoi deux chemins ? L’expérience doit être **rapide et reproductible** (temps simulé, graines). L’API montre le comportement HTTP réel (codes 403/404/409, Gini live).

Le rapport et les CSV viennent de **l’expérience**, pas d’appels HTTP.

---

## 3. Ce qui a été corrigé (par rapport à l’ancienne version)

1. **M2** : les contributions sont traitées **dans l’ordre de durée** (les plus lents en dernier). Avant, on coupait dans l’ordre de sélection → M2 ne retirait pas vraiment les stragglers.
2. **M3** : en expérience, délai **simulé 0,5 s** (pas `time.time()` à 5 s pendant que `sleep=False`). Sinon M3 = M1 presque toujours.
3. **S1** : tirage **sans remise** (plus de doublons possibles avec `random.choices`).
4. **API** : clôture de tour, FedAvg à la clôture, **409** si contribution après clôture, **Gini** dans `/v1/metrics`, champ `reliability`.
5. **Chiffres du rapport** : alignés sur `resultats.csv` (plus de tableau « lissé »).
6. **Livrables** : tests, figures Pareto, `requirements.txt`, `Makefile`, CSV bruts, README au bon nom.

---

## 4. Fichiers du dépôt (qui fait quoi)

```
projet-federe/
├── federated_simulator.py   # Fourni : clients, entraînement local factice, FedAvg
├── strategies.py            # S0 S1 S2 S3 S4 — qui sélectionner
├── stragglers.py            # M1 M2 M3 — quand clôturer
├── metrics.py               # Gini, Pearson, t-test, IC
├── coordinator.py           # API REST
├── experiment.py            # 12 combinaisons → resultats.csv + bruts
├── approfondissement.py     # S0 vs S4 → resultats_approfondissement*.csv
├── plot_figures.py          # Pareto PNG
├── openapi.yaml             # Spec API versionnée
├── tests/test_core.py       # Tests pytest
├── requirements.txt / Makefile / README.md
├── CHIFFRES_RAPPORT.md      # Tableau des nombres (aide rédaction)
└── GUIDE_EXPLICATIF.md      # Ce fichier
```

**Hors dossier GitHub (sur le Desktop ProjetMAco) :**
- `rapport_projet_federe_FINAL.docx` — rapport à jour
- `Projet_D7.docx` — énoncé
- Ce guide peut être copié dans le README ou remis à part au correcteur si besoin

---

## 5. Comment lancer (reproduction)

```bash
cd projet-federe
python3 -m pip install -r requirements.txt
make all
```

Équivalent manuel :

```bash
python3 experiment.py              # → resultats.csv + resultats_bruts.csv
python3 approfondissement.py       # → resultats_approfondissement*.csv
python3 plot_figures.py            # → figures/*.png
python3 -m pytest -q
```

Serveur API (démo) :

```bash
python3 -m uvicorn coordinator:app --reload
# docs : http://127.0.0.1:8000/docs
```

---

## 6. Lecture guidée du code

### 6.1 `strategies.py` — qui participe ?

Chaque stratégie a la **même signature** : `selectionner(clients, nombre) → liste`.

| Code | Idée simple |
|---|---|
| S0 | Tirage au sort (`random.sample`) |
| S1 | Plus on a de données (`data_size`), plus on a de chances (sans doublon) |
| S2 | Toujours les plus rapides (`capacity`) |
| S3 | 50 % rapides + 50 % au hasard parmi le reste |
| S4 | Les plus fiables (`reliability`) — approfondissement seulement |

### 6.2 `stragglers.py` — quand arrêter d’attendre ?

| Code | Idée simple |
|---|---|
| M1 | On attend **tout le monde** |
| M2 | On s’arrête à **80 %** d’arrivées |
| M3 | On s’arrête si le **temps** dépasse le plafond (0,5 s simulé / 5 s API) |

Le paramètre `temps_ecoule_s` = horloge de l’expérience. S’il est `None`, M3 utilise l’horloge réelle (API).

### 6.3 `experiment.py` — cœur de la note

Pour chaque tour :

1. Sélectionner 10 clients  
2. Simuler leur entraînement local (chacun a une `duration_s`)  
3. **Trier** par durée croissante (= ordre d’arrivée)  
4. Demander à M1/M2/M3 si on clôture  
5. Agréger (FedAvg) les contributions `completed=True`  
6. Après 50 tours × 3 graines : Gini, moyennes, σ, % jamais contribué  

### 6.4 `coordinator.py` — API

État en mémoire (`clients`, `contributions`, `tour_actuel`).  
À chaque contribution : on teste la clôture ; si oui → FedAvg + statut `termine`.  
Une contribution tardive → **409** `ROUND_CLOSED`.

### 6.5 `metrics.py`

- `coefficient_gini` : équité des **sélections** (0 = égal, proche de 1 = inégal)  
- `pearson` / `ttest_ind` / `intervalle_confiance` : pour l’approfondissement (H1–H3)

---

## 7. Comment lire les résultats (sans se tromper)

**Pareto / reco du rapport :**
- Plus **rapide** : S2+M2 (~0,11 s) mais Gini 0,90 (très inéquitable)
- **Compromis** : S3+M1 (~0,50 s, Gini ~0,60)
- Plus **équitable** : S0+M1 (Gini ~0,23)

**Piège classique :** S2+M1 = S2+M3. Ce n’est **pas** un bug après correctif : les 10 plus rapides finissent avant 0,5 s, donc M3 ne coupe personne.

**Approfondissement S4 :** plus de contributions complètes, Gini × ~4, durée ~1,4× plus courte que S0 — mais Pearson(reliability, capacity) ≈ 0 → on ne force pas une histoire de corrélation inventée.

---

## 8. Rapport Word — lequel utiliser ?

| Fichier | Statut |
|---|---|
| `rapport_projet_federe_v2.docx` | Ancienne version (chiffres faux) — **ne plus rendre** |
| `rapport_projet_federe_v3.docx` / `FINAL.docx` | Version alignée CSV + annexes |

Avant dépôt GitHub : pousser le dossier `projet-federe/` mis à jour, et joindre le rapport FINAL.

---

## 9. Checklist avant remise

- [ ] `make all` passe sans erreur  
- [ ] `resultats.csv` = mêmes nombres que le tableau §8.2 du rapport  
- [ ] README : nom **Pape Macodou Seye**  
- [ ] Figures présentes dans `figures/`  
- [ ] Ne pas inventer de nouveaux chiffres dans le résumé  

---

## 10. Contact / maintenance

Pour changer S0/M1 par défaut dans l’API : modifier les variables globales `strategie` et `mecanisme` en tête de `coordinator.py`.  
Pour changer le délai M3 d’expérience : `DELAI_M3_SIMULE_S` dans `experiment.py`, puis relancer et **recopier** les CSV dans le rapport.
