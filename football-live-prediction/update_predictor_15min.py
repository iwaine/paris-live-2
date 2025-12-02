"""Mise à jour du predictor pour intervalles 15min"""

with open('predictors/interval_predictor.py', 'r') as f:
    content = f.read()

# Remplacer determine_current_interval
old_method = """    def determine_current_interval(self, current_minute: int) -> str:
        \"\"\"Détermine l'intervalle ACTUEL (où on est maintenant)\"\"\"
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
            return None"""

new_method = """    def determine_current_interval(self, current_minute: int) -> str:
        \"\"\"Détermine l'intervalle ACTUEL de 15min (où on est maintenant)\"\"\"
        if 0 <= current_minute <= 15:
            return "0-15"
        elif 16 <= current_minute <= 30:
            return "16-30"
        elif 31 <= current_minute <= 45:
            return "31-45"
        elif 46 <= current_minute <= 60:
            return "46-60"
        elif 61 <= current_minute <= 75:
            return "61-75"
        elif 76 <= current_minute <= 90:
            return "76-90"
        else:
            return None"""

content = content.replace(old_method, new_method)

with open('predictors/interval_predictor.py', 'w') as f:
    f.write(content)

print("✅ Predictor mis à jour pour intervalles 15min")
