"""Ottimizzatore dei workflow per ridurre le chiamate API e ottimizzare l'uso dei token."""

import logging
from typing import Dict, Any, List, Optional, Tuple
from .cache_manager import CacheManager
from .llm_optimizer import LLMOptimizer
from .token_manager import TokenManager
from .workflow_chunking import WorkflowChunking

class WorkflowOptimizer:
    """Ottimizza i workflow degli agenti per ridurre le chiamate API."""
    
    def __init__(self, cache_manager: CacheManager, llm_optimizer: LLMOptimizer, 
                 logger: Optional[logging.Logger] = None):
        """Inizializza l'ottimizzatore dei workflow.
        
        Args:
            cache_manager: Gestore della cache
            llm_optimizer: Ottimizzatore LLM
            logger: Logger opzionale
        """
        self.cache_manager = cache_manager
        self.llm_optimizer = llm_optimizer
        self.logger = logger or logging.getLogger(__name__)
        self.workflow_stats = {}
        
        # Inizializza il gestore dei token e il sistema di chunking
        self.token_manager = TokenManager(logger=self.logger)
        self.workflow_chunking = WorkflowChunking(self.token_manager, logger=self.logger)
    
    def optimize_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Ottimizza un workflow per ridurre le chiamate API.
        
        Args:
            workflow_config: Configurazione originale del workflow
            
        Returns:
            Configurazione ottimizzata del workflow
        """
        if not workflow_config or "steps" not in workflow_config:
            self.logger.warning("Configurazione workflow non valida")
            return workflow_config
        
        steps = workflow_config["steps"]
        optimized_steps = self._merge_compatible_steps(steps)
        
        # Aggiorna la configurazione con i passaggi ottimizzati
        optimized_config = workflow_config.copy()
        optimized_config["steps"] = optimized_steps
        
        # Calcola e registra le statistiche di ottimizzazione
        original_steps = len(steps)
        new_steps = len(optimized_steps)
        reduction = ((original_steps - new_steps) / original_steps) * 100 if original_steps > 0 else 0
        
        workflow_name = workflow_config.get("name", "unnamed")
        self.workflow_stats[workflow_name] = {
            "original_steps": original_steps,
            "optimized_steps": new_steps,
            "reduction_percentage": reduction,
            "estimated_api_calls_saved": original_steps - new_steps
        }
        
        self.logger.info(f"Workflow '{workflow_name}' ottimizzato: {original_steps} → {new_steps} steps ({reduction:.1f}% riduzione)")
        
        return optimized_config
    
    def _merge_compatible_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Unisce passaggi compatibili per ridurre le chiamate API.
        
        Args:
            steps: Lista originale dei passaggi del workflow
            
        Returns:
            Lista ottimizzata dei passaggi
        """
        if not steps or len(steps) <= 1:
            return steps
        
        # Identifica gruppi di passaggi che possono essere uniti
        optimized_steps = []
        current_group = [steps[0]]
        
        for i in range(1, len(steps)):
            current_step = steps[i]
            prev_step = steps[i-1]
            
            # Verifica se i passaggi possono essere uniti
            if self._can_merge_steps(prev_step, current_step):
                current_group.append(current_step)
            else:
                # Unisci il gruppo corrente e inizia un nuovo gruppo
                if len(current_group) > 1:
                    merged_step = self._create_merged_step(current_group)
                    optimized_steps.append(merged_step)
                else:
                    optimized_steps.append(current_group[0])
                current_group = [current_step]
        
        # Gestisci l'ultimo gruppo
        if current_group:
            if len(current_group) > 1:
                merged_step = self._create_merged_step(current_group)
                optimized_steps.append(merged_step)
            else:
                optimized_steps.append(current_group[0])
        
        return optimized_steps
    
    def _can_merge_steps(self, step1: Dict[str, Any], step2: Dict[str, Any]) -> bool:
        """Determina se due passaggi possono essere uniti.
        
        Args:
            step1: Primo passaggio
            step2: Secondo passaggio
            
        Returns:
            True se i passaggi possono essere uniti, False altrimenti
        """
        # Criteri per determinare se i passaggi possono essere uniti:
        # 1. Entrambi i passaggi sono dello stesso tipo o complementari
        # 2. Non ci sono dipendenze complesse tra i passaggi
        
        # Passaggi che possono essere uniti - versione più aggressiva
        mergeable_pairs = [
            # Ricerca e outline possono essere uniti
            ("research", "outline"),
            # Outline e bozza possono essere uniti
            ("outline", "draft"),
            # Bozza e revisione possono essere unite
            ("draft", "review"),
            # Editing e finalizzazione possono essere uniti
            ("edit", "finalize"),
            # Brainstorming e bozza possono essere uniti
            ("brainstorm", "draft"),
            # Revisione e finalizzazione possono essere uniti
            ("review", "finalize"),
            # Ottimizzazione e finalizzazione possono essere uniti
            ("optimize", "finalize"),
            # Review ed edit possono essere uniti (nuovo)
            ("review", "edit")
        ]
        
        task1 = step1.get("task", "")
        task2 = step2.get("task", "")
        
        # Verifica se la coppia di task è nella lista delle coppie unibili
        for pair in mergeable_pairs:
            if (task1 == pair[0] and task2 == pair[1]) or (task1 == pair[1] and task2 == pair[0]):
                return True
        
        # Verifica se entrambi i task sono di bassa complessità
        low_complexity_tasks = ["finalize", "optimize", "brainstorm", "outline"]
        if task1 in low_complexity_tasks and task2 in low_complexity_tasks:
            return True
            
        return False
    
    def _create_merged_step(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea un passaggio unito da un gruppo di passaggi.
        
        Args:
            steps: Lista di passaggi da unire
            
        Returns:
            Passaggio unito
        """
        if not steps:
            return {}
        
        # Estrai i nomi dei task
        task_names = [step.get("task", "") for step in steps]
        merged_task_name = "_and_".join(task_names)
        
        # Combina le descrizioni
        descriptions = [step.get("description", "") for step in steps]
        merged_description = " + ".join(descriptions)
        
        return {
            "task": merged_task_name,
            "description": merged_description,
            "original_tasks": task_names,
            "merged": True
        }
    
    def assign_optimal_models(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Assegna i modelli ottimali per ogni passaggio del workflow.
        
        Args:
            workflow_config: Configurazione del workflow
            
        Returns:
            Configurazione con modelli ottimali assegnati
        """
        if not workflow_config or "steps" not in workflow_config:
            return workflow_config
        
        steps = workflow_config["steps"]
        for step in steps:
            task_name = step.get("task", "")
            # Assegna la complessità del task in base al tipo
            complexity = self._determine_task_complexity(task_name)
            # Assegna il provider preferito in base al tipo di task
            provider = self._determine_provider_preference(task_name)
            
            # Aggiungi le informazioni di ottimizzazione al passaggio
            step["optimization"] = {
                "task_complexity": complexity,
                "provider_preference": provider,
                "auto_select_model": True
            }
        
        return workflow_config
    
    def _determine_task_complexity(self, task_name: str) -> str:
        """Determina la complessità di un task.
        
        Args:
            task_name: Nome del task
            
        Returns:
            Livello di complessità ('high', 'medium', 'low')
        """
        # Task che richiedono modelli potenti
        high_complexity_tasks = ["expert_review", "technical_draft", "research"]
        
        # Task di media complessità
        medium_complexity_tasks = ["outline", "draft", "edit", "review"]
        
        # Task semplici
        low_complexity_tasks = ["finalize", "optimize", "brainstorm"]
        
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
    
    def _determine_provider_preference(self, task_name: str) -> Optional[str]:
        """Determina il provider preferito per un task.
        
        Args:
            task_name: Nome del task
            
        Returns:
            Provider preferito ('openai', 'anthropic', 'deepseek') o None
        """
        # Task che funzionano meglio con OpenAI
        openai_tasks = ["research", "outline", "finalize"]
        
        # Task che funzionano meglio con Anthropic
        anthropic_tasks = ["draft", "technical_draft", "edit"]
        
        # Task che funzionano meglio con DeepSeek (modalità economica)
        deepseek_tasks = ["research", "draft", "finalize"]
        
        # Verifica se è attiva la modalità economica
        economic_mode = os.getenv('ECONOMIC_MODE', 'false').lower() == 'true'
        
        # Gestisci i task uniti
        if "_and_" in task_name:
            subtasks = task_name.split("_and_")
            
            if economic_mode:
                # In modalità economica, preferisci DeepSeek quando possibile
                deepseek_count = sum(1 for t in subtasks if t in deepseek_tasks)
                if deepseek_count > 0:
                    return "deepseek"
                return None  # Nessuna preferenza specifica, usa il default economico
            else:
                # In modalità normale, bilancia tra OpenAI e Anthropic
                openai_count = sum(1 for t in subtasks if t in openai_tasks)
                anthropic_count = sum(1 for t in subtasks if t in anthropic_tasks)
                
                if openai_count > anthropic_count:
                    return "openai"
                elif anthropic_count > openai_count:
                    return "anthropic"
                else:
                    return None  # Nessuna preferenza
        
        # Task singoli
        if economic_mode:
            if task_name in deepseek_tasks:
                return "deepseek"
            return None  # Nessuna preferenza specifica, usa il default economico
        else:
            if task_name in openai_tasks:
                return "openai"
            elif task_name in anthropic_tasks:
                return "anthropic"
            else:
                return None  # Nessuna preferenza
    
    def optimize_agent_communication(self, messages: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
        """Ottimizza i messaggi tra agenti per rispettare i limiti di token.
        
        Args:
            messages: Lista di messaggi tra agenti
            model: Modello LLM da utilizzare
            
        Returns:
            Lista di messaggi ottimizzata
        """
        # Utilizza il workflow_chunking per ottimizzare i messaggi
        return self.workflow_chunking.optimize_agent_messages(messages, model)
    
    def process_chunked_content(self, content: str, process_func: callable, model: str, **kwargs) -> str:
        """Elabora un contenuto lungo dividendolo in chunk se necessario.
        
        Args:
            content: Contenuto da elaborare
            process_func: Funzione che elabora un singolo chunk
            model: Modello LLM da utilizzare
            **kwargs: Argomenti aggiuntivi da passare alla funzione di elaborazione
            
        Returns:
            Risultato dell'elaborazione
        """

    def check_guidelines_adherence(self, content: str, guidelines: str, threshold: float = 0.85) -> bool:
        """Verifica se il contenuto è già aderente alle linee guida.
        
        Args:
            content: Contenuto da verificare
            guidelines: Linee guida da rispettare
            threshold: Soglia di aderenza (da 0 a 1)
            
        Returns:
            True se il contenuto è già aderente alle linee guida, False altrimenti
        """
        # Implementazione semplificata che può essere migliorata con NLP più avanzato
        if not content or not guidelines:
            return False
            
        # Estrai i punti chiave dalle linee guida
        key_points = self._extract_key_points(guidelines)
        
        # Verifica quanti punti chiave sono presenti nel contenuto
        matches = 0
        for point in key_points:
            if point.lower() in content.lower():
                matches += 1
                
        # Calcola la percentuale di aderenza
        adherence_score = matches / max(1, len(key_points))
        
        self.logger.info(f"Aderenza alle linee guida: {adherence_score:.2f} ({matches}/{len(key_points)} punti)")
        
        return adherence_score >= threshold
    
    def _extract_key_points(self, guidelines: str) -> List[str]:
        """Estrae i punti chiave dalle linee guida.
        
        Args:
            guidelines: Linee guida
            
        Returns:
            Lista di punti chiave
        """
        # Questa è una versione semplificata che può essere migliorata
        # Estrae elementi da elenchi puntati e titoli
        key_points = []
        
        # Estrai i titoli (## Heading)
        import re
        headings = re.findall(r'##\s+(.+?)$', guidelines, re.MULTILINE)
        key_points.extend(headings)
        
        # Estrai elementi puntati (- Item o * Item)
        bullet_points = re.findall(r'[-*]\s+(.+?)$', guidelines, re.MULTILINE)
        key_points.extend(bullet_points)
        
        # Estrai elementi in grassetto (**Item**)
        bold_items = re.findall(r'\*\*(.+?)\*\*', guidelines)
        key_points.extend(bold_items)
        
        return key_points

        # Verifica se il contenuto è troppo lungo per il modello
        content_tokens = self.token_manager.count_tokens(content, model)
        model_limit = self.token_manager.get_model_token_limit(model)
        
        # Se il contenuto è abbastanza corto, elaboralo direttamente
        if content_tokens <= model_limit * 0.7:  # 70% del limite
            return process_func(content, **kwargs)
        
        # Altrimenti, dividi in chunk e processa separatamente
        self.logger.warning(f"Contenuto troppo lungo per {model}: {content_tokens} token (limite: {model_limit})")
        chunks = self.workflow_chunking.chunk_workflow_content(content, model)
        self.logger.info(f"Contenuto diviso in {len(chunks)} chunk")
        
        return self.workflow_chunking.process_chunked_workflow(chunks, process_func, model=model, **kwargs)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche di ottimizzazione dei workflow.
        
        Returns:
            Dizionario con statistiche di ottimizzazione
        """
        total_original_steps = sum(stats["original_steps"] for stats in self.workflow_stats.values())
        total_optimized_steps = sum(stats["optimized_steps"] for stats in self.workflow_stats.values())
        total_reduction = ((total_original_steps - total_optimized_steps) / total_original_steps) * 100 if total_original_steps > 0 else 0
        total_saved_calls = total_original_steps - total_optimized_steps
        
        return {
            "workflows_optimized": len(self.workflow_stats),
            "total_original_steps": total_original_steps,
            "total_optimized_steps": total_optimized_steps,
            "total_reduction_percentage": total_reduction,
            "total_api_calls_saved": total_saved_calls,
            "workflow_details": self.workflow_stats
        }