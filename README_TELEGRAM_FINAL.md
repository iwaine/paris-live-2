# 📱 SYSTÈME D'ALERTES TELEGRAM - OPÉRATIONNEL ✅

## 🎉 FÉLICITATIONS !

Votre système d'alertes Telegram est **100% fonctionnel** !

---

## 🚀 DÉMARRAGE RAPIDE

### Lancer les alertes (2 championnats)
```bash
cd /workspaces/paris-live
./start_live_alerts.sh both
```

### Ou par championnat
```bash
./start_live_alerts.sh bulgaria     # Bulgarie uniquement
./start_live_alerts.sh netherlands  # Pays-Bas uniquement
```

---

## 📊 COMMENT ÇA MARCHE

1. **Scan automatique** toutes les 60 secondes
2. **Détection** matches bulgares/néerlandais en cours
3. **Analyse** : 80% pattern + 20% momentum live
4. **Alerte Telegram** si probabilité ≥ 80% ET intervalle critique actif

---

## 📱 FORMAT ALERTE

```
🚨 ALERTE PAYS-BAS 🇳🇱

Vitesse Arnhem vs De Graafschap
⏱️ Minute 45 | Score: 1-1

⚡ INTERVALLE 31-45 ACTIF

📊 PROBABILITÉS:
  �� Vitesse Arnhem: 81.8%
  ✈️ De Graafschap: 91.9%
  🎯 COMBINÉ: 98.5%

🟢 SIGNAL TRÈS FORT
💡 Pari fortement recommandé

🔗 Lien match
```

---

## ⚙️ CONFIGURATION

**Fichier** : `telegram_config.py`

```python
TELEGRAM_BOT_TOKEN = "8085055094:AAG2Dn..."  ✅
TELEGRAM_CHAT_ID = "6942358056"              ✅
ALERT_THRESHOLD_COMBINED = 0.80   # 80%
ALERT_THRESHOLD_SINGLE = 0.75     # 75%
ALERTS_ENABLED = True
```

---

## 🧪 TESTER

```bash
# Test envoi Telegram
python3 /workspaces/paris-live/telegram_notifier.py

# Scan unique (sans mode continu)
cd football-live-prediction
python3 netherlands_live_monitor.py --once
```

---

## 🛑 ARRÊTER

`Ctrl+C` dans le terminal ou :
```bash
ps aux | grep live_monitor
kill <PID>
```

---

## 📈 STATISTIQUES

- **642 matches** analysés
- **144 patterns** générés
- **26 patterns EXCELLENT** (très fiables)
- **2 championnats** surveillés

---

## 🔒 SÉCURITÉ

⚠️ `telegram_config.py` est dans `.gitignore` - Ne jamais commit !

---

**Status** : 🟢 PRODUCTION  
**Date** : 4 Décembre 2025
