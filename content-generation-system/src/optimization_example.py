"""Esempio di integrazione del sistema di ottimizzazione dei costi API."""

import logging
import os
import yaml
from dotenv import load_dotenv

# Importa i componenti del sistema di ottimizzazione
from .api_cost_optimizer import APICostOptimizer
from .config_manager import ConfigManager

# Importa i componenti del sistema esistente
from .tools import WebSearchTool, MarkdownParserTool
from .agents import AgentsFactory
from .tasks import WorkflowManager
from .config import SERPER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

# Importa CrewAI
from crewai import Crew, Process

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("optimization.log")
    ]
)
logger = logging.getLogger("optimization_example")

def load_workflow_config(config_path):
    """Carica la configurazione dei workflow."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Errore nel caricamento della configurazione: {str(e)}")
        return None

def main():
    """Funzione principale per dimostrare l'integrazione del sistema di ottimizzazione."""
    # Carica le variabili d'ambiente
    load_dotenv()
    
    # Inizializza il sistema di ottimizzazione
    optimizer = APICostOptimizer(cache_dir="./cache", logger=logger)
    
    # Imposta i limiti di quota per i modelli
    optimizer.set_model_quotas({
        "gpt-4": 50,  # Limite di 50 chiamate per ora
        "gpt-3.5-turbo": 200,  # Limite di 200 chiamate per ora
        "claude-3-opus-20240229": 30,  # Limite di 30 chiamate per ora
        "claude-3-sonnet-20240229": 100  # Limite di 100 chiamate per ora
    }, reset_interval=3600)  # Reset ogni ora
    
    # Carica e ottimizza i workflow
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
    workflows_path = os.path.join(config_dir, 'workflows.yaml')
    
    workflows_config = load_workflow_config(workflows_path)
    if not workflows_config:
        logger.error("Impossibile caricare la configurazione dei workflow")
        return
    
    # Ottimizza i workflow
    optimized_workflows = optimizer.optimize_workflows(workflows_config)
    
    # Salva i workflow ottimizzati
    optimized_path = os.path.join(config_dir, 'optimized_workflows.yaml')
    try:
        with open(optimized_path, 'w') as f:
            yaml.dump(optimized_workflows, f, default_flow_style=False)
        logger.info(f"Workflow ottimizzati salvati in {optimized_path}")
    except Exception as e:
        logger.error(f"Errore nel salvare i workflow ottimizzati: {str(e)}")
    
    # Esempio di utilizzo del sistema ottimizzato per generare contenuti
    generate_optimized_content(optimizer, optimized_workflows)
    
    # Salva le statistiche di ottimizzazione
    stats_path = os.path.join(config_dir, 'optimization_stats.json')
    optimizer.save_stats_to_file(stats_path)
    
    # Mostra un riepilogo delle statistiche
    stats = optimizer.get_optimization_stats()
    logger.info(f"Riepilogo ottimizzazione:")
    logger.info(f"- Chiamate API totali: {stats['total_api_calls']}")
    logger.info(f"- Chiamate dalla cache: {stats['total_cached_calls']}")
    logger.info(f"- Costo totale: ${stats['total_cost']:.2f}")
    logger.info(f"- Risparmio stimato: ${stats['total_saved_cost']:.2f} ({stats['cost_reduction_percentage']:.1f}%)")

def generate_optimized_content(optimizer, workflow_config):
    """Genera contenuti utilizzando il sistema ottimizzato."""
    # Inizializza gli strumenti
    web_search_tool = WebSearchTool(api_key=SERPER_API_KEY)
    markdown_tool = MarkdownParserTool()
    
    # Inizializza la factory degli agenti
    agents_factory = AgentsFactory(logger=logger)
    
    # Crea gli agenti
    agents = agents_factory.create_agents(web_search_tool, markdown_tool)
    
    # Inizializza il workflow manager
    workflow_manager = WorkflowManager(agents, logger=logger)
    
    # Esempio di topic
    topic = "Strategie di investimento per millennials"
    
    # Seleziona un workflow ottimizzato
    workflow_name = "standard"
    if workflow_name in workflow_config.get("workflows", {}):
        # Crea i task in base al workflow ottimizzato
        tasks = workflow_manager.create_tasks_from_config(topic, workflow_config["workflows"][workflow_name])
        
        # Crea il crew
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            verbose=True,
            process=Process.sequential
        )
        
        # Esegui il crew con ottimizzazione delle chiamate LLM
        # Nota: questo è un esempio concettuale, l'implementazione reale dipende da come è strutturato il metodo run di CrewAI
        try:
            # Qui dovremmo applicare il decoratore optimize_llm_call alle funzioni che fanno chiamate LLM
            # Ma poiché non possiamo modificare direttamente CrewAI, mostriamo solo il concetto
            logger.info(f"Avvio generazione contenuto ottimizzata per topic: {topic}")
            
            # Esempio concettuale
            # result = optimizer.optimize_llm_call(crew.run)()
            
            # Per ora, eseguiamo normalmente
            result = crew.run()
            
            logger.info(f"Generazione completata con successo")
            return result
        except Exception as e:
            logger.error(f"Errore nella generazione del contenuto: {str(e)}")
            return None
    else:
        logger.error(f"Workflow '{workflow_name}' non trovato nella configurazione")
        return None

if __name__ == "__main__":
    main()