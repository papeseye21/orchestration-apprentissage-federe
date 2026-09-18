# ============================================================
# APPROFONDISSEMENT : RÉPUTATION DES CLIENTS (S4 vs S0)
#
# Hypothèses testées :
#   H1 : S4 (reliability) → plus de contributions complètes que S0
#   H2 : S4 → Gini plus élevé (moins d'équité)
#   H3 : corrélation reliability / capacity (exploratoire)
#
# Même protocole que l'expérience : M1 fixe, 50 tours × 3 graines,
# calendrier simulé (via simuler_tour de experiment.py).
# ============================================================

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from experiment import simuler_tour
from federated_simulator import generate_clients, initial_model
from metrics import coefficient_gini, intervalle_confiance, pearson, ttest_ind
from strategies import StrategieS0, StrategieS4
from stragglers import MecanisteM1

NB_CLIENTS = 100
NB_TOURS = 50
NB_REPETITIONS = 3
ROOT = Path(__file__).resolve().parent


def evaluer_strategie(nom: str, strategie):
    """Évalue une stratégie seule (mécanisme M1 toujours)."""
    resultats_repetitions = []
    for rep in range(NB_REPETITIONS):
        clients = generate_clients(NB_CLIENTS, seed=rep)
        modele = initial_model()
        compteur_selections = {c.id: 0 for c in clients}
        durees_tours = []
        contributions_tours = []
        mecanisme = MecanisteM1()

        for tour in range(NB_TOURS):
            # Même moteur de tour que l'évaluation croisée
            resultat = simuler_tour(
                clients, strategie, mecanisme, modele, seed=tour * 1000 + rep + 1
            )
            modele = resultat["modele"]
            durees_tours.append(resultat["duree"])
            contributions_tours.append(resultat["contributions"])
            for client_id in resultat["selectionnes"]:
                compteur_selections[client_id] += 1

        gini = coefficient_gini(list(compteur_selections.values()))
        resultats_repetitions.append({
            "strategie": nom,
            "repetition": rep,
            "graine": rep,
            "duree_moyenne": statistics.mean(durees_tours),
            "contributions_moyenne": statistics.mean(contributions_tours),
            "gini": gini,
        })
    return resultats_repetitions


def main():
    strategies = {
        "S0 (aléatoire)": StrategieS0(),
        "S4 (réputation)": StrategieS4(),
    }

    brutes = []
    resultats = []

    print(f"{'Stratégie':<20} {'Durée':>10} {'σ':>8} {'Contrib':>10} {'Gini':>8}")
    print("-" * 60)

    reps_par_nom = {}
    for nom, strategie in strategies.items():
        reps = evaluer_strategie(nom, strategie)
        reps_par_nom[nom] = reps
        brutes.extend(reps)

        durees = [r["duree_moyenne"] for r in reps]
        contribs = [r["contributions_moyenne"] for r in reps]
        ginis = [r["gini"] for r in reps]
        resultats.append({
            "strategie": nom,
            "duree_moyenne": round(statistics.mean(durees), 4),
            "duree_std": round(statistics.stdev(durees), 4) if len(durees) > 1 else 0.0,
            "contributions_moyenne": round(statistics.mean(contribs), 2),
            "gini": round(statistics.mean(ginis), 4),
            "gini_std": round(statistics.stdev(ginis), 4) if len(ginis) > 1 else 0.0,
        })
        r = resultats[-1]
        print(
            f"{nom:<20} {r['duree_moyenne']:>10.4f} {r['duree_std']:>8.4f} "
            f"{r['contributions_moyenne']:>10.2f} {r['gini']:>8.4f}"
        )

    # Sauvegarde CSV (agrégé + brut)
    with open(ROOT / "resultats_approfondissement.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=resultats[0].keys())
        writer.writeheader()
        writer.writerows(resultats)

    with open(ROOT / "resultats_approfondissement_bruts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=brutes[0].keys())
        writer.writeheader()
        writer.writerows(brutes)

    # --- H3 + tests de significativité ---
    pop = generate_clients(NB_CLIENTS, seed=0)
    corr = pearson([c.reliability for c in pop], [c.capacity for c in pop])

    s0 = reps_par_nom["S0 (aléatoire)"]
    s4 = reps_par_nom["S4 (réputation)"]
    t_c, df_c, p_c = ttest_ind(
        [r["contributions_moyenne"] for r in s0],
        [r["contributions_moyenne"] for r in s4],
    )
    t_g, df_g, p_g = ttest_ind(
        [r["gini"] for r in s0],
        [r["gini"] for r in s4],
    )
    _, lo_g4, hi_g4 = intervalle_confiance([r["gini"] for r in s4])

    print("\n--- TESTS / H3 ---")
    print(f"Pearson(reliability, capacity) = {corr:.4f}")
    print(f"t-test contributions S0 vs S4 : t={t_c:.3f}, df≈{df_c:.1f}, p={p_c:.4f}")
    print(f"t-test Gini S0 vs S4          : t={t_g:.3f}, df≈{df_g:.1f}, p={p_g:.4f}")
    print(f"IC 95 % Gini(S4)              : [{lo_g4:.4f}, {hi_g4:.4f}]")

    agg = {r["strategie"]: r for r in resultats}
    if agg["S4 (réputation)"]["contributions_moyenne"] > agg["S0 (aléatoire)"]["contributions_moyenne"]:
        print("H1 : S4 produit plus de contributions complètes que S0")
    else:
        print("H1 : non confirmée sur les contributions")
    if agg["S4 (réputation)"]["gini"] > agg["S0 (aléatoire)"]["gini"]:
        print("H2 : S4 est moins équitable que S0 (Gini plus élevé)")
    else:
        print("H2 : non confirmée sur le Gini")

    print(f"\nCSV → {ROOT / 'resultats_approfondissement.csv'}")
    print(f"Bruts → {ROOT / 'resultats_approfondissement_bruts.csv'}")


if __name__ == "__main__":
    main()
