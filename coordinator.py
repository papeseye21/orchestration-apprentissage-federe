# ============================================================
# COORDINATEUR D'APPRENTISSAGE FÉDÉRÉ
# Ce fichier gère le serveur central qui coordonne les clients
# ============================================================

from fastapi import FastAPI, Response
from pydantic import BaseModel
from strategies import StrategieS0, StrategieS1, StrategieS2, StrategieS3
from stragglers import MecanisteM1, MecanisteM2, MecanisteM3

# Création du serveur FastAPI
app = FastAPI()

# ============================================================
# DONNÉES EN MÉMOIRE
# Ces variables stockent l'état du système
# ============================================================

# Dictionnaire de tous les clients inscrits
# Format : {"client-001": ClientInscription, ...}
clients = {}

# Dictionnaire des contributions reçues pour le tour actuel
# Format : {"client-001": ContributionData, ...}
contributions = {}

# Stratégie de sélection active 
strategie = StrategieS0()  # Par défaut : aléatoire

# Mécanisme de gestion des stragglers actif
mecanisme = MecanisteM1()  # Par défaut : attente complète

# État du tour actuel
tour_actuel = {
    "id": 1,                    # Numéro du tour
    "statut": "en_attente",     # en_attente, en_cours, termine
    "modele": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Vecteur IA
    "clients_selectionnes": ["client-001"]  # Clients choisis pour ce tour
}

# ============================================================
# MODÈLES DE DONNÉES
# Ces classes définissent la structure des données reçues
# ============================================================

# Structure des données d'un client lors de son inscription
class ClientInscription(BaseModel):
    id: str           # Identifiant unique du client
    data_size: int    # Taille de ses données (50 à 5000)
    capacity: float   # Vitesse de calcul (0.5 à 8.0)

# Structure des données d'une contribution envoyée par un client
class ContributionData(BaseModel):
    client_id: str      # Identifiant du client qui contribue
    vector: list        # Résultat de l'entraînement local (8 nombres)
    data_size: int      # Taille des données utilisées
    duration_s: float   # Durée du calcul en secondes
    completed: bool     # True si l'entraînement a réussi

# ============================================================
# ROUTES DE L'API
# Chaque route = un point d'entrée accessible via HTTP
# ============================================================

# Route de test - vérifie que le serveur tourne
@app.get("/")
def accueil():
    return {"message": "Coordinateur d'apprentissage fédéré"}

# ------- GESTION DES CLIENTS -------

# Inscrire un nouveau client
# Retourne 201 si créé, 409 si déjà inscrit
@app.post("/v1/clients")
def inscrire_client(client: ClientInscription, response: Response):
    if client.id in clients:
        response.status_code = 409  # Conflit - client déjà inscrit
        return {"erreur": "client déjà inscrit"}
    clients[client.id] = client
    response.status_code = 201  # Créé avec succès
    return {"message": "client inscrit", "id": client.id}

# Désinscrire un client existant
# Retourne 200 si supprimé, 404 si introuvable
@app.delete("/v1/clients/{client_id}")
def desinscrire_client(client_id: str, response: Response):
    if client_id not in clients:
        response.status_code = 404  # Non trouvé
        return {"erreur": "client inexistant"}
    del clients[client_id]
    return {"message": "client désinscrit", "id": client_id}

# ------- GESTION DES TOURS -------

# Consulter le tour actuel (numéro, statut, modèle, clients sélectionnés)
@app.get("/v1/round")
def get_round():
    return tour_actuel

# Démarrer un nouveau tour et sélectionner les clients automatiquement
@app.post("/v1/round/start")
def demarrer_tour(response: Response):
    global tour_actuel, contributions

    if len(clients) == 0:
        response.status_code = 400
        return {"erreur": "aucun client inscrit"}

    # Sélectionne automatiquement les clients avec la stratégie active
    selectionnes = strategie.selectionner(list(clients.values()), 10)

    # Remet les contributions à zéro pour le nouveau tour
    contributions = {}

    # Met à jour le tour actuel
    tour_actuel["id"] += 1
    tour_actuel["statut"] = "en_cours"
    tour_actuel["clients_selectionnes"] = [c.id for c in selectionnes]

    # Démarre le timer pour M3
    if hasattr(mecanisme, 'demarrer'):
        mecanisme.demarrer()

    return {
        "message": "tour démarré",
        "tour_id": tour_actuel["id"],
        "clients_selectionnes": tour_actuel["clients_selectionnes"],
        "mecanisme": mecanisme.__class__.__name__
    }    


# Récupérer le modèle actuel (seulement pour les clients sélectionnés)
# Retourne 404 si le tour n'existe pas, 403 si client non autorisé
@app.get("/v1/round/{round_id}/parameters")
def get_parameters(round_id: int, client_id: str, response: Response):
    if round_id != tour_actuel["id"]:
        response.status_code = 404  # Tour inexistant
        return {"erreur": "tour inexistant"}
    if client_id not in tour_actuel["clients_selectionnes"]:
        response.status_code = 403  # Accès refusé
        return {"erreur": "client non sélectionné"}
    return {"modele": tour_actuel["modele"]}

# Déposer une contribution pour un tour
# Retourne 201 si reçue, 404 si tour inexistant,
# 403 si non autorisé, 409 si contribution en double
@app.post("/v1/round/{round_id}/contributions")
def deposer_contribution(round_id: int, contribution: ContributionData, response: Response):
    if round_id != tour_actuel["id"]:
        response.status_code = 404  # Tour inexistant
        return {"erreur": "tour inexistant"}
    if contribution.client_id not in tour_actuel["clients_selectionnes"]:
        response.status_code = 403  # Client non autorisé
        return {"erreur": "client non autorisé"}
    if contribution.client_id in contributions:
        response.status_code = 409  # Contribution en double
        return {"erreur": "contribution déjà envoyée"}
    contributions[contribution.client_id] = contribution
    response.status_code = 201  # Contribution créée avec succès
    return {"message": "contribution reçue", "client_id": contribution.client_id}

# ------- MÉTRIQUES -------

# Voir les statistiques du tour en cours
@app.get("/v1/metrics")
def get_metrics():
    return {
        "tour_id": tour_actuel["id"],
        "statut": tour_actuel["statut"],
        "clients_inscrits": len(clients),          # Nombre total de clients inscrits
        "clients_selectionnes": len(tour_actuel["clients_selectionnes"]),  # Sélectionnés ce tour
        "contributions_recues": len(contributions)  # Contributions reçues ce tour
    }