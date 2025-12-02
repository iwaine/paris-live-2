"""
Configuration Loader - Charge et valide la configuration YAML
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Charge et gère la configuration du projet"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le chargeur de configuration
        
        Args:
            config_path: Chemin vers le fichier config.yaml
                        Si None, cherche dans config/config.yaml
        """
        if config_path is None:
            # Trouver le répertoire racine du projet
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
        
    def _load_config(self):
        """Charge le fichier de configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration avec notation par points
        
        Args:
            key_path: Chemin de la clé (ex: "soccerstats.scraping.timeout")
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            Valeur de configuration ou default
            
        Example:
            >>> config = ConfigLoader()
            >>> timeout = config.get("soccerstats.scraping.timeout", 30)
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_league(self, league_code: str) -> Optional[Dict[str, Any]]:
        """
        Récupère la configuration d'une ligue par son code
        
        Args:
            league_code: Code de la ligue (ex: "england")
            
        Returns:
            Dict avec config de la ligue ou None
        """
        leagues = self.get("leagues", [])
        for league in leagues:
            if league.get("code") == league_code:
                return league
        return None
    
    def get_enabled_leagues(self) -> list:
        """Retourne la liste des ligues activées"""
        leagues = self.get("leagues", [])
        return [league for league in leagues if league.get("enabled", False)]
    
    def get_test_teams(self) -> list:
        """Retourne la liste des équipes de test"""
        return self.get("test_teams", [])
    
    def get_soccerstats_url(self, endpoint: str, **kwargs) -> str:
        """
        Construit une URL SoccerStats
        
        Args:
            endpoint: Nom de l'endpoint (ex: "timing_stats")
            **kwargs: Paramètres à remplacer dans l'URL (ex: league_code="england")
            
        Returns:
            URL complète
            
        Example:
            >>> config = ConfigLoader()
            >>> url = config.get_soccerstats_url("timing_stats", league_code="england")
            >>> print(url)
            https://www.soccerstats.com/timing.asp?league=england
        """
        base_url = self.get("soccerstats.base_url")
        endpoint_path = self.get(f"soccerstats.urls.{endpoint}")
        
        if not endpoint_path:
            raise ValueError(f"Unknown endpoint: {endpoint}")
        
        # Remplacer les placeholders
        url = base_url + endpoint_path.format(**kwargs)
        return url
    
    def get_time_intervals(self, format_type: str = "target") -> list:
        """
        Récupère les intervalles de temps
        
        Args:
            format_type: "original" (15min) ou "target" (10min)
            
        Returns:
            Liste des intervalles
        """
        if format_type == "target":
            first_half = self.get("time_intervals.target.first_half", [])
            second_half = self.get("time_intervals.target.second_half", [])
            return first_half + second_half
        else:
            return self.get("time_intervals.original", [])
    
    def get_prediction_weights(self) -> Dict[str, float]:
        """Retourne les poids pour le moteur de prédiction"""
        return self.get("prediction.weights", {})
    
    def get_data_directory(self, dir_name: str) -> Path:
        """
        Retourne le chemin d'un répertoire de données
        
        Args:
            dir_name: Nom du répertoire (ex: "team_profiles_json")
            
        Returns:
            Path object du répertoire
        """
        # Trouver le répertoire racine du projet
        current_file = Path(__file__)
        project_root = current_file.parent.parent
        
        rel_path = self.get(f"data.directories.{dir_name}")
        if not rel_path:
            raise ValueError(f"Unknown data directory: {dir_name}")
        
        full_path = project_root / rel_path
        
        # Créer le répertoire s'il n'existe pas
        full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    def is_debug_mode(self) -> bool:
        """Vérifie si le mode debug est activé"""
        return self.get("development.debug_mode", False)
    
    def __repr__(self) -> str:
        return f"ConfigLoader(config_path={self.config_path})"


# Instance globale pour faciliter l'import
_config_instance: Optional[ConfigLoader] = None

def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Récupère l'instance singleton de ConfigLoader
    
    Args:
        config_path: Chemin du fichier config (seulement au premier appel)
        
    Returns:
        Instance de ConfigLoader
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)
    
    return _config_instance


# Exemple d'utilisation
if __name__ == "__main__":
    # Test du chargeur de configuration
    config = ConfigLoader()
    
    print("=== TEST CONFIGURATION LOADER ===\n")
    
    # Test 1: Récupération de valeurs simples
    print("1. Project name:", config.get("project.name"))
    print("2. SoccerStats base URL:", config.get("soccerstats.base_url"))
    print("3. Timeout:", config.get("soccerstats.scraping.timeout"))
    
    # Test 2: Récupération d'une ligue
    print("\n4. Premier League config:")
    pl = config.get_league("england")
    print(f"   Name: {pl['name']}, Enabled: {pl['enabled']}")
    
    # Test 3: Ligues activées
    print("\n5. Enabled leagues:")
    for league in config.get_enabled_leagues():
        print(f"   - {league['name']} ({league['code']})")
    
    # Test 4: Construction d'URL
    print("\n6. URLs:")
    url = config.get_soccerstats_url("timing_stats", league_code="england")
    print(f"   Timing stats: {url}")
    
    # Test 5: Intervalles de temps
    print("\n7. Time intervals (target format):")
    intervals = config.get_time_intervals("target")
    print(f"   {intervals}")
    
    # Test 6: Répertoires de données
    print("\n8. Data directories:")
    json_dir = config.get_data_directory("team_profiles_json")
    print(f"   Profiles JSON: {json_dir}")
    
    print("\n✅ Configuration chargée avec succès!")
