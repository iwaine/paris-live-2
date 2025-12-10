#!/bin/bash
#
# Workflow complet : Scraping → Génération whitelist → Monitoring optimisé
# À exécuter chaque semaine pour mettre à jour les patterns
#

echo "🚀 WORKFLOW COMPLET - MISE À JOUR HEBDOMADAIRE"
echo "======================================================================"
echo ""

# 1. SCRAPING des nouvelles données
echo "📥 ÉTAPE 1/4 : Scraping des matchs récents..."
echo "----------------------------------------------------------------------"
echo "   → Scraping toutes les ligues suivies..."
python3 scrape_all_leagues_auto.py --league france --workers 2
python3 scrape_all_leagues_auto.py --league germany --workers 2
python3 scrape_all_leagues_auto.py --league england --workers 2
python3 scrape_all_leagues_auto.py --league netherlands2 --workers 2
python3 scrape_all_leagues_auto.py --league bolivia --workers 2
python3 scrape_all_leagues_auto.py --league bulgaria --workers 2
python3 scrape_all_leagues_auto.py --league portugal --workers 2
echo ""

# 2. CALCUL des patterns historiques
echo "📊 ÉTAPE 2/4 : Calcul des patterns historiques..."
echo "----------------------------------------------------------------------"
python3 football-live-prediction/build_team_recurrence_stats.py
echo ""

# 3. GÉNÉRATION des whitelists
echo "🎯 ÉTAPE 3/4 : Génération whitelists équipes performantes..."
echo "----------------------------------------------------------------------"
echo "   → Génération pour TOUTES les ligues (seuil 65%, min 4 matchs)..."
python3 generate_top_teams_whitelist.py --all --threshold 65 --min-matches 4
echo ""

# 4. AFFICHAGE du résumé
echo "✅ ÉTAPE 4/4 : Résumé des whitelists"
echo "----------------------------------------------------------------------"
if [ -d "whitelists" ]; then
    whitelist_count=$(ls whitelists/*_whitelist.json 2>/dev/null | wc -l)
    echo "✓ Whitelists générées : $whitelist_count ligues"
    echo "✓ Dossier : whitelists/"
    echo "✓ Date : $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "📋 Fichiers créés :"
    ls -lh whitelists/*.json | awk '{print "   - " $9 " (" $5 ")"}'
else
    echo "❌ Erreur : Dossier whitelists non trouvé"
fi

echo ""
echo "======================================================================"
echo "✅ WORKFLOW TERMINÉ"
echo "======================================================================"
echo ""
echo "📌 PROCHAINES ÉTAPES :"
echo "   1. Vérifier whitelists/*.json (7 ligues)"
echo "   2. Lancer le monitoring optimisé :"
echo "      python3 live_monitor_optimized.py --use-whitelist"
echo ""
echo "📊 LIGUES SUIVIES :"
echo "   🇫🇷 France  🇩🇪 Germany  🇩🇪 Germany2  🏴󠁧󠁢󠁥󠁮󠁧󠁿 England"
echo "   🇳🇱 Netherlands2  🇧🇴 Bolivia  🇧🇬 Bulgaria"
echo ""
echo "🔄 À relancer chaque semaine après les matchs du weekend"
echo "======================================================================"
