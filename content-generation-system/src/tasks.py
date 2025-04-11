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
            description=f"""Research and analysis for a whitepaper on '{topic}'. Complete these tasks thoroughly:

1. COMPREHENSIVE RESEARCH:
   a) Conduct extensive market research using authoritative sources
   b) Use your web search tool to gather current data and statistics
   c) Identify industry-specific needs, challenges, and pain points
   d) Analyze competitive solutions and their limitations
   e) Research key stakeholders and target audience needs

2. EVIDENCE GATHERING:
   a) Collect minimum 5 relevant statistics from reliable sources
   b) Identify 3+ expert opinions or quotes that provide insights
   c) Find case studies or examples that illustrate key points
   d) Document emerging trends and future projections
   e) Record market size and growth potential data

3. ANALYSIS AND SYNTHESIS:
   a) Analyze findings to identify primary insights and opportunities
   b) Segment information into logical categories
   c) Evaluate reliability and relevance of all sources
   d) Identify contradictory viewpoints and reconcile differences
   e) Assess gaps in available information

Your output must include a detailed research report with comprehensive market analysis, supported by concrete evidence suitable for a whitepaper with at least 2000 words of actual content (excluding visual placeholders).""",
            expected_output="A comprehensive research report with market analysis and supporting evidence in markdown format.",
            agent=self.agents["web_searcher"],
            async_execution=False
        )

        # Task 2: Outline e Struttura del white paper
        outline_structure_task = Task(
            description=f"""Create a detailed outline and structure for a whitepaper on '{topic}' based on the provided research. 

1. STRUCTURAL FRAMEWORK:
   Design a professional whitepaper structure with at least 2000 words of actual content (excluding visual placeholders) with the following MANDATORY components:
   a) Executive summary (200-300 words)
   b) Introduction to the problem/challenge (300-400 words)
   c) Background and current landscape (400-500 words)
   d) Proposed approach/solution (400-500 words)
   e) Implementation considerations (300-400 words)
   f) Case studies or examples (300-400 words)
   g) Future outlook (200-300 words)
   h) Conclusion (200-300 words)

2. DETAILED SECTION PLANNING:
   a) Create detailed section breakdowns with specific subsections
   b) Define 3-5 key points for each main section
   c) Plan information hierarchy with primary and secondary arguments
   d) Identify placement for statistics, quotes and case examples
   e) Map logical flow between sections to ensure coherence

3. CONTENT ALLOCATION:
   a) Assign specific word count targets for each section and subsection
   b) Balance content distribution based on importance
   c) Plan space for evidence integration (quotes, statistics)
   d) Identify opportunities for visual elements
   e) Ensure total content meets minimum 2000-word requirement

Your output must be a comprehensive whitepaper outline with detailed section breakdowns, key points for each section, and specific word count targets to ensure proper content distribution.""",
            expected_output="A detailed whitepaper outline with section breakdowns, key points, and word count targets in markdown format.",
            agent=self.agents["copywriter"],
            async_execution=False,
            dependencies=[research_analysis_task]
        )

        # Task 3: Sviluppo dei contenuti
        content_development_task = Task(
            description=f"""Develop the main content for a whitepaper on '{topic}' following the provided outline. 

1. CONTENT DEVELOPMENT:
   a) Write comprehensive content for each section of the whitepaper
   b) Adhere strictly to the word count guidance for each section
   c) Ensure a MINIMUM of 2000 words of actual content (excluding visual placeholders)
   d) Maintain consistent depth of analysis across all sections
   e) Develop all arguments fully with supporting evidence

2. EVIDENCE INTEGRATION:
   a) Incorporate research findings throughout the document
   b) Include minimum 5 statistics or data points with sources
   c) Integrate expert insights and quotes appropriately
   d) Reference case studies or real-world examples
   e) Cite all sources properly within the text

3. STYLE AND TONE REQUIREMENTS:
   a) Maintain a professional, authoritative tone appropriate for a whitepaper
   b) Use industry-specific terminology with explanations where needed
   c) Ensure logical progression of ideas within each section
   d) Create smooth transitions between sections and arguments
   e) Balance technical depth with accessibility based on audience
   f) Verify technical accuracy of all content

4. QUALITY VERIFICATION:
   a) Count the words in your draft (excluding visual placeholders)
   b) Verify minimum 2000-word requirement is met
   c) Check logical flow and coherence between sections
   d) Review for gaps in argumentation or reasoning
   e) Ensure consistent quality across all sections

Your output must be a fully developed whitepaper draft with all sections completed according to the outline, containing at least 2000 words of actual content (excluding any placeholders).""",
            expected_output="A fully developed whitepaper draft with at least 2000 words of actual content (excluding visual placeholders) in markdown format.",
            agent=self.agents["copywriter"],
            async_execution=False,
            dependencies=[outline_structure_task]
        )

        # Task 4: Revisione tecnica e ottimizzazione
        expert_review_task = Task(
            description=f"""Conduct an expert technical review and optimize the whitepaper on '{topic}'.

1. REFERENCE FILE ACCESS - REQUIRED FIRST STEP:
   a) Extract brand guidelines using markdown_reference({{"section": "Brand Voice"}})
   b) Extract style guidance using markdown_reference({{"section": "Style Guide"}})
   c) Extract structure patterns using markdown_reference({{"section": "Content Structure"}})
   d) Extract terminology preferences using markdown_reference({{"section": "Terminology Preferences"}})
   
   Document all successful and failed access attempts in your thinking process.

2. TECHNICAL ACCURACY REVIEW:
   a) Verify technical precision of all concepts and terminology
   b) Ensure all claims are supported by research evidence
   c) Confirm accuracy of statistics, dates, and attributed quotes
   d) Check logical coherence and absence of contradictions
   e) Ensure all arguments are fully developed and sound

3. CONTENT OPTIMIZATION:
   a) Align with brand voice and style guidelines from reference file
   b) Optimize flow between sections and logical progression
   c) Enhance clarity of complex concepts and technical explanations
   d) Strengthen persuasive elements and argumentation
   e) Improve professional tone and language consistency
   f) Replace vague statements with specific, actionable insights

4. STRUCTURAL VERIFICATION:
   a) Ensure proper heading hierarchy and document structure
   b) Verify section proportions follow the outline specifications
   c) Confirm minimum 2000 words of actual content (excluding visuals)
   d) Add substantive content if word count is below requirement
   e) Check formatting consistency throughout the document

Your output must be a revised and optimized whitepaper that maintains technical accuracy while being engaging and persuasive, with at least 2000 words of actual content.""",
            expected_output="A revised and optimized whitepaper draft with at least 2000 words of actual content (excluding visual placeholders) in markdown format.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=[content_development_task],
            tools=[self.agents["editor"].tools[0]] if len(self.agents["editor"].tools) > 0 else []
        )

        # Task 5: Pianificazione elementi visivi e finalizzazione
        visual_planning_task = Task(
            description=f"""Plan visual elements and finalize the whitepaper on '{topic}'.

1. BRAND ALIGNMENT - MANDATORY FIRST STEP:
   a) Use the markdown tool to extract brand guidelines with specific commands:
      - markdown_reference({{"section": "Brand Voice"}})
      - markdown_reference({{"section": "Visual Identity"}}) if available
      - markdown_reference({{"section": "Content Structure"}}) if available
   b) If extraction fails, document attempts and proceed with professional standards
   c) Apply brand guidelines throughout the document
   d) If a specific brand is identified, ensure content represents their perspective
   e) Ensure brand name appears in title and is referenced consistently

2. VISUAL ELEMENTS PLANNING:
   a) Identify strategic locations for visual elements throughout the document:
      - Key data visualizations for statistics and trends
      - Conceptual diagrams or flowcharts for processes
      - Infographics for complex information synthesis
      - Tables for comparative data presentation
   b) Create minimum 3 visual element recommendations
   c) Ensure visuals enhance understanding rather than duplicate text
   d) Place visuals at logical points in the content flow

3. VISUAL PLACEHOLDERS CREATION:
   ADD EXPLICITLY MARKED VISUAL PLACEHOLDERS with detailed descriptions. Format exactly as:

   [VISUAL: Type - Detailed description of what the visual should show]

   Example: [VISUAL: Chart - Line graph showing investment trends from 2020-2025 with highlighted areas of growth]

4. DESIGN SPECIFICATIONS:
   a) Add a dedicated 'Design Notes' section at the end with:
      - Visual style guide recommendations aligned with brand
      - Technical specifications for each visual (dimensions, colors)
      - Accessibility requirements (contrast, text size, alt text)
      - Data source requirements for charts and graphs

5. FINAL QUALITY ASSURANCE:
   a) Conduct comprehensive proofreading and formatting:
      - Ensure consistent heading structure
      - Verify proper citation of all sources
      - Format according to professional whitepaper standards
   b) Verify the final document contains at least 2000 words of actual content
   c) Include an explicit word count statement at the end

YOUR OUTPUT MUST INCLUDE ALL VISUAL PLACEHOLDERS clearly marked AND the complete publication-ready whitepaper with all sections.""",
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
            description=f"""Research and outline for topic: '{topic}'. Complete these tasks thoroughly:

1. RESEARCH PHASE:
   a) Conduct comprehensive research using authoritative sources
   b) Gather current, accurate information with relevant statistics
   c) Identify 3-5 key points supported by evidence
   d) Document all sources properly for citation

2. OUTLINE DEVELOPMENT:
   a) Structure an 800-1000 word article with:
      - Compelling introduction with hook (100-150 words)
      - 2-3 main sections (200-300 words each)
      - Clear conclusion with call-to-action (100-150 words)
   b) Create logical flow between sections
   c) Plan for data integration and examples
   d) Define key messaging for each section

Your output must include:
1. A comprehensive research summary with key findings and sources
2. A detailed content outline with section breakdowns and word count allocations""",
            expected_output="A research summary and content outline for a 800-1000 word article in markdown format.",
            agent=self.agents["web_searcher"],
            async_execution=False
        )

        # Task 2: Content Creation + Initial Editing
        writing_editing_task = Task(
            description=f"""Create and optimize an article on '{topic}' following these specific guidelines:

1. CONTENT CREATION:
   a) Follow the provided outline structure precisely
   b) Develop an engaging introduction with a strong hook (100-150 words)
   c) Create 2-3 main sections (200-300 words each) with:
      - Clear subheadings that incorporate key terms
      - Concrete examples and evidence
      - Logical transitions between paragraphs
   d) Write a conclusion that summarizes key points and includes a clear call-to-action (100-150 words)

2. WRITING STYLE REQUIREMENTS:
   a) Professional yet conversational tone
   b) Active voice (minimum 80% of sentences)
   c) Varied sentence structure and length
   d) Paragraph length of 3-5 sentences maximum
   e) Industry-appropriate terminology explained when necessary
   f) Engagement elements (questions, scenarios, examples)

3. OPTIMIZATION:
   a) Verify total word count (800-1000 words)
   b) Ensure proper formatting with consistent heading hierarchy
   c) Check all statements are factually accurate and supported
   d) Add appropriate transitions between sections

Your output must be a complete, well-structured article with all sections fully developed and ready for final review.""",
            expected_output="A well-structured and initially optimized article of 800-1000 words in markdown format.",
            agent=self.agents["copywriter"],
            async_execution=False,
            dependencies=[research_outline_task]
        )

        # Task 3: Final Review + Brand Alignment
        review_finalize_task = Task(
            description=f"""Review and finalize the article about '{topic}' following these MANDATORY steps:

1. REFERENCE FILE ACCESS - FIRST REQUIRED STEP:
   a) Extract brand guidelines using markdown_reference({{"section": "Brand Voice"}})
   b) Extract style guidance using markdown_reference({{"section": "Style Guide"}})
   c) Extract structure patterns using markdown_reference({{"section": "Content Structure"}})
   d) Extract terminology preferences using markdown_reference({{"section": "Terminology Preferences"}})
   
   Document all successful and failed access attempts in your thinking.

2. CONTENT REVIEW AND ALIGNMENT:
   a) Ensure factual accuracy by comparing with research summary
   b) Apply brand voice characteristics (document specific applications)
   c) Implement style guide formatting requirements
   d) Follow content structure patterns from guidelines
   e) Use preferred terminology and avoid prohibited terms
   f) Verify technical accuracy and clarity

3. QUALITY ENHANCEMENT:
   a) Improve transitions between sections
   b) Enhance engagement elements
   c) Optimize headings for clarity and SEO
   d) Ensure consistent tone throughout
   e) Verify logical flow and argumentation

4. FINALIZATION:
   a) Format according to markdown standards
   b) Verify final word count (800-1000 words)
   c) Ensure all brand guidelines have been properly applied

If reference files cannot be accessed, document the specific errors encountered and proceed using professional standards.

YOUR OUTPUT MUST BE THE COMPLETE, PUBLICATION-READY ARTICLE with all brand alignments implemented.""",
            expected_output="The final, publication-ready article in markdown format, incorporating all brand guidelines.",
            agent=self.agents["editor"],
            async_execution=False,
            dependencies=[writing_editing_task],
            tools=[self.agents["editor"].tools[0]] if len(self.agents["editor"].tools) > 0 else []
        )

        # Always include the final review step for brand alignment
        tasks = [research_outline_task, writing_editing_task, review_finalize_task]
        return tasks

    def _check_guideline_adherence(self, content, guidelines=None):
        """Verifica se il contenuto è aderente alle linee guida del brand.
        
        Args:
            content: Contenuto da verificare
            guidelines: Linee guida da rispettare (opzionale)
            
        Returns:
            True se il contenuto è aderente alle linee guida, False altrimenti
        """
        from .utils import handle_markdown_reference
        
        # Se non sono state fornite linee guida, prova a estrarle dal file di riferimento
        if not guidelines:
            try:
                # Usa il nuovo handler per una gestione più robusta
                results = handle_markdown_reference("Brand Voice", 
                                                   ["Style Guide", "Content Structure", "Terminology Preferences"])
                
                if results["successful_sections"]:
                    guidelines = "\n\n".join(results["successful_sections"].values())
                    self.logger.info(f"Estratte {len(results['successful_sections'])} sezioni di linee guida")
                else:
                    self.logger.warning("Impossibile estrarre le linee guida, utilizzo controllo base")
                    return len(content) > 800  # Criterio base più stringente: almeno 800 caratteri
            except Exception as e:
                self.logger.error(f"Errore nell'estrazione delle linee guida: {str(e)}")
                return len(content) > 800  # Criterio base più stringente: almeno 800 caratteri
        
        # Implementazione reale del controllo di aderenza
        if content and guidelines:
            # Estrai termini e frasi chiave dalle linee guida
            import re
            
            # Estrai elementi chiave dalle linee guida
            keywords = []
            
            # Estrai elementi in grassetto (**testo**)
            bold_items = re.findall(r'\*\*(.+?)\*\*', guidelines)
            keywords.extend(bold_items)
            
            # Estrai elementi puntati (- elemento o * elemento)
            bullet_points = re.findall(r'[-*]\s+(.+?)$', guidelines, re.MULTILINE)
            keywords.extend(bullet_points)
            
            # Estrai titoli di sezione (## Titolo)
            headings = re.findall(r'##\s+(.+?)$', guidelines, re.MULTILINE)
            keywords.extend(headings)
            
            # Se non ci sono elementi chiave estratti, usa un approccio di base
            if not keywords:
                return len(content) > 800
            
            # Verifica la presenza dei termini chiave nel contenuto
            matches = 0
            for keyword in keywords:
                if keyword.lower() in content.lower():
                    matches += 1
            
            # Calcola il punteggio di aderenza
            adherence_score = matches / max(1, len(keywords))
            self.logger.info(f"Aderenza alle linee guida: {adherence_score:.2f} ({matches}/{len(keywords)} termini)")
            
            # Soglia di aderenza: 70%
            return adherence_score >= 0.7
        
        # Se non ci sono contenuti o linee guida, usa un approccio di base
        return len(content) > 800