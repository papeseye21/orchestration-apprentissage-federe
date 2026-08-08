# ============================================================
# STRATÉGIES DE SÉLECTION DES CLIENTS
# Chaque stratégie implémente la même interface (selectionner)
# mais avec une logique différente
# ============================================================

from abc import ABC, abstractmethod
import random

# ============================================================
# INTERFACE COMMUNE
# Toutes les stratégies doivent hériter de cette classe
# et implémenter la méthode selectionner()
# ============================================================

class StrategieSelection(ABC):
    
    @abstractmethod
    def selectionner(self, clients: list, nombre: int) -> list:
        """
        Sélectionne 'nombre' clients parmi la liste
        - clients : liste de tous les clients inscrits
        - nombre  : combien de clients on veut sélectionner
        - retourne : liste des clients sélectionnés
        """
        pass


# ============================================================
# S0 — SÉLECTION ALÉATOIRE UNIFORME
# Choisit 'nombre' clients au hasard
# C'est la stratégie de référence
# ============================================================

class StrategieS0(StrategieSelection):
    
    def selectionner(self, clients: list, nombre: int) -> list:
        nombre = min(nombre, len(clients))
        return random.sample(clients, nombre)

# ============================================================
# S1 — SÉLECTION PROPORTIONNELLE
# Les clients avec plus de données ont plus de chances
# d'être sélectionnés
# ============================================================

class StrategieS1(StrategieSelection):
    
    def selectionner(self, clients: list, nombre: int) -> list:
        nombre = min(nombre, len(clients))
        # Le poids de chaque client = sa taille de données
        poids = [c.data_size for c in clients]
        return random.choices(clients, weights=poids, k=nombre)        

# ============================================================
# S2 — SÉLECTION PAR CAPACITÉ
# Privilégie les clients les plus rapides (grande capacity)
# ============================================================

class StrategieS2(StrategieSelection):
    
    def selectionner(self, clients: list, nombre: int) -> list:
        nombre = min(nombre, len(clients))
        # Trie les clients du plus rapide au plus lent
        tries = sorted(clients, key=lambda c: c.capacity, reverse=True)
        # Prend les 'nombre' premiers (les plus rapides)
        return tries[:nombre]    

# ============================================================
# S3 — SÉLECTION HYBRIDE (vitesse + équité)
# Combine S2 (capacité) et S0 (aléatoire)
# 50% des clients choisis par capacité (vitesse)
# 50% des clients choisis au hasard (équité)
# Hypothèse : cette combinaison réduit la durée du tour
# tout en donnant une chance aux clients lents
# ============================================================

class StrategieS3(StrategieSelection):
    
    def selectionner(self, clients: list, nombre: int) -> list:
        nombre = min(nombre, len(clients))
        
        # Moitié par capacité (les plus rapides)
        nombre_rapides = nombre // 2
        tries = sorted(clients, key=lambda c: c.capacity, reverse=True)
        rapides = tries[:nombre_rapides]
        
        # Moitié au hasard parmi les clients restants
        restants = [c for c in clients if c not in rapides]
        nombre_aleatoires = nombre - nombre_rapides
        aleatoires = random.sample(restants, min(nombre_aleatoires, len(restants)))
        
        return rapides + aleatoires            