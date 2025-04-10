import os
from crewai import Task
import logging
from typing import Dict, Any, List, Optional

class WorkflowManager:
    """Gestisce i diversi flussi di lavoro per la generazione dei contenuti."""

    def __init__(self, agents, logger=None):
        """Inizializza il workflow manager."""
        self.agents = agents
        self.logger = logger or logging.getLogger(__name__)
        self.adherence_check_enabled = True  # Flag per abilitare/disabilitare il controllo di aderenza

    def create_tasks(self, topic, content_type="article"):
        """Crea la sequenza di task appropriata in base al tipo di contenuto."""
        if content_type == "whitepaper":
            return self._create_whitepaper_workflow(topic)
        return self._create_standard_workflow(topic)

    def _create_standard_workflow(self, topic):
        """Crea il flusso di lavoro standard ottimizzato per articoli di media lunghezza (800-1000 parole)."""
        # Task 1: Research + Outline (Combinati)
        research_outline_task = Task(
            description=f"Research and outline for topic: '{topic}'. Complete these two tasks together:\n\n1. Research thoroughly on the topic. Find current, accurate information using your web search tool.\n2. Based on your research, design a content structure for a 800-1000 word article with introduction, 2-3 main sections, and conclusion.\n\nYour output should include both a comprehensive research summary and a detailed content outline with section breakdowns.",
            expected_output="A research summary and content outline for a 800-1000 word article in markdown format.",
            agent=self.agents["web_searcher"],  # Utilizziamo il web_searcher che può fare anche l'outline
            async_execution=False
        )

        # Task 2: Content Creation + Initial Editing
        writing_editing_task = Task(
            description=f"Create and optimize an article on '{topic}' following these steps:\n\n1. Write an engaging and informative article of 800-1000 words based on the provided research and outline.\n2. Follow the structure with introduction, 2-3 main sections (200-300 words each), and conclusion.\n3. Apply best practices for writing style:\n   - Use a professional yet conversational tone\n   - Ensure active voice and proper sentence structure\n   - Maintain logical flow with clear headings and subheadings\n   - Make content accessible and interesting for the target audience\n\nYour output should be a well-structured and polished article ready for final review.",
            expected_output="A well-structured and initially optimized article of 800-1000 words in markdown format.",
            agent=self.agents["copywriter"],  # Il copywriter si occupa sia della scrittura che dell'editing iniziale
            async_execution=False,
            dependencies=[research_outline_task]
        )

        # Task 3: Final Review + Optimization
        review_finalize_task = Task(
            description=f"Review and finalize the article about '{topic}' following these steps:\n\n1. Use the MarkdownParserTool to extract brand guidelines from the reference file.\n2. Review and optimize the content based on:\n   - Factual accuracy against the research summary\n   - Alignment with brand voice and style guidelines\n   - Content structure and logical flow\n   - Quality and engagement level\n   - Technical accuracy\n3. Make all necessary improvements and generate the final output:\n   - Apply corrections for any inaccuracies\n   - Enhance flow and transitions where needed\n   - Adjust tone and style to match brand guidelines\n   - Ensure the article maintains its target length (800-1000 words)\n   - Format according to markdown standards\n\nThe final output should be the complete, publication-ready article.",
            expected_output="The final, publication-ready article in markdown format, incorporating all necessary improvements and aligned with brand guidelines.",
            agent=self.agents["editor"],  # L'editor si occupa sia della revisione che della finalizzazione
            async_execution=False,
            dependencies=[writing_editing_task],
            tools=[self.agents["editor"].tools[0]]  # Assicuriamo che lo strumento markdown sia disponibile
        )

        tasks = [research_outline_task, writing_editing_task]
        if self.adherence_check_enabled and self._check_guideline_adherence(writing_editing_task.expected_output):
            self.logger.info("Guideline adherence sufficient; skipping final review.")
        else:
            tasks.append(review_finalize_task)
        return tasks

    def _check_guideline_adherence(self, content):
        # Placeholder for a real guideline adherence check
        # In a real application, this would involve comparing the content against a set of guidelines.
        return len(content) > 500 #Simulate:  If more than 500 characters, assume adherence


    def _create_extended_article_workflow(self, topic):
        """Crea il flusso di lavoro per articoli lunghi (1500+ parole)."""
        # Task 1: Web Research
        research_task = Task(
            description=f"Research thoroughly on the topic: '{topic}'. Focus on gathering comprehensive information, current trends, and expert insights. Structure your findings in a JSON format with the following keys: 'key_points' (list of main insights), 'sources' (list of dictionaries with 'title', 'link', 'snippet'), 'statistics' (list of relevant numbers and data), 'expert_quotes' (list of expert opinions), and 'full_summary' (comprehensive overview).",
            expected_output="A JSON object containing structured research data with key_points, sources, statistics, expert_quotes, and full_summary fields.",
            agent=self.agents["web_searcher"],
            async_execution=False
        )

        # Task 2: Content Architecture
        architecture_task = Task(
            description=f"Design a detailed structure for a 1500-word article on '{topic}'. Create a JSON structure that specifies: title, target_word_count (1500), and sections array with title, target_words, key_points, and subsections for each section. Ensure logical flow and comprehensive coverage.",
            expected_output="A JSON object representing the article structure with title, target word count, sections array containing title, target words, key points, and subsections.",
            agent=self.agents["architect"],
            async_execution=False,
            dependencies=[research_task]
        )

        # Task 3: Section Writing with Word Count Guidelines
        section_tasks = []
        section_descriptions = [
            {"name": "Introduction and Context", "words": 250},
            {"name": "Main Concepts and Analysis", "words": 500},
            {"name": "Practical Applications and Benefits", "words": 500},
            {"name": "Conclusions and Future Perspectives", "words": 250}
        ]

        for section in section_descriptions:
            section_task = Task(
                description=f"Write the '{section['name']}' section for the article on '{topic}'. Target length: {section['words']} words. Follow the outline provided by the Content Architect. Ensure depth, clarity, and maintain consistency with other sections. Focus on providing valuable insights while staying within the word limit.",
                expected_output=f"Completed {section['name']} section in markdown format with approximately {section['words']} words.",
                agent=self.agents["section_writer"],
                async_execution=True,
                dependencies=[architecture_task]
            )
            section_tasks.append(section_task)

        # Task 4: Content Assembly and Editing
        editing_task = Task(
            description=f"Assemble and optimize the complete article on '{topic}' (1500 words) following these steps:\n\n1. Use the MarkdownParserTool to extract and analyze these specific sections from the reference file:\n   - Brand Voice: Apply the professional yet conversational tone\n   - Content Structure: Follow the blog post structure guidelines\n   - Writing Guidelines: Ensure active voice and proper sentence structure\n   - Terminology Preferences: Use preferred terms and avoid discouraged ones\n\n2. Apply the extracted guidelines:\n   - Verify the content follows the specified blog post structure (clear headline, introduction, body with subheadings, conclusion)\n   - Ensure the tone is professional yet conversational as specified in the Brand Voice section\n   - Apply the writing guidelines for active voice, sentence structure, and grammar\n   - Check and replace terminology according to the preferences\n\n3. Final Checks:\n   - Verify the content maintains the target length (1500 words)\n   - Ensure consistent style throughout all sections\n   - Confirm sections flow logically and maintain coherence\n   - Validate factual accuracy is preserved",
            expected_output="Complete, polished article in markdown format, precisely aligned with Fylle's brand voice and style guidelines.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=section_tasks
        )

        # Task 6: Quality Review (Optional)
        review_task = Task(
            description=f"Review the final white paper about '{topic}' following these criteria:\n\n1. Factual Accuracy and Research Quality:\n   - Verify all facts against the research summary\n   - Check for any outdated or incorrect information\n   - Validate statistics and data points\n   - Ensure proper citation of sources\n   - Verify credibility of expert quotes and references\n\n2. Content Structure and Flow:\n   - Ensure logical progression of ideas across all sections\n   - Verify smooth transitions between sections\n   - Check if the content follows the outlined structure\n   - Evaluate the effectiveness of section organization\n   - Verify proper development of arguments\n\n3. Technical Depth and Accuracy:\n   - Assess appropriate level of technical detail\n   - Verify accuracy of technical concepts\n   - Check consistency in technical terminology\n   - Ensure proper explanation of complex ideas\n   - Validate technical recommendations\n\n4. Professional Standards:\n   - Confirm adherence to white paper format\n   - Check executive summary effectiveness\n   - Verify proper presentation of data\n   - Ensure professional tone and style\n   - Validate conclusions and recommendations\n\n5. Quality and Polish:\n   - Review grammar and spelling\n   - Check for proper formatting\n   - Verify consistent terminology\n   - Ensure visual elements are properly integrated\n   - Validate references and citations\n\nProvide a detailed review report including:\n- Strengths of the white paper\n- Areas for improvement\n- Technical accuracy assessment\n- Specific recommendations for enhancement\n- Optional: Suggested revisions or edits",
            expected_output="A comprehensive review report in markdown format with specific feedback and suggestions for improvement.",
            agent=self.agents["quality_reviewer"],
            async_execution=False,
            dependencies=[editing_task]
        )

        return [research_task, architecture_task] + section_tasks + [editing_task, review_task]

    def _create_extended_workflow(self, topic):
        """Crea il flusso di lavoro esteso per white paper e report."""
        # Task 1: Web Research
        research_task = Task(
            description=f"Conduct comprehensive research on '{topic}'. Focus on gathering in-depth information, current trends, statistics, and expert insights. Structure your findings in a JSON format with the following keys: 'key_points' (list of main insights), 'sources' (list of dictionaries with 'title', 'link', 'snippet', 'credibility_score'), 'statistics' (list of relevant numbers and data), 'expert_quotes' (list of dictionaries with 'quote', 'author', 'credentials'), 'market_trends' (list of current industry trends), 'full_summary' (comprehensive overview).",
            expected_output="A JSON object containing structured research data with key_points, sources, statistics, expert_quotes, market_trends, and full_summary fields.",
            agent=self.agents["web_searcher"],
            async_execution=False
        )

        # Task 2: Content Architecture
        architecture_task = Task(
            description=f"Design a detailed structure for a white paper on '{topic}'. Create a JSON structure that specifies: 'title', 'document_type': 'white_paper', 'target_word_count': 5000, 'executive_summary': {'key_points': [strings]}, 'sections': [{'title': string, 'target_words': number, 'key_arguments': [strings], 'data_points': [strings], 'subsections': [{'title': string, 'target_words': number, 'focus_areas': [strings]}]}]. Ensure logical flow and progression of ideas.",
            expected_output="A JSON object representing the white paper structure with title, document type, target word count, executive summary, and detailed section hierarchy including key arguments and data points.",
            agent=self.agents["architect"],
            async_execution=False,
            dependencies=[research_task]
        )

        # Task 3: Section Writing (Multiple Parallel Tasks)
        section_tasks = []
        section_descriptions = [
            "Introduction and Executive Summary",
            "Background and Context",
            "Main Analysis and Findings",
            "Technical Details and Implementation",
            "Conclusions and Recommendations"
        ]

        for section in section_descriptions:
            section_task = Task(
                description=f"Write the '{section}' section for the white paper on '{topic}'. Follow the outline provided by the Content Architect. Ensure comprehensive coverage while maintaining consistency with other sections.",
                expected_output=f"Completed {section} section in markdown format.",
                agent=self.agents["section_writer"],
                async_execution=True,
                dependencies=[architecture_task]
            )
            section_tasks.append(section_task)

        # Task 4: Content Assembly and Editing
        editing_task = Task(
            description=f"Assemble and optimize the complete white paper on '{topic}' following these steps:\n\n1. Use the MarkdownParserTool to extract and analyze these specific sections from the reference file:\n   - Brand Voice: Apply the professional yet conversational tone while maintaining technical accuracy\n   - Content Structure: Adapt the structure guidelines for a white paper format\n   - Writing Guidelines: Implement active voice and professional sentence structure\n   - Terminology Preferences: Use preferred technical terms and industry-specific language\n\n2. Apply the extracted guidelines:\n   - Ensure each section follows a clear, logical structure with proper technical depth\n   - Maintain the professional tone while keeping content accessible\n   - Apply consistent formatting and citation standards\n   - Use appropriate technical terminology while avoiding jargon\n\n3. Final Checks:\n   - Verify technical accuracy and completeness of all sections\n   - Ensure consistent style and tone throughout the document\n   - Validate proper flow between sections\n   - Confirm all citations and references are properly formatted",
            expected_output="Complete, polished white paper in markdown format, precisely aligned with Fylle's brand voice and technical documentation standards.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=section_tasks
        )

        return [research_task, architecture_task] + section_tasks + [editing_task]
    def _create_whitepaper_workflow(self, topic):
        """Crea il flusso di lavoro ottimizzato per white paper."""
        # Task 1: Ricerca e Analisi
        research_analysis_task = Task(
            description=f"Conduci una ricerca approfondita e analisi su '{topic}'. Focalizzati su:\n\n"
                       f"1. Analisi del mercato attuale e tendenze future\n"
                       f"2. Problematiche specifiche del settore target\n"
                       f"3. Soluzioni esistenti e loro limiti\n"
                       f"4. Opportunità di innovazione\n"
                       f"5. Statistiche rilevanti e dati di supporto\n\n"
                       f"Organizza i risultati in formato JSON con: 'market_analysis', 'industry_challenges', "
                       f"'existing_solutions', 'innovation_opportunities', 'key_statistics'.",
            expected_output="Un documento JSON strutturato con analisi di mercato, sfide del settore, soluzioni esistenti, opportunità di innovazione e statistiche chiave.",
            agent=self.agents["web_searcher"],
            async_execution=False
        )

        # Task 2: Struttura e Outline
        outline_structure_task = Task(
            description=f"Crea una struttura dettagliata per un white paper su '{topic}' basandoti sull'analisi di mercato. Sviluppa:\n\n"
                       f"1. Un titolo accattivante e sottotitolo esplicativo\n"
                       f"2. Sommario esecutivo (max 250 parole)\n"
                       f"3. Struttura dettagliata con sezioni e sottosezioni (5-7 sezioni principali)\n"
                       f"4. Per ogni sezione: titolo, obiettivo, punti chiave da sviluppare (3-5 per sezione)\n"
                       f"5. Allocazione della lunghezza stimata per ogni sezione\n\n"
                       f"La struttura deve guidare il lettore logicamente dalle problematiche alle soluzioni.",
            expected_output="Una struttura dettagliata del white paper in formato markdown con titolo, sommario esecutivo, sezioni complete di sottosezioni e punti chiave.",
            agent=self.agents["architect"],
            async_execution=False,
            dependencies=[research_analysis_task]
        )

        # Task 3: Sviluppo Contenuti
        content_development_task = Task(
            description=f"Sviluppa il contenuto completo del white paper su '{topic}' seguendo la struttura fornita. Assicurati di:\n\n"
                       f"1. Elaborare ogni sezione con contenuto sostanziale e approfondito\n"
                       f"2. Incorporare dati e statistiche dall'analisi di mercato\n"
                       f"3. Fornire esempi concreti e casi studio rilevanti\n"
                       f"4. Mantenere uno stile professionale ma accessibile\n"
                       f"5. Sviluppare argomentazioni solide supportate da evidenze\n\n"
                       f"Il contenuto deve risultare autorevole, informativo e orientato alle soluzioni.",
            expected_output="Contenuto completo del white paper in formato markdown, strutturato secondo l'outline e arricchito con dati, statistiche ed esempi.",
            agent=self.agents["section_writer"],
            async_execution=False,
            dependencies=[outline_structure_task]
        )

        # Task 4: Revisione Tecnica e Editing
        expert_review_edit_task = Task(
            description=f"Esegui una revisione tecnica approfondita e ottimizza il white paper su '{topic}'. Concentrati su:\n\n"
                       f"1. Accuratezza tecnica e fattuale di tutti i contenuti\n"
                       f"2. Coerenza del tono e dello stile in tutto il documento\n"
                       f"3. Chiarezza dell'argomentazione e flusso logico\n"
                       f"4. Ottimizzazione della struttura delle frasi e scelta delle parole\n"
                       f"5. Verificare che tutte le affermazioni siano supportate da evidenze\n\n"
                       f"Utilizza gli strumenti di editing per garantire un documento di qualità professionale.",
            expected_output="White paper rivisto e ottimizzato, con correzioni tecniche, miglioramenti stilistici e strutturali in formato markdown.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=[content_development_task],
            tools=[self.agents["editor"].tools[0]]  # Markdown parser tool
        )

        # Task 5: Pianificazione Visiva e Finalizzazione
        visual_planning_finalize_task = Task(
            description=f"Finalizza il white paper su '{topic}' e fornisci note per elementi visivi. Completa:\n\n"
                       f"1. Aggiungi annotazioni per grafici, diagrammi o infografiche da includere\n"
                       f"2. Suggerisci posizionamento di elementi visivi con descrizioni dettagliate\n"
                       f"3. Ottimizza la formattazione markdown per la leggibilità\n"
                       f"4. Aggiungi note per il design della copertina e delle pagine interne\n"
                       f"5. Inserisci riferimenti e citazioni in formato appropriato\n\n"
                       f"Il documento finale deve essere pronto per la consegna al team di design grafico.",
            expected_output="White paper finalizzato con annotazioni per elementi visivi, suggerimenti di design, formattazione ottimizzata e riferimenti completi.",
            agent=self.agents["quality_reviewer"],
            async_execution=False,
            dependencies=[expert_review_edit_task]
        )

        return [research_analysis_task, outline_structure_task, content_development_task, 
                expert_review_edit_task, visual_planning_finalize_task]

    def create_tasks_from_config(self, topic: str, workflow_config: Dict[str, Any]) -> List[Task]:
        """Crea i task basati sulla configurazione del workflow."""
        if not workflow_config or "steps" not in workflow_config:
            self.logger.error("Configurazione workflow non valida")
            return []

        steps = workflow_config["steps"]
        tasks = []

        # Verifica se la modalità economica è attiva
        economic_mode = os.getenv('ECONOMIC_MODE', 'false').lower() == 'true'
        if economic_mode:
            self.logger.info("Creazione tasks in modalità economica (DeepSeek)")

        for step in steps:
            task_name = step.get("task", "")
            description = step.get("description", "")

            # Ottieni le preferenze di provider e complessità
            provider_preference = step.get("provider_preference", "auto")
            complexity = step.get("complexity", "medium")

            # Se provider_preference è "auto", determina in base alla modalità
            if provider_preference == "auto" and economic_mode:
                provider_preference = "deepseek"

            # Crea il task appropriato in base al nome con le preferenze
            task = self._create_task_by_name(
                task_name, 
                topic, 
                description, 
                provider_preference=provider_preference, 
                complexity=complexity
            )
            if task:
                tasks.append(task)

        return tasks

    def _create_task_by_name(
            self, 
            task_name: str, 
            topic: str, 
            description: str, 
            provider_preference: str = None, 
            complexity: str = "medium"
        ) -> Optional[Task]:
        """Crea un task specifico in base al nome.

        Args:
            task_name: Nome del task
            topic: Argomento del contenuto
            description: Descrizione del task
            provider_preference: Provider preferito (openai, anthropic, deepseek)
            complexity: Complessità del task (high, medium, low)
        """
        # Tieni traccia dei parametri per ogni task
        extra_params = {
            "provider_preference": provider_preference,
            "complexity": complexity
        }

        try:
            if task_name == "research":
                return self._create_research_task(topic, **extra_params)
            elif task_name == "outline":
                return self._create_outline_task(topic, **extra_params)
            elif task_name == "draft":
                return self._create_draft_task(topic, **extra_params)
            elif task_name == "review":
                return self._create_review_task(topic, **extra_params)
            elif task_name == "edit":
                return self._create_edit_task(topic, **extra_params)
            elif task_name == "finalize":
                return self._create_finalize_task(topic, **extra_params)
            else:
                return None # Handle unknown task names

        except Exception as e:
            self.logger.error(f"Errore durante la creazione del task '{task_name}': {e}")
            return None

    # Placeholder functions -  Replace with your actual task creation logic
    def _create_research_task(self, topic: str, **kwargs) -> Optional[Task]:
        description = f"Research task for '{topic}' with provider preference {kwargs.get('provider_preference', 'auto')} and complexity {kwargs.get('complexity','medium')}"
        return Task(description=description, agent=self.agents["web_searcher"])

    def _create_outline_task(self, topic: str, **kwargs) -> Optional[Task]:
        description = f"Outline task for '{topic}' with provider preference {kwargs.get('provider_preference', 'auto')} and complexity {kwargs.get('complexity','medium')}"
        return Task(description=description, agent=self.agents["architect"])

    def _create_draft_task(self, topic: str, **kwargs) -> Optional[Task]:
        description = f"Draft task for '{topic}' with provider preference {kwargs.get('provider_preference', 'auto')} and complexity {kwargs.get('complexity','medium')}"
        return Task(description=description, agent=self.agents["copywriter"])

    def _create_review_task(self, topic: str, **kwargs) -> Optional[Task]:
        description = f"Review task for '{topic}' with provider preference {kwargs.get('provider_preference', 'auto')} and complexity {kwargs.get('complexity','medium')}"
        return Task(description=description, agent=self.agents["editor"])

    def _create_edit_task(self, topic: str, **kwargs) -> Optional[Task]:
        description = f"Edit task for '{topic}' with provider preference {kwargs.get('provider_preference', 'auto')} and complexity {kwargs.get('complexity','medium')}"
        return Task(description=description, agent=self.agents["editor"])

    def _create_finalize_task(self, topic: str, **kwargs) -> Optional[Task]:
        description = f"Finalize task for '{topic}' with provider preference {kwargs.get('provider_preference', 'auto')} and complexity {kwargs.get('complexity','medium')}"
        return Task(description=description, agent=self.agents["editor"])