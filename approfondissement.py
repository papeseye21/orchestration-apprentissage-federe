# ============================================================
# SECTION 5 — APPROFONDISSEMENT : RÉPUTATION DES CLIENTS
#
# Hypothèse : sélectionner les clients selon leur réputation
# (reliability) améliore le nombre de contributions complètes
# mais réduit l'équité car les clients peu fiables sont exclus.
#
# Protocole :
# - Comparer S0 (aléatoire) vs S4 (réputation)
# - Mécanisme fixe : M1 (attente complète)
# - 50 tours, répété 3 fois
# - Mesures : contributions complètes, Gini, durée
# ============================================================

import csv
import statistics
from federated_simulator import generate_clients, initial_model, simulate_local_training, weighted_average
from strategies import StrategieS0, StrategieS4
from stragglers import MecanisteM1
from metrics import coefficient_gini

NB_CLIENTS = 100
NB_SELECTIONNES = 10
NB_TOURS = 50
NB_REPETITIONS = 3


def simuler_tour(clients, strategie, mecanisme, modele, seed):
    selectionnes = strategie.selectionner(clients, NB_SELECTIONNES)
    contributions = []
    durees = []
    for client in selectionnes:
        contrib = simulate_local_training(client, modele, seed=seed)
        durees.append(contrib.duration_s)
        if contrib.completed:
            contributions.append(contrib)
        contribs_dict = {c.client_id: c for c in contributions}
        if mecanisme.attendre_contributions(selectionnes, contribs_dict):
            break
    return {
        "selectionnes": [c.id for c in selectionnes],
        "contributions_completes": len(contributions),
        "duree": max(durees) if durees else 0.0,
        "modele": weighted_average(contributions) if contributions else modele
    }


def evaluer_strategie(nom, strategie):
    resultats_repetitions = []
    for rep in range(NB_REPETITIONS):
        clients = generate_clients(NB_CLIENTS, seed=rep)
        modele = initial_model()
        compteur_selections = {c.id: 0 for c in clients}
        durees_tours = []
        contributions_tours = []
        mecanisme = MecanisteM1()

        for tour in range(NB_TOURS):
            resultat = simuler_tour(clients, strategie, mecanisme, modele, seed=tour * rep + 1)
            modele = resultat["modele"]
            durees_tours.append(resultat["duree"])
            contributions_tours.append(resultat["contributions_completes"])
            for client_id in resultat["selectionnes"]:
                compteur_selections[client_id] += 1

        gini = coefficient_gini(list(compteur_selections.values()))
        resultats_repetitions.append({
            "duree_moyenne": statistics.mean(durees_tours),
            "contributions_moyenne": statistics.mean(contributions_tours),
            "gini": gini
        })
    return resultats_repetitions


# Évaluation des deux stratégies
strategies = {
    "S0 (aléatoire)": StrategieS0(),
    "S4 (réputation)": StrategieS4(),
}

resultats = []
print(f"{'Stratégie':<20} {'Durée moy':>10} {'Contributions':>15} {'Gini':>8}")
print("-" * 58)

for nom, strategie in strategies.items():
    reps = evaluer_strategie(nom, strategie)
    duree_moy = statistics.mean([r["duree_moyenne"] for r in reps])
    contrib_moy = statistics.mean([r["contributions_moyenne"] for r in reps])
    gini_moy = statistics.mean([r["gini"] for r in reps])
    resultats.append({
        "strategie": nom,
        "duree_moyenne": round(duree_moy, 4),
        "contributions_moyenne": round(contrib_moy, 2),
        "gini": round(gini_moy, 4)
    })
    print(f"{nom:<20} {duree_moy:>10.4f} {contrib_moy:>15.2f} {gini_moy:>8.4f}")

# Sauvegarde en CSV
with open("resultats_approfondissement.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=resultats[0].keys())
    writer.writeheader()
    writer.writerows(resultats)

print("\n✅ Résultats sauvegardés dans resultats_approfondissement.csv")

# Discussion
print("\n--- DISCUSSION ---")
s0 = resultats[0]
s4 = resultats[1]

if s4["contributions_moyenne"] > s0["contributions_moyenne"]:
    print("✅ Hypothèse confirmée : S4 produit plus de contributions complètes que S0")
else:
    print("❌ Hypothèse infirmée : S4 ne produit pas plus de contributions complètes")

if s4["gini"] > s0["gini"]:
    print("✅ Hypothèse confirmée : S4 est moins équitable que S0 (Gini plus élevé)")
else:
    print("❌ Hypothèse infirmée : S4 n'est pas moins équitable que S0")
