"""
Logger - Système de logging configuré avec loguru
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional


class Logger:
    """Gestionnaire de logging centralisé"""
    
    def __init__(self, log_file: Optional[str] = None, level: str = "INFO"):
        """
        Initialise le logger
        
        Args:
            log_file: Chemin du fichier de log (None = pas de fichier)
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        """
        # Supprimer le logger par défaut
        logger.remove()
        
        # Ajouter console output avec couleurs
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True
        )
        
        # Ajouter fichier log si spécifié
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
                level=level,
                rotation="10 MB",  # Rotation à 10MB
                retention="1 week",  # Garder 1 semaine
                compression="zip"  # Compresser les anciens logs
            )
        
        self.logger = logger
    
    def get_logger(self):
        """Retourne l'instance logger"""
        return self.logger


# Instance globale
_logger_instance: Optional[Logger] = None


def setup_logger(log_file: Optional[str] = None, level: str = "INFO") -> logger:
    """
    Configure et retourne le logger
    
    Args:
        log_file: Chemin du fichier de log
        level: Niveau de log
        
    Returns:
        Instance du logger
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = Logger(log_file=log_file, level=level)
    
    return _logger_instance.get_logger()


def get_logger() -> logger:
    """
    Récupère l'instance du logger
    
    Returns:
        Instance du logger
    """
    global _logger_instance
    
    if _logger_instance is None:
        # Créer un logger par défaut
        _logger_instance = Logger()
    
    return _logger_instance.get_logger()


# Exemple d'utilisation
if __name__ == "__main__":
    # Test du logger
    log = setup_logger(log_file="data/logs/test.log", level="DEBUG")
    
    log.debug("Message de debug")
    log.info("Message d'information")
    log.warning("Message d'avertissement")
    log.error("Message d'erreur")
    log.success("Message de succès")
    
    # Test avec contexte
    log.info("Démarrage du scraper pour {team}", team="Manchester United")
    
    print("\n✅ Logger testé avec succès!")
