#!/usr/bin/env python3
# ============================================================================
# PARIS LIVE - SCORING DEBUGGER
# ============================================================================
# Test le scoring et la prise de décision avec des données personnalisées
# ============================================================================

import sys
import math
from datetime import datetime

sys.path.insert(0, '/workspaces/paris-live/football-live-prediction')

def calculate_ttl_decay(signal_age_seconds: float, ttl: float = 300) -> float:
    """Calcule la décroissance exponentielle TTL"""
    return math.exp(-signal_age_seconds / ttl)

def test_scoring_example(
    minute: int,
    danger_score_raw: float,
    signal_age_seconds: float = 15,
    is_penalty_active: bool = False,
    confidence_threshold: float = 0.50,
    danger_threshold: float = 0.50
) -> dict:
    """
    Teste le scoring avec des données personnalisées
    
    Args:
        minute: Minute du match
        danger_score_raw: Score brut du modèle ML (0-100)
        signal_age_seconds: Âge du signal en secondes
        is_penalty_active: Si un penalty est actif
        confidence_threshold: Seuil de confiance (Conservative: 50%)
        danger_threshold: Seuil de danger (Conservative: 50%)
    """
    
    print("\n" + "="*80)
    print(f"🎯 SCORING TEST - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    # === ÉTAPE 1: ENTRÉE ===
    print("\n[ÉTAPE 1] INPUT")
    print(f"  - Minute: {minute}")
    print(f"  - Danger Score (brut): {danger_score_raw:.1f}%")
    print(f"  - Signal Age: {signal_age_seconds:.0f}s")
    print(f"  - Penalty Active: {'OUI' if is_penalty_active else 'NON'}")
    
    # === ÉTAPE 2: VÉRIFIER INTERVAL ===
    print("\n[ÉTAPE 2] VÉRIFICATION INTERVAL")
    in_interval = (30 <= minute <= 45) or (75 <= minute <= 90)
    interval_str = "(30-45)" if 30 <= minute <= 45 else "(75-90)" if 75 <= minute <= 90 else "HORS INTERVAL"
    interval_status = "✅ PASS" if in_interval else "❌ FAIL"
    print(f"  - Minute {minute} dans {interval_str}: {interval_status}")
    
    if not in_interval:
        return {
            'decision': 'SKIP',
            'reason': f'MINUTE_OUT_OF_RANGE ({minute} not in [30-45] or [75-90])',
            'danger_score': danger_score_raw,
            'confidence': 0,
        }
    
    # === ÉTAPE 3: APPLIQUER PÉNALITÉ PENALTY ===
    print("\n[ÉTAPE 3] PÉNALITÉ PENALTY")
    danger_score_adjusted = danger_score_raw
    if is_penalty_active:
        danger_score_adjusted = danger_score_raw * 0.5
        print(f"  - Penalty actif: {danger_score_raw:.1f}% → {danger_score_adjusted:.1f}% (×0.5)")
    else:
        print(f"  - Pas de penalty: {danger_score_raw:.1f}% (inchangé)")
    
    # === ÉTAPE 4: APPLIQUER TTL DECAY ===
    print("\n[ÉTAPE 4] DÉCROISSANCE EXPONENTIELLE TTL")
    freshness_factor = calculate_ttl_decay(signal_age_seconds)
    confidence_after_ttl = (danger_score_adjusted / 100) * freshness_factor
    danger_score_after_ttl = danger_score_adjusted * freshness_factor
    
    print(f"  - TTL Coefficient: e^(-{signal_age_seconds:.0f}/300) = {freshness_factor:.4f}")
    print(f"  - Danger Score: {danger_score_adjusted:.1f}% × {freshness_factor:.4f} = {danger_score_after_ttl:.1f}%")
    print(f"  - Confidence: {danger_score_adjusted:.1f}% × {freshness_factor:.4f} = {confidence_after_ttl:.1%}")
    
    # === ÉTAPE 5: VÉRIFIER SEUILS ===
    print("\n[ÉTAPE 5] VÉRIFICATION SEUILS (Conservative)")
    print(f"  - Confidence threshold: {confidence_threshold:.0%}")
    print(f"  - Danger threshold: {danger_threshold:.0%}")
    print(f"  - Confidence actuelle: {confidence_after_ttl:.1%} {'✅' if confidence_after_ttl >= confidence_threshold else '❌'}")
    print(f"  - Danger actuelle: {danger_score_after_ttl:.1f}% {'✅' if danger_score_after_ttl >= (danger_threshold * 100) else '❌'}")
    
    # === ÉTAPE 6: PRISE DE DÉCISION ===
    print("\n[ÉTAPE 6] PRISE DE DÉCISION")
    
    reason = ""
    should_bet = False
    
    if is_penalty_active:
        reason = "MARKET_SUSPENDED (Penalty active)"
    elif signal_age_seconds > 300:
        reason = f"SIGNAL_STALE ({signal_age_seconds:.0f}s > 300s)"
    elif confidence_after_ttl < confidence_threshold:
        reason = f"LOW_CONFIDENCE ({confidence_after_ttl:.1%} < {confidence_threshold:.0%})"
    elif danger_score_after_ttl < (danger_threshold * 100):
        reason = f"LOW_DANGER ({danger_score_after_ttl:.1f}% < {danger_threshold*100:.0f}%)"
    else:
        reason = "BETTING_SIGNAL_ACTIVE ✅"
        should_bet = True
    
    decision = "BUY ✅" if should_bet else "SKIP ❌"
    print(f"  - Raison: {reason}")
    print(f"  - DÉCISION FINALE: {decision}")
    
    if should_bet:
        print(f"\n  💰 ACTION: Alerte Telegram envoyée")
        print(f"     'Au moins 1 but attendu (Danger: {danger_score_after_ttl:.1f}%, Confiance: {confidence_after_ttl:.1%})'")
    else:
        print(f"\n  ⏳ ACTION: Aucune alerte (attendre)")
    
    # === RÉSUMÉ FINAL ===
    result = {
        'decision': decision.split()[0],  # 'BUY' ou 'SKIP'
        'reason': reason,
        'should_bet': should_bet,
        'danger_score': danger_score_after_ttl,
        'confidence': confidence_after_ttl,
        'freshness_factor': freshness_factor,
        'minute': minute,
        'interval': (30, 45) if 30 <= minute <= 45 else (75, 90),
    }
    
    return result


def main():
    """Menu d'test interactif"""
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + " "*20 + "PARIS LIVE - SCORING DEBUGGER" + " "*29 + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Exemples prédéfinis
    examples = {
        '1': {
            'name': 'PSG 2-1 Marseille (Minute 38, Excellent)',
            'minute': 38,
            'danger_score_raw': 68,
            'signal_age_seconds': 15,
            'is_penalty_active': False,
        },
        '2': {
            'name': 'Lyon 1-0 Monaco (Minute 42, Faible)',
            'minute': 42,
            'danger_score_raw': 35,
            'signal_age_seconds': 45,
            'is_penalty_active': False,
        },
        '3': {
            'name': 'Real 3-2 Barcelona (Minute 80, Très bon)',
            'minute': 80,
            'danger_score_raw': 75,
            'signal_age_seconds': 5,
            'is_penalty_active': False,
        },
        '4': {
            'name': 'Liverpool 1-1 Man City (Minute 38, Penalty actif)',
            'minute': 38,
            'danger_score_raw': 70,
            'signal_age_seconds': 10,
            'is_penalty_active': True,
        },
        '5': {
            'name': 'Juventus 0-0 Milan (Minute 38, Signal vieux)',
            'minute': 38,
            'danger_score_raw': 65,
            'signal_age_seconds': 350,
            'is_penalty_active': False,
        },
    }
    
    print("\nExemples prédéfinis:")
    print("─" * 80)
    for key, example in examples.items():
        print(f"  {key}. {example['name']}")
    
    print("\n" + "─" * 80)
    choice = input("\nChoisir un exemple (1-5) ou 'custom' pour personnalisé: ").strip()
    
    if choice in examples:
        params = examples[choice]
        print(f"\n📝 Exemple sélectionné: {params['name']}")
        test_scoring_example(**{k: v for k, v in params.items() if k != 'name'})
    
    elif choice.lower() == 'custom':
        print("\n🎯 TEST PERSONNALISÉ")
        print("─" * 80)
        
        try:
            minute = int(input("Minute du match (0-90): "))
            danger_raw = float(input("Danger Score brut (0-100): "))
            signal_age = float(input("Âge du signal en secondes (0-600): "))
            penalty_str = input("Penalty actif? (oui/non): ").lower()
            is_penalty = penalty_str in ['oui', 'yes', 'y', '1']
            
            test_scoring_example(
                minute=minute,
                danger_score_raw=danger_raw,
                signal_age_seconds=signal_age,
                is_penalty_active=is_penalty
            )
        except ValueError as e:
            print(f"❌ Erreur: {e}")
    
    else:
        print("❌ Choix invalide")
    
    print("\n" + "="*80)
    print("✅ Test terminé")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
