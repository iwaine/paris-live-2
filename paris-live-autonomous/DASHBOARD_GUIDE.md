# 🌐 DASHBOARD WEB - Guide Complet

## 📊 Interface Graphique Temps Réel

Le **Dashboard Web** est une interface graphique moderne pour visualiser et contrôler le système de monitoring en temps réel.

---

## 🚀 Lancement Rapide

### Option 1 : Via le menu
```bash
./start.sh
# Choisir option 1
```

### Option 2 : Directement
```bash
./start_dashboard.sh
```

### Option 3 : Commande Python
```bash
python3 dashboard_web.py
```

**URL d'accès :**
- **Local** : http://localhost:5000
- **Réseau** : http://[VOTRE_IP]:5000

---

## 🎨 Fonctionnalités

### 1️⃣ **Vue d'ensemble en temps réel**
- 📊 **4 statistiques principales**
  - Nombre de scans effectués
  - Matchs détectés
  - Signaux envoyés
  - Probabilité moyenne

### 2️⃣ **Liste des matchs live**
- ⚽ Affichage des matchs en cours
- 🎯 Score actuel
- ⏱️ Minute du match
- 📈 Probabilité de but
- 🏆 Ligue
- 🔵 Intervalle surveillé (31-45' ou 76-90')
- ✅ Badge "Signal Qualifié" si ≥65%

### 3️⃣ **Graphique d'évolution**
- 📈 Courbes de probabilité en temps réel
- 🔄 Mise à jour toutes les 60 secondes
- 🎨 Couleur unique par match
- 📊 Historique des 20 derniers points

### 4️⃣ **Contrôles interactifs**
- ▶️ **Démarrer** le monitoring
- ⏹️ **Arrêter** le monitoring
- 🟢 Indicateur de statut (actif/inactif)

---

## 🎯 Utilisation

### Démarrage du monitoring

1. **Ouvrir le dashboard** : http://localhost:5000
2. **Cliquer sur "▶️ Démarrer"**
3. **Observer les mises à jour** automatiques toutes les 60s

### Arrêt du monitoring

1. **Cliquer sur "⏹️ Arrêter"**
2. **Ou** fermer le navigateur et arrêter le serveur (Ctrl+C dans le terminal)

---

## 📱 Interface

### Exemple d'affichage d'un match :

```
┌─────────────────────────────────────────────────────────┐
│ PSG vs Marseille                           1 - 0        │
├─────────────────────────────────────────────────────────┤
│ Ligue: France Ligue 1                                   │
│ Minute: 78'                                             │
│ Intervalle: 76-90                                       │
│ Probabilité: 72.5%                                      │
│                                                         │
│ ✅ Signal Qualifié                                      │
└─────────────────────────────────────────────────────────┘
```

### Statistiques affichées :

- **🔍 Scans** : Nombre de cycles de scraping effectués
- **⚽ Matchs détectés** : Nombre de matchs live trouvés
- **🚨 Signaux envoyés** : Nombre d'alertes envoyées (≥65%)
- **📊 Prob. moyenne** : Probabilité moyenne de tous les signaux

---

## 🔄 Mise à jour automatique

Le dashboard se met à jour **automatiquement** grâce à WebSocket :

- ✅ Pas besoin de rafraîchir la page
- ✅ Mises à jour en temps réel
- ✅ Synchronisation avec le serveur

**Fréquence :** Toutes les 60 secondes

---

## 🛠️ Architecture Technique

### Backend (Flask + Socket.IO)
```python
dashboard_web.py
├─ Flask (serveur web)
├─ Flask-SocketIO (WebSocket temps réel)
├─ DashboardMonitor (scraping en arrière-plan)
└─ API REST
    ├─ /api/status (état du système)
    ├─ /api/matches (matchs live)
    ├─ /api/signals (historique)
    └─ /api/whitelists (statistiques)
```

### Frontend (HTML + JavaScript)
```javascript
templates/dashboard.html
├─ Chart.js (graphiques)
├─ Socket.IO client (temps réel)
└─ CSS moderne (design responsive)
```

