#!/usr/bin/env python3
"""
Module de formatage des alertes Telegram pour prédictions live
Affichage riche avec stats complètes, timing, patterns et momentum
"""

from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from live_predictor_v2 import LiveMatchContext, IntervalPrediction


class TelegramFormatter:
    """Formatte les prédictions pour affichage Telegram riche"""
    
    def __init__(self, db_path: str = "data/predictions.db"):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def format_match_info(self, context: LiveMatchContext) -> str:
        """
        Formatte les informations du match en cours
        
        Returns:
            Texte formaté avec émojis pour Telegram
        """
        lines = []
        lines.append("⚽ MATCH EN COURS")
        lines.append("=" * 50)
        lines.append(f"🏟️  {context.home_team} vs {context.away_team}")
        lines.append(f"⏱️  Minute : {context.current_minute}'")
        lines.append(f"📊 Score : {context.home_score}-{context.away_score}")
        lines.append("")
        
        # Stats live si disponibles
        if self._has_live_stats(context):
            lines.append("📈 STATS LIVE")
            lines.append("-" * 50)
            
            if context.possession_home is not None:
                lines.append(f"⚪ Possession : {context.possession_home:.0f}% - {context.possession_away:.0f}% ✓")
            
            if context.corners_home is not None:
                lines.append(f"🚩 Corners : {context.corners_home} - {context.corners_away} ✓")
            
            if context.shots_home is not None:
                total_shots_home = context.shots_home
                total_shots_away = context.shots_away
                lines.append(f"⚽ Total shots : {total_shots_home} - {total_shots_away} ✓")
            
            if context.shots_on_target_home is not None:
                lines.append(f"🎯 Shots on target : {context.shots_on_target_home} - {context.shots_on_target_away} ✓")
            
            if context.attacks_home is not None:
                lines.append(f"⚔️  Attacks : {context.attacks_home} - {context.attacks_away} ✓")
            
            if context.dangerous_attacks_home is not None:
                lines.append(f"🔥 Dangerous attacks : {context.dangerous_attacks_home} - {context.dangerous_attacks_away} ✓")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def format_prediction(self, 
                         prediction: IntervalPrediction,
                         team_name: str,
                         is_home: bool,
                         context: LiveMatchContext,
                         historical_prob: float) -> str:
        """
        Formatte une prédiction individuelle (HOME ou AWAY)
        
        Args:
            prediction: Résultat prédiction
            team_name: Nom de l'équipe
            is_home: True si domicile
            context: Contexte match
            historical_prob: Probabilité avant ajustement momentum
            
        Returns:
            Texte formaté avec émojis
        """
        lines = []
        
        # En-tête
        config = "HOME" if is_home else "AWAY"
        lines.append(f"📊 {team_name} ({config})")
        lines.append("-" * 50)
        
        # Probabilité finale avec delta
        prob_pct = prediction.probability * 100
        hist_pct = historical_prob * 100
        delta = prob_pct - hist_pct
        delta_str = f"{delta:+.1f}%" if delta != 0 else "="
        
        lines.append(f"🎯 Probabilité finale : {prob_pct:.1f}% ({delta_str} vs historique {hist_pct:.1f}%)")
        
        # Confiance avec fréquence
        confidence_emoji = self._get_confidence_emoji(prediction.confidence_level)
        freq_pct = prediction.freq_any_goal * 100
        lines.append(f"⭐ Confiance : {freq_pct:.1f}% ({prediction.confidence_level} {confidence_emoji})")
        
        # Récurrence
        if prediction.recurrence_last_5 is not None:
            rec_pct = prediction.recurrence_last_5 * 100
            rec_emoji = "✅" if prediction.recurrence_last_5 >= 0.6 else "⚠️"
            lines.append(f"🔄 Récurrence 5 derniers : {rec_pct:.0f}% {rec_emoji}")
        
        # Timing avec précision
        if prediction.avg_minute is not None:
            timing_str = self._format_timing(
                prediction.avg_minute,
                prediction.std_minute,
                prediction.interval_name
            )
            lines.append(timing_str)
        
        # Stats pattern détaillées
        lines.append("")
        lines.append("📈 STATISTIQUES PATTERN")
        lines.append(f"   • Fréquence globale : {prediction.matches_with_goal}/{prediction.total_matches} = {prediction.freq_any_goal*100:.0f}%")
        lines.append(f"   • Buts marqués : {prediction.goals_scored}")
        lines.append(f"   • Buts encaissés : {prediction.goals_conceded}")
        lines.append(f"   • Total buts : {prediction.goals_scored + prediction.goals_conceded}")
        
        # Force à domicile/extérieur (nouveau)
        force_info = self._get_team_strength(team_name, is_home, prediction.interval_name)
        if force_info:
            lines.append("")
            lines.append(force_info)
        
        lines.append("")
        
        return "\n".join(lines)
    
    def format_combined_prediction(self, 
                                   combined_prob: float,
                                   is_active: bool,
                                   interval_name: str) -> str:
        """
        Formatte la probabilité combinée avec signal
        
        Args:
            combined_prob: Probabilité combinée (0-1)
            is_active: True si intervalle actuellement actif
            interval_name: "31-45+" ou "75-90+"
            
        Returns:
            Texte formaté
        """
        lines = []
        lines.append("=" * 50)
        
        prob_pct = combined_prob * 100
        
        # Signal selon seuil (avec pourcentage)
        if prob_pct >= 90:
            signal = f"{prob_pct:.1f}% - 🟢 TRÈS FORT"
            recommendation = "✅ PARI FORTEMENT RECOMMANDÉ"
        elif prob_pct >= 75:
            signal = f"{prob_pct:.1f}% - 🟡 FORT"
            recommendation = "✓ Pari modéré possible"
        elif prob_pct >= 60:
            signal = f"{prob_pct:.1f}% - ⚪ MOYEN"
            recommendation = "⚠️  Prudence requise"
        else:
            signal = f"{prob_pct:.1f}% - 🔴 FAIBLE"
            recommendation = "❌ NE PAS PARIER"
        
        # Intervalle
        interval_status = "🚨 ACTIF" if is_active else "⏳ Prochain"
        lines.append(f"🎯 Intervalle {interval_name} ({interval_status})")
        lines.append(f"📡 Signal : {signal}")
        lines.append(f"💡 {recommendation}")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def format_top_patterns(self, 
                           country: str,
                           min_total_goals: int = 6,
                           limit: int = 5) -> str:
        """
        Formatte les meilleurs patterns du championnat
        
        Args:
            country: Pays (ex: "Bulgaria")
            min_total_goals: Minimum buts totaux requis
            limit: Nombre de patterns à afficher
            
        Returns:
            Texte formaté avec top patterns
        """
        query = '''
            SELECT 
                team_name,
                is_home,
                interval_name,
                freq_any_goal,
                goals_scored,
                goals_conceded,
                matches_with_any_goal,
                total_matches,
                any_goal_total
            FROM team_critical_intervals
            WHERE country = ?
                AND any_goal_total >= ?
            ORDER BY freq_any_goal DESC, any_goal_total DESC
            LIMIT ?
        '''
        
        self.cursor.execute(query, (country, min_total_goals, limit))
        results = self.cursor.fetchall()
        
        if not results:
            return "Aucun pattern trouvé"
        
        lines = []
        lines.append("🏆 MEILLEURS PATTERNS (≥6 buts totaux)")
        lines.append("=" * 50)
        
        for i, row in enumerate(results, 1):
            team, is_home, interval, freq, scored, conceded, matches_goal, total_matches, total_goals = row
            config = "HOME" if is_home else "AWAY"
            freq_pct = freq * 100
            
            line = (f"{i}. {team} {config} {interval} : {freq_pct:.0f}% "
                   f"({total_goals} buts sur {matches_goal} matches) - "
                   f"{scored} marqués + {conceded} encaissés")
            lines.append(line)
        
        lines.append("")
        return "\n".join(lines)
    
    def format_complete_alert(self,
                             context: LiveMatchContext,
                             predictions: Dict,
                             historical_probs: Dict[str, float]) -> str:
        """
        Formatte une alerte complète Telegram avec toutes les infos
        
        Args:
            context: Contexte match live
            predictions: Résultats prédictions (home_active, away_active, combined_active, etc.)
            historical_probs: Probabilités historiques avant momentum {'home': 0.89, 'away': 0.75}
            
        Returns:
            Message Telegram formaté complet
        """
        lines = []
        
        # 1. Info match
        lines.append(self.format_match_info(context))
        
        # 2. Prédictions individuelles
        if 'home_active' in predictions and predictions['home_active']:
            lines.append(self.format_prediction(
                predictions['home_active'],
                context.home_team,
                True,
                context,
                historical_probs.get('home', predictions['home_active'].freq_any_goal)
            ))
        
        if 'away_active' in predictions and predictions['away_active']:
            lines.append(self.format_prediction(
                predictions['away_active'],
                context.away_team,
                False,
                context,
                historical_probs.get('away', predictions['away_active'].freq_any_goal)
            ))
        
        # 3. Probabilité combinée (intervalle actif)
        if 'combined_active' in predictions:
            combined = predictions['combined_active']
            lines.append(self.format_combined_prediction(
                combined['probability'],
                is_active=True,
                interval_name=combined['interval']
            ))
        
        # 4. Probabilité combinée (prochain intervalle)
        if 'combined_next' in predictions:
            combined = predictions['combined_next']
            lines.append("\n" + self.format_combined_prediction(
                combined['probability'],
                is_active=False,
                interval_name=combined['interval']
            ))
        
        # 4. Top patterns du championnat
        lines.append("")
        lines.append(self.format_top_patterns(context.country))
        
        return "\n".join(lines)
    
    # === MÉTHODES AUXILIAIRES ===
    
    def _has_live_stats(self, context: LiveMatchContext) -> bool:
        """Vérifie si stats live disponibles"""
        return any([
            context.possession_home is not None,
            context.corners_home is not None,
            context.shots_home is not None,
            context.shots_on_target_home is not None,
            context.attacks_home is not None,
            context.dangerous_attacks_home is not None
        ])
    
    def _get_confidence_emoji(self, confidence: str) -> str:
        """Retourne emoji selon niveau confiance"""
        emojis = {
            "EXCELLENT": "🔥",
            "TRES_BON": "✨",
            "BON": "👍",
            "MOYEN": "⚠️",
            "FAIBLE": "❌"
        }
        return emojis.get(confidence, "")
    
    def _format_timing(self, 
                      avg_minute: float,
                      std_minute: Optional[float],
                      interval_name: str) -> str:
        """
        Formatte le timing avec précision
        
        Returns:
            Ex: "⏰ Timing : Minute 83.8 (±6.5) → Buts entre 77'-90' ⚠️ Variable"
        """
        # Bornes intervalle
        if interval_name == "31-45+":
            interval_min, interval_max = 31, 45
        else:  # 75-90+
            interval_min, interval_max = 75, 90
        
        base = f"⏰ Timing : Minute {avg_minute:.1f}"
        
        if std_minute is not None:
            # Plage attendue
            min_range = max(avg_minute - std_minute, interval_min)
            max_range = min(avg_minute + std_minute, interval_max)
            
            base += f" (±{std_minute:.1f}) → Buts entre {min_range:.0f}'-{max_range:.0f}'"
            
            # Indication précision
            if std_minute < 4:
                base += " 💡 TRÈS PRÉCIS !"
            elif std_minute > 6:
                base += " ⚠️ Variable"
        
        return base
    
    def _get_team_strength(self, 
                          team_name: str,
                          is_home: bool,
                          interval_name: str) -> Optional[str]:
        """
        Analyse la force de l'équipe dans sa configuration
        
        Returns:
            Ex: "💪 FORCE À DOMICILE : 89% (8/9 matches) - Excellent en fin de match"
        """
        # Récupérer stats globales (tous intervalles)
        query = '''
            SELECT 
                interval_name,
                freq_any_goal,
                matches_with_any_goal,
                total_matches,
                avg_goals_full_match,
                avg_goals_first_half,
                avg_goals_second_half
            FROM team_critical_intervals
            WHERE team_name = ? AND is_home = ?
        '''
        
        self.cursor.execute(query, (team_name, is_home))
        results = self.cursor.fetchall()
        
        if not results:
            return None
        
        # Calculer fréquence moyenne sur tous intervalles
        total_freq = sum(row[1] for row in results) / len(results)
        total_matches = results[0][3] if results else 0
        
        # Calculer matches avec but sur tous intervalles
        total_matches_with_goal = sum(row[2] for row in results)
        
        config = "DOMICILE" if is_home else "EXTÉRIEUR"
        
        # Déterminer force avec pourcentage
        if total_freq >= 0.65:
            strength = f"{total_freq*100:.1f}% - 💪 TRÈS FORT"
        elif total_freq >= 0.50:
            strength = f"{total_freq*100:.1f}% - 👍 FORT"
        elif total_freq >= 0.40:
            strength = f"{total_freq*100:.1f}% - ⚪ MOYEN"
        else:
            strength = f"{total_freq*100:.1f}% - ⚠️ FAIBLE"
        
        # Moyennes buts
        avg_full = results[0][4] if results and results[0][4] else 0
        avg_1st = results[0][5] if results and results[0][5] else 0
        avg_2nd = results[0][6] if results and results[0][6] else 0
        
        lines = []
        lines.append(f"💪 FORCE À {config} : {strength}")
        lines.append(f"   • Ratio global : {total_matches_with_goal}/{total_matches*len(results)} matches avec but ({total_freq*100:.1f}%)")
        lines.append(f"   • Moyenne buts/match : {avg_full:.1f} (1ère MT: {avg_1st:.1f}, 2nde MT: {avg_2nd:.1f})")
        
        # Spécialité par intervalle avec pourcentage
        best_interval = max(results, key=lambda x: x[1])
        if best_interval[1] >= 0.60:
            interval_label = "fin 1ère MT" if best_interval[0] == "31-45+" else "fin de match"
            lines.append(f"   • ⭐ Excellent en {interval_label} ({best_interval[1]*100:.0f}%)")
        
        return "\n".join(lines)
    
    def close(self):
        """Ferme connexion DB"""
        if self.conn:
            self.conn.close()


