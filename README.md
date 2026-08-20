# Plan de contrôle pour l'orchestration de tours d'apprentissage fédéré

**INF1036 — Projet de recherche en informatique**  
**Étudiant :** Abdoulaye Cissé  
**Session :** Été 2026

---

## Description

Ce projet implémente un plan de contrôle pour l'orchestration de tours d'apprentissage fédéré. Il comprend :

- Une API REST (coordinateur) pour gérer les clients, les tours et les contributions
- 4 stratégies de sélection des clients (S0, S1, S2, S3)
- 3 mécanismes de gestion des stragglers (M1, M2, M3)
- Une évaluation croisée des 12 combinaisons
- Un approfondissement sur la réputation des clients (S4)

---

## Structure du projet

```
projet-federe/
├── federated_simulator.py      # Simulateur fourni par le prof
├── coordinator.py              # Serveur HTTP (API REST)
├── strategies.py               # Stratégies de sélection S0-S4
├── stragglers.py               # Mécanismes de clôture M1-M3
├── metrics.py                  # Coefficient de Gini
├── experiment.py               # Évaluation croisée 12 combinaisons
├── approfondissement.py        # Section 5 - réputation des clients
├── openapi.yaml                # Documentation API
├── resultats.csv               # Données brutes Section 4
├── resultats_approfondissement.csv  # Données brutes Section 5
└── README.md                   # Ce fichier
```

---

## Installation

### Prérequis

- Python 3.9+
- pip

### Installer les dépendances

```bash
pip3 install fastapi uvicorn pydantic
```

---

## Exécution

### Lancer le serveur (coordinateur)

```bash
python3 -m uvicorn coordinator:app --reload
```

Le serveur tourne sur `http://127.0.0.1:8000`

La documentation interactive est disponible sur `http://127.0.0.1:8000/docs`

### Lancer l'évaluation croisée (Section 4)

```bash
python3 experiment.py
```

Génère `resultats.csv` avec les 12 combinaisons.

### Lancer l'approfondissement (Section 5)

```bash
python3 approfondissement.py
```

Génère `resultats_approfondissement.csv`.

---

## Routes de l'API

| Méthode | Route | Description |
|---|---|---|
| POST | /v1/clients | Inscrire un client |
| DELETE | /v1/clients/{id} | Désinscrire un client |
| GET | /v1/round | Voir le tour actuel |
| POST | /v1/round/start | Démarrer un tour |
| GET | /v1/round/{id}/parameters | Récupérer le modèle |
| POST | /v1/round/{id}/contributions | Déposer une contribution |
| GET | /v1/metrics | Statistiques du tour |

---

## Stratégies de sélection

- **S0** — Aléatoire uniforme (référence)
- **S1** — Proportionnelle à la taille des données
- **S2** — Par capacité (les plus rapides)
- **S3** — Hybride vitesse + équité (50/50)
- **S4** — Par réputation (fiabilité)

## Mécanismes de gestion des stragglers

- **M1** — Attente complète (100%)
- **M2** — Attente partielle (80%)
- **M3** — Délai borné (5 secondes)

---

## Versions des outils

- Python 3.9
- FastAPI 0.100+
- Uvicorn 0.23+
- Pydantic 2.0+
