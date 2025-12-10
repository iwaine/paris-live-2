#!/bin/bash

echo "🚀 MISE À JOUR HEBDOMADAIRE"
echo "======================================================================"

# ÉTAPE 1 : Scraping
echo ""
echo "📥 ÉTAPE 1/3 : Scraping des nouvelles données..."
echo "----------------------------------------------------------------------"
for league in france germany germany2 england netherlands2 bolivia bulgaria portugal; do
    echo "   → Scraping $league..."
    python3 scrape_all_leagues_auto.py --league $league --workers 2
done

# ÉTAPE 2 : Génération patterns
echo ""
echo "📊 ÉTAPE 2/3 : Génération des patterns..."
echo "----------------------------------------------------------------------"
cd football-live-prediction
python3 build_team_recurrence_stats.py
cd ..

# ÉTAPE 3 : Génération whitelists
echo ""
echo "🎯 ÉTAPE 3/3 : Génération des whitelists..."
echo "----------------------------------------------------------------------"
python3 generate_top_teams_whitelist.py --all --threshold 65 --min-matches 4

# RÉSUMÉ
echo ""
echo "✅ MISE À JOUR TERMINÉE"
echo "======================================================================"
echo "Date : $(date '+%Y-%m-%d %H:%M:%S')"
echo "Whitelists générées : $(ls whitelists/*_whitelist.json 2>/dev/null | wc -l)"
echo ""
