# Plan de contrôle pour l'orchestration de tours d'apprentissage fédéré

**INF1036 — Projet de recherche en informatique**  
**Étudiant :** Pape Macodou Seye  
**Session :** Été 2026

---

## Description

Plan de contrôle (pas d'entraînement d'un vrai réseau) : API REST, stratégies S0–S4,
mécanismes M1–M3, évaluation croisée 12 combinaisons (100 clients, 10 sélectionnés,
50 tours × 3 graines), approfondissement réputation (S4).

Deux chemins distincts :
- **API** (`coordinator.py`) — tours HTTP, clôture, FedAvg, Gini dans `/v1/metrics`
- **Expérience** (`experiment.py`) — calendrier **simulé** (pas d'appel HTTP)

**Docs hors rapport :** lire [`GUIDE_EXPLICATIF.md`](GUIDE_EXPLICATIF.md) (mode d’emploi du dépôt, corrections, lecture du code) et [`CHIFFRES_RAPPORT.md`](CHIFFRES_RAPPORT.md) (tableaux CSV).

---

## Structure

```
projet-federe/
├── federated_simulator.py
├── coordinator.py
├── strategies.py / stragglers.py / metrics.py
├── experiment.py / approfondissement.py / plot_figures.py
├── openapi.yaml
├── tests/
├── figures/                    # générées par make figures
├── resultats.csv / resultats_bruts.csv
├── resultats_approfondissement.csv
├── requirements.txt / Makefile
└── README.md
```

---

## Installation

Python **3.11+** recommandé (3.9 minimum).

```bash
python3 -m pip install -r requirements.txt
```

Ou tout d'un coup :

```bash
make all
```

(`make all` = install + expérience + approfondissement + figures + tests)

---

## Reproduction des résultats

```bash
python3 experiment.py              # → resultats.csv + resultats_bruts.csv
python3 approfondissement.py       # → resultats_approfondissement*.csv
python3 plot_figures.py            # → figures/pareto_*.png
python3 -m pytest -q
```

M3 côté expérience utilise un **délai simulé de 0,5 s** (proche du p50–p80 de S0).
Côté API, M3 peut utiliser l'horloge réelle via `mecanisme.demarrer()`.

---

## Serveur HTTP

```bash
python3 -m uvicorn coordinator:app --reload
```

- API : http://127.0.0.1:8000  
- Docs : http://127.0.0.1:8000/docs  
- Spec versionnée : `openapi.yaml`

Identité client = `client_id` (query / corps) — pas de jeton.

| Méthode | Route | Notes |
|---|---|---|
| POST | /v1/clients | `reliability` optionnel ∈ [0,1] |
| DELETE | /v1/clients/{id} | |
| GET | /v1/round | |
| POST | /v1/round/start | sélection + ouverture |
| GET | /v1/round/{id}/parameters | 409 si tour clôturé |
| POST | /v1/round/{id}/contributions | clôture + FedAvg ; **409 hors délai** |
| GET | /v1/metrics | compteurs + **gini_selections** |

Erreur structurée : `{ "erreur", "code", "tour_id" }`.

---

## Stratégies / mécanismes

- **S0** aléatoire sans remise · **S1** pondéré `data_size` sans remise  
- **S2** capacity · **S3** hybride 50/50 · **S4** reliability  
- **M1** attente complète · **M2** quota 80 % (arrivées ordonnées) · **M3** délai borné  

---

## Versions

- Python 3.11 (testé) / 3.9+  
- FastAPI ≥ 0.110 · Uvicorn ≥ 0.27 · Pydantic ≥ 2 · pytest ≥ 8 · matplotlib ≥ 3.8
