\"""Sistema integrato di ottimizzazione dei costi API."""

import logging
import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .cache_manager import CacheManager
from .llm_optimizer import LLMOptimizer
from .workflow_optimizer import WorkflowOptimizer

class APICostOptimizer:
    """Sistema integrato per ottimizzare i costi delle chiamate API."""
    
    def __init__(self, cache_dir: str = "./cache", logger: Optional[logging.Logger] = None):
        """Inizializza il sistema di ottimizzazione dei costi API.
        
        Args:
            cache_dir: Directory per la cache
            logger: Logger opzionale
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Inizializza i componenti
        self.cache_manager = CacheManager(cache_dir=cache_dir, logger=self.logger)
        self.llm_optimizer = LLMOptimizer(logger=self.logger)
        self.workflow_optimizer = WorkflowOptimizer(
            cache_manager=self.cache_manager,
            llm_optimizer=self.llm_optimizer,
            logger=self.logger
        )
        
        # Statistiche globali
        self.start_time = datetime.now()
        self.total_api_calls = 0
        self.total_cached_calls = 0
        self.total_cost = 0.0
        self.total_saved_cost = 0.0
        
        self.logger.info("Sistema di ottimizzazione dei costi API inizializzato")
    
    def optimize_workflows(self, workflows_config: Dict[str, Any]) -> Dict[str, Any]:
        """Ottimizza tutti i workflow definiti nella configurazione.
        
        Args:
            workflows_config: Configurazione dei workflow
            
        Returns:
            Configurazione ottimizzata dei workflow
        """
        if not workflows_config or "workflows" not in workflows_config:
            self.logger.warning("Configurazione workflow non valida")
            return workflows_config
        
        workflows = workflows_config["workflows"]
        optimized_workflows = {}
        
        for name, workflow in workflows.items():
            # Aggiungi il nome al workflow per riferimento
            workflow["name"] = name
            # Ottimizza il workflow
            optimized_workflow = self.workflow_optimizer.optimize_workflow(workflow)
            # Assegna i modelli ottimali
            optimized_workflow = self.workflow_optimizer.assign_optimal_models(optimized_workflow)
            optimized_workflows[name] = optimized_workflow
        
        # Aggiorna la configurazione
        optimized_config = workflows_config.copy()
        optimized_config["workflows"] = optimized_workflows
        
        self.logger.info(f"Ottimizzati {len(optimized_workflows)} workflow")
        return optimized_config
    
    def cached_api_call(self, prefix: str, func: callable, params: Dict[str, Any], 
                       max_age: Optional[int] = None, cost_estimate: float = 0.0) -> Any:
        """Esegue una chiamata API con caching.
        
        Args:
            prefix: Prefisso per la chiave di cache
            func: Funzione da chiamare
            params: Parametri per la funzione
            max_age: Età massima della cache in secondi
            cost_estimate: Stima del costo della chiamata
            
        Returns:
            Risultato della funzione
        """
        result = self.cache_manager.cached_api_call(
            prefix=prefix,
            func=func,
            params=params,
            max_age=max_age,
            cost_estimate=cost_estimate
        )
        
        # Aggiorna le statistiche
        cache_stats = self.cache_manager.get_cache_stats()
        self.total_cached_calls = cache_stats["saved_calls"]
        self.total_saved_cost = cache_stats["estimated_savings"]
        
        return result
    
    def optimize_llm_call(self, func: callable) -> callable:
        """Decoratore per ottimizzare le chiamate LLM.
        
        Args:
            func: Funzione da decorare
            
        Returns:
            Funzione decorata
        """
        # Aggiungi i metodi di controllo del budget all'ottimizzatore LLM
        self.llm_optimizer._check_budget = self._check_budget
        self.llm_optimizer._update_daily_cost = self._update_daily_cost
        
        optimized_func = self.llm_optimizer.optimize_llm_call(func)
        
        # Aggiorna le statistiche dopo ogni chiamata
        def wrapper(*args, **kwargs):
            result = optimized_func(*args, **kwargs)
            
            # Aggiorna le statistiche globali
            usage_stats = self.llm_optimizer.get_usage_stats()
            self.total_api_calls = usage_stats["total_calls"]
            self.total_cost = usage_stats["total_cost"]
            
            return result
        
        return wrapper
    
    def set_model_quotas(self, quotas: Dict[str, int], reset_interval: int = 3600) -> None:
        """Imposta i limiti di quota per i modelli.
        
        Args:
            quotas: Dizionario con i limiti di quota per modello
            reset_interval: Intervallo di reset in secondi
        """
        for model, limit in quotas.items():
            self.llm_optimizer.set_quota_limit(model, limit, reset_interval)
            
    def set_daily_budget(self, budget_limit: float) -> None:
        """Imposta un budget giornaliero massimo per le chiamate API.
        
        Args:
            budget_limit: Limite di budget giornaliero in dollari
        """
        self.daily_budget_limit = budget_limit
        self.daily_cost = 0.0
        self.budget_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.logger.info(f"Impostato budget giornaliero: ${budget_limit:.2f}")
    
    def _check_budget(self, estimated_cost: float) -> bool:
        """Verifica se una chiamata API rientra nel budget giornaliero.
        
        Args:
            estimated_cost: Costo stimato della chiamata
            
        Returns:
            True se la chiamata rientra nel budget, False altrimenti
        """
        # Resetta il budget se è un nuovo giorno
        now = datetime.now()
        if now.date() > self.budget_reset_time.date():
            self.daily_cost = 0.0
            self.budget_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.logger.info("Budget giornaliero resettato")
        
        # Verifica se abbiamo superato il budget
        if hasattr(self, 'daily_budget_limit') and self.daily_cost + estimated_cost > self.daily_budget_limit:
            self.logger.warning(f"Budget giornaliero superato: ${self.daily_cost:.2f} + ${estimated_cost:.2f} > ${self.daily_budget_limit:.2f}")
            return False
            
        return True
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche complete di ottimizzazione.
        
        Returns:
            Dizionario con statistiche di ottimizzazione
        """
        # Raccogli statistiche da tutti i componenti
        cache_stats = self.cache_manager.get_cache_stats()
        llm_stats = self.llm_optimizer.get_usage_stats()
        workflow_stats = self.workflow_optimizer.get_optimization_stats()
        
        # Calcola il tempo di esecuzione
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        # Calcola il risparmio totale stimato
        total_saved = self.total_saved_cost
        if workflow_stats["total_api_calls_saved"] > 0:
            # Stima il risparmio dai workflow ottimizzati
            avg_call_cost = self.total_cost / max(1, self.total_api_calls)
            workflow_savings = workflow_stats["total_api_calls_saved"] * avg_call_cost
            total_saved += workflow_savings
        
        return {
            "runtime_seconds": runtime,
            "total_api_calls": self.total_api_calls,
            "total_cached_calls": self.total_cached_calls,
            "total_cost": self.total_cost,
            "total_saved_cost": total_saved,
            "cost_reduction_percentage": (total_saved / (self.total_cost + total_saved)) * 100 if (self.total_cost + total_saved) > 0 else 0,
            "cache": cache_stats,
            "llm": llm_stats,
            "workflow": workflow_stats
        }
    
    def save_stats_to_file(self, file_path: str) -> None:
        """Salva le statistiche di ottimizzazione su file.
        
        Args:
            file_path: Percorso del file
        """
        stats = self.get_optimization_stats()
        stats["timestamp"] = datetime.now().isoformat()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Statistiche salvate in {file_path}")
        except Exception as e:
            self.logger.error(f"Errore nel salvare le statistiche: {str(e)}")
    
    def clear_expired_cache(self, max_age: int = 86400) -> int:
        """Elimina le voci di cache scadute.
        
        Args:
            max_age: Età massima in secondi (default: 24 ore)
            
        Returns:
            Numero di file eliminati
        """
        return self.cache_manager.clear_expired_cache(max_age)