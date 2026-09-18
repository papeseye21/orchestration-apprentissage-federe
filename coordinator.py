# ============================================================
# COORDINATEUR D'APPRENTISSAGE FÉDÉRÉ
# Serveur HTTP (FastAPI) : clients, tours, clôture, FedAvg, métriques
#
# Ce fichier = démonstration du plan de contrôle via une API REST.
# Les expériences chiffrées du rapport sont dans experiment.py
# (elles n'appellent PAS ce serveur).
# ============================================================

from __future__ import annotations

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field

from federated_simulator import Contribution, weighted_average
from metrics import coefficient_gini
from strategies import StrategieS0
from stragglers import MecanisteM1

# Application FastAPI (docs auto sur /docs)
app = FastAPI(
    title="Coordinateur d'apprentissage fédéré",
    version="1.0.0",
    description="Plan de contrôle : sélection, stragglers, FedAvg (vecteur dim-8).",
)

# ------- État en mémoire (redémarre = tout perdu) -------
clients: dict = {}                 # id → ClientInscription
contributions: dict = {}           # id → ContributionData du tour en cours
historique_selections: dict[str, int] = {}  # compte combien de fois chaque client a été choisi

# Par défaut : aléatoire + attente complète (modifiable ici)
strategie = StrategieS0()
mecanisme = MecanisteM1()

tour_actuel = {
    "id": 0,
    "statut": "en_attente",  # en_attente | en_cours | termine
    "modele": [0.0] * 8,     # vecteur global (dim 8, pas un vrai NN)
    "clients_selectionnes": [],
}


# ------- Schémas Pydantic = contrat des requêtes JSON -------

class ClientInscription(BaseModel):
    id: str
    data_size: int = Field(..., ge=1)                    # >= 1
    capacity: float = Field(..., gt=0)                   # > 0
    reliability: float = Field(1.0, ge=0.0, le=1.0)      # entre 0 et 1


class ContributionData(BaseModel):
    client_id: str
    vector: list[float]
    data_size: int = Field(..., ge=1)
    duration_s: float = Field(..., ge=0)
    completed: bool


def _erreur(response: Response, status: int, erreur: str, code: str, **extra):
    """Réponse d'erreur structurée : {erreur, code, tour_id, ...}."""
    response.status_code = status
    payload = {"erreur": erreur, "code": code, "tour_id": tour_actuel["id"]}
    payload.update(extra)
    return payload


def _clients_selectionnes_objets():
    """Retrouve les objets clients à partir des id stockés dans le tour."""
    return [clients[cid] for cid in tour_actuel["clients_selectionnes"] if cid in clients]


def _cloturer_si_necessaire(temps_ecoule_s: float | None = None) -> bool:
    """
    Après chaque contribution : on demande au mécanisme si on clôture.
    Si oui → FedAvg sur les contributions completed, statut = termine.
    """
    if tour_actuel["statut"] != "en_cours":
        return tour_actuel["statut"] == "termine"

    selectionnes = _clients_selectionnes_objets()
    if mecanisme.attendre_contributions(
        selectionnes,
        contributions,
        temps_ecoule_s=temps_ecoule_s,
    ):
        # Convertit vers le type Contribution du simulateur pour FedAvg
        valides = [
            Contribution(
                client_id=c.client_id,
                data_size=c.data_size,
                vector=list(c.vector),
                duration_s=c.duration_s,
                completed=c.completed,
            )
            for c in contributions.values()
            if c.completed
        ]
        if valides:
            tour_actuel["modele"] = weighted_average(valides)  # FedAvg
        tour_actuel["statut"] = "termine"
        return True
    return False


@app.get("/")
def accueil():
    return {"message": "Coordinateur d'apprentissage fédéré"}


@app.post("/v1/clients")
def inscrire_client(client: ClientInscription, response: Response):
    """Inscrit un client. 201 si OK, 409 si l'id existe déjà."""
    if client.id in clients:
        return _erreur(response, 409, "client déjà inscrit", "CLIENT_EXISTS")
    clients[client.id] = client
    historique_selections.setdefault(client.id, 0)
    response.status_code = 201
    return {"message": "client inscrit", "id": client.id}


