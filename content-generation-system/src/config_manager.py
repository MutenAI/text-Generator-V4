"""Gestisce la configurazione del sistema di generazione contenuti."""
import os
import yaml
import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

@dataclass
class Config:
    """Classe per la configurazione del sistema."""
    serper_api_key: str
    cache_dir: str = "./cache"
    brand_reference_file: Optional[str] = None
    openai_api_key: Optional[str] = None
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    workflows: Dict[str, Dict[str, List[Dict[str, str]]]] = None
    fallback_models: List[str] = None
    api_quota_limit: Optional[int] = None
    api_quota_reset_interval: int = 3600  # Reset intervallo in secondi (default 1 ora)
    api_quota_used: int = 0
    last_quota_reset: float = 0.0

    def dict(self) -> Dict[str, Any]:
        """Converte la configurazione in dizionario."""
        return {
            "serper_api_key": self.serper_api_key,
            "cache_dir": self.cache_dir,
            "brand_reference_file": self.brand_reference_file,
            "openai_api_key": self.openai_api_key,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

class ConfigManager:
    """Gestisce il caricamento e la validazione della configurazione."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Inizializza il config manager."""
        self.logger = logger or logging.getLogger(__name__)
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        # Crea la directory config se non esiste
        os.makedirs(self.config_dir, exist_ok=True)
        self.workflows_path = os.path.join(self.config_dir, 'workflows.yaml')
        self.quota_path = os.path.join(self.config_dir, 'api_quota.yaml')
        self._load_quota_state()
        
        # Crea il file workflows.yaml con configurazione predefinita se non esiste
        if not os.path.exists(self.workflows_path):
            default_workflows = {
                'workflows': {
                    'standard': {
                        'steps': [
                            {'task': 'research', 'description': 'Ricerca e raccolta informazioni sul tema'},
                            {'task': 'outline', 'description': 'Creazione della struttura del contenuto'},
                            {'task': 'draft', 'description': 'Scrittura della prima bozza'},
                            {'task': 'review', 'description': 'Revisione e miglioramento del contenuto'},
                            {'task': 'finalize', 'description': 'Finalizzazione e formattazione'}
                        ]
                    }
                }
            }
            try:
                with open(self.workflows_path, 'w') as f:
                    yaml.dump(default_workflows, f, default_flow_style=False)
                self.logger.info(f"Creato file workflows.yaml con configurazione predefinita in {self.workflows_path}")
            except Exception as e:
                self.logger.error(f"Errore nella creazione del file workflows.yaml: {str(e)}")
                raise

    def load_config(self, config_path: str) -> Config:
        """Carica la configurazione da file YAML."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Carica le chiavi API dalle variabili d'ambiente
            serper_api_key = os.getenv('SERPER_API_KEY')
            openai_api_key = os.getenv('OPENAI_API_KEY')
            
            if not serper_api_key:
                raise ValueError("SERPER_API_KEY mancante nel file .env")

            # Carica i workflow se disponibili
            workflows = None
            if os.path.exists(self.workflows_path):
                try:
                    with open(self.workflows_path, 'r') as f:
                        workflows_data = yaml.safe_load(f)
                        workflows = workflows_data.get('workflows')
                except Exception as e:
                    self.logger.error(f"Errore nel caricamento dei workflow: {str(e)}")
                    raise ValueError("Errore nel caricamento del file di configurazione dei workflow. Verificare che il file config/workflows.yaml sia presente e correttamente formattato.")

            # Carica configurazione quota e fallback
            fallback_models = config_data.get("fallback_models", ["gpt-3.5-turbo", "text-davinci-003"])
            api_quota_limit = config_data.get("api_quota_limit")
            api_quota_reset_interval = config_data.get("api_quota_reset_interval", 3600)

            # Ottieni il percorso del file di riferimento dalla configurazione
            brand_reference_file = config_data.get("brand_reference_file")
            
            # Crea istanza Config con valori di default per campi opzionali
            config = Config(
                serper_api_key=serper_api_key,
                cache_dir=config_data.get("cache_dir", "./cache"),
                brand_reference_file=brand_reference_file,
                openai_api_key=openai_api_key,
                model_name=config_data.get("model_name", "gpt-4"),
                fallback_models=fallback_models,
                api_quota_limit=api_quota_limit,
                api_quota_reset_interval=api_quota_reset_interval,
                api_quota_used=self._get_quota_used(),
                last_quota_reset=self._get_last_reset(),
                temperature=config_data.get("temperature", 0.7),
                max_tokens=config_data.get("max_tokens", 2000),
                workflows=workflows
            )

            return config

        except Exception as e:
            self.logger.error(f"Errore nel caricamento della configurazione: {str(e)}")
            raise

    def _load_quota_state(self) -> None:
        """Carica lo stato della quota API dal file."""
        if os.path.exists(self.quota_path):
            try:
                with open(self.quota_path, 'r') as f:
                    quota_data = yaml.safe_load(f)
                    if quota_data:
                        self._quota_used = quota_data.get('quota_used', 0)
                        self._last_reset = quota_data.get('last_reset', 0.0)
            except Exception as e:
                self.logger.error(f"Errore nel caricamento dello stato della quota: {str(e)}")
                self._quota_used = 0
                self._last_reset = 0.0
        else:
            self._quota_used = 0
            self._last_reset = 0.0

    def _save_quota_state(self) -> None:
        """Salva lo stato della quota API su file."""
        try:
            quota_data = {
                'quota_used': self._quota_used,
                'last_reset': self._last_reset
            }
            with open(self.quota_path, 'w') as f:
                yaml.dump(quota_data, f)
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio dello stato della quota: {str(e)}")

    def _get_quota_used(self) -> int:
        """Restituisce il numero di token utilizzati nel periodo corrente."""
        return self._quota_used

    def _get_last_reset(self) -> float:
        """Restituisce il timestamp dell'ultimo reset della quota."""
        return self._last_reset

    def check_and_update_quota(self, config: Config, tokens_to_use: int) -> Tuple[bool, Optional[str]]:
        """Verifica la disponibilità della quota e aggiorna il conteggio.

        Args:
            config: Configurazione corrente
            tokens_to_use: Numero di token da utilizzare

        Returns:
            Tuple[bool, Optional[str]]: (quota disponibile, modello alternativo da usare)
        """
        current_time = time.time()

        # Reset quota se necessario
        if current_time - self._last_reset >= config.api_quota_reset_interval:
            self._quota_used = 0
            self._last_reset = current_time
            self._save_quota_state()

        # Se non c'è limite di quota, permetti sempre
        if not config.api_quota_limit:
            return True, None

        # Verifica se c'è quota sufficiente
        if self._quota_used + tokens_to_use <= config.api_quota_limit:
            self._quota_used += tokens_to_use
            self._save_quota_state()
            return True, None

        # Cerca un modello alternativo
        if config.fallback_models:
            current_model_index = config.fallback_models.index(config.model_name) if config.model_name in config.fallback_models else -1
            if current_model_index < len(config.fallback_models) - 1:
                next_model = config.fallback_models[current_model_index + 1]
                return False, next_model

        return False, None