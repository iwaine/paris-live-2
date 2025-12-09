def compute_inplay_domination(stats_a, stats_b):
    """
    Calcule un score de domination in-play pour stats_a vs stats_b (valeurs brutes live).
    Retourne un score entre 0 (faible) et 1 (domination totale).
    """
    # Nouvelle logique : même calcul que pattern chaud
    def ratio(a, b):
        return a / (a + b) if (a + b) > 0 else 0.5

    # Pondérations par stat
    # Nouveau mapping pour coller aux clés du dict live
    weights = {
        'Possession': 0.25,
        'Attacks': 0.2,
        'Dangerous_attacks': 0.2,
        'Shots': 0.2,
        'Shots_on_target': 0.15
    }
    stats_keys = ['Possession', 'Attacks', 'Dangerous_attacks', 'Shots', 'Shots_on_target']
    score = 0.0
    # Suppression du debug détaillé, affichage final synthétique
    return score
    return score

# -*- coding: utf-8 -*-
"""
Scoring combiné pour match live : affichage détaillé de chaque critère et score final.
"""

def scoring_detaille(
    pattern_score: float,
    saturation_score: float,
    inplay_stats: dict,
    red_cards: dict,
    corners: dict,
    momentum_5min: float,
    momentum_2min: float,
    debug: bool = True
):
    """
    Calcule et affiche le score détaillé pour un match live.
    pattern_score : score historique (0-1)
    saturation_score : pénalité (0-1)
    inplay_stats : dict avec 'possession', 'tirs', 'tirs_cadres', 'attaques', 'attaques_dangereuses'
    red_cards : dict {home: int, away: int}
    corners : dict {home: int, away: int}
    momentum_5min : score momentum 5min (0-1)
    momentum_2min : score momentum 2min (0-1)
    """
    # 0. Domination in-play brute (live)
    # Si stats adverses fournies dans inplay_stats['opponent'], on affiche la domination live
    if 'opponent' in inplay_stats:
        score_a = compute_inplay_domination(inplay_stats, inplay_stats['opponent'])
        score_b = compute_inplay_domination(inplay_stats['opponent'], inplay_stats)
        total = score_a + score_b
        if total > 0:
            dom_a_pct = score_a / total * 100
            dom_b_pct = score_b / total * 100
        else:
            dom_a_pct = dom_b_pct = 50.0
        print(f"Total domination A ≈ {score_a:.2f} (soit {score_a*100:.0f}%), domination B ≈ {score_b:.2f} (soit {score_b*100:.0f}%)")

    # 1. Patterns historiques (80%)
    # Correction : potentiel restant basé sur le score live et la moyenne attendue (MT1 ou MT2 selon la période)
    score_hist = pattern_score * saturation_score
    def format_saturation(score_live, moyenne_attendue):
        if moyenne_attendue == 0:
            return "Pas de référence historique pour le potentiel."
        ratio = score_live / moyenne_attendue
        if ratio >= 1.0:
            return f"Potentiel restant faible (score live {score_live} / attendu {moyenne_attendue:.2f}) — le nombre de buts attendus est déjà atteint, peu de potentiel pour nouveaux buts."
        def rel_gap(a, b):
            return (a - b) / (a + b) if (a + b) > 0 else 0.0

        # Correction : pour la possession, on prend le pourcentage direct (A/100)
        # Nouvelle logique : normalisation et pondération
        def norm(a, b):
            return a / (a + b) if (a + b) > 0 else 0.5

        # Poids par stat (somme = 1)
        weights = {
            'possession': 0.15,
            'shots': 0.15,
            'shots_on_target': 0.25,
            'shots_inside_box': 0.15,
            'shots_outside_box': 0.05,
            'attacks': 0.10,
            'dangerous_attacks': 0.15
        }
        # Récupérer les stats, fallback à 0 si absentes
        a_stats = {
            'possession': stats_a.get('possession', 0),
            'shots': stats_a.get('shots', 0),
            'shots_on_target': stats_a.get('shots_on_target', 0),
            'shots_inside_box': stats_a.get('shots_inside_box', 0),
            'shots_outside_box': stats_a.get('shots_outside_box', 0),
            'attacks': stats_a.get('attacks', 0),
            'dangerous_attacks': stats_a.get('dangerous_attacks', 0)
        }
        b_stats = {
            'possession': stats_b.get('possession', 0),
            'shots': stats_b.get('shots', 0),
            'shots_on_target': stats_b.get('shots_on_target', 0),
            'shots_inside_box': stats_b.get('shots_inside_box', 0),
            'shots_outside_box': stats_b.get('shots_outside_box', 0),
            'attacks': stats_b.get('attacks', 0),
            'dangerous_attacks': stats_b.get('dangerous_attacks', 0)
        }
        score_a = 0.0
        print("[DOMINATION LIVE - DÉTAILS]")
        for k, w in weights.items():
            va = a_stats[k]
            vb = b_stats[k]
            pa = norm(va, vb)
            pb = norm(vb, va)
            contrib_a = w * pa
            contrib_b = w * pb
            score_a += contrib_a
            print(f"  {k} : A={va} / B={vb} | ratio_A={pa:.3f} | ratio_B={pb:.3f} | poids={w:.2f} | contrib_A={contrib_a:.3f} | contrib_B={contrib_b:.3f}")
        print(f"  TOTAL DOMINATION A : {score_a:.3f} (soit {score_a*100:.1f}%)")
        return score_a
        # Moyenne des gaps, normalisée de [-1,1] à [0,1]
        score = (sum(gaps) / len(gaps) + 1) / 2
        return score
    # ...existing code...

