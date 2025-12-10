# METHODOLOGIE_TOP_PATTERNS_GLOBAL.md

## Méthodologie pour l’extraction des top patterns toutes ligues confondues

### 1. Pré-requis
- Scraper toutes les ligues activées dans `CLEAN_WORKFLOW/config.yaml` pour garantir une base à jour.
- Utiliser le workflow centralisé pour le scraping (voir `METHODOLOGIE_SCRAPING_LIGUES.md`).

### 2. Script d’extraction
- Utiliser le script `CLEAN_WORKFLOW/top_patterns_global.py` pour extraire les meilleurs patterns par intervalle (31-45+ et 75-90+) sur toutes les ligues présentes en base.
- Le script trie les équipes par récurrence décroissante et total de buts dans l’intervalle.
- Affichage du top N (ex : 20) pour chaque intervalle, toutes ligues confondues.

### 3. Commande à lancer
```
python3 /workspaces/paris-live/CLEAN_WORKFLOW/top_patterns_global.py | tee /workspaces/paris-live/CLEAN_WORKFLOW/top_patterns_global.out.txt
```

### 4. Fichier de sortie
- Les résultats complets sont sauvegardés dans `CLEAN_WORKFLOW/top_patterns_global.out.txt` pour archivage et exploitation.

### 5. Avantages
- Vue globale et comparative sur toutes les ligues suivies.
- Méthode reproductible et compatible avec l’évolution du workflow.

---

**En cas d’oubli, se référer à ce fichier pour reproduire la méthodologie ou régénérer les top patterns globaux.**
