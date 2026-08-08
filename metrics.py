# ============================================================
# MÉTRIQUES EXPÉRIMENTALES
# Fonctions pour mesurer l'équité et les performances
# ============================================================

def coefficient_gini(selections: list) -> float:
    """
    Calcule le coefficient de Gini sur le nombre de sélections
    de chaque client sur plusieurs tours.
    
    - selections : liste du nombre de fois que chaque client 
                   a été sélectionné
                   ex: [5, 5, 5, 5] → équitable → Gini = 0
                       [20, 0, 0, 0] → inéquitable → Gini = 1
    - retourne : float entre 0 et 1
    """
    if not selections or sum(selections) == 0:
        return 0.0
    
    n = len(selections)
    selections_tries = sorted(selections)
    total = sum(selections_tries)
    
    # Formule du coefficient de Gini
    cumul = 0
    for i, valeur in enumerate(selections_tries):
        cumul += (2 * (i + 1) - n - 1) * valeur
    
    return cumul / (n * total)