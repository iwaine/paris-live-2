#!/usr/bin/env python3
"""
Formatter Telegram ENRICHI avec toutes les stats détaillées
- Minute moyenne + écart-type
- Récurrence 5 derniers
- Timing précis avec interprétation
- Stats domicile/extérieur par mi-temps
- Top patterns du championnat
"""

def format_telegram_alert_enriched(match_data, prediction_home, prediction_away, combined_prob):
    """
    Génère une alerte Telegram enrichie complète
    
    Args:
        match_data: Données du match live (score, minute, stats)
        prediction_home: Prédiction équipe domicile
        prediction_away: Prédiction équipe extérieur
        combined_prob: Probabilité combinée
    
    Returns:
        Message Telegram formaté
    """
    
    lines = []
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════════════
    lines.append("╔═══════════════════════════════════════════════════════════════════════════════╗")
    lines.append("║                   🚨 ALERTE BUT - TELEGRAM NOTIFICATION                      ║")
    lines.append("╚═══════════════════════════════════════════════════════════════════════════════╝")
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MATCH EN COURS
    # ═══════════════════════════════════════════════════════════════════════════════
    lines.append("⚽ MATCH EN COURS")
    lines.append("="*50)
    lines.append(f"🏟️  {match_data['home_team']} vs {match_data['away_team']}")
    lines.append(f"⏱️  Minute : {match_data['current_minute']}'")
    lines.append(f"📊 Score : {match_data['score_home']}-{match_data['score_away']}")
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # STATS LIVE - AFFICHER TOUTES LES STATS DISPONIBLES
    # ═══════════════════════════════════════════════════════════════════════════════
    if match_data.get('live_stats'):
        lines.append("📈 STATS LIVE")
        lines.append("-"*50)
        stats = match_data['live_stats']
        
        # Afficher toutes les stats dans l'ordre prioritaire
        # 1. Possession (toujours importante)
        if stats.get('possession_home') is not None or stats.get('possession_away') is not None:
            poss_h = stats.get('possession_home', 0)
            poss_a = stats.get('possession_away', 0)
            lines.append(f"✅ Possession : {poss_h:.0f}% - {poss_a:.0f}% ✓")
        
        # 2. Corners
        if stats.get('corners_home') is not None or stats.get('corners_away') is not None:
            corn_h = stats.get('corners_home', 0)
            corn_a = stats.get('corners_away', 0)
            lines.append(f"✅ Corners : {corn_h} - {corn_a} ✓")
        
        # 3. Total shots (IMPORTANT - souvent manquant dans l'ancien code)
        if stats.get('shots_home') is not None or stats.get('shots_away') is not None:
            shots_h = stats.get('shots_home', 0)
            shots_a = stats.get('shots_away', 0)
            lines.append(f"✅ Total shots : {shots_h} - {shots_a} ✓")
        
        # 4. Shots on target (IMPORTANT - souvent manquant)
        if stats.get('shots_on_target_home') is not None or stats.get('shots_on_target_away') is not None:
            sot_h = stats.get('shots_on_target_home', 0)
            sot_a = stats.get('shots_on_target_away', 0)
            lines.append(f"✅ Shots on target : {sot_h} - {sot_a} ✓")
        
        # 5. Attacks (IMPORTANT - souvent manquant)
        if stats.get('attacks_home') is not None or stats.get('attacks_away') is not None:
            att_h = stats.get('attacks_home', 0)
            att_a = stats.get('attacks_away', 0)
            lines.append(f"✅ Attacks : {att_h} - {att_a} ✓")
        
        # 6. Dangerous attacks
        if stats.get('dangerous_attacks_home') is not None or stats.get('dangerous_attacks_away') is not None:
            dang_h = stats.get('dangerous_attacks_home', 0)
            dang_a = stats.get('dangerous_attacks_away', 0)
            lines.append(f"✅ Dangerous attacks : {dang_h} - {dang_a} ✓")
        
        # 7. Shots inside/outside box (si disponibles)
        if stats.get('shots_inside_box_home') is not None or stats.get('shots_inside_box_away') is not None:
            sib_h = stats.get('shots_inside_box_home', 0)
            sib_a = stats.get('shots_inside_box_away', 0)
            lines.append(f"📍 Shots inside box : {sib_h} - {sib_a}")
        
        if stats.get('shots_outside_box_home') is not None or stats.get('shots_outside_box_away') is not None:
            sob_h = stats.get('shots_outside_box_home', 0)
            sob_a = stats.get('shots_outside_box_away', 0)
            lines.append(f"📍 Shots outside box : {sob_h} - {sob_a}")
        
        lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PRÉDICTION INTERVALLE ACTIF
    # ═══════════════════════════════════════════════════════════════════════════════
    interval = prediction_home['interval_name']
    lines.append("━"*78)
    lines.append(f"🎯 PRÉDICTION INTERVALLE {interval} MIN")
    lines.append("━"*78)
    lines.append("")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # ÉQUIPE DOMICILE
    # ─────────────────────────────────────────────────────────────────────────────
    lines.append(f"📊 {match_data['home_team'].upper()} (HOME)")
    lines.append("-"*50)
    
    # Ajout : gestion des données historiques manquantes/faibles
    def format_prob(prob, threshold=10):
        if prob is None or prob < threshold:
            return f"Données insuffisantes ({prob if prob is not None else 'N/A'}%) ⚠️"
        return f"{prob:.1f}%"
    
    # Probabilité finale
    prob_home = prediction_home.get('probability_final', None)
    prob_hist_home = prediction_home.get('probability_historical', None)
    delta_home = (prob_home - prob_hist_home) if (prob_home is not None and prob_hist_home is not None) else 0
    lines.append(f"🎯 Probabilité finale : {format_prob(prob_home)} ({delta_home:+.1f}% vs historique {format_prob(prob_hist_home)})")
    
    # Confiance
    confidence_home = prediction_home['confidence_level']
    lines.append(f"✅ Confiance : {confidence_home}")
    
    # Récurrence 5 derniers
    rec5_home = prediction_home.get('recurrence_last_5', 0)
    rec5_home_pct = rec5_home * 100
    rec5_emoji = "✅" if rec5_home >= 0.6 else "⚠️"
    lines.append(f"🔄 Récurrence 5 derniers : {rec5_home_pct:.0f}% {rec5_emoji}")
    
    # TIMING PRÉCIS (minute moyenne + SEM + IQR)
    avg_min_home = prediction_home.get('avg_minute', 0)
    sem_min_home = prediction_home.get('sem_minute', 0)
    iqr_q1_home = prediction_home.get('iqr_q1', 0)
    iqr_q3_home = prediction_home.get('iqr_q3', 0)
    
    if avg_min_home > 0:
        # Afficher SEM et IQR
        if sem_min_home < 3:
            precision = "💡 TRÈS PRÉCIS !"
        elif sem_min_home < 5:
            precision = "✅ Précis"
        else:
            precision = "⚠️ Variable"
        
        lines.append(f"⏱️  Timing : Minute {avg_min_home:.1f} ±{sem_min_home:.1f}' (SEM) {precision}")
        if iqr_q1_home > 0 and iqr_q3_home > 0:
            lines.append(f"   └─ Zone de danger : [{iqr_q1_home:.0f}' - {iqr_q3_home:.0f}'] (50% des buts)")
    
    # Facteurs appliqués
    lines.append("")
    lines.append("📈 Facteurs appliqués :")
    lines.append(f"  • Pattern historique    : {prob_hist_home:.1f}% (base)")
    
    if 'momentum_boost' in prediction_home:
        momentum = prediction_home['momentum_boost']
        lines.append(f"  • Momentum live         : {momentum:+.0f}% (attaques: {match_data['live_stats'].get('dangerous_attacks_home', 0)})")
    
    if 'saturation_factor' in prediction_home:
        sat = prediction_home['saturation_factor']
        sat_pct = (sat - 1) * 100
        lines.append(f"  • Saturation            : {sat_pct:+.0f}% ({match_data['score_home'] + match_data['score_away']} buts déjà)")
    
    lines.append(f"  • Localisation          : +5% (domicile)")
    
    # Stats pattern
    lines.append("")
    lines.append(f"🔥 Statistiques {interval} min ({match_data['home_team']} HOME):")
    total_matches_home = prediction_home.get('total_matches', 0)
    any_goal_total_home = prediction_home.get('any_goal_total', 0)
    if total_matches_home > 0:
        moyenne_home = any_goal_total_home / total_matches_home
        lines.append(f"  • {any_goal_total_home} buts totaux ({prediction_home['goals_scored']} marqués + {prediction_home['goals_conceded']} encaissés)")
        lines.append(f"  • Récurrence : {prediction_home['freq_any_goal']*100:.1f}% des matchs")
        lines.append(f"  • Moyenne : {moyenne_home:.2f} buts/match dans cet intervalle")
    else:
        lines.append(f"  • Données insuffisantes pour calculer la moyenne et la récurrence dans cet intervalle ⚠️")
    
    # Stats globales domicile/extérieur par mi-temps
    if 'avg_goals_first_half' in prediction_home:
        lines.append("")
        lines.append(f"📊 Force à domicile ({match_data['home_team']}):")
        lines.append(f"  • 1ère mi-temps : {prediction_home['avg_goals_first_half']:.2f} buts/match")
        lines.append(f"  • 2ème mi-temps : {prediction_home['avg_goals_second_half']:.2f} buts/match")
        lines.append(f"  • Total match   : {prediction_home['avg_goals_full_match']:.2f} buts/match")
    
    lines.append("")
    lines.append("")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # ÉQUIPE EXTÉRIEUR
    # ─────────────────────────────────────────────────────────────────────────────
    lines.append(f"📊 {match_data['away_team'].upper()} (AWAY)")
    lines.append("-"*50)
    
    # Probabilité finale
    prob_away = prediction_away.get('probability_final', None)
    prob_hist_away = prediction_away.get('probability_historical', None)
    delta_away = (prob_away - prob_hist_away) if (prob_away is not None and prob_hist_away is not None) else 0
    lines.append(f"🎯 Probabilité finale : {format_prob(prob_away)} ({delta_away:+.1f}% vs historique {format_prob(prob_hist_away)})")
    
    # Confiance
    confidence_away = prediction_away['confidence_level']
    lines.append(f"⚠️  Confiance : {confidence_away}")
    
    # Récurrence 5 derniers
    rec5_away = prediction_away.get('recurrence_last_5', 0)
    rec5_away_pct = rec5_away * 100
    rec5_emoji_away = "✅" if rec5_away >= 0.6 else "⚠️"
    lines.append(f"🔄 Récurrence 5 derniers : {rec5_away_pct:.0f}% {rec5_emoji_away}")
    
    # TIMING PRÉCIS (minute moyenne + SEM + IQR)
    avg_min_away = prediction_away.get('avg_minute', 0)
    sem_min_away = prediction_away.get('sem_minute', 0)
    iqr_q1_away = prediction_away.get('iqr_q1', 0)
    iqr_q3_away = prediction_away.get('iqr_q3', 0)
    
    if avg_min_away > 0:
        if sem_min_away < 3:
            precision_away = "💡 TRÈS PRÉCIS !"
        elif sem_min_away < 5:
            precision_away = "✅ Précis"
        else:
            precision_away = "⚠️ Variable"
        
        lines.append(f"⏱️  Timing : Minute {avg_min_away:.1f} ±{sem_min_away:.1f}' (SEM) {precision_away}")
        if iqr_q1_away > 0 and iqr_q3_away > 0:
            lines.append(f"   └─ Zone de danger : [{iqr_q1_away:.0f}' - {iqr_q3_away:.0f}'] (50% des buts)")
    
    # Facteurs
    lines.append("")
    lines.append("📈 Facteurs appliqués :")
    lines.append(f"  • Pattern historique    : {prob_hist_away:.1f}% (base)")
    
    if 'momentum_boost' in prediction_away:
        momentum_away = prediction_away['momentum_boost']
        lines.append(f"  • Momentum live         : {momentum_away:+.0f}% (attaques: {match_data['live_stats'].get('dangerous_attacks_away', 0)})")
    
    if 'saturation_factor' in prediction_away:
        sat_away = prediction_away['saturation_factor']
        sat_pct_away = (sat_away - 1) * 100
        lines.append(f"  • Saturation            : {sat_pct_away:+.0f}% ({match_data['score_home'] + match_data['score_away']} buts déjà)")
    
    lines.append(f"  • Localisation          : 0% (extérieur)")
    
    # Stats pattern
    lines.append("")
    lines.append(f"⚡ Statistiques {interval} min ({match_data['away_team']} AWAY):")
    total_matches_away = prediction_away.get('total_matches', 0)
    any_goal_total_away = prediction_away.get('any_goal_total', 0)
    if total_matches_away > 0:
        moyenne_away = any_goal_total_away / total_matches_away
        lines.append(f"  • {any_goal_total_away} buts totaux ({prediction_away['goals_scored']} marqués + {prediction_away['goals_conceded']} encaissés)")
        lines.append(f"  • Récurrence : {prediction_away['freq_any_goal']*100:.1f}% des matchs")
        lines.append(f"  • Moyenne : {moyenne_away:.2f} buts/match dans cet intervalle")
        if prediction_away['goals_conceded'] > prediction_away['goals_scored']:
            lines.append(f"  • ⚠️ Défense fragile en fin de match !")
    else:
        lines.append(f"  • Données insuffisantes pour calculer la moyenne et la récurrence dans cet intervalle ⚠️")
    
    lines.append("")
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PROBABILITÉ COMBINÉE
    # ═══════════════════════════════════════════════════════════════════════════════
    lines.append("━"*78)
    lines.append("🎲 PROBABILITÉ COMBINÉE (AU MOINS 1 BUT)")
    lines.append("━"*78)
    lines.append("")
    
    combined_pct = combined_prob * 100
    
    if combined_pct >= 85:
        signal = "🔥 SIGNAL TRÈS FORT"
    elif combined_pct >= 75:
        signal = "🟢 TRÈS PROBABLE"
    elif combined_pct >= 65:
        signal = "✅ PROBABLE"
    else:
        signal = "⚠️ MODÉRÉ"
    
    lines.append(f"⚽ Intervalle actif ({interval} min) : {combined_pct:.1f}%")
    lines.append(f"   └─ {signal}")
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ANALYSE SATURATION
    # ═══════════════════════════════════════════════════════════════════════════════
    total_goals = match_data['score_home'] + match_data['score_away']
    current_min = match_data['current_minute']
    expected_goals = (current_min / 90) * 2.7
    goal_diff = total_goals - expected_goals
    
    if goal_diff > 2:
        sat_factor = 0.70
        sat_level = "Beaucoup trop de buts"
    elif goal_diff > 1:
        sat_factor = 0.85
        sat_level = "Pas mal de buts"
    elif goal_diff > 0:
        sat_factor = 0.95
        sat_level = "Légèrement au-dessus"
    else:
        sat_factor = 1.00
        sat_level = "Normal"
    
    lines.append("━"*78)
    lines.append("💡 ANALYSE SATURATION")
    lines.append("━"*78)
    lines.append("")
    lines.append(f"Buts actuels     : {total_goals} buts ({match_data['score_home']}-{match_data['score_away']})")
    lines.append(f"Buts attendus    : {expected_goals:.1f} buts à la {current_min}e minute")
    lines.append(f"Différence       : {goal_diff:+.1f} but ({sat_level})")
    lines.append(f"Facteur appliqué : {sat_factor:.2f} (réduction {(1-sat_factor)*100:.0f}%)")
    lines.append("")
    
    # Interprétation
    if sat_factor < 0.80:
        interp = "Match très saturé en buts. Probabilité fortement réduite."
    elif sat_factor < 0.95:
        interp = "Match légèrement saturé. Probabilité modérément réduite."
    else:
        interp = "Match normal en buts. Aucune réduction significative."
    
    lines.append(f"💬 Interprétation : {interp}")
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TOP PATTERNS DU CHAMPIONNAT
    # ═══════════════════════════════════════════════════════════════════════════════
    lines.append("━"*78)
    league_name = match_data.get('league', 'N/A')
    lines.append(f"🏆 TOP PATTERNS {league_name.upper()} - INTERVALLE {interval}")
    lines.append("━"*78)
    lines.append("")
    
    # Ici on afficherait les top patterns du championnat
    # Pour l'exemple, données statiques
    top_patterns = [
        {"team": "Spartak Varna", "loc": "HOME", "interval": "76-90", "pct": 89, "goals": 10, "matches": "8/9", "scored": 4, "conceded": 6},
        {"team": "Slavia Sofia", "loc": "AWAY", "interval": "76-90", "pct": 75, "goals": 7, "matches": "6/8", "scored": 4, "conceded": 3},
        {"team": "Levski Sofia", "loc": "HOME", "interval": "76-90", "pct": 56, "goals": 8, "matches": "5/9", "scored": 6, "conceded": 2},
    ]
    
    for i, p in enumerate(top_patterns, 1):
        lines.append(f"{i}. {p['team']} {p['loc']} {p['interval']} : {p['pct']}% ({p['goals']} buts sur {p['matches']} matches)")
        lines.append(f"   └─ {p['scored']} marqués + {p['conceded']} encaissés")
    
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # RECOMMANDATION FINALE
    # ═══════════════════════════════════════════════════════════════════════════════
    lines.append("━"*78)
    lines.append("✅ RECOMMANDATION")
    lines.append("━"*78)
    lines.append("")
    
    if combined_pct >= 75:
        recommendation = "FORT"
    elif combined_pct >= 65:
        recommendation = "MODÉRÉ"
    else:
        recommendation = "FAIBLE"
    
    lines.append(f"🎯 SIGNAL : {recommendation} ({combined_pct:.1f}%)")
    
    # Confiance globale
    if confidence_home == "EXCELLENT" and confidence_away == "EXCELLENT":
        lines.append(f"📊 Confiance : TRÈS ÉLEVÉE (les deux équipes ont d'excellents patterns)")
    elif confidence_home == "EXCELLENT" or confidence_away == "EXCELLENT":
        lines.append(f"📊 Confiance : ÉLEVÉE")
    else:
        lines.append(f"📊 Confiance : MODÉRÉE")
    
    # Fenêtre de tir
    remaining_min = int(interval.split('-')[1]) - current_min
    lines.append(f"⏱️  Fenêtre : {current_min}-{interval.split('-')[1]} min ({remaining_min} minutes restantes)")
    lines.append("")
    lines.append("Action suggérée :")
    lines.append(f"  ✅ Parier sur AU MOINS 1 BUT entre {interval} min")
    
    if prob_home > prob_away:
        lines.append(f"  ✅ {match_data['home_team']} a le pattern le plus fort ({prob_home:.1f}%)")
    else:
        lines.append(f"  ✅ {match_data['away_team']} a le pattern le plus fort ({prob_away:.1f}%)")
    
    if sat_factor < 0.90:
        lines.append(f"  ⚠️  Saturation {(1-sat_factor)*100:.0f}% mais compensée par les patterns")
    
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════════════════════
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    lines.append("╚═══════════════════════════════════════════════════════════════════════════════╝")
    lines.append(f"              📱 Généré à {timestamp} - Paris Live Prediction System")
    lines.append("╚═══════════════════════════════════════════════════════════════════════════════╝")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLE D'UTILISATION
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Données d'exemple
    match_data = {
        'home_team': 'Levski Sofia',
        'away_team': 'Spartak Varna',
        'current_minute': 78,
        'score_home': 2,
        'score_away': 1,
        'league': 'Bulgaria - Parva Liga',
        'live_stats': {
            'possession_home': 58,
            'possession_away': 42,
            'corners_home': 7,
            'corners_away': 3,
            'shots_home': 14,
            'shots_away': 8,
            'shots_on_target_home': 6,
            'shots_on_target_away': 3,
            'attacks_home': 87,
            'attacks_away': 62,
            'dangerous_attacks_home': 24,
            'dangerous_attacks_away': 15
        }
    }
    
    prediction_home = {
        'interval_name': '76-90',
        'probability_final': 62.3,
        'probability_historical': 55.6,
        'confidence_level': 'EXCELLENT',
        'recurrence_last_5': 0.80,
        'avg_minute': 83.8,
        'std_minute': 6.5,
        'sem_minute': 2.4,
        'iqr_q1': 78,
        'iqr_q3': 89,
        'momentum_boost': 12,
        'saturation_factor': 0.95,
        'any_goal_total': 8,
        'goals_scored': 6,
        'goals_conceded': 2,
        'freq_any_goal': 0.556,
        'total_matches': 9,
        'avg_goals_first_half': 1.2,
        'avg_goals_second_half': 1.5,
        'avg_goals_full_match': 2.7
    }
    
    prediction_away = {
        'interval_name': '76-90',
        'probability_final': 41.2,
        'probability_historical': 44.4,
        'confidence_level': 'BON',
        'recurrence_last_5': 0.60,
        'avg_minute': 82.8,
        'std_minute': 3.7,
        'sem_minute': 1.3,
        'iqr_q1': 79,
        'iqr_q3': 87,
        'momentum_boost': -8,
        'saturation_factor': 0.95,
        'any_goal_total': 7,
        'goals_scored': 1,
        'goals_conceded': 6,
        'freq_any_goal': 0.444,
        'total_matches': 9,
        'avg_goals_first_half': 0.8,
        'avg_goals_second_half': 1.1,
        'avg_goals_full_match': 1.9
    }
    
    combined_prob = 0.774
    
    # Générer le message
    message = format_telegram_alert_enriched(match_data, prediction_home, prediction_away, combined_prob)
    print(message)
