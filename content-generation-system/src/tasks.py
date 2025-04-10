from crewai import Task
import logging

class WorkflowManager:
    """Gestisce i diversi flussi di lavoro per la generazione dei contenuti."""

    def __init__(self, agents, logger=None):
        """Inizializza il workflow manager."""
        self.agents = agents
        self.logger = logger or logging.getLogger(__name__)
        self.adherence_check_enabled = True  # Flag per abilitare/disabilitare il controllo di aderenza

    def create_tasks(self, topic, content_type="article"):
        """Crea la sequenza di task appropriata in base al tipo di contenuto."""
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