# === FONCTION DE DÉMONSTRATION ===

def demo_telegram_formatter():
    """Démonstration du formatage Telegram"""
    from live_predictor_v2 import LivePredictorV2, LiveMatchContext
    
    # Créer contexte match
    context = LiveMatchContext(
        home_team="Spartak Varna",
        away_team="Slavia Sofia",
        current_minute=78,
        home_score=1,
        away_score=1,
        country="Bulgaria",
        league="bulgaria",
        # Stats live
        possession_home=55.0,
        possession_away=45.0,
        shots_home=8,
        shots_away=5,
        shots_on_target_home=4,
        shots_on_target_away=2,
        attacks_home=36,
        attacks_away=28,
        dangerous_attacks_home=12,
        dangerous_attacks_away=8,
        corners_home=4,
        corners_away=2
    )
    
    # Générer prédictions
    predictor = LivePredictorV2()
    predictions = predictor.predict(context)
    
    # Probs historiques (avant momentum)
    historical_probs = {
        'home': 0.89,
        'away': 0.75
    }
    
    # Formatter
    formatter = TelegramFormatter()
    
    # Générer message complet
    message = formatter.format_complete_alert(context, predictions, historical_probs)
    
    print("=" * 60)
    print("📱 APERÇU MESSAGE TELEGRAM")
    print("=" * 60)
    print(message)
    print("=" * 60)
    
    # Cleanup
    formatter.close()
    predictor.close()


if __name__ == "__main__":
    demo_telegram_formatter()
