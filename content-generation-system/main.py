import os
import argparse
from crewai import Crew
from src.agents import AgentsFactory
from src.tools import WebSearchTool, MarkdownParserTool
from src.tasks import WorkflowManager
from src.utils import ensure_directory_exists, generate_output_filename
from src.config import DEFAULT_OUTPUT_DIR, DEFAULT_REFERENCE_FILE

def main():
    """Funzione principale che orchestratra il processo di generazione contenuti."""
    
    # Parser argomenti da riga di comando
    parser = argparse.ArgumentParser(description="Generate optimized content on any topic")
    parser.add_argument("--topic", required=True, help="Topic for content generation")
    parser.add_argument("--type", default="article", choices=["article", "extended_article", "whitepaper"], help="Type of content to generate")
    parser.add_argument("--reference", default=DEFAULT_REFERENCE_FILE, help="Path to reference markdown file")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Directory for output")
    
    args = parser.parse_args()
    
    # Verifica esistenza file di riferimento
    if not os.path.exists(args.reference):
        print(f"Error: Reference file '{args.reference}' not found.")
        return
    
    # Crea directory output se non esiste
    output_dir = ensure_directory_exists(args.output)
    
    # Inizializza tool
    web_search_tool = WebSearchTool()
    markdown_tool = MarkdownParserTool(file_path=args.reference)
    
    # Crea agenti
    agents_factory = AgentsFactory()
    agents = agents_factory.create_agents(web_search_tool, markdown_tool)
    
    # Creazione del workflow manager e dei task
    workflow_manager = WorkflowManager(agents)
    tasks = workflow_manager.create_tasks(args.topic, args.type)
    
    # Crea e avvia crew
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=True
    )
    
    print(f"Starting content generation for topic: '{args.topic}'")
    print(f"Using reference file: {args.reference}")
    
    # Esegui crew e ottieni risultato
    result = crew.kickoff()
    
    # Salva l'output
    output_file = generate_output_filename(args.topic, output_dir)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"Content generation completed! Output saved to: {output_file}")

if __name__ == "__main__":
    main()