def compute_pattern_chaud(inplay_stats, debug=False):
    # Possession
    poss_a = inplay_stats.get('raw_possession_a', 0)
    poss_b = inplay_stats.get('raw_possession_b', 0)
    delta_poss = abs(poss_a - poss_b)
    score_poss = max(0.0, min(1.0, 1 - (delta_poss / 50)))  # max 1 si delta = 0, min 0 si delta = 50
    if debug:
        print(f"[Pattern chaud] Delta possession : {delta_poss:.1f}% → score {score_poss*100:.1f}%")
    # Attaques
    att_a = inplay_stats.get('raw_attaques_a', 0)
    att_b = inplay_stats.get('raw_attaques_b', 0)
    delta_att = abs(att_a - att_b)
    total_att = att_a + att_b
    score_att = 1 - (delta_att / total_att) if total_att > 0 else 0
    score_att = max(0.0, min(1.0, score_att))
    if debug:
        print(f"[Pattern chaud] Delta attaques : {delta_att} / {total_att} → score {score_att*100:.1f}%")
    # Attaques dangereuses
    da_a = inplay_stats.get('raw_attaques_dangereuses_a', 0)
    da_b = inplay_stats.get('raw_attaques_dangereuses_b', 0)
    delta_da = abs(da_a - da_b)
    total_da = da_a + da_b
    score_da = 1 - (delta_da / total_da) if total_da > 0 else 0
    score_da = max(0.0, min(1.0, score_da))
    if debug:
        print(f"[Pattern chaud] Delta attaques dangereuses : {delta_da} / {total_da} → score {score_da*100:.1f}%")
    # Tirs cadrés / tirs totaux
    tirs_a = inplay_stats.get('raw_tirs_a', 0)
    tirs_b = inplay_stats.get('raw_tirs_b', 0)
    tirs_cadres_a = inplay_stats.get('raw_tirs_cadres_a', 0)
    tirs_cadres_b = inplay_stats.get('raw_tirs_cadres_b', 0)
    total_tirs = tirs_a + tirs_b
    total_tirs_cadres = tirs_cadres_a + tirs_cadres_b
    ratio_tirs_cadres = (total_tirs_cadres / total_tirs) if total_tirs > 0 else 0
    score_tirs = ratio_tirs_cadres
    if debug:
        print(f"[Pattern chaud] Ratio tirs cadrés : {total_tirs_cadres} / {total_tirs} → score {score_tirs*100:.1f}%")
    # Pondération
    score_chaud = 0.3 * score_poss + 0.2 * score_att + 0.2 * score_da + 0.3 * score_tirs
    if debug:
        print(f"→ Score pattern chaud (but imminent) : {score_chaud*100:.1f}%")
    return score_chaud

# Exemple d'appel (à remplacer par les vraies données live/historiques)
if __name__ == "__main__":
    scoring_detaille(
        pattern_score=0.85,
        saturation_score=0.95,
        inplay_stats={
            'possession': 0.6,
            'tirs': 0.7,
            'tirs_cadres': 0.5,
            'attaques': 0.65,
            'attaques_dangereuses': 0.7
        },
        red_cards={'home': 1, 'away': 0},
        corners={'home': 6, 'away': 5},
        momentum_5min=0.8,
        momentum_2min=0.75,
        debug=True
    )
