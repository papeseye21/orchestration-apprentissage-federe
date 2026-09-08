# ============================================================
# MÉCANISMES DE GESTION DES STRAGGLERS
# Un straggler = un client lent qui tarde à contribuer
# Chaque mécanisme décide quand clôturer un tour
# ============================================================

from abc import ABC, abstractmethod
import time

# ============================================================
# INTERFACE COMMUNE
# Tous les mécanismes doivent implémenter la méthode
# attendre_contributions()
# ============================================================

class MecanismeStragglers(ABC):

    @abstractmethod
    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict
    ) -> bool:
        """
        Décide si le tour doit se clôturer
        - clients_selectionnes : liste des clients choisis
        - contributions : dictionnaire des contributions reçues
        - retourne : True si on clôture, False si on attend encore
        """
        pass


# ============================================================
# M1 — ATTENTE COMPLÈTE
# Le tour attend TOUTES les contributions
# Avantage : résultat complet
# Inconvénient : un seul lent bloque tout le monde
# ============================================================

class MecanisteM1(MecanismeStragglers):

    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict
    ) -> bool:
        # On clôture seulement si TOUS les clients ont contribué
        return len(contributions) >= len(clients_selectionnes)


# ============================================================
# M2 — ATTENTE PARTIELLE
# Le tour se clôt dès qu'un quota est atteint (ex: 80%)
# Avantage : plus rapide
# Inconvénient : on perd des contributions
# ============================================================

class MecanisteM2(MecanismeStragglers):

    def __init__(self, quota: float = 0.8):
        # quota = proportion minimale de contributions requises
        # 0.8 = 80% des clients sélectionnés doivent contribuer
        self.quota = quota

    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict
    ) -> bool:
        minimum = len(clients_selectionnes) * self.quota
        return len(contributions) >= minimum


# ============================================================
# M3 — DÉLAI BORNÉ
# Le tour se clôt après un délai maximal
# Avantage : durée prévisible
# Inconvénient : les lents sont toujours exclus
# ============================================================

class MecanisteM3(MecanismeStragglers):

    def __init__(self, delai_max_s: float = 5.0):
        # delai_max_s = durée maximale du tour en secondes
        self.delai_max_s = delai_max_s
        self.debut_tour = None

    def demarrer(self):
        # Enregistre l'heure de début du tour
        self.debut_tour = time.time()

    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict
    ) -> bool:
        if self.debut_tour is None:
            return False
        # Clôture si le délai est dépassé
        temps_ecoule = time.time() - self.debut_tour
        return temps_ecoule >= self.delai_max_s