@app.delete("/v1/clients/{client_id}")
def desinscrire_client(client_id: str, response: Response):
    """Désinscrit un client. 404 s'il n'existe pas."""
    if client_id not in clients:
        return _erreur(response, 404, "client inexistant", "CLIENT_NOT_FOUND")
    del clients[client_id]
    return {"message": "client désinscrit", "id": client_id}


@app.get("/v1/round")
def get_round():
    """État du tour courant (id, statut, modèle, sélection)."""
    return tour_actuel


@app.post("/v1/round/start")
def demarrer_tour(response: Response):
    """Démarre un tour : sélectionne jusqu'à 10 clients et ouvre les contributions."""
    global contributions

    if len(clients) == 0:
        return _erreur(response, 400, "aucun client inscrit", "NO_CLIENTS")

    selectionnes = strategie.selectionner(list(clients.values()), min(10, len(clients)))
    contributions = {}  # reset des contributions du tour précédent

    tour_actuel["id"] += 1
    tour_actuel["statut"] = "en_cours"
    tour_actuel["clients_selectionnes"] = [c.id for c in selectionnes]

    # Compte les sélections (sert au Gini dans /metrics)
    for c in selectionnes:
        historique_selections[c.id] = historique_selections.get(c.id, 0) + 1

    # Démarre le chronomètre mural si M3
    if hasattr(mecanisme, "demarrer"):
        mecanisme.demarrer()

    return {
        "message": "tour démarré",
        "tour_id": tour_actuel["id"],
        "clients_selectionnes": tour_actuel["clients_selectionnes"],
        "mecanisme": mecanisme.__class__.__name__,
        "strategie": strategie.__class__.__name__,
    }


@app.get("/v1/round/{round_id}/parameters")
def get_parameters(round_id: int, client_id: str, response: Response):
    """
    Donne le modèle global à un client sélectionné.
    Identité = query param client_id (pas de jeton).
    """
    if round_id != tour_actuel["id"]:
        return _erreur(response, 404, "tour inexistant", "ROUND_NOT_FOUND")
    if tour_actuel["statut"] == "termine":
        return _erreur(response, 409, "tour déjà clôturé", "ROUND_CLOSED")
    if client_id not in tour_actuel["clients_selectionnes"]:
        return _erreur(response, 403, "client non sélectionné", "CLIENT_NOT_SELECTED")
    return {"modele": tour_actuel["modele"], "tour_id": tour_actuel["id"]}


@app.post("/v1/round/{round_id}/contributions")
def deposer_contribution(
    round_id: int, contribution: ContributionData, response: Response
):
    """
    Reçoit une contribution. Peut clôturer le tour (mécanisme).
    409 si le tour est déjà terminé (hors délai) ou contribution en double.
    """
    if round_id != tour_actuel["id"]:
        return _erreur(response, 404, "tour inexistant", "ROUND_NOT_FOUND")
    if tour_actuel["statut"] != "en_cours":
        return _erreur(
            response,
            409,
            "contribution hors délai : tour clôturé",
            "ROUND_CLOSED",
        )
    if contribution.client_id not in tour_actuel["clients_selectionnes"]:
        return _erreur(response, 403, "client non autorisé", "CLIENT_NOT_ALLOWED")
    if contribution.client_id in contributions:
        return _erreur(response, 409, "contribution déjà envoyée", "DUP_CONTRIBUTION")

    contributions[contribution.client_id] = contribution
    # Après chaque dépôt : le mécanisme décide éventuellement de clôturer
    cloture = _cloturer_si_necessaire(temps_ecoule_s=contribution.duration_s)

    response.status_code = 201
    return {
        "message": "contribution reçue",
        "client_id": contribution.client_id,
        "tour_cloture": cloture,
        "statut": tour_actuel["statut"],
    }


@app.get("/v1/metrics")
def get_metrics():
    """Compteurs du tour + Gini sur l'historique des sélections."""
    counts = [
        historique_selections.get(cid, 0) for cid in clients
    ] or list(historique_selections.values())
    gini = coefficient_gini(counts) if counts else 0.0
    return {
        "tour_id": tour_actuel["id"],
        "statut": tour_actuel["statut"],
        "clients_inscrits": len(clients),
        "clients_selectionnes": len(tour_actuel["clients_selectionnes"]),
        "contributions_recues": len(contributions),
        "gini_selections": round(gini, 4),
        "historique_selections": dict(historique_selections),
    }