### Communication temps réel (WebSocket)
```
Client ←→ Server
  │         │
  ├─ 'connect' → Connexion établie
  ├─ 'start_monitoring' → Démarre le monitoring
  ├─ 'stop_monitoring' → Arrête le monitoring
  │         │
  │    ←── 'matches_update' (toutes les 60s)
  │    ←── 'monitoring_status' (changement statut)
  └────┴──── 'signal_added' (nouveau signal)
```

---

## 📊 API REST

### GET /api/status
**Retourne l'état du système**
```json
{
  "monitoring_active": true,
  "last_update": "2025-12-06T00:05:30",
  "stats": {
    "total_scans": 15,
    "matches_detected": 2,
    "signals_sent": 1,
    "avg_probability": 72.5
  },
  "predictors_available": true
}
```

### GET /api/matches
**Retourne les matchs live**
```json
{
  "matches": [
    {
      "id": "france_psg_marseille",
      "league": "france",
      "home_team": "PSG",
      "away_team": "Marseille",
      "home_score": 1,
      "away_score": 0,
      "minute": 78,
      "probability": 72.5,
      "interval": "76-90",
      "status": "qualified"
    }
  ],
  "count": 1
}
```

### GET /api/whitelists
**Retourne les statistiques des whitelists**
```json
{
  "france": {
    "name": "France Ligue 1",
    "teams_count": 10,
    "threshold": 65,
    "min_matches": 4
  },
  ...
}
```

---

## 🎨 Personnalisation

### Modifier le port (par défaut 5000)

```python
# dashboard_web.py (ligne finale)
socketio.run(app, host='0.0.0.0', port=8080)  # Changer 5000 → 8080
```

### Modifier la fréquence de mise à jour

```python
# dashboard_web.py (dans _monitor_loop)
for _ in range(30):  # 30s au lieu de 60s
    if not self.running:
        break
    time.sleep(1)
```

### Modifier le design

```html
<!-- templates/dashboard.html -->
<!-- Modifier les styles CSS dans la section <style> -->
```

---

## 🔒 Sécurité

⚠️ **Important** : Le dashboard est en mode **développement**

### Pour la production :

1. **Utiliser un serveur WSGI** (gunicorn)
```bash
pip install gunicorn
gunicorn --worker-class eventlet -w 1 dashboard_web:app --bind 0.0.0.0:5000
```

2. **Ajouter une authentification**
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == 'admin' and password == 'secret':
        return username
```

3. **Utiliser HTTPS** (certificat SSL)

---

## 🆘 Dépannage

### Problème : "Address already in use"
```bash
# Trouver le processus sur le port 5000
lsof -i :5000

# Tuer le processus
kill -9 [PID]
```

### Problème : "Module 'flask' not found"
```bash
pip install flask flask-socketio
```

### Problème : Dashboard ne se met pas à jour
1. Vérifier que le monitoring est démarré (bouton ▶️)
2. Vérifier la console du navigateur (F12)
3. Vérifier les logs du serveur

---

## 📱 Accès depuis un autre appareil

### Sur le même réseau local :

1. **Trouver l'IP de votre machine**
```bash
# macOS/Linux
hostname -I

# Résultat : 192.168.1.50
```

2. **Ouvrir sur smartphone/tablette**
```
http://192.168.1.50:5000
```

---

## ✨ Améliorations futures possibles

- 🔔 **Notifications push** (navigateur)
- 📧 **Export des signaux** (CSV/JSON)
- 📊 **Statistiques avancées** (taux de réussite)
- 🎯 **Filtres** (par ligue, équipe, probabilité)
- 🌓 **Mode sombre**
- 📱 **Application mobile** (PWA)
- 🔐 **Authentification** multi-utilisateurs
- 💾 **Historique persistant** (base de données)

---

## 📚 Ressources

- **Flask** : https://flask.palletsprojects.com/
- **Flask-SocketIO** : https://flask-socketio.readthedocs.io/
- **Chart.js** : https://www.chartjs.org/
- **Socket.IO** : https://socket.io/

---

**🎉 Profitez du dashboard en temps réel !**
