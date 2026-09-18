# ============================================================
# MÉCANISMES DE GESTION DES STRAGGLERS
# Un straggler = un client lent qui tarde à contribuer.
# Chaque mécanisme répond : « Est-ce qu'on clôture le tour maintenant ? »
# ============================================================

from abc import ABC, abstractmethod
import time


class MecanismeStragglers(ABC):
    """Contrat commun pour M1, M2, M3."""

    @abstractmethod
    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict,
        temps_ecoule_s: float | None = None,
    ) -> bool:
        """
        Retourne True si le tour doit se clôturer, False sinon.

        - clients_selectionnes : clients choisis pour ce tour
        - contributions : {client_id: contribution} déjà reçues
        - temps_ecoule_s :
            * fourni en expérience (= duration_s du dernier arrivé) → horloge simulée
            * None côté API → M3 utilisera time.time()
        """
        pass


class MecanisteM1(MecanismeStragglers):
    """Attente complète : on n'arrête que quand tout le monde a répondu."""

    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict,
        temps_ecoule_s: float | None = None,
    ) -> bool:
        return len(contributions) >= len(clients_selectionnes)


class MecanisteM2(MecanismeStragglers):
    """
    Quota partiel (défaut 80 %) : dès que assez de monde est arrivé, on coupe.
    En expérience, les arrivées sont triées par durée → on exclut les plus lents.
    """

    def __init__(self, quota: float = 0.8):
        self.quota = quota  # ex. 0.8 → 8 clients sur 10 suffisent

    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict,
        temps_ecoule_s: float | None = None,
    ) -> bool:
        if not clients_selectionnes:
            return True
        minimum = len(clients_selectionnes) * self.quota
        return len(contributions) >= minimum


class MecanisteM3(MecanismeStragglers):
    """
    Délai borné : on clôture si le temps dépasse delai_max_s
    (ou si tout le monde a déjà répondu).

    - Expérience : passer temps_ecoule_s (souvent 0,5 s de délai max)
    - API : appeler demarrer() au début du tour, puis laisser temps_ecoule_s=None
    """

    def __init__(self, delai_max_s: float = 5.0):
        self.delai_max_s = delai_max_s
        self.debut_tour = None  # horloge murale (API)

    def demarrer(self):
        """À appeler au POST /v1/round/start (chemin API seulement)."""
        self.debut_tour = time.time()

    def attendre_contributions(
        self,
        clients_selectionnes: list,
        contributions: dict,
        temps_ecoule_s: float | None = None,
    ) -> bool:
        # Tout le monde est là → on peut clôturer sans attendre le délai
        if len(contributions) >= len(clients_selectionnes) and clients_selectionnes:
            return True
        # Chemin expérience : compare au calendrier simulé
        if temps_ecoule_s is not None:
            return temps_ecoule_s >= self.delai_max_s
        # Chemin API : compare à l'horloge réelle
        if self.debut_tour is None:
            return False
        return (time.time() - self.debut_tour) >= self.delai_max_s
