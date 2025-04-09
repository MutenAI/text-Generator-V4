"""Integrazione del sistema di ottimizzazione dei costi API nell'applicazione Streamlit."""

import logging
import os
import yaml
import time
from typing import Dict, Any, Optional

# Importa i componenti del sistema di ottimizzazione
from .api_cost_optimizer import APICostOptimizer
from .config_manager import ConfigManager

class OptimizationIntegration:
    """Classe per integrare il sistema di ottimizzazione nell'applicazione esistente."""
    
    def __init__(self, config_manager: ConfigManager = None, logger: Optional[logging.Logger] = None):
        """Inizializza l'integrazione del sistema di ottimizzazione.
        
        Args:
            config_manager: Gestore della configurazione esistente
            logger: Logger opzionale
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config_manager = config_manager
        self.optimizer = None
        self.optimization_enabled = False
        self.optimization_config = None
        self.last_stats_save = 0
        
        # Carica la configurazione di ottimizzazione
        self._load_optimization_config()
        
        # Inizializza l'ottimizzatore se abilitato
        if self.optimization_enabled:
            self._initialize_optimizer()
    
    def _load_optimization_config(self) -> None:
        """Carica la configurazione di ottimizzazione."""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        config_path = os.path.join(config_dir, 'optimization_config.yaml')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.optimization_config = yaml.safe_load(f)
                self.optimization_enabled = True
                self.logger.info("Configurazione di ottimizzazione caricata con successo")
            except Exception as e:
                self.logger.error(f"Errore nel caricamento della configurazione di ottimizzazione: {str(e)}")
                self.optimization_enabled = False
        else:
            self.logger.warning(f"File di configurazione di ottimizzazione non trovato: {config_path}")
            self.optimization_enabled = False
    
    def _initialize_optimizer(self) -> None:
        """Inizializza il sistema di ottimizzazione."""
        if not self.optimization_config:
            return
        
        try:
            # Estrai configurazione della cache
            cache_config = self.optimization_config.get('cache', {})
            cache_dir = cache_config.get('directory', './cache')
            
            # Inizializza l'ottimizzatore
            self.optimizer = APICostOptimizer(cache_dir=cache_dir, logger=self.logger)
            
            # Configura le quote dei modelli
            llm_config = self.optimization_config.get('llm_optimizer', {})
            if llm_config.get('enabled', True):
                quotas = llm_config.get('quotas', {})
                reset_interval = llm_config.get('quota_reset_interval', 3600)
                if quotas:
                    self.optimizer.set_model_quotas(quotas, reset_interval)
            
            self.logger.info("Sistema di ottimizzazione inizializzato con successo")
        except Exception as e:
            self.logger.error(f"Errore nell'inizializzazione del sistema di ottimizzazione: {str(e)}")
            self.optimization_enabled = False
    
    def optimize_workflows(self, workflows_config: Dict[str, Any]) -> Dict[str, Any]:
        """Ottimizza i workflow se l'ottimizzazione è abilitata.
        
        Args:
            workflows_config: Configurazione dei workflow
            
        Returns:
            Configurazione ottimizzata o originale
        """
        if not self.optimization_enabled or not self.optimizer:
            return workflows_config
        
        workflow_config = self.optimization_config.get('workflow_optimizer', {})
        if not workflow_config.get('enabled', True):
            return workflows_config
        
        try:
            return self.optimizer.optimize_workflows(workflows_config)
        except Exception as e:
            self.logger.error(f"Errore nell'ottimizzazione dei workflow: {str(e)}")
            return workflows_config
    
    def get_cached_api_call(self, prefix: str, func: callable, params: Dict[str, Any], 
                          max_age: Optional[int] = None, cost_estimate: float = 0.0) -> callable:
        """Restituisce una funzione con caching se l'ottimizzazione è abilitata.
        
        Args:
            prefix: Prefisso per la chiave di cache
            func: Funzione da chiamare
            params: Parametri per la funzione
            max_age: Età massima della cache in secondi
            cost_estimate: Stima del costo della chiamata
            
        Returns:
            Funzione con caching o originale
        """
        if not self.optimization_enabled or not self.optimizer:
            return lambda: func(**params)
        
        cache_config = self.optimization_config.get('cache', {})
        if not cache_config.get('enabled', True):
            return lambda: func(**params)
        
        # Usa l'età massima dalla configurazione se non specificata
        if max_age is None:
            max_age = cache_config.get('default_max_age', 86400)
        
        return lambda: self.optimizer.cached_api_call(prefix, func, params, max_age, cost_estimate)
    
    def get_optimized_llm_call(self, func: callable) -> callable:
        """Restituisce una funzione ottimizzata per le chiamate LLM se l'ottimizzazione è abilitata.
        
        Args:
            func: Funzione da ottimizzare
            
        Returns:
            Funzione ottimizzata o originale
        """
        if not self.optimization_enabled or not self.optimizer:
            return func
        
        llm_config = self.optimization_config.get('llm_optimizer', {})
        if not llm_config.get('enabled', True):
            return func
        
        return self.optimizer.optimize_llm_call(func)
    
    def save_optimization_stats(self, force: bool = False) -> None:
        """Salva le statistiche di ottimizzazione se necessario.
        
        Args:
            force: Forza il salvataggio anche se non è passato l'intervallo
        """
        if not self.optimization_enabled or not self.optimizer:
            return
        
        monitoring_config = self.optimization_config.get('monitoring', {})
        if not monitoring_config.get('enabled', True) or not monitoring_config.get('save_stats', True):
            return
        
        current_time = time.time()
        save_interval = monitoring_config.get('save_interval', 3600)
        
        if force or (current_time - self.last_stats_save >= save_interval):
            stats_file = monitoring_config.get('stats_file', './config/optimization_stats.json')
            try:
                self.optimizer.save_stats_to_file(stats_file)
                self.last_stats_save = current_time
            except Exception as e:
                self.logger.error(f"Errore nel salvataggio delle statistiche: {str(e)}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche di ottimizzazione.
        
        Returns:
            Statistiche di ottimizzazione o dizionario vuoto
        """
        if not self.optimization_enabled or not self.optimizer:
            return {}
        
        try:
            return self.optimizer.get_optimization_stats()
        except Exception as e:
            self.logger.error(f"Errore nel recupero delle statistiche: {str(e)}")
            return {}
    
    def is_optimization_enabled(self) -> bool:
        """Verifica se l'ottimizzazione è abilitata.
        
        Returns:
            True se l'ottimizzazione è abilitata, False altrimenti
        """
        return self.optimization_enabled
    
    def cleanup_cache(self) -> None:
        """Pulisce la cache scaduta."""
        if not self.optimization_enabled or not self.optimizer:
            return
        
        cache_config = self.optimization_config.get('cache', {})
        if not cache_config.get('enabled', True):
            return
        
        max_age = cache_config.get('cleanup_interval', 604800)  # 7 giorni di default
        try:
            deleted = self.optimizer.clear_expired_cache(max_age)
            self.logger.info(f"Pulizia cache completata: {deleted} file eliminati")
        except Exception as e:
            self.logger.error(f"Errore nella pulizia della cache: {str(e)}")