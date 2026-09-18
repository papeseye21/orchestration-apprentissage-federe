"""
D7 - simulateur FOURNI pour les tours d'apprentissage fédéré.

À ne pas réécrire : c'est la base neutre du projet.
Ce que ça fait, simplement :
  - generate_clients : crée 100 clients hétérogènes (data_size, capacity, reliability)
  - simulate_local_training : invente une durée + un vecteur dim-8 (pas un vrai NN)
  - weighted_average : FedAvg (moyenne pondérée par data_size)

Le projet porte sur le PLAN DE CONTRÔLE (sélection / stragglers), pas sur le ML.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
import statistics
import time
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Client:
    """Un appareil / participant du réseau fédéré."""
    id: str
    data_size: int          # taille du jeu de données local
    capacity: float         # vitesse de calcul (plus grand = plus rapide)
    reliability: float = 1.0  # proba de réussir l'entraînement local


@dataclass(frozen=True)
class Contribution:
    """Résultat renvoyé par un client après l'entraînement local."""
    client_id: str
    data_size: int
    vector: List[float]     # mise à jour du modèle (dim 8)
    duration_s: float       # durée simulée
    completed: bool         # False = échec / contribution non utilisable


def generate_clients(count: int = 100, seed: int | None = 42) -> list[Client]:
    rng = random.Random(seed)
    clients: list[Client] = []
    for i in range(count):
        data_size = rng.randint(50, 5000)
        capacity = rng.uniform(0.5, 8.0)
        reliability = rng.uniform(0.85, 1.0)
        clients.append(Client(id=f"client-{i+1:03d}", data_size=data_size, capacity=capacity, reliability=reliability))
    return clients


def initial_model(dim: int = 8) -> list[float]:
    return [0.0 for _ in range(dim)]


def simulate_local_training(
    client: Client,
    model: Sequence[float],
    *,
    seed: int | None = None,
    sleep: bool = False,
    max_sleep_s: float = 0.25,
) -> Contribution:
    rng = random.Random(f'{seed}:{client.id}:{tuple(round(x, 6) for x in model)}')
    expected_duration = client.data_size / (client.capacity * 5000.0)
    noise = rng.lognormvariate(0.0, 0.25)
    duration_s = expected_duration * noise
    completed = rng.random() <= client.reliability
    if sleep:
        time.sleep(min(duration_s, max_sleep_s))
    if not completed:
        return Contribution(client.id, client.data_size, list(model), duration_s, False)
    vector = [float(x) + rng.uniform(-0.05, 0.05) + (client.data_size / 100000.0) for x in model]
    return Contribution(client.id, client.data_size, vector, duration_s, True)


def weighted_average(contributions: Iterable[Contribution]) -> list[float]:
    valid = [c for c in contributions if c.completed]
    if not valid:
        raise ValueError("aucune contribution valide à agréger")
    dim = len(valid[0].vector)
    total_weight = sum(c.data_size for c in valid)
    result = []
    for j in range(dim):
        result.append(sum(c.vector[j] * c.data_size for c in valid) / total_weight)
    return result


def summarize_round(contributions: Sequence[Contribution]) -> dict:
    completed = [c for c in contributions if c.completed]
    durations = [c.duration_s for c in contributions]
    return {
        "selected": len(contributions),
        "completed": len(completed),
        "mean_duration_s": statistics.mean(durations) if durations else 0.0,
        "max_duration_s": max(durations) if durations else 0.0,
        "integrated_data_size": sum(c.data_size for c in completed),
    }


if __name__ == "__main__":
    clients = generate_clients(10, seed=42)
    model = initial_model()
    selected = random.sample(clients, 5)
    contributions = [simulate_local_training(c, model, seed=123) for c in selected]
    new_model = weighted_average(contributions)
    print("summary:", summarize_round(contributions))
    print("new_model:", [round(x, 4) for x in new_model])
