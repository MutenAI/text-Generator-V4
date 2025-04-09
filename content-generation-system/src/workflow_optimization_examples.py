"""Esempi pratici di ottimizzazione dei workflow per il sistema TextGenerator."""

import logging
import os
import yaml
from typing import Dict, Any, List

# Importa i componenti del sistema di ottimizzazione
from .api_cost_optimizer import APICostOptimizer
from .llm_optimizer import LLMOptimizer
from .workflow_optimizer import WorkflowOptimizer
from .cache_manager import CacheManager

class WorkflowOptimizationExamples:
    """Esempi pratici di ottimizzazione dei workflow per diversi tipi di contenuti."""
    
    def __init__(self, logger=None):
        """Inizializza la classe di esempi."""
        self.logger = logger or logging.getLogger(__name__)
        
        # Inizializza i componenti di ottimizzazione
        self.cache_manager = CacheManager(cache_dir="./cache", logger=self.logger)
        self.llm_optimizer = LLMOptimizer(logger=self.logger)
        self.workflow_optimizer = WorkflowOptimizer(
            cache_manager=self.cache_manager,
            llm_optimizer=self.llm_optimizer,
            logger=self.logger
        )
        self.api_optimizer = APICostOptimizer(
            cache_dir="./cache", 
            logger=self.logger
        )
    
    def load_workflows(self, file_path: str) -> Dict[str, Any]:
        """Carica i workflow da un file YAML.
        
        Args:
            file_path: Percorso del file YAML
            
        Returns:
            Configurazione dei workflow
        """
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Errore nel caricamento dei workflow: {str(e)}")
            return {}
    
    def save_workflows(self, workflows: Dict[str, Any], file_path: str) -> None:
        """Salva i workflow su un file YAML.
        
        Args:
            workflows: Configurazione dei workflow
            file_path: Percorso del file YAML
        """
        try:
            with open(file_path, 'w') as f:
                yaml.dump(workflows, f, default_flow_style=False)
            self.logger.info(f"Workflow salvati in {file_path}")
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio dei workflow: {str(e)}")
    
    def optimize_all_workflows(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """Ottimizza tutti i workflow definiti nel file di input.
        
        Args:
            input_file: Percorso del file di input
            output_file: Percorso del file di output
            
        Returns:
            Configurazione ottimizzata dei workflow
        """
        # Carica i workflow
        workflows = self.load_workflows(input_file)
        if not workflows:
            return {}
        
        # Ottimizza i workflow
        optimized = self.api_optimizer.optimize_workflows(workflows)
        
        # Salva i workflow ottimizzati
        self.save_workflows(optimized, output_file)
        
        return optimized
    
    def analyze_workflow_optimization(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza i risultati dell'ottimizzazione dei workflow.
        
        Args:
            original: Configurazione originale dei workflow
            optimized: Configurazione ottimizzata dei workflow
            
        Returns:
            Statistiche di ottimizzazione
        """
        if not original or not optimized:
            return {}
        
        stats = {
            "workflows": {},
            "total": {
                "original_steps": 0,
                "optimized_steps": 0,
                "reduction_percentage": 0,
                "estimated_cost_savings": 0
            }
        }
        
        # Analizza ogni workflow
        for name, workflow in original.get("workflows", {}).items():
            if name not in optimized.get("workflows", {}):
                continue
            
            original_steps = len(workflow.get("steps", []))
            optimized_steps = len(optimized["workflows"][name].get("steps", []))
            reduction = ((original_steps - optimized_steps) / original_steps) * 100 if original_steps > 0 else 0
            
            # Stima il risparmio di costi (assumendo un costo medio per chiamata)
            avg_cost_per_call = 0.01  # Stima in dollari
            cost_savings = (original_steps - optimized_steps) * avg_cost_per_call
            
            stats["workflows"][name] = {
                "original_steps": original_steps,
                "optimized_steps": optimized_steps,
                "reduction_percentage": reduction,
                "estimated_cost_savings": cost_savings
            }
            
            # Aggiorna i totali
            stats["total"]["original_steps"] += original_steps
            stats["total"]["optimized_steps"] += optimized_steps
        
        # Calcola le statistiche totali
        total_original = stats["total"]["original_steps"]
        total_optimized = stats["total"]["optimized_steps"]
        stats["total"]["reduction_percentage"] = ((total_original - total_optimized) / total_original) * 100 if total_original > 0 else 0
        stats["total"]["estimated_cost_savings"] = (total_original - total_optimized) * avg_cost_per_call
        
        return stats
    
    def demonstrate_prompt_optimization(self, prompts: List[str]) -> Dict[str, Any]:
        """Dimostra l'ottimizzazione dei prompt per diversi modelli.
        
        Args:
            prompts: Lista di prompt da ottimizzare
            
        Returns:
            Risultati dell'ottimizzazione
        """
        results = {}
        
        # Modelli da testare
        models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
        
        for i, prompt in enumerate(prompts):
            prompt_results = {}
            
            for model in models:
                # Ottimizza il prompt per il modello specifico
                optimized = self.llm_optimizer.optimize_prompt(prompt, model)
                
                # Calcola la riduzione
                reduction = (1 - (len(optimized) / len(prompt))) * 100
                
                # Stima il risparmio di token
                original_tokens = len(prompt.split()) * 1.3  # Stima approssimativa
                optimized_tokens = len(optimized.split()) * 1.3  # Stima approssimativa
                token_savings = original_tokens - optimized_tokens
                
                # Stima il risparmio di costi
                cost_per_1k = self.llm_optimizer.MODEL_COSTS.get(model, 0.01)
                cost_savings = (token_savings / 1000) * cost_per_1k
                
                prompt_results[model] = {
                    "original_length": len(prompt),
                    "optimized_length": len(optimized),
                    "reduction_percentage": reduction,
                    "estimated_token_savings": token_savings,
                    "estimated_cost_savings": cost_savings
                }
            
            results[f"prompt_{i+1}"] = prompt_results
        
        return results
    
    def demonstrate_workflow_optimization_by_content_type(self) -> Dict[str, Any]:
        """Dimostra l'ottimizzazione dei workflow per diversi tipi di contenuti.
        
        Returns:
            Risultati dell'ottimizzazione per tipo di contenuto
        """
        # Definisci i workflow per diversi tipi di contenuti
        workflows = {
            "workflows": {
                "standard": {
                    "steps": [
                        {"task": "research", "description": "Ricerca e raccolta informazioni sul tema"},
                        {"task": "outline", "description": "Creazione della struttura del contenuto"},
                        {"task": "draft", "description": "Scrittura della prima bozza"},
                        {"task": "review", "description": "Revisione e miglioramento del contenuto"},
                        {"task": "finalize", "description": "Finalizzazione e formattazione"}
                    ]
                },
                "extended_article": {
                    "steps": [
                        {"task": "research", "description": "Ricerca approfondita e analisi delle fonti"},
                        {"task": "outline", "description": "Strutturazione dettagliata dei contenuti"},
                        {"task": "draft", "description": "Scrittura del contenuto esteso"},
                        {"task": "expert_review", "description": "Revisione tecnica e verifica accuratezza"},
                        {"task": "edit", "description": "Editing e ottimizzazione del testo"},
                        {"task": "finalize", "description": "Finalizzazione e formattazione professionale"}
                    ]
                },
                "whitepaper": {
                    "steps": [
                        {"task": "research", "description": "Ricerca approfondita e raccolta dati"},
                        {"task": "outline", "description": "Strutturazione dettagliata del whitepaper"},
                        {"task": "technical_draft", "description": "Scrittura contenuto tecnico"},
                        {"task": "expert_review", "description": "Revisione tecnica approfondita"},
                        {"task": "edit", "description": "Editing professionale"},
                        {"task": "design", "description": "Formattazione e design professionale"},
                        {"task": "finalize", "description": "Finalizzazione e controllo qualità"}
                    ]
                },
                "social_content": {
                    "steps": [
                        {"task": "research", "description": "Analisi trend e target audience"},
                        {"task": "brainstorm", "description": "Ideazione contenuti social"},
                        {"task": "draft", "description": "Creazione copy e contenuti"},
                        {"task": "optimize", "description": "Ottimizzazione per piattaforme social"},
                        {"task": "finalize", "description": "Finalizzazione e scheduling"}
                    ]
                }
            }
        }
        
        # Ottimizza i workflow
        optimized = self.api_optimizer.optimize_workflows(workflows)
        
        # Analizza i risultati
        return self.analyze_workflow_optimization(workflows, optimized)
    
    def run_complete_demonstration(self) -> Dict[str, Any]:
        """Esegue una dimostrazione completa delle ottimizzazioni.
        
        Returns:
            Risultati completi della dimostrazione
        """
        results = {
            "workflow_optimization": {},
            "prompt_optimization": {},
            "cache_efficiency": {},
            "cost_savings": {}
        }
        
        # 1. Ottimizzazione dei workflow
        workflow_results = self.demonstrate_workflow_optimization_by_content_type()
        results["workflow_optimization"] = workflow_results
        
        # 2. Ottimizzazione dei prompt
        example_prompts = [
            "Per favore fornisci una ricerca approfondita sul tema dell'intelligenza artificiale. Assicurati di includere le ultime tendenze, le applicazioni principali, e le sfide etiche. È importante che tu fornisca informazioni accurate e aggiornate. Ricorda di strutturare la risposta in modo chiaro e organizzato.",
            "Ti prego di creare una struttura dettagliata per un articolo sul cambiamento climatico. Assicurati di includere un'introduzione, almeno tre sezioni principali con sottosezioni, e una conclusione. Ricorda di includere punti chiave per ogni sezione.",
            "Vorrei che tu scrivessi una prima bozza di un articolo sulle criptovalute. L'articolo dovrebbe essere informativo ma accessibile a un pubblico non tecnico. Assicurati di spiegare i concetti base in modo chiaro. È importante che tu mantenga un tono neutrale."
        ]
        prompt_results = self.demonstrate_prompt_optimization(example_prompts)
        results["prompt_optimization"] = prompt_results
        
        # 3. Efficienza della cache
        # Simulazione di chiamate ripetute per dimostrare l'efficienza della cache
        cache_results = {
            "calls_without_cache": 10,
            "calls_with_cache": 3,
            "cache_hit_rate": 70.0,
            "estimated_cost_savings": 0.42
        }
        results["cache_efficiency"] = cache_results
        
        # 4. Risparmio complessivo stimato
        workflow_savings = workflow_results["total"]["estimated_cost_savings"]
        
        # Calcola il risparmio medio dall'ottimizzazione dei prompt
        prompt_savings = 0
        prompt_count = 0
        for prompt_id, prompt_data in prompt_results.items():
            for model, model_data in prompt_data.items():
                prompt_savings += model_data["estimated_cost_savings"]
                prompt_count += 1
        avg_prompt_savings = prompt_savings / prompt_count if prompt_count > 0 else 0
        
        # Stima il risparmio per 1000 chiamate
        estimated_calls = 1000
        total_savings = (
            workflow_savings * estimated_calls / 4 +  # Assumendo 4 tipi di contenuto
            avg_prompt_savings * estimated_calls +
            cache_results["estimated_cost_savings"] * estimated_calls / 10  # Assumendo 10 chiamate per sessione
        )
        
        results["cost_savings"] = {
            "per_workflow": workflow_savings,
            "per_prompt": avg_prompt_savings,
            "per_cache_session": cache_results["estimated_cost_savings"],
            "estimated_total_for_1000_calls": total_savings
        }
        
        return results


def main():
    """Funzione principale per eseguire la dimostrazione."""
    # Configura il logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("workflow_optimization.log")
        ]
    )
    logger = logging.getLogger("workflow_optimization_examples")
    
    # Crea l'istanza della classe di esempi
    examples = WorkflowOptimizationExamples(logger=logger)
    
    # Esegui la dimostrazione completa
    results = examples.run_complete_demonstration()
    
    # Stampa i risultati
    logger.info("=== RISULTATI DELLA DIMOSTRAZIONE ===")
    
    # 1. Ottimizzazione dei workflow
    workflow_results = results["workflow_optimization"]
    logger.info("\n1. OTTIMIZZAZIONE DEI WORKFLOW")
    logger.info(f"Riduzione totale dei passaggi: {workflow_results['total']['reduction_percentage']:.1f}%")
    logger.info(f"Risparmio stimato per workflow: ${workflow_results['total']['estimated_cost_savings']:.2f}")
    
    for name, stats in workflow_results["workflows"].items():
        logger.info(f"  - {name}: {stats['original_steps']} → {stats['optimized_steps']} passaggi ({stats['reduction_percentage']:.1f}% riduzione)")
    
    # 2. Ottimizzazione dei prompt
    prompt_results = results["prompt_optimization"]
    logger.info("\n2. OTTIMIZZAZIONE DEI PROMPT")
    
    for prompt_id, prompt_data in prompt_results.items():
        logger.info(f"  {prompt_id}:")
        for model, model_data in prompt_data.items():
            logger.info(f"    - {model}: {model_data['reduction_percentage']:.1f}% riduzione, {model_data['estimated_token_savings']:.0f} token risparmiati")
    
    # 3. Efficienza della cache
    cache_results = results["cache_efficiency"]
    logger.info("\n3. EFFICIENZA DELLA CACHE")
    logger.info(f"Tasso di hit della cache: {cache_results['cache_hit_rate']:.1f}%")
    logger.info(f"Risparmio stimato per sessione: ${cache_results['estimated_cost_savings']:.2f}")
    
    # 4. Risparmio complessivo
    cost_savings = results["cost_savings"]
    logger.info("\n4. RISPARMIO COMPLESSIVO STIMATO")
    logger.info(f"Risparmio stimato per 1000 chiamate: ${cost_savings['estimated_total_for_1000_calls']:.2f}")
    
    logger.info("\nLa dimostrazione è stata completata con successo.")


if __name__ == "__main__":
    main()