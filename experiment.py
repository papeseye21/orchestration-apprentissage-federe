"""
Évaluation croisée des 12 combinaisons stratégie × mécanisme.

C'EST CE SCRIPT QUI PRODUIT LES CHIFFRES DU RAPPORT (resultats.csv).

Le temps est entièrement simulé (pas d'horloge murale) :
1. chaque client produit une duration_s ;
2. on trie les arrivées du plus rapide au plus lent ;
3. M1 / M2 / M3 décident quand clôturer sur ce calendrier.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from federated_simulator import (
    generate_clients,
    initial_model,
    simulate_local_training,
    weighted_average,
)
from metrics import coefficient_gini
from strategies import StrategieS0, StrategieS1, StrategieS2, StrategieS3
from stragglers import MecanisteM1, MecanisteM2, MecanisteM3

# ------- Paramètres du protocole (énoncé) -------
NB_CLIENTS = 100
NB_SELECTIONNES = 10
NB_TOURS = 50
NB_REPETITIONS = 3  # 3 graines → moyenne ± écart-type

# Délai M3 en temps simulé (~ p50–p80 de S0).
# Un plafond à 5 s ne changerait rien (durées typiques < 1 s).
DELAI_M3_SIMULE_S = 0.5

STRATEGIES = {
    "S0": StrategieS0(),
    "S1": StrategieS1(),
    "S2": StrategieS2(),
    "S3": StrategieS3(),
}

# lambda = nouvelle instance à chaque répétition (important pour M3)
MECANISMES = {
    "M1": lambda: MecanisteM1(),
    "M2": lambda: MecanisteM2(quota=0.8),
    "M3": lambda: MecanisteM3(delai_max_s=DELAI_M3_SIMULE_S),
}

ROOT = Path(__file__).resolve().parent


def simuler_tour(clients, strategie, mecanisme, modele, seed):
    """
    Un tour complet :
    sélection → entraînements locaux → arrivées ordonnées → clôture → FedAvg.
    """
    selectionnes = strategie.selectionner(clients, NB_SELECTIONNES)

    # Tous s'entraînent (on obtient duration_s + completed pour chacun)
    brutes = [
        simulate_local_training(client, modele, seed=seed)
        for client in selectionnes
    ]
    # Ordre d'arrivée simulé : les plus lents (= stragglers) en dernier
    brutes_triees = sorted(brutes, key=lambda c: c.duration_s)

    integratees = []          # contributions completed gardées pour FedAvg
    contributions_recues = {} # toutes les arrivées (même failed)
    duree_tour = 0.0

    for contrib in brutes_triees:
        contributions_recues[contrib.client_id] = contrib
        duree_tour = contrib.duration_s  # temps simulé = durée du dernier arrivé accepté
        if contrib.completed:
            integratees.append(contrib)
        # Le mécanisme décide : on continue ou on coupe ici ?
        if mecanisme.attendre_contributions(
            selectionnes,
            contributions_recues,
            temps_ecoule_s=duree_tour,
        ):
            break

    # Clients sélectionnés non intégrés (lents coupés ou completed=False)
    ids_integres = {c.client_id for c in integratees}
    exclus = [c.id for c in selectionnes if c.id not in ids_integres]

    return {
        "selectionnes": [c.id for c in selectionnes],
        "contributions": len(integratees),
        "duree": duree_tour,
        "exclus": exclus,
        "modele": weighted_average(integratees) if integratees else list(modele),
    }


def evaluer_combinaison(nom_strategie: str, nom_mecanisme: str):
    """Lance NB_REPETITIONS × NB_TOURS pour une paire Sx+My."""
    resultats_repetitions = []
    lignes_brutes = []
    strategie = STRATEGIES[nom_strategie]

    for rep in range(NB_REPETITIONS):
        clients = generate_clients(NB_CLIENTS, seed=rep)  # graine = rep
        modele = initial_model()
        compteur_selections = {c.id: 0 for c in clients}
        compteur_contributions = {c.id: 0 for c in clients}
        durees_tours = []
        contributions_tours = []
        mecanisme = MECANISMES[nom_mecanisme]()

        for tour in range(NB_TOURS):
            resultat = simuler_tour(
                clients,
                strategie,
                mecanisme,
                modele,
                seed=tour * 1000 + rep + 1,
            )
            modele = resultat["modele"]
            durees_tours.append(resultat["duree"])
            contributions_tours.append(resultat["contributions"])
            exclus_set = set(resultat["exclus"])
            for client_id in resultat["selectionnes"]:
                compteur_selections[client_id] += 1
                if client_id not in exclus_set:
                    compteur_contributions[client_id] += 1

        # Proportion de clients jamais intégrés sur les 50 tours
        jamais_contribue = sum(
            1 for c in clients if compteur_contributions[c.id] == 0
        ) / NB_CLIENTS
        gini = coefficient_gini(list(compteur_selections.values()))
        run = {
            "combinaison": f"{nom_strategie}+{nom_mecanisme}",
            "repetition": rep,
            "graine": rep,
            "duree_moyenne": statistics.mean(durees_tours),
            "duree_p95": sorted(durees_tours)[min(int(0.95 * NB_TOURS), NB_TOURS - 1)],
            "contributions_moyenne": statistics.mean(contributions_tours),
            "gini": gini,
            "jamais_contribue": jamais_contribue,
        }
        resultats_repetitions.append(run)
        lignes_brutes.append(run)

    return resultats_repetitions, lignes_brutes


def _agg(vals):
    """Moyenne et écart-type (σ) sur les répétitions."""
    moy = statistics.mean(vals)
    std = statistics.stdev(vals) if len(vals) > 1 else 0.0
    return round(moy, 4), round(std, 4)


def main():
    resultats = []
    brutes = []

    header = (
        f"{'Combinaison':<12} {'Durée':>8} {'σ':>6} {'p95':>8} "
        f"{'Contrib':>8} {'Gini':>6} {'Jamais%':>8}"
    )
    print(header)
    print("-" * len(header))

    for nom_s in STRATEGIES:
        for nom_m in MECANISMES:
            nom = f"{nom_s}+{nom_m}"
            reps, lignes = evaluer_combinaison(nom_s, nom_m)
            brutes.extend(lignes)

            duree_moy, duree_std = _agg([r["duree_moyenne"] for r in reps])
            p95_moy, _ = _agg([r["duree_p95"] for r in reps])
            contrib_moy, contrib_std = _agg([r["contributions_moyenne"] for r in reps])
            gini_moy, gini_std = _agg([r["gini"] for r in reps])
            jamais_moy, _ = _agg([r["jamais_contribue"] for r in reps])

            resultats.append({
                "combinaison": nom,
                "duree_moyenne": duree_moy,
                "duree_std": duree_std,
                "p95": p95_moy,
                "contributions_moyenne": round(statistics.mean(
                    [r["contributions_moyenne"] for r in reps]
                ), 2),
                "contributions_std": contrib_std,
                "gini": gini_moy,
                "gini_std": gini_std,
                "jamais_contribue": jamais_moy,
            })
            print(
                f"{nom:<12} {duree_moy:>8.4f} {duree_std:>6.4f} {p95_moy:>8.4f} "
                f"{resultats[-1]['contributions_moyenne']:>8.2f} {gini_moy:>6.4f} "
                f"{100 * jamais_moy:>7.1f}%"
            )

    # CSV agrégé (tableau du rapport) + CSV brut (une ligne par run)
    with open(ROOT / "resultats.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=resultats[0].keys())
        writer.writeheader()
        writer.writerows(resultats)

    with open(ROOT / "resultats_bruts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=brutes[0].keys())
        writer.writeheader()
        writer.writerows(brutes)

    print(f"\nRésultats agrégés → {ROOT / 'resultats.csv'}")
    print(f"Résultats bruts   → {ROOT / 'resultats_bruts.csv'}")


if __name__ == "__main__":
    main()
