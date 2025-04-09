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
            return self._create_extended_workflow(topic)
        elif content_type == "extended_article":
            return self._create_extended_article_workflow(topic)
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