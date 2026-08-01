from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Liste qui stocke les clients inscrits
clients = {}

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