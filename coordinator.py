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
        return {"erreur": "client déjà inscrit"}, 409
    clients[client.id] = client
    return {"message": "client inscrit", "id": client.id}