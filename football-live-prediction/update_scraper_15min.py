"""Mise à jour pour intervalles de 15 minutes"""

with open('scrapers/soccerstats_historical.py', 'r') as f:
    content = f.read()

# Ajouter méthode de conversion 10min → 15min
new_method = '''
    def convert_10min_to_15min(self, timing_data_10min: pd.DataFrame) -> pd.DataFrame:
        """
        Convertit les données d'intervalles de 10min en intervalles de 15min
        
        Intervalles 10min sur le site:
        1-10, 11-20, 21-30, 31-40, 41-50, 51-60, 61-70, 71-80, 81-90
        
        Nouveaux intervalles 15min:
        0-15, 16-30, 31-45, 46-60, 61-75, 76-90
        """
        if timing_data_10min is None or timing_data_10min.empty:
            return timing_data_10min
        
        # Créer un nouveau DataFrame avec les colonnes nécessaires
        df_15min = timing_data_10min[['team', 'gp']].copy()
        
        # Mapping des intervalles 10min vers 15min
        # Format: {intervalle_15min: [intervalles_10min_à_combiner]}
        interval_mapping = {
            '0-15': ['1-10', '11-20'],       # Prendre 1-10 complet + moitié de 11-20
            '16-30': ['11-20', '21-30'],     # Prendre moitié de 11-20 + 21-30 complet
            '31-45': ['31-40', '41-50'],     # 31-40 complet + moitié de 41-50 (avant HT)
            '46-60': ['41-50', '51-60'],     # Moitié de 41-50 (après HT) + 51-60 complet
            '61-75': ['61-70', '71-80'],     # 61-70 complet + moitié de 71-80
            '76-90': ['71-80', '81-90']      # Moitié de 71-80 + 81-90 complet
        }
        
        # Pour chaque intervalle 15min
        for interval_15, intervals_10 in interval_mapping.items():
            scored_col = f'{interval_15}_scored'
            conceded_col = f'{interval_15}_conceded'
            
            # Initialiser les colonnes
            df_15min[scored_col] = 0.0
            df_15min[conceded_col] = 0.0
            
            # Combiner les données des intervalles 10min
            for interval_10 in intervals_10:
                col_scored = f'{interval_10}_scored'
                col_conceded = f'{interval_10}_conceded'
                
                if col_scored in timing_data_10min.columns:
                    # Si l'intervalle 10min est partagé entre deux 15min
                    if interval_10 in ['11-20', '41-50', '71-80']:
                        # Prendre 50% pour chaque intervalle 15min
                        df_15min[scored_col] += timing_data_10min[col_scored] * 0.5
                        df_15min[conceded_col] += timing_data_10min[col_conceded] * 0.5
                    else:
                        # Prendre 100%
                        df_15min[scored_col] += timing_data_10min[col_scored]
                        df_15min[conceded_col] += timing_data_10min[col_conceded]
        
        # Créer la structure goals_by_interval
        goals_by_interval = {}
        
        for interval in ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90']:
            scored_col = f'{interval}_scored'
            conceded_col = f'{interval}_conceded'
            
            if scored_col in df_15min.columns:
                goals_by_interval[interval] = {
                    'scored': df_15min[scored_col].values[0],
                    'conceded': df_15min[conceded_col].values[0]
                }
        
        # Calculer first_half et second_half
        first_half = {
            'scored': sum(goals_by_interval[i]['scored'] for i in ['0-15', '16-30', '31-45']),
            'conceded': sum(goals_by_interval[i]['conceded'] for i in ['0-15', '16-30', '31-45'])
        }
        
        second_half = {
            'scored': sum(goals_by_interval[i]['scored'] for i in ['46-60', '61-75', '76-90']),
            'conceded': sum(goals_by_interval[i]['conceded'] for i in ['46-60', '61-75', '76-90'])
        }
        
        # Ajouter à df_15min
        df_15min['goals_by_interval'] = [goals_by_interval]
        df_15min['first_half'] = [first_half]
        df_15min['second_half'] = [second_half]
        
        return df_15min

'''

# Trouver où insérer (après scrape_recent_form)
insert_pos = content.find('    def cleanup(self):')

if insert_pos == -1:
    print("❌ Position d'insertion non trouvée")
    exit(1)

content = content[:insert_pos] + new_method + '\n' + content[insert_pos:]

# Modifier scrape_timing_stats_all_venues pour convertir automatiquement
old_return = """        return {
            'overall': overall_df,
            'home': home_df,
            'away': away_df
        }"""

new_return = """        # Convertir en intervalles 15min
        overall_15min = self.convert_10min_to_15min(overall_df) if overall_df is not None else None
        home_15min = self.convert_10min_to_15min(home_df) if home_df is not None else None
        away_15min = self.convert_10min_to_15min(away_df) if away_df is not None else None
        
        return {
            'overall': overall_15min,
            'home': home_15min,
            'away': away_15min
        }"""

content = content.replace(old_return, new_return)

with open('scrapers/soccerstats_historical.py', 'w') as f:
    f.write(content)

print("✅ Scraper mis à jour pour intervalles 15min")
