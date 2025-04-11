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
        """Crea il flusso di lavoro per white paper (minimo 2000 parole effettive, escluse indicazioni visive)."""
        # Task 1: Research e Analisi approfondita
        research_analysis_task = Task(
            description=f"Research and analysis for a whitepaper on '{topic}'. Complete these tasks:\n\n1. Conduct thorough market research on the topic using your web search tool.\n2. Analyze industry-specific needs and pain points.\n3. Identify key trends, statistics, and expert opinions to support your arguments.\n4. Prepare a comprehensive research summary with key findings.\n\nYour output should include a detailed research report with market analysis, trends, and supporting evidence for a whitepaper with at least 2000 words of actual content (excluding visual placeholders).",
            expected_output="A comprehensive research report with market analysis and supporting evidence in markdown format.",
            agent=self.agents["web_searcher"],
            async_execution=False
        )

        # Task 2: Outline e Struttura del white paper
        outline_structure_task = Task(
            description=f"Create a detailed outline and structure for a whitepaper on '{topic}' based on the provided research. Complete these tasks:\n\n1. Design a professional whitepaper structure with at least 2000 words of actual content (excluding visual placeholders) with the following components:\n   - Executive summary (200-300 words)\n   - Introduction to the problem/challenge (300-400 words)\n   - Background and current landscape (400-500 words)\n   - Proposed approach/solution (400-500 words)\n   - Implementation considerations (300-400 words)\n   - Case studies or examples (300-400 words)\n   - Future outlook (200-300 words)\n   - Conclusion (200-300 words)\n2. Create detailed section breakdowns with subsections.\n3. Define the key points and arguments for each section.\n4. Include word count guidance for each section to ensure the total content meets the minimum 2000-word requirement.\n\nYour output should be a comprehensive whitepaper outline with section descriptions and key points to cover, with specific word count targets for each section.",
            expected_output="A detailed whitepaper outline with section breakdowns, key points, and word count targets in markdown format.",
            agent=self.agents["copywriter"],
            async_execution=False,
            dependencies=[research_analysis_task]
        )

        # Task 3: Sviluppo dei contenuti
        content_development_task = Task(
            description=f"Develop the main content for a whitepaper on '{topic}' following the provided outline. Complete these tasks:\n\n1. Write comprehensive content for each section of the whitepaper with a MINIMUM of 2000 words of actual content (excluding visual placeholders and recommendations).\n2. Follow the word count guidance for each section specified in the outline.\n3. Incorporate research findings, data, and expert insights throughout the document.\n4. Maintain a professional, authoritative tone appropriate for a whitepaper.\n5. Ensure logical flow between sections and arguments.\n6. Use technical terminology appropriate for the target audience.\n7. Count the words in your draft (excluding visual placeholders) to verify it meets the 2000-word minimum requirement.\n\nYour output should be a fully developed whitepaper draft with all sections completed according to the outline, with at least 2000 words of actual content.",
            expected_output="A fully developed whitepaper draft with at least 2000 words of actual content (excluding visual placeholders) in markdown format.",
            agent=self.agents["copywriter"],
            async_execution=False,
            dependencies=[outline_structure_task]
        )

        # Task 4: Revisione tecnica e ottimizzazione
        expert_review_task = Task(
            description=f"Conduct an expert technical review and optimize the whitepaper on '{topic}'. Complete these tasks:\n\n1. If a markdown tool is available, use it to extract brand guidelines from the reference file. Try sections like 'Brand Voice', 'Style Guide', or check the complete document.\n2. Review the whitepaper for technical accuracy and logical coherence.\n3. Verify that all claims are supported by research.\n4. Optimize the content based on:\n   - Technical precision and accuracy\n   - Logical flow and argumentation\n   - Alignment with brand voice and style guidelines (if available)\n   - Professional tone and language\n5. Make necessary improvements to strengthen the document.\n6. Ensure the content maintains at least 2000 words (excluding visual placeholders).\n7. Add more substantive content if the word count is below the minimum requirement.\n\nYour output should be a revised and optimized whitepaper that maintains technical accuracy while being engaging and persuasive, with at least 2000 words of actual content.",
            expected_output="A revised and optimized whitepaper draft with at least 2000 words of actual content (excluding visual placeholders) in markdown format.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=[content_development_task],
            tools=[self.agents["editor"].tools[0]] if len(self.agents["editor"].tools) > 0 else []
        )

        # Task 5: Pianificazione elementi visivi e finalizzazione
        visual_planning_task = Task(
            description=f"Plan visual elements and finalize the whitepaper on '{topic}' for Siebert Financial Corp. Complete these tasks:\n\n1. MANDATORY: Use the markdown tool to extract brand guidelines with the command: \"markdown_reference('Brand Voice')\". Ensure you explicitly mention Siebert Financial Corp throughout the document and align with their brand voice.\n\n2. Identify opportunities for visual elements throughout the document:\n   - Key data visualizations (charts, graphs)\n   - Conceptual diagrams or flowcharts\n   - Infographics for complex information\n   - Tables for comparative data\n\n3. ADD EXPLICITLY MARKED VISUAL PLACEHOLDERS with detailed descriptions. Format these as:\n\n```\n[VISUAL: Type - Detailed description of what the visual should show]\n```\n\nFor example: [VISUAL: Chart - Line graph showing investment trends from 2020-2025 with highlighted areas of growth]\n\n4. Add a dedicated 'Design Notes' section at the end with:\n   - Visual style guide recommendations\n   - Technical specifications for visuals\n   - Accessibility requirements\n\n5. Conduct final proofreading and formatting:\n   - Ensure consistent heading structure\n   - Verify proper citation of sources\n   - Format according to professional whitepaper standards\n   - CRITICAL: Ensure the content explicitly represents Siebert Financial Corp's perspective and includes their brand name in the title and throughout the document\n\n6. Verify the final document contains at least 2000 words of actual content (excluding all visual placeholders and recommendations).\n7. Include a word count at the end of the document to confirm compliance with the 2000-word minimum requirement.\n\nIMPORTANT: The whitepaper MUST be branded as a Siebert Financial Corp publication. Their name should appear in the title and be referenced consistently throughout the document. The tone must follow their brand voice: authoritative, clear, empowering, and personal but professional. The final output MUST include ALL VISUAL PLACEHOLDERS clearly marked AND the complete publication-ready whitepaper with all sections.",
            expected_output="The final, publication-ready whitepaper with clearly marked visual recommendations in markdown format, with at least 2000 words of actual content (excluding visual placeholders).",
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
            description=f"Review and finalize the article about '{topic}' following these steps:\n\n1. If a markdown tool is available, use it to extract brand guidelines from the reference file. Try sections like 'Brand Voice', 'Style Guide', or check the complete document.\n2. Review and optimize the content based on:\n   - Factual accuracy against the research summary\n   - Alignment with brand voice and style guidelines (if available)\n   - Content structure and logical flow\n   - Quality and engagement level\n   - Technical accuracy\n3. Make all necessary improvements and generate the final output:\n   - Apply corrections for any inaccuracies\n   - Enhance flow and transitions where needed\n   - Adjust tone and style to match brand guidelines (if available)\n   - Ensure the article maintains its target length (800-1000 words)\n   - Format according to markdown standards\n\nIMPORTANT: The final output MUST be the complete, publication-ready article, not just a comment or status update.",
            expected_output="The final, publication-ready article in markdown format, incorporating all necessary improvements.",
            agent=self.agents["editor"],  # L'editor si occupa sia della revisione che della finalizzazione
            async_execution=False,
            dependencies=[writing_editing_task],
            tools=[self.agents["editor"].tools[0]] if len(self.agents["editor"].tools) > 0 else []  # Aggiungi lo strumento markdown solo se disponibile
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