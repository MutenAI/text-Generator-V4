"""Ottimizzatore per l'uso dei modelli LLM per ridurre i costi delle API."""

import logging
import time
import re
from typing import Dict, Any, Optional, List, Tuple, Callable, Union
from functools import wraps
from .token_manager import TokenManager

class LLMOptimizer:
    """Gestisce l'ottimizzazione dell'uso dei modelli LLM per ridurre i costi."""
    
    # Costi stimati per 1000 token (input + output) in dollari
    MODEL_COSTS = {
        # OpenAI
        "gpt-4": 0.06,  # $0.03 input, $0.06 output
        "gpt-4-turbo": 0.03,  # $0.01 input, $0.03 output
        "gpt-3.5-turbo": 0.0015,  # $0.0005 input, $0.0015 output
        # Anthropic
        "claude-3-opus-20240229": 0.045,  # $0.015 input, $0.075 output (media)
        "claude-3-sonnet-20240229": 0.015,  # $0.003 input, $0.015 output (media)
        "claude-3-haiku-20240307": 0.0025,  # $0.00025 input, $0.0025 output (media)
        # DeepSeek
        "deepseek-chat": 0.0005,  # Costo stimato per 1000 token
        "deepseek-coder": 0.0008  # Costo stimato per 1000 token
    }
    
    # Modelli in ordine di capacità (dal più potente al meno potente)
    MODEL_TIERS = [
        ["gpt-4", "claude-3-opus-20240229"],  # Tier 1 (più potente)
        ["gpt-4-turbo", "claude-3-sonnet-20240229"],  # Tier 2
        ["gpt-3.5-turbo", "claude-3-haiku-20240307", "deepseek-chat", "deepseek-coder"]  # Tier 3 (meno potente)
    ]
    
    # Mappatura diretta dei task ai tier di modelli (0=Tier1, 1=Tier2, 2=Tier3)
    # Questa mappatura è più aggressiva nell'uso di modelli economici
    TASK_MODEL_MAPPING = {
        # Solo i task più critici usano Tier 1
        "expert_review": 0,
        "technical_draft": 0,
        
        # La maggior parte dei task usa Tier 2
        "research": 1,
        "draft": 1,
        "edit": 1,
        "review": 1,
        
        # Task semplici usano Tier 3
        "outline": 2,
        "finalize": 2,
        "optimize": 2,
        "brainstorm": 2,
        
        # Task combinati
        "research_and_outline": 1,
        "outline_and_draft": 1,
        "draft_and_review": 1,
        "review_and_finalize": 1,
        "edit_and_finalize": 2,
        "brainstorm_and_draft": 1,
        "optimize_and_finalize": 2
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Inizializza l'ottimizzatore LLM.
        
        Args:
            logger: Logger opzionale per il logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.call_history: List[Dict[str, Any]] = []
        self.quota_limits: Dict[str, int] = {}
        self.quota_used: Dict[str, int] = {}
        self.last_reset_time = time.time()
        self.reset_interval = 3600  # 1 ora di default
        self.token_manager = TokenManager(logger=self.logger)
        
    def set_quota_limit(self, model: str, limit: int, reset_interval: int = 3600) -> None:
        """Imposta un limite di quota per un modello specifico.
        
        Args:
            model: Nome del modello
            limit: Limite di chiamate in un intervallo
            reset_interval: Intervallo di reset in secondi
        """
        self.quota_limits[model] = limit
        self.quota_used.setdefault(model, 0)
        self.reset_interval = reset_interval
        self.logger.info(f"Impostato limite di quota per {model}: {limit} chiamate ogni {reset_interval} secondi")
    
    def _check_and_reset_quota(self) -> None:
        """Controlla e resetta le quote se necessario."""
        current_time = time.time()
        if current_time - self.last_reset_time >= self.reset_interval:
            self.quota_used = {model: 0 for model in self.quota_used}
            self.last_reset_time = current_time
            self.logger.info("Quote API resettate")
    
    def _can_use_model(self, model: str) -> bool:
        """Verifica se un modello può essere utilizzato in base alle quote.
        
        Args:
            model: Nome del modello da verificare
            
        Returns:
            True se il modello può essere utilizzato, False altrimenti
        """
        self._check_and_reset_quota()
        
        if model not in self.quota_limits:
            return True
        
        return self.quota_used.get(model, 0) < self.quota_limits[model]
    
    def _record_model_usage(self, model: str, tokens: int, cost: float) -> None:
        """Registra l'utilizzo di un modello.
        
        Args:
            model: Nome del modello utilizzato
            tokens: Numero di token utilizzati
            cost: Costo stimato della chiamata
        """
        self.quota_used[model] = self.quota_used.get(model, 0) + 1
        
        self.call_history.append({
            "timestamp": time.time(),
            "model": model,
            "tokens": tokens,
            "cost": cost
        })
    
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Stima il costo di una chiamata API.
        
        Args:
            model: Nome del modello
            input_tokens: Numero di token di input
            output_tokens: Numero di token di output
            
        Returns:
            Costo stimato in dollari
        """
        if model not in self.MODEL_COSTS:
            self.logger.warning(f"Modello {model} non trovato nella tabella dei costi, utilizzo stima predefinita")
            return 0.01  # Stima predefinita
        
        # Calcola il costo basato sul numero di token
        cost_per_1k = self.MODEL_COSTS[model]
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * cost_per_1k
    
    def _determine_task_complexity(self, task_name: str) -> str:
        """Determina la complessità di un task.
        
        Args:
            task_name: Nome del task
            
        Returns:
            Livello di complessità ('high', 'medium', 'low')
        """
        # Task che richiedono modelli potenti - ridotti al minimo essenziale
        high_complexity_tasks = ["expert_review", "technical_draft"]
        
        # Task di media complessità - incluso research (abbassato da high)
        medium_complexity_tasks = ["research", "draft", "edit", "review"]
        
        # Task semplici - incluso outline (abbassato da medium)
        low_complexity_tasks = ["outline", "finalize", "optimize", "brainstorm"]
        
        # Gestisci i task uniti
        if "_and_" in task_name:
            subtasks = task_name.split("_and_")
            # Usa la complessità più alta tra i subtask
            for subtask in subtasks:
                if subtask in high_complexity_tasks:
                    return "high"
            for subtask in subtasks:
                if subtask in medium_complexity_tasks:
                    return "medium"
            return "low"
        
        # Task singoli
        if task_name in high_complexity_tasks:
            return "high"
        elif task_name in medium_complexity_tasks:
            return "medium"
        else:
            return "low"
            
    def select_optimal_model(self, task_complexity: str, provider_preference: Optional[str] = None, task_name: Optional[str] = None) -> str:
        """Seleziona il modello ottimale in base alla complessità del task e al nome del task.
        
        Args:
            task_complexity: Complessità del task ('high', 'medium', 'low')
            provider_preference: Provider preferito ('openai' o 'anthropic')
            task_name: Nome del task specifico (opzionale)
            
        Returns:
            Nome del modello ottimale
        """
        self._check_and_reset_quota()
        
        # Se abbiamo il nome del task, usiamo la mappatura predefinita più aggressiva
        if task_name and task_name in self.TASK_MODEL_MAPPING:
            tier_index = self.TASK_MODEL_MAPPING[task_name]
        else:
            # Altrimenti usiamo la complessità del task con preferenza per modelli più economici
            tier_index = {
                "high": 0,  # Tier 1 (più potente)
                "medium": 1,  # Tier 2
                "low": 2  # Tier 3 (meno potente)
            }.get(task_complexity.lower(), 1)  # Default a Tier 2 invece di Tier 1
        
        # Seleziona i modelli nel tier appropriato
        tier_models = self.MODEL_TIERS[tier_index]
        
        # Filtra per provider se specificato
        if provider_preference:
            filtered_models = [m for m in tier_models if provider_preference.lower() in m.lower()]
            if filtered_models:
                tier_models = filtered_models
        
        # Verifica quale modello può essere utilizzato in base alle quote
        for model in tier_models:
            if self._can_use_model(model):
                return model
        
        # Se nessun modello nel tier può essere utilizzato, prova con il tier successivo
        for i in range(tier_index + 1, len(self.MODEL_TIERS)):
            for model in self.MODEL_TIERS[i]:
                if self._can_use_model(model):
                    self.logger.warning(f"Utilizzando modello di tier inferiore {model} a causa dei limiti di quota")
                    return model
        
        # Se tutti i modelli hanno raggiunto la quota, usa il primo del tier originale
        self.logger.warning(f"Tutti i modelli hanno raggiunto la quota, utilizzo {tier_models[0]} comunque")
        return tier_models[0]
    
    def optimize_prompt(self, prompt: str, model: str) -> str:
        """Ottimizza un prompt per ridurre il numero di token.
        
        Args:
            prompt: Prompt originale
            model: Modello target
            
        Returns:
            Prompt ottimizzato
        """
        # Ottimizzazione avanzata con TokenManager
        
        # Ottieni il limite di token per il modello
        model_token_limit = self.token_manager.get_model_token_limit(model)
        
        # Conta i token nel prompt originale
        original_token_count = self.token_manager.count_tokens(prompt, model)
        
        # Se il prompt è già sotto il 70% del limite, applica solo ottimizzazioni leggere
        if original_token_count < model_token_limit * 0.7:
            # Rimuovi spazi e newline multipli
            optimized = ' '.join(prompt.split())
            
            # Rimuovi istruzioni ridondanti comuni
            redundant_phrases = [
                "Per favore fornisci", 
                "Ti prego di", 
                "Assicurati di", 
                "Ricorda di",
                "È importante che tu",
                "Vorrei che tu",
                "Mi piacerebbe che tu",
                "Potresti per favore"
            ]
            
            for phrase in redundant_phrases:
                optimized = optimized.replace(phrase, "")
                
        else:
            # Ottimizzazione più aggressiva per prompt lunghi
            self.logger.warning(f"Prompt lungo rilevato per {model}: {original_token_count} token (limite: {model_token_limit})")
            
            # Rimuovi spazi e newline multipli
            optimized = ' '.join(prompt.split())
            
            # Rimuovi istruzioni ridondanti comuni (lista estesa)
            redundant_phrases = [
                "Per favore fornisci", 
                "Ti prego di", 
                "Assicurati di", 
                "Ricorda di",
                "È importante che tu",
                "Vorrei che tu",
                "Mi piacerebbe che tu",
                "Potresti per favore",
                "Tieni presente che",
                "Non dimenticare di",
                "Considera che",
                "Tieni a mente che",
                "Ricordati di",
                "Fai attenzione a"
            ]
            
            for phrase in redundant_phrases:
                optimized = optimized.replace(phrase, "")
            
            # Riduci lunghezza degli esempi se presenti
            if "esempio" in optimized.lower():
                # Strategia avanzata: tronca gli esempi lunghi
                parts = re.split(r'(?i)(esempio[^\n.]*)[:\n]', optimized)
                if len(parts) > 2:  # Abbiamo trovato almeno un esempio
                    result_parts = [parts[0]]  # Inizia con il testo prima del primo esempio
                    
                    for i in range(1, len(parts), 2):
                        if i+1 < len(parts):
                            example_intro = parts[i]  # "Esempio 1:" o simile
                            example_content = parts[i+1]
                            
                            # Se l'esempio è troppo lungo, troncalo
                            if len(example_content) > 200:
                                example_content = example_content[:200] + "..."
                                
                            result_parts.append(example_intro)
                            result_parts.append(example_content)
                    
                    optimized = ''.join(result_parts)
            
            # Se ancora troppo lungo, tronca il prompt
            current_token_count = self.token_manager.count_tokens(optimized, model)
            max_allowed_tokens = int(model_token_limit * 0.8)  # Lascia il 20% per la risposta
            
            if current_token_count > max_allowed_tokens:
                self.logger.warning(f"Troncatura necessaria: {current_token_count} token (max: {max_allowed_tokens})")
                optimized = self.token_manager.truncate_text(optimized, max_allowed_tokens, model)
        
        # Log della riduzione
        final_token_count = self.token_manager.count_tokens(optimized, model)
        reduction = (1 - (final_token_count / original_token_count)) * 100
        
        self.logger.info(f"Prompt ottimizzato: da {original_token_count} a {final_token_count} token ({reduction:.1f}% riduzione)")
        
        return optimized
    
    def optimize_llm_call(self, func: Callable) -> Callable:
        """Decoratore per ottimizzare le chiamate LLM.
        
        Args:
            func: Funzione da decorare che effettua chiamate LLM
            
        Returns:
            Funzione decorata
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Estrai parametri rilevanti
            model = kwargs.get("model", "gpt-4")
            prompt = kwargs.get("prompt", kwargs.get("messages", []))
            task_complexity = kwargs.pop("task_complexity", "high")
            provider_preference = kwargs.pop("provider_preference", None)
            task_name = kwargs.pop("task_name", None)
            
            # Ottieni il limite di token per il modello
            model_token_limit = self.token_manager.get_model_token_limit(model)
            
            # Conta i token nel prompt/messaggi originali
            original_token_count = self.token_manager.count_tokens(prompt, model)
            
            # Log del conteggio dei token
            self.logger.info(f"Token nel prompt originale: {original_token_count} (limite modello {model}: {model_token_limit})")
            
            # Seleziona il modello ottimale se non specificato esplicitamente
            if kwargs.get("auto_select_model", True):
                model = self.select_optimal_model(task_complexity, provider_preference, task_name)
                kwargs["model"] = model
                # Aggiorna il limite di token per il nuovo modello
                model_token_limit = self.token_manager.get_model_token_limit(model)
            
            # Stima preliminare del costo per il controllo del budget
            preliminary_cost = self.estimate_cost(model, original_token_count, int(original_token_count * 0.5))
            
            # Verifica se la chiamata supera il budget (se integrato con APICostOptimizer)
            if hasattr(self, '_check_budget') and callable(self._check_budget):
                if not self._check_budget(preliminary_cost):
                    self.logger.warning(f"Chiamata LLM bloccata: supera il budget giornaliero (costo stimato: ${preliminary_cost:.4f})")
                    # Fallback a un modello più economico se possibile
                    if model in self.MODEL_TIERS[0]:  # Se è un modello Tier 1
                        model = self.MODEL_TIERS[1][0]  # Usa il primo modello Tier 2
                        kwargs["model"] = model
                        self.logger.info(f"Fallback al modello più economico: {model}")
                    elif model in self.MODEL_TIERS[1]:  # Se è un modello Tier 2
                        model = self.MODEL_TIERS[2][0]  # Usa il primo modello Tier 3
                        kwargs["model"] = model
                        self.logger.info(f"Fallback al modello più economico: {model}")
                    # Aggiorna il limite di token per il nuovo modello
                    model_token_limit = self.token_manager.get_model_token_limit(model)
            
            # Verifica se il prompt supera il limite di token e ottimizza
            if original_token_count > model_token_limit * 0.8:  # Se supera l'80% del limite
                self.logger.warning(f"Prompt troppo lungo per {model}: {original_token_count} token (limite: {model_token_limit})")
                
                # Ottimizza in base al tipo di prompt
                if isinstance(prompt, str):
                    # Ottimizza il prompt testuale
                    optimized_prompt = self.optimize_prompt(prompt, model)
                    kwargs["prompt"] = optimized_prompt
                    
                    # Verifica se è ancora troppo lungo
                    optimized_token_count = self.token_manager.count_tokens(optimized_prompt, model)
                    if optimized_token_count > model_token_limit * 0.8:
                        self.logger.warning(f"Prompt ancora troppo lungo dopo ottimizzazione: {optimized_token_count} token")
                        # Tronca il prompt se necessario
                        max_allowed_tokens = int(model_token_limit * 0.8)  # 80% del limite
                        truncated_prompt = self.token_manager.truncate_text(optimized_prompt, max_allowed_tokens, model)
                        kwargs["prompt"] = truncated_prompt
                        self.logger.info(f"Prompt troncato a {self.token_manager.count_tokens(truncated_prompt, model)} token")
                        
                elif isinstance(prompt, list) and prompt:  # Per formati di messaggi come in OpenAI/DeepSeek
                    # Ottimizza i messaggi
                    optimized_messages = self.token_manager.optimize_messages(prompt, model)
                    
                    # Verifica se l'ottimizzazione è sufficiente
                    optimized_token_count = self.token_manager.count_tokens(optimized_messages, model)
                    if optimized_token_count > model_token_limit * 0.8:
                        self.logger.warning(f"Messaggi ancora troppo lunghi dopo ottimizzazione: {optimized_token_count} token")
                        
                        # Ottimizza ulteriormente riducendo il numero di messaggi
                        # Mantieni solo il messaggio di sistema (se presente) e l'ultimo messaggio utente
                        system_message = None
                        last_user_message = None
                        
                        for msg in reversed(optimized_messages):
                            if msg.get("role") == "user" and not last_user_message:
                                last_user_message = msg
                            elif msg.get("role") == "system":
                                system_message = msg
                        
                        reduced_messages = []
                        if system_message:
                            reduced_messages.append(system_message)
                        if last_user_message:
                            reduced_messages.append(last_user_message)
                        
                        # Ottimizza i contenuti dei messaggi rimanenti
                        for msg in reduced_messages:
                            if "content" in msg and isinstance(msg["content"], str):
                                msg["content"] = self.optimize_prompt(msg["content"], model)
                        
                        kwargs["messages"] = reduced_messages
                        self.logger.info(f"Messaggi ridotti a {len(reduced_messages)} con {self.token_manager.count_tokens(reduced_messages, model)} token")
                    else:
                        kwargs["messages"] = optimized_messages
                        self.logger.info(f"Messaggi ottimizzati a {self.token_manager.count_tokens(optimized_messages, model)} token")
            else:
                # Se il prompt è già abbastanza corto, applica solo ottimizzazioni leggere
                if isinstance(prompt, str):
                    optimized_prompt = self.optimize_prompt(prompt, model)
                    kwargs["prompt"] = optimized_prompt
                elif isinstance(prompt, list) and prompt:  # Per formati di messaggi come in OpenAI
                    # Ottimizza solo i contenuti dei messaggi
                    for i, msg in enumerate(prompt):
                        if "content" in msg and isinstance(msg["content"], str):
                            msg["content"] = self.optimize_prompt(msg["content"], model)
                    kwargs["messages"] = prompt
            
            # Esegui la chiamata
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                # Stima token e costi
                input_tokens = kwargs.get("input_tokens", 0)
                output_tokens = 0
                
                # Estrai token di output dal risultato se disponibile
                if hasattr(result, "usage") and hasattr(result.usage, "completion_tokens"):
                    output_tokens = result.usage.completion_tokens
                    input_tokens = result.usage.prompt_tokens
                
                # Stima il costo
                cost = self.estimate_cost(model, input_tokens, output_tokens)
                
                # Registra l'utilizzo
                self._record_model_usage(model, input_tokens + output_tokens, cost)
                
                # Aggiorna il costo giornaliero se integrato con APICostOptimizer
                if hasattr(self, '_update_daily_cost') and callable(self._update_daily_cost):
                    self._update_daily_cost(cost)
                
                self.logger.info(f"Chiamata LLM: modello={model}, tempo={elapsed:.2f}s, token={input_tokens+output_tokens}, costo=${cost:.4f}")
                
                return result
            except Exception as e:
                # Gestisci errori specifici relativi ai token
                error_str = str(e).lower()
                if "token" in error_str and ("limit" in error_str or "exceed" in error_str or "context length" in error_str):
                    self.logger.error(f"Errore di limite token con {model}: {e}")
                    
                    # Se è un errore di token con DeepSeek, prova a ridurre drasticamente
                    if "deepseek" in model.lower():
                        self.logger.warning("Tentativo di recupero con riduzione drastica dei token per DeepSeek")
                        
                        # Riduci drasticamente i messaggi
                        if isinstance(prompt, list) and prompt:
                            # Mantieni solo il messaggio di sistema (se presente) e l'ultimo messaggio utente
                            system_message = None
                            last_user_message = None
                            
                            for msg in prompt:
                                if msg.get("role") == "user":
                                    last_user_message = msg
                                elif msg.get("role") == "system":
                                    system_message = msg
                            
                            emergency_messages = []
                            if system_message:
                                # Tronca il messaggio di sistema se necessario
                                content = system_message.get("content", "")
                                if len(content) > 1000:
                                    system_message["content"] = content[:1000] + "..."
                                emergency_messages.append(system_message)
                            
                            if last_user_message:
                                # Tronca l'ultimo messaggio utente se necessario
                                content = last_user_message.get("content", "")
                                max_content_tokens = 3000  # Limite arbitrario per DeepSeek
                                if self.token_manager.count_tokens(content, model) > max_content_tokens:
                                    last_user_message["content"] = self.token_manager.truncate_text(content, max_content_tokens, model)
                                emergency_messages.append(last_user_message)
                            
                            kwargs["messages"] = emergency_messages
                            
                            # Riprova la chiamata
                            self.logger.info(f"Riprovo con messaggi ridotti: {self.token_manager.count_tokens(emergency_messages, model)} token")
                            return func(*args, **kwargs)
                    
                # Rilancia l'eccezione originale se non gestita
                raise
        
        return wrapper
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche di utilizzo.
        
        Returns:
            Dizionario con statistiche di utilizzo
        """
        total_cost = sum(call["cost"] for call in self.call_history)
        total_tokens = sum(call["tokens"] for call in self.call_history)
        calls_per_model = {}
        cost_per_model = {}
        
        for call in self.call_history:
            model = call["model"]
            calls_per_model[model] = calls_per_model.get(model, 0) + 1
            cost_per_model[model] = cost_per_model.get(model, 0) + call["cost"]
        
        return {
            "total_calls": len(self.call_history),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "calls_per_model": calls_per_model,
            "cost_per_model": cost_per_model,
            "quota_used": self.quota_used,
            "quota_limits": self.quota_limits
        }