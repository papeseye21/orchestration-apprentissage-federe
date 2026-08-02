from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Liste qui stocke les clients inscrits
clients = {}
# État du tour actuel
tour_actuel = {
    "id": 1,
    "statut": "en_attente",
    "modele": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "clients_selectionnes": ["client-001"]
}

# Modèle de données d'un client
class ClientInscription(BaseModel):
    id: str
    data_size: int
    capacity: float

@app.get("/")
def accueil():
    return {"message": "Coordinateur d'apprentissage fédéré"}

@app.post("/v1/clients")
def inscrire_client(client: ClientInscription):
    if client.id in clients:
        return {"erreur": "client déjà inscrit"}
    clients[client.id] = client
    return {"message": "client inscrit", "id": client.id}

#suppression d un client 
@app.delete("/v1/clients/{client_id}")
def desinscrire_client(client_id: str):
    if client_id not in clients:
        return {"erreur": "client inexistant"}
    del clients[client_id]
    return {"message": "client désinscrit", "id": client_id}
@app.get("/v1/round")
def get_round():
    return tour_actuel    

#GET /v1/round/{id}/parameters
@app.get("/v1/round/{round_id}/parameters")
def get_parameters(round_id: int, client_id: str):
    if round_id != tour_actuel["id"]:
        return {"erreur": "tour inexistant"}
    if client_id not in tour_actuel["clients_selectionnes"]:
        return {"erreur": "client non sélectionné"}
    return {"modele": tour_actuel["modele"]}

# Stocke les contributions reçues pour le tour actuel
contributions = {}

# Modèle de données d'une contribution
class ContributionData(BaseModel):
    client_id: str
    vector: list
    data_size: int
    duration_s: float
    completed: bool

@app.post("/v1/round/{round_id}/contributions")
def deposer_contribution(round_id: int, contribution: ContributionData):
    if round_id != tour_actuel["id"]:
        return {"erreur": "tour inexistant"}
    if contribution.client_id not in tour_actuel["clients_selectionnes"]:
        return {"erreur": "client non autorisé"}
    if contribution.client_id in contributions:
        return {"erreur": "contribution déjà envoyée"}, 409
    contributions[contribution.client_id] = contribution
    return {"message": "contribution reçue", "client_id": contribution.client_id}  

    #statistiques d avancememt et metriques experimentales
@app.get("/v1/metrics")
def get_metrics():
    return {
        "tour_id": tour_actuel["id"],
        "statut": tour_actuel["statut"],
        "clients_inscrits": len(clients),
        "clients_selectionnes": len(tour_actuel["clients_selectionnes"]),
        "contributions_recues": len(contributions)
    }      
