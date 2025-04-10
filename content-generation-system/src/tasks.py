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
        if content_type == "whitepaper":
            return self._create_whitepaper_workflow(topic)
        else:
            return self._create_standard_workflow(topic)

    def _create_whitepaper_workflow(self, topic):
        """Crea il flusso di lavoro per white paper (3000+ parole)."""
        # Task 1: Research e Analisi approfondita
        research_analysis_task = Task(
            description=f"Research and analysis for a whitepaper on '{topic}'. Complete these tasks:\n\n1. Conduct thorough market research on the topic using your web search tool.\n2. Analyze industry-specific needs and pain points.\n3. Identify key trends, statistics, and expert opinions to support your arguments.\n4. Prepare a comprehensive research summary with key findings.\n\nYour output should include a detailed research report with market analysis, trends, and supporting evidence for a 3000+ word whitepaper.",
            expected_output="A comprehensive research report with market analysis and supporting evidence in markdown format.",
            agent=self.agents["web_searcher"],
            async_execution=False
        )

        # Task 2: Outline e Struttura del white paper
        outline_structure_task = Task(
            description=f"Create a detailed outline and structure for a whitepaper on '{topic}' based on the provided research. Complete these tasks:\n\n1. Design a professional whitepaper structure (3000+ words) with the following components:\n   - Executive summary\n   - Introduction to the problem/challenge\n   - Background and current landscape\n   - Proposed approach/solution\n   - Implementation considerations\n   - Case studies or examples\n   - Future outlook\n   - Conclusion\n2. Create detailed section breakdowns with subsections.\n3. Define the key points and arguments for each section.\n\nYour output should be a comprehensive whitepaper outline with section descriptions and key points to cover.",
            expected_output="A detailed whitepaper outline with section breakdowns and key points in markdown format.",
            agent=self.agents["copywriter"],
            async_execution=False,
            dependencies=[research_analysis_task]
        )

        # Task 3: Sviluppo dei contenuti
        content_development_task = Task(
            description=f"Develop the main content for a whitepaper on '{topic}' following the provided outline. Complete these tasks:\n\n1. Write comprehensive content for each section of the whitepaper (3000+ words total).\n2. Incorporate research findings, data, and expert insights throughout the document.\n3. Maintain a professional, authoritative tone appropriate for a whitepaper.\n4. Ensure logical flow between sections and arguments.\n5. Use technical terminology appropriate for the target audience.\n\nYour output should be a fully developed whitepaper draft with all sections completed according to the outline.",
            expected_output="A fully developed whitepaper draft (3000+ words) in markdown format.",
            agent=self.agents["copywriter"],
            async_execution=False,
            dependencies=[outline_structure_task]
        )

        # Task 4: Revisione tecnica e ottimizzazione
        expert_review_task = Task(
            description=f"Conduct an expert technical review and optimize the whitepaper on '{topic}'. Complete these tasks:\n\n1. Use the MarkdownParserTool to extract brand guidelines from the reference file.\n2. Review the whitepaper for technical accuracy and logical coherence.\n3. Verify that all claims are supported by research.\n4. Optimize the content based on:\n   - Technical precision and accuracy\n   - Logical flow and argumentation\n   - Alignment with brand voice and style guidelines\n   - Professional tone and language\n5. Make necessary improvements to strengthen the document.\n\nYour output should be a revised and optimized whitepaper that maintains technical accuracy while being engaging and persuasive.",
            expected_output="A revised and optimized whitepaper draft in markdown format.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=[content_development_task],
            tools=[self.agents["editor"].tools[0]] if len(self.agents["editor"].tools) > 0 else []
        )

        # Task 5: Pianificazione elementi visivi e finalizzazione
        visual_planning_task = Task(
            description=f"Plan visual elements and finalize the whitepaper on '{topic}'. Complete these tasks:\n\n1. Identify opportunities for visual elements throughout the document:\n   - Key data visualizations (charts, graphs)\n   - Conceptual diagrams or flowcharts\n   - Infographics for complex information\n   - Tables for comparative data\n2. Add placeholders and descriptions for recommended visuals.\n3. Conduct final proofreading and formatting:\n   - Ensure consistent heading structure\n   - Verify proper citation of sources\n   - Format according to professional whitepaper standards\n4. Prepare final notes for designers (if applicable).\n\nYour output should be the complete, publication-ready whitepaper with visual element recommendations and final formatting.",
            expected_output="The final, publication-ready whitepaper with visual recommendations in markdown format.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=[expert_review_task],
            tools=[self.agents["editor"].tools[0]] if len(self.agents["editor"].tools) > 0 else []
        )

        tasks = [research_analysis_task, outline_structure_task, content_development_task, expert_review_task, visual_planning_task]
        return tasks


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