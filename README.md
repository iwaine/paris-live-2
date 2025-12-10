# paris-live

## Système de Prédiction Live Football

Système intelligent de prédiction de buts sur matchs live avec monitoring Telegram.

### 🎯 Fonctionnalités principales

- **Prédicteur hybride** : 80% patterns historiques + 20% momentum live
- **Ajustement saturation** : Modulation selon nombre de buts déjà marqués ([docs](SATURATION_FEATURE.md))
- **Scraper live** : Détection temps réel scores/minutes/équipes
- **Alertes Telegram** : Notifications sur prédictions haute probabilité
- **Multi-championnats** : Bulgarie, Pays-Bas, France (extensible)

### 📚 Documentation

- **[Guide complet](METHODOLOGIE_COMPLETE_V2.md)** : Méthodologie et algorithmes
- **[Saturation](SATURATION_FEATURE.md)** : Intelligence contextuelle buts
- **[Déploiement](DEPLOYMENT_COMPLETE.md)** : Configuration production
- **[Quick Start](QUICK_START_v2.md)** : Lancement rapide

### 🚀 Démarrage rapide

```bash
# Lancer monitoring avec alertes Telegram
./start_live_alerts.sh both
```
