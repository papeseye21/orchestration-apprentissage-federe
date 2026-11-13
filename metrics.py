# ============================================================
# MÉTRIQUES EXPÉRIMENTALES
# - Gini : mesure d'équité des sélections (0 = égal, ~1 = inégal)
# - Pearson : corrélation entre deux listes (ex. reliability vs capacity)
# - t-test / IC : significativité pour l'approfondissement S0 vs S4
# ============================================================

from __future__ import annotations

import math
from typing import Sequence


def coefficient_gini(selections: list) -> float:
    """
    Gini sur le nombre de fois que chaque client a été sélectionné.

    Exemples :
      [5, 5, 5, 5] → 0 (parfaitement équitable)
      [20, 0, 0, 0] → proche de 1 (très inégal)
    Formule standard sur le vecteur trié.
    """
    if not selections or sum(selections) == 0:
        return 0.0

    n = len(selections)
    selections_tries = sorted(selections)
    total = sum(selections_tries)

    cumul = 0
    for i, valeur in enumerate(selections_tries):
        cumul += (2 * (i + 1) - n - 1) * valeur

    return cumul / (n * total)


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    """Corrélation de Pearson (−1 à +1). 0 ≈ pas de lien linéaire."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den_x = sum((a - mx) ** 2 for a in x)
    den_y = sum((b - my) ** 2 for b in y)
    den = math.sqrt(den_x * den_y)
    if den == 0:
        return 0.0
    return num / den


def _betacf(a: float, b: float, x: float) -> float:
    """Fraction continue de Lentz pour la fonction bêta incomplète."""
    max_iter = 200
    eps = 3e-12
    fpmin = 1e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Fonction bêta incomplète régularisée I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - ln_beta)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def p_value_student(t: float, df: float) -> float:
    """p-value bilatérale d'une loi de Student approximée via I_x."""
    if df <= 0 or math.isnan(t):
        return 1.0
    x = df / (df + t * t)
    return _betai(df / 2.0, 0.5, x)


def ttest_ind(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    """
    Test t de Welch (échantillons indépendants, variances inégales).
    Retourne (statistique_t, degres_liberte, p_value_bilaterale).
    """
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return 0.0, 0.0, 1.0
    m1 = sum(a) / n1
    m2 = sum(b) / n2
    v1 = sum((x - m1) ** 2 for x in a) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in b) / (n2 - 1)
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return 0.0, float(n1 + n2 - 2), 1.0
    t = (m1 - m2) / se
    num = (v1 / n1 + v2 / n2) ** 2
    den = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    df = num / den if den else float(n1 + n2 - 2)
    p = p_value_student(t, df)
    return t, df, p


def intervalle_confiance(valeurs: Sequence[float], z: float = 1.96) -> tuple[float, float, float]:
    """Retourne (moyenne, borne_inf, borne_sup) à ~95 % (approximation normale)."""
    n = len(valeurs)
    if n == 0:
        return 0.0, 0.0, 0.0
    m = sum(valeurs) / n
    if n == 1:
        return m, m, m
    var = sum((x - m) ** 2 for x in valeurs) / (n - 1)
    se = math.sqrt(var / n)
    return m, m - z * se, m + z * se
