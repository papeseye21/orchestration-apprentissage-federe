"""
Génère les 2 figures Pareto du rapport à partir de resultats.csv :
  - durée vs Gini
  - durée vs contributions
Lancer après experiment.py : python3 plot_figures.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)  # crée le dossier s'il n'existe pas


def _load():
    """Lit le CSV agrégé produit par experiment.py."""
    with open(ROOT / "resultats.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def plot_pareto():
    rows = _load()
    durees = [float(r["duree_moyenne"]) for r in rows]
    ginis = [float(r["gini"]) for r in rows]
    contribs = [float(r["contributions_moyenne"]) for r in rows]
    labels = [r["combinaison"] for r in rows]

    # Forme = stratégie, couleur = mécanisme
    markers = {"S0": "o", "S1": "s", "S2": "^", "S3": "D"}
    colors = {"M1": "#1f4e79", "M2": "#c45c26", "M3": "#2a7a4b"}

    # Figure 1 : vitesse vs équité
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for d, g, lab in zip(durees, ginis, labels):
        s, m = lab.split("+")
        ax.scatter(d, g, marker=markers.get(s, "o"), c=colors.get(m, "gray"), s=70, zorder=3)
        ax.annotate(lab, (d, g), textcoords="offset points", xytext=(4, 4), fontsize=7)
    ax.set_xlabel("Durée moyenne d'un tour (s)")
    ax.set_ylabel("Coefficient de Gini (sélections)")
    ax.set_title("Frontière empirique — durée vs équité")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "pareto_duree_gini.png", dpi=150)
    plt.close(fig)

    # Figure 2 : vitesse vs complétude
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for d, c, lab in zip(durees, contribs, labels):
        s, m = lab.split("+")
        ax.scatter(d, c, marker=markers.get(s, "o"), c=colors.get(m, "gray"), s=70, zorder=3)
        ax.annotate(lab, (d, c), textcoords="offset points", xytext=(4, 4), fontsize=7)
    ax.set_xlabel("Durée moyenne d'un tour (s)")
    ax.set_ylabel("Contributions intégrées / tour")
    ax.set_title("Frontière empirique — durée vs complétude")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "pareto_duree_contributions.png", dpi=150)
    plt.close(fig)
    print(f"Figures → {FIG}")


if __name__ == "__main__":
    plot_pareto()
