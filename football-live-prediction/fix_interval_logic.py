"""Correction: analyser l'intervalle ACTUEL, pas le suivant"""

with open('predictors/interval_predictor.py', 'r') as f:
    content = f.read()

# Remplacer determine_next_interval par determine_current_interval
old_method = '''    def determine_next_interval(self, current_minute: int) -> str:
        """Détermine l'intervalle suivant basé sur la minute actuelle"""
        if current_minute < 10:
            return "11-20"
        elif current_minute < 20:
            return "21-30"
        elif current_minute < 30:
            return "31-40"
        elif current_minute < 40:
            return "41-50"
        elif current_minute < 50:
            return "51-60"
        elif current_minute < 60:
            return "61-70"
        elif current_minute < 70:
            return "71-80"
        elif current_minute < 80:
            return "81-90"
        else:
            return None'''

new_method = '''    def determine_current_interval(self, current_minute: int) -> str:
        """Détermine l'intervalle ACTUEL (où on est maintenant)"""
        if 1 <= current_minute <= 10:
            return "1-10"
        elif 11 <= current_minute <= 20:
            return "11-20"
        elif 21 <= current_minute <= 30:
            return "21-30"
        elif 31 <= current_minute <= 40:
            return "31-40"
        elif 41 <= current_minute <= 50:
            return "41-50"
        elif 51 <= current_minute <= 60:
            return "51-60"
        elif 61 <= current_minute <= 70:
            return "61-70"
        elif 71 <= current_minute <= 80:
            return "71-80"
        elif 81 <= current_minute <= 90:
            return "81-90"
        else:
            return None'''

content = content.replace(old_method, new_method)

# Remplacer les appels
content = content.replace(
    'next_interval = self.determine_next_interval(current_minute)',
    'current_interval = self.determine_current_interval(current_minute)'
)

content = content.replace(
    "if not next_interval:",
    "if not current_interval:"
)

content = content.replace(
    "'next_interval': next_interval,",
    "'current_interval': current_interval,"
)

# Dans le message
content = content.replace(
    'f"Predicting: {home_team} vs {away_team} @ {current_minute}\'"',
    'f"Analyzing CURRENT interval: {home_team} vs {away_team} @ {current_minute}\'"'
)

with open('predictors/interval_predictor.py', 'w') as f:
    f.write(content)

print("✅ Logique corrigée: analyse l'intervalle ACTUEL")
print("   Minute 62' → Intervalle 61-70 (on est dedans)")
