# Procédure de mise à jour de la base de données SoccerStats

Pour garantir la qualité des analyses, il est recommandé de régénérer la base de données au moins une fois par semaine.

## Étapes

1. **Lancer la mise à jour**

   Dans le dossier `CLEAN_WORKFLOW`, exécutez :
   ```bash
   python3 refresh_database.py
   ```
   Cela télécharge les données SoccerStats pour les ligues suivies et remplit la base `CLEAN_WORKFLOW/data/predictions.db`.

2. **Automatisation (optionnel)**

   Pour automatiser la mise à jour chaque semaine, ajoutez une tâche cron :
   ```bash
   0 3 * * 1 cd /workspaces/paris-live/CLEAN_WORKFLOW && python3 refresh_database.py
   ```

3. **Vérification**

   - Vérifiez que le fichier `CLEAN_WORKFLOW/data/predictions.db` est bien mis à jour.
   - Les scripts d’analyse utiliseront automatiquement cette base.

## Remarques
- Modifiez la liste des ligues à suivre dans `refresh_database.py` si besoin.
- Adaptez la logique d’extraction selon l’évolution du site SoccerStats.
- Toute la logique et les données doivent rester dans le dossier `CLEAN_WORKFLOW`.
