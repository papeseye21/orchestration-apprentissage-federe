# ============================================================
# STRATÉGIES DE SÉLECTION DES CLIENTS
# Qui participe à chaque tour ? (même interface pour toutes)
# ============================================================

from abc import ABC, abstractmethod
import random


class StrategieSelection(ABC):
    """Contrat commun : toutes les stratégies doivent fournir selectionner()."""

    @abstractmethod
    def selectionner(self, clients: list, nombre: int) -> list:
        """
        Choisit 'nombre' clients parmi la liste, sans doublon.
        - clients : tous les clients inscrits
        - nombre  : combien on en veut (souvent 10)
        """
        pass


def _tirage_pondere_sans_remise(clients: list, poids: list, k: int) -> list:
    """
    Tirage au sort où un poids plus grand = plus de chances d'être pris.
    Sans remise = on ne peut pas tirer deux fois le même client.
    (Contrairement à random.choices, qui pouvait créer des doublons.)
    """
    pool = list(zip(list(clients), list(poids)))
    choisis = []
    k = min(k, len(pool))
    for _ in range(k):
        total = sum(max(w, 0.0) for _, w in pool)
        if total <= 0:
            # Poids tous nuls → on tire au hasard uniforme
            idx = random.randrange(len(pool))
        else:
            # Roulette : on tire un seuil dans [0, total]
            seuil = random.random() * total
            acc = 0.0
            idx = len(pool) - 1
            for i, (_, w) in enumerate(pool):
                acc += max(w, 0.0)
                if acc >= seuil:
                    idx = i
                    break
        client, _ = pool.pop(idx)  # retire du pool (= sans remise)
        choisis.append(client)
    return choisis


class StrategieS0(StrategieSelection):
    """Baseline : tirage uniforme au hasard (équitable sur le long terme)."""

    def selectionner(self, clients: list, nombre: int) -> list:
        if not clients or nombre <= 0:
            return []
        nombre = min(nombre, len(clients))  # ne pas demander plus que disponible
        return random.sample(clients, nombre)


class StrategieS1(StrategieSelection):
    """Favorise les clients qui ont beaucoup de données locales (data_size)."""

    def selectionner(self, clients: list, nombre: int) -> list:
        if not clients or nombre <= 0:
            return []
        nombre = min(nombre, len(clients))
        poids = [getattr(c, "data_size", 1) for c in clients]
        return _tirage_pondere_sans_remise(clients, poids, nombre)


class StrategieS2(StrategieSelection):
    """Toujours les plus rapides (capacity élevée) → tours courts, mais Gini élevé."""

    def selectionner(self, clients: list, nombre: int) -> list:
        if not clients or nombre <= 0:
            return []
        nombre = min(nombre, len(clients))
        tries = sorted(clients, key=lambda c: c.capacity, reverse=True)
        return tries[:nombre]


class StrategieS3(StrategieSelection):
    """
    Compromis 50/50 : moitié les plus rapides, moitié au hasard parmi le reste.
    Hypothèse : plus équitable que S2, plus rapide que S0.
    Attention : les N/2 rapides sont toujours les mêmes → plancher de Gini.
    """

    def selectionner(self, clients: list, nombre: int) -> list:
        if not clients or nombre <= 0:
            return []
        nombre = min(nombre, len(clients))
        nombre_rapides = nombre // 2
        tries = sorted(clients, key=lambda c: c.capacity, reverse=True)
        rapides = tries[:nombre_rapides]
        ids_rapides = {c.id for c in rapides}
        restants = [c for c in clients if c.id not in ids_rapides]
        nombre_aleatoires = nombre - nombre_rapides
        if nombre_aleatoires <= 0 or not restants:
            return rapides
        aleatoires = random.sample(restants, min(nombre_aleatoires, len(restants)))
        return rapides + aleatoires


class StrategieS4(StrategieSelection):
    """Les plus fiables (reliability) — utilisé seulement dans l'approfondissement."""

    def selectionner(self, clients: list, nombre: int) -> list:
        if not clients or nombre <= 0:
            return []
        nombre = min(nombre, len(clients))
        tries = sorted(
            clients, key=lambda c: getattr(c, "reliability", 1.0), reverse=True
        )
        return tries[:nombre]
