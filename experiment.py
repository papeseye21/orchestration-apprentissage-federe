import csv
import statistics
from federated_simulator import generate_clients, initial_model, simulate_local_training, weighted_average
from strategies import StrategieS0, StrategieS1, StrategieS2, StrategieS3
from stragglers import MecanisteM1, MecanisteM2, MecanisteM3
from metrics import coefficient_gini

NB_CLIENTS = 100
NB_SELECTIONNES = 10
NB_TOURS = 50
NB_REPETITIONS = 3

STRATEGIES = {
    "S0": StrategieS0(),
    "S1": StrategieS1(),
    "S2": StrategieS2(),
    "S3": StrategieS3(),
}

MECANISMES = {
    "M1": lambda: MecanisteM1(),
    "M2": lambda: MecanisteM2(quota=0.8),
    "M3": lambda: MecanisteM3(delai_max_s=5.0),
}


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
        "contributions": len(contributions),
        "duree": max(durees) if durees else 0.0,
        "modele": weighted_average(contributions) if contributions else modele
    }


def evaluer_combinaison(nom_strategie, nom_mecanisme):
    resultats_repetitions = []
    for rep in range(NB_REPETITIONS):
        clients = generate_clients(NB_CLIENTS, seed=rep)
        modele = initial_model()
        compteur_selections = {c.id: 0 for c in clients}
        durees_tours = []
        contributions_tours = []
        mecanisme = MECANISMES[nom_mecanisme]()
        strategie = STRATEGIES[nom_strategie]
        if hasattr(mecanisme, 'demarrer'):
            mecanisme.demarrer()
        for tour in range(NB_TOURS):
            resultat = simuler_tour(clients, strategie, mecanisme, modele, seed=tour * rep + 1)
            modele = resultat["modele"]
            durees_tours.append(resultat["duree"])
            contributions_tours.append(resultat["contributions"])
            for client_id in resultat["selectionnes"]:
                compteur_selections[client_id] += 1
        gini = coefficient_gini(list(compteur_selections.values()))
        resultats_repetitions.append({
            "duree_moyenne": statistics.mean(durees_tours),
            "duree_p95": sorted(durees_tours)[int(0.95 * NB_TOURS)],
            "contributions_moyenne": statistics.mean(contributions_tours),
            "gini": gini
        })
    return resultats_repetitions


resultats = []
print(f"{'Combinaison':<12} {'Durée moy':>10} {'p95':>8} {'Contributions':>15} {'Gini':>8}")
print("-" * 60)

for nom_s in STRATEGIES:
    for nom_m in MECANISMES:
        nom = f"{nom_s}+{nom_m}"
        reps = evaluer_combinaison(nom_s, nom_m)
        duree_moy = statistics.mean([r["duree_moyenne"] for r in reps])
        p95 = statistics.mean([r["duree_p95"] for r in reps])
        contrib_moy = statistics.mean([r["contributions_moyenne"] for r in reps])
        gini_moy = statistics.mean([r["gini"] for r in reps])
        resultats.append({
            "combinaison": nom,
            "duree_moyenne": round(duree_moy, 4),
            "p95": round(p95, 4),
            "contributions_moyenne": round(contrib_moy, 2),
            "gini": round(gini_moy, 4)
        })
        print(f"{nom:<12} {duree_moy:>10.4f} {p95:>8.4f} {contrib_moy:>15.2f} {gini_moy:>8.4f}")

with open("resultats.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=resultats[0].keys())
    writer.writeheader()
    writer.writerows(resultats)

print("\n✅ Résultats sauvegardés dans resultats.csv")
