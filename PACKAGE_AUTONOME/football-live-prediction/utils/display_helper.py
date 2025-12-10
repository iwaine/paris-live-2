"""
Display Helper - Affichage amélioré des prédictions
"""


def get_danger_emoji(score: float) -> str:
    """Retourne les emojis en fonction du danger score"""
    if score >= 80:
        return "🔥🔥🔥🔥🔥"
    elif score >= 70:
        return "🔥🔥🔥🔥"
    elif score >= 60:
        return "🔥🔥🔥"
    elif score >= 50:
        return "⚡⚡"
    elif score >= 40:
        return "⚡"
    else:
        return "❄️"


def get_danger_label(score: float) -> str:
    """Retourne le label textuel du danger"""
    if score >= 80:
        return "ULTRA DANGEREUX"
    elif score >= 70:
        return "TRÈS DANGEREUX"
    elif score >= 60:
        return "DANGEREUX"
    elif score >= 50:
        return "MODÉRÉ"
    elif score >= 40:
        return "FAIBLE"
    else:
        return "TRÈS FAIBLE"


def format_boost_percentage(boost: float) -> str:
    """Formate le boost en pourcentage avec signe"""
    percentage = (boost - 1.0) * 100
    if percentage > 0:
        return f"+{percentage:.0f}%"
    elif percentage < 0:
        return f"{percentage:.0f}%"
    else:
        return "neutre"


def display_prediction_result(result: dict, home_team: str, away_team: str):
    """
    Affiche les résultats de prédiction de manière détaillée et visuelle
    """
    if not result.get('success'):
        print(f"\n❌ ERREUR: {result.get('error', 'Unknown error')}")
        return
    
    details = result.get('details', {})
    bet = result.get('bet_recommendation', {})
    
    current_minute = result.get('current_minute', 0)
    current_score = result.get('current_score', '0-0')
    current_interval = result.get('current_interval', 'N/A')
    
    # En-tête
    print("\n")
    print("╔══════════════════════════════════════════════════════════════╗")
    print(f"║  🔴 {home_team:<20s} vs 🔵 {away_team:<20s}        ║")
    print(f"║  MIN {current_minute:2d}  |  Score: {current_score:5s}                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    print(f"\n⏰ INTERVALLE ACTUEL : {current_interval} min")
    
    # Scores de danger
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  🔥 DANGER SCORES COMBINÉS (Attaque + Défense adverse)     │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│                                                             │")
    
    # Home team
    home_score = details.get('home_score', 0)
    home_emoji = get_danger_emoji(home_score)
    home_label = get_danger_label(home_score)
    home_attack = details.get('home_attack_rate', 0)
    away_def_weak = details.get('away_defense_weakness', 0)
    home_boost = details.get('home_form_boost', 1.0)
    home_boost_str = format_boost_percentage(home_boost)
    
    print(f"│  🔴 {home_team:<18s} : {home_score:5.1f}/100  {home_emoji:10s} │")
    print(f"│     {home_label:<15s}                                      │")
    print(f"│     Attaque         : {home_attack:.2f} buts/match                        │")
    print(f"│     Déf adverse     : {away_def_weak:.2f} buts/match                        │")
    print(f"│     Forme boost     : ×{home_boost:.2f} ({home_boost_str})                         │")
    print("│                                                             │")
    
    # Away team
    away_score = details.get('away_score', 0)
    away_emoji = get_danger_emoji(away_score)
    away_label = get_danger_label(away_score)
    away_attack = details.get('away_attack_rate', 0)
    home_def_weak = details.get('home_defense_weakness', 0)
    away_boost = details.get('away_form_boost', 1.0)
    away_boost_str = format_boost_percentage(away_boost)
    
    print(f"│  🔵 {away_team:<18s} : {away_score:5.1f}/100  {away_emoji:10s} │")
    print(f"│     {away_label:<15s}                                      │")
    print(f"│     Attaque         : {away_attack:.2f} buts/match                        │")
    print(f"│     Déf adverse     : {home_def_weak:.2f} buts/match                        │")
    print(f"│     Forme boost     : ×{away_boost:.2f} ({away_boost_str})                         │")
    print("│                                                             │")
    print("└─────────────────────────────────────────────────────────────┘")
    
    # Ajustements
    saturation = details.get('saturation_factor', 1.0)
    sat_percentage = format_boost_percentage(saturation)
    total_goals = sum(map(int, current_score.split('-')))
    
    print(f"\n⚖️ AJUSTEMENTS DYNAMIQUES:")
    print(f"   Saturation      : ×{saturation:.2f} ({sat_percentage}) - {total_goals} buts déjà")
    
    # Recommandation
    confidence = bet.get('confidence', 'N/A')
    action = bet.get('action', 'N/A')
    likely_scorer = bet.get('likely_scorer', 'N/A')
    minutes_left = bet.get('minutes_left_in_interval', 0)
    
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  💡 RECOMMANDATION                                          │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│                                                             │")
    
    # Icône de recommandation
    if confidence in ['TRES HAUTE', 'HAUTE']:
        rec_icon = "✅"
    elif confidence == 'MOYENNE':
        rec_icon = "⚠️"
    else:
        rec_icon = "❌"
    
    print(f"│  {rec_icon} Confiance  : {confidence:<45s} │")
    print(f"│     Action     : {action[:45]:<45s} │")
    print(f"│     Scoreur    : {likely_scorer:<45s} │")
    print(f"│     Temps rest.: {minutes_left} min dans l'intervalle                   │")
    print("│                                                             │")
    print("└─────────────────────────────────────────────────────────────┘")
    
    # Probabilités individuelles
    home_prob = bet.get('home_goal_prob', '0%')
    away_prob = bet.get('away_goal_prob', '0%')
    
    print(f"\n📊 PROBABILITÉS DE BUT:")
    print(f"   {home_team:<20s} : {home_prob}")
    print(f"   {away_team:<20s} : {away_prob}")
    
    print("\n" + "="*64 + "\n")
