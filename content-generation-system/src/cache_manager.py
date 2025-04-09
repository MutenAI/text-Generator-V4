"""Gestore avanzato della cache per ridurre le chiamate API."""

import os
import json
import hashlib
import time
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Union
from datetime import datetime, timedelta

T = TypeVar('T')

class CacheManager:
    """Gestisce il caching dei risultati delle chiamate API per ridurre i costi."""
    
    def __init__(self, cache_dir: str = "./cache", logger: Optional[logging.Logger] = None):
        """Inizializza il gestore della cache.
        
        Args:
            cache_dir: Directory dove salvare i file di cache
            logger: Logger opzionale per il logging
        """
        self.cache_dir = cache_dir
        self.logger = logger or logging.getLogger(__name__)
        self._ensure_cache_dir()
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "saved_calls": 0,
            "estimated_savings": 0.0  # Stima del risparmio in dollari
        }
        
    def _ensure_cache_dir(self) -> None:
        """Assicura che la directory della cache esista."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            self.logger.info(f"Creata directory cache: {self.cache_dir}")
    
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Genera una chiave di cache univoca basata sui parametri.
        
        Args:
            prefix: Prefisso per la chiave (es. 'search', 'completion')
            params: Parametri della chiamata API
            
        Returns:
            Chiave di cache univoca
        """
        # Crea una copia dei parametri per la normalizzazione
        normalized_params = params.copy()
        
        # Normalizza i prompt per aumentare le possibilità di hit della cache
        if "prompt" in normalized_params and isinstance(normalized_params["prompt"], str):
            # Rimuovi spazi extra, normalizza punteggiatura
            prompt = normalized_params["prompt"]
            prompt = " ".join(prompt.split())  # Normalizza spazi
            prompt = prompt.lower()  # Converti in minuscolo per aumentare le hit
            normalized_params["prompt"] = prompt
        
        # Normalizza anche i messaggi per le API di chat
        if "messages" in normalized_params and isinstance(normalized_params["messages"], list):
            for i, msg in enumerate(normalized_params["messages"]):
                if "content" in msg and isinstance(msg["content"], str):
                    content = msg["content"]
                    content = " ".join(content.split())  # Normalizza spazi
                    content = content.lower()  # Converti in minuscolo
                    normalized_params["messages"][i]["content"] = content
        
        # Converti i parametri normalizzati in una stringa JSON ordinata
        param_str = json.dumps(normalized_params, sort_keys=True)
        # Genera un hash SHA-256 dei parametri
        param_hash = hashlib.sha256(param_str.encode()).hexdigest()
        return f"{prefix}_{param_hash}"
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Ottiene il percorso del file di cache per una chiave.
        
        Args:
            cache_key: Chiave di cache
            
        Returns:
            Percorso completo del file di cache
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get_from_cache(self, prefix: str, params: Dict[str, Any], max_age: Optional[int] = None) -> Optional[Any]:
        """Recupera un risultato dalla cache se disponibile e non scaduto.
        Implementa anche una ricerca fuzzy per trovare risultati simili.
        
        Args:
            prefix: Prefisso per la chiave di cache
            params: Parametri della chiamata API
            max_age: Età massima in secondi (None = nessun limite)
            
        Returns:
            Risultato dalla cache o None se non trovato/scaduto
        """
        # Genera la chiave di cache esatta
        cache_key = self._generate_cache_key(prefix, params)
        
        # Prova prima la cache in memoria con chiave esatta
        if cache_key in self.memory_cache:
            cache_entry = self.memory_cache[cache_key]
            if max_age is None or (time.time() - cache_entry["timestamp"] <= max_age):
                self.cache_stats["hits"] += 1
                self.cache_stats["saved_calls"] += 1
                self.logger.debug(f"Cache hit esatta (memory): {cache_key}")
                return cache_entry["data"]
        
        # Prova la cache su disco con chiave esatta
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_entry = json.load(f)
                
                # Verifica se la cache è scaduta
                if max_age is None or (time.time() - cache_entry["timestamp"] <= max_age):
                    # Aggiorna anche la cache in memoria
                    self.memory_cache[cache_key] = cache_entry
                    self.cache_stats["hits"] += 1
                    self.cache_stats["saved_calls"] += 1
                    self.logger.debug(f"Cache hit esatta (disk): {cache_key}")
                    return cache_entry["data"]
            except Exception as e:
                self.logger.warning(f"Errore nel leggere la cache: {str(e)}")
        
        # Se non troviamo una corrispondenza esatta, proviamo con una ricerca fuzzy
        # ma solo per prompt e completamenti (non per altre API)
        if prefix in ["prompt", "completion", "chat"]:
            # Cerca nella cache in memoria per prompt simili
            for key, entry in self.memory_cache.items():
                if not key.startswith(prefix):
                    continue
                    
                # Verifica se la cache è scaduta
                if max_age is not None and (time.time() - entry["timestamp"] > max_age):
                    continue
                    
                # Verifica similarità dei parametri
                if self._are_params_similar(params, entry["params"]):
                    self.cache_stats["hits"] += 1
                    self.cache_stats["saved_calls"] += 1
                    self.logger.info(f"Cache hit fuzzy (memory): {key}")
                    return entry["data"]
            
            # Cerca nella cache su disco per prompt simili
            for filename in os.listdir(self.cache_dir):
                if not filename.startswith(prefix) or not filename.endswith('.json'):
                    continue
                    
                file_path = os.path.join(self.cache_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entry = json.load(f)
                    
                    # Verifica se la cache è scaduta
                    if max_age is not None and (time.time() - entry["timestamp"] > max_age):
                        continue
                        
                    # Verifica similarità dei parametri
                    if self._are_params_similar(params, entry["params"]):
                        # Aggiorna anche la cache in memoria
                        key = filename[:-5]  # Rimuovi .json
                        self.memory_cache[key] = entry
                        self.cache_stats["hits"] += 1
                        self.cache_stats["saved_calls"] += 1
                        self.logger.info(f"Cache hit fuzzy (disk): {key}")
                        return entry["data"]
                except Exception as e:
                    self.logger.warning(f"Errore nel leggere la cache: {str(e)}")
        
        self.cache_stats["misses"] += 1
        self.logger.debug(f"Cache miss: {cache_key}")
        return None
    
    def save_to_cache(self, prefix: str, params: Dict[str, Any], data: Any, cost_estimate: float = 0.0) -> None:
        """Salva un risultato nella cache.
        
        Args:
            prefix: Prefisso per la chiave di cache
            params: Parametri della chiamata API
            data: Dati da salvare
            cost_estimate: Stima del costo della chiamata API in dollari
        """
        cache_key = self._generate_cache_key(prefix, params)
        cache_entry = {
            "timestamp": time.time(),
            "data": data,
            "params": params,
            "cost_estimate": cost_estimate
        }
        
        # Salva in memoria
        self.memory_cache[cache_key] = cache_entry
        
        # Salva su disco
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Salvato in cache: {cache_key}")
            self.cache_stats["estimated_savings"] += cost_estimate
        except Exception as e:
            self.logger.error(f"Errore nel salvare la cache: {str(e)}")
    
    def _are_params_similar(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> bool:
        """Verifica se due set di parametri sono semanticamente simili.
        
        Args:
            params1: Primo set di parametri
            params2: Secondo set di parametri
            
        Returns:
            True se i parametri sono simili, False altrimenti
        """
        # Verifica se entrambi hanno prompt o messaggi
        if "prompt" in params1 and "prompt" in params2:
            # Per prompt di testo semplice
            prompt1 = params1["prompt"].lower() if isinstance(params1["prompt"], str) else ""
            prompt2 = params2["prompt"].lower() if isinstance(params2["prompt"], str) else ""
            
            # Se uno dei prompt è molto breve, richiedi una corrispondenza più precisa
            if len(prompt1) < 50 or len(prompt2) < 50:
                return prompt1 == prompt2
            
            # Altrimenti, verifica la similarità semantica
            # Implementazione semplice: verifica se condividono almeno il 70% delle parole
            words1 = set(prompt1.split())
            words2 = set(prompt2.split())
            
            if not words1 or not words2:
                return False
                
            common_words = words1.intersection(words2)
            similarity = len(common_words) / max(len(words1), len(words2))
            
            return similarity >= 0.7  # 70% di similarità
            
        elif "messages" in params1 and "messages" in params2:
            # Per messaggi di chat
            messages1 = params1["messages"]
            messages2 = params2["messages"]
            
            # Verifica se hanno lo stesso numero di messaggi
            if len(messages1) != len(messages2):
                return False
                
            # Verifica ogni messaggio
            for i in range(len(messages1)):
                msg1 = messages1[i]
                msg2 = messages2[i]
                
                # Verifica ruolo
                if msg1.get("role") != msg2.get("role"):
                    return False
                    
                # Verifica contenuto
                content1 = msg1.get("content", "").lower() if isinstance(msg1.get("content"), str) else ""
                content2 = msg2.get("content", "").lower() if isinstance(msg2.get("content"), str) else ""
                
                # Se uno dei contenuti è molto breve, richiedi una corrispondenza più precisa
                if len(content1) < 50 or len(content2) < 50:
                    if content1 != content2:
                        return False
                else:
                    # Verifica similarità semantica
                    words1 = set(content1.split())
                    words2 = set(content2.split())
                    
                    if not words1 or not words2:
                        continue
                        
                    common_words = words1.intersection(words2)
                    similarity = len(common_words) / max(len(words1), len(words2))
                    
                    if similarity < 0.7:  # 70% di similarità
                        return False
            
            return True
        
        # Se non hanno né prompt né messaggi, o hanno tipi diversi, non sono simili
        return False
    
    def cached_api_call(self, prefix: str, func: Callable[..., T], params: Dict[str, Any], 
                       max_age: Optional[int] = None, cost_estimate: float = 0.0) -> T:
        """Esegue una chiamata API con caching.
        
        Args:
            prefix: Prefisso per la chiave di cache
            func: Funzione da chiamare se non in cache
            params: Parametri per la funzione e la chiave di cache
            max_age: Età massima della cache in secondi
            cost_estimate: Stima del costo della chiamata API
            
        Returns:
            Risultato della funzione (dalla cache o chiamata diretta)
        """
        # Cerca nella cache (include ricerca fuzzy)
        cached_result = self.get_from_cache(prefix, params, max_age)
        if cached_result is not None:
            return cached_result
        
        # Esegui la chiamata API
        result = func(**params)
        
        # Salva il risultato in cache
        self.save_to_cache(prefix, params, result, cost_estimate)
        
        return result
    
    def get_cache_stats(self) -> Dict[str, Union[int, float]]:
        """Restituisce le statistiche della cache.
        
        Returns:
            Dizionario con statistiche della cache
        """
        return self.cache_stats
    
    def clear_expired_cache(self, max_age: int) -> int:
        """Elimina le voci di cache più vecchie di max_age secondi.
        
        Args:
            max_age: Età massima in secondi
            
        Returns:
            Numero di file eliminati
        """
        count = 0
        current_time = time.time()
        
        # Pulisci la cache in memoria
        keys_to_remove = []
        for key, entry in self.memory_cache.items():
            if current_time - entry["timestamp"] > max_age:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.memory_cache[key]
        
        # Pulisci la cache su disco
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(self.cache_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    cache_entry = json.load(f)
                
                if current_time - cache_entry["timestamp"] > max_age:
                    os.remove(file_path)
                    count += 1
            except Exception as e:
                self.logger.warning(f"Errore nell'elaborare il file cache {filename}: {str(e)}")
        
        self.logger.info(f"Eliminati {count} file di cache scaduti")
        return count