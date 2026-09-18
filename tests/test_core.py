"""
Tests automatisés (pytest).
Vérifient : Gini, stratégies (signature / pas de doublon), M1–M3, API (409, Gini).
Lancer : python3 -m pytest -q
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import coordinator
from metrics import coefficient_gini
from strategies import StrategieS0, StrategieS1, StrategieS2, StrategieS3, StrategieS4
from stragglers import MecanisteM1, MecanisteM2, MecanisteM3
from federated_simulator import Client, generate_clients


def test_gini_uniforme():
    """Tous égaux → Gini = 0."""
    assert coefficient_gini([5, 5, 5, 5]) == pytest.approx(0.0)


def test_gini_un_seul():
    """Un seul client sélectionné parmi n → Gini ≈ 1 − 1/n."""
    n = 10
    vals = [20] + [0] * (n - 1)
    g = coefficient_gini(vals)
    assert g == pytest.approx(1 - 1 / n, abs=0.02)


def test_strategies_signature_et_taille():
    """Chaque stratégie renvoie exactement 10 clients distincts."""
    clients = generate_clients(100, seed=1)
    for cls in (StrategieS0, StrategieS1, StrategieS2, StrategieS3, StrategieS4):
        s = cls()
        sel = s.selectionner(clients, 10)
        assert len(sel) == 10
        assert len({c.id for c in sel}) == 10


def test_selection_n_superieur_au_pool():
    """Demander plus de clients qu'il n'y en a ne doit pas planter."""
    clients = generate_clients(5, seed=2)
    sel = StrategieS0().selectionner(clients, 10)
    assert len(sel) == 5


def test_s1_sans_doublon():
    clients = generate_clients(30, seed=3)
    sel = StrategieS1().selectionner(clients, 10)
    assert len(sel) == len({c.id for c in sel})


def test_m2_quota_80():
    clients = [Client(id=f"c{i}", data_size=100, capacity=1.0) for i in range(10)]
    m = MecanisteM2(quota=0.8)
    assert m.attendre_contributions(clients, {c.id: c for c in clients[:7]}) is False
    assert m.attendre_contributions(clients, {c.id: c for c in clients[:8]}) is True


def test_m3_temps_simule():
    clients = [Client(id="c1", data_size=100, capacity=1.0)]
    m = MecanisteM3(delai_max_s=0.5)
    assert m.attendre_contributions(clients, {}, temps_ecoule_s=0.2) is False
    assert m.attendre_contributions(clients, {}, temps_ecoule_s=0.5) is True


def test_m1_complet():
    clients = [Client(id=f"c{i}", data_size=1, capacity=1.0) for i in range(3)]
    m = MecanisteM1()
    assert m.attendre_contributions(clients, {"c0": 1, "c1": 1}) is False
    assert m.attendre_contributions(clients, {"c0": 1, "c1": 1, "c2": 1}) is True


@pytest.fixture
def api_client(monkeypatch):
    # Réinitialise l'état du module entre tests
    coordinator.clients.clear()
    coordinator.contributions.clear()
    coordinator.historique_selections.clear()
    coordinator.tour_actuel.update({
        "id": 0,
        "statut": "en_attente",
        "modele": [0.0] * 8,
        "clients_selectionnes": [],
    })
    coordinator.strategie = StrategieS0()
    coordinator.mecanisme = MecanisteM1()
    return TestClient(coordinator.app)


def test_api_inscription_et_metrics(api_client):
    r = api_client.post(
        "/v1/clients",
        json={"id": "client-001", "data_size": 100, "capacity": 2.0, "reliability": 0.9},
    )
    assert r.status_code == 201
    r2 = api_client.post(
        "/v1/clients",
        json={"id": "client-001", "data_size": 100, "capacity": 2.0},
    )
    assert r2.status_code == 409
    m = api_client.get("/v1/metrics")
    assert m.status_code == 200
    assert "gini_selections" in m.json()


def test_api_cloture_et_409(api_client):
    # M2 à 50 % : 2 clients sur 4 suffisent à clôturer → le 3e reçoit 409
    coordinator.mecanisme = MecanisteM2(quota=0.5)
    for i in range(4):
        api_client.post(
            "/v1/clients",
            json={"id": f"client-{i:03d}", "data_size": 100, "capacity": 5.0, "reliability": 1.0},
        )
    start = api_client.post("/v1/round/start")
    assert start.status_code == 200
    rid = start.json()["tour_id"]
    selected = start.json()["clients_selectionnes"]
    assert len(selected) == 4

    vec = [0.1] * 8
    for cid in selected[:2]:
        r = api_client.post(
            f"/v1/round/{rid}/contributions",
            json={
                "client_id": cid,
                "vector": vec,
                "data_size": 100,
                "duration_s": 0.1,
                "completed": True,
            },
        )
        assert r.status_code == 201

    assert api_client.get("/v1/round").json()["statut"] == "termine"
    late = api_client.post(
        f"/v1/round/{rid}/contributions",
        json={
            "client_id": selected[2],
            "vector": vec,
            "data_size": 100,
            "duration_s": 0.2,
            "completed": True,
        },
    )
    assert late.status_code == 409
    assert late.json()["code"] == "ROUND_CLOSED"
    assert "gini_selections" in api_client.get("/v1/metrics").json()
