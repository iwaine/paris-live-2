def print_fictive_live_match():
    print("""
=============== LIVE MATCH =================
URL : https://www.soccerstats.com/pmatch.asp?league=bolivia&stats=227-3-7-2025 | minute : 48 | Nacional Potosi 1 – 0 ABB

--- PATTERNS HISTORIQUES ---
Nacional Potosi HOME 75-90+ : 76.9% (16 buts sur 13 matches) - 9 marqués + 7 encaissés | But récurrent (avec but) : 1.60 | Min but: 86.1 SEM: 0.99 IQR: [79; 90]
  Moyenne buts MT1: 1.46 SEM: 0.33 | MT2: 2.00 SEM: 0.25
    → Récurrence globale : 76.9% sur 13 matchs
    → Meilleure récurrence récente : 80.0% (fenêtre 5)
    → Score combiné (moyenne) : 78.5%
ABB AWAY 75-90+ : 69.2% (12 buts sur 13 matches) - 5 marqués + 7 encaissés | But récurrent (avec but) : 1.33 | Min but: 83.3 SEM: 1.52 IQR: [75; 90]
  Moyenne buts MT1: 1.69 SEM: 0.33 | MT2: 2.08 SEM: 0.33
    → Récurrence globale : 69.2% sur 13 matchs
    → Meilleure récurrence récente : 75.0% (fenêtre 4)
    → Score combiné (moyenne) : 72.1%
[Proba au moins un but dans l'intervalle] : 92.9%

--- STATISTIQUES IN-PLAY ---
  Possession : 69.0% / 31.0%
  Total tirs : 6 / 3
  Tirs cadrés : 1 / 1
  Shots inside box : 6 / 0
  Shots outside box : 0 / 3
  Attaques : 60 / 20
  Attaques dangereuses : 11 / 3

--- SCORING DÉTAILLÉ ---
[Pattern utilisé] : Nacional Potosi (HOME)

[Patterns historiques] : 76.9%
[Saturation] : 94.1%
[Potentiel restant élevé (score live 1 / attendu 2.04) — il reste du potentiel, peu de buts ont été marqués par rapport à l'attendu.] (pondérée sur patterns)
→ Score historique pondéré : 72.4%

→ Score pattern chaud (but imminent) : 32.4%
→ Score in-play pondéré (intensité) : 32.4%

[SCORE FINAL] : 64.4%
[RECOMMANDATION] : À surveiller
""")

if __name__ == "__main__":
    print_fictive_live_match()
