from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOpenAI as LangchainChatOpenAI
from .config import LLM_MODELS, OPENAI_API_KEY, ANTHROPIC_API_KEY, validate_environment
import os

class AgentsFactory:
    """Factory per creare gli agenti specializzati per la generazione di contenuti."""

    def __init__(self, config=None, logger=None):
        # Valida la presenza delle variabili d'ambiente necessarie
        validate_environment()
        self.config = config
        self.logger = logger

        # Metriche di performance
        self.calls_per_agent = {}
        self.execution_times = {}
        self.errors_per_agent = {}

    def create_agents(self, web_search_tool, markdown_tool):
        """Crea gli agenti con i loro rispettivi tool."""

        # Usa i parametri dalla configurazione se disponibili
        model_name = self.config.get('model_name', LLM_MODELS['openai']['default']) if self.config else LLM_MODELS['openai']['default']
        temperature = self.config.get('temperature', LLM_MODELS['openai']['temperature']['medium']) if self.config else LLM_MODELS['openai']['temperature']['medium']
        openai_api_key = self.config.get('openai_api_key', OPENAI_API_KEY) if self.config else OPENAI_API_KEY

        # Verifica se è attiva la modalità economica
        use_economic_mode = self.config.get('use_economic_mode', False) if self.config else False
        provider_preference = self.config.get('provider_preference', None) if self.config else None

        # Se è attiva la modalità economica, usa DeepSeek come provider principale
        if use_economic_mode and provider_preference == "deepseek":
            self.logger.info("Modalità economica attivata: utilizzo DeepSeek come provider principale")
            deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
            if not deepseek_api_key:
                self.logger.warning("DEEPSEEK_API_KEY non trovata, utilizzo OpenAI come fallback")
                use_economic_mode = False

        # 1. Web Searcher
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Web Searcher in modalità economica
            web_searcher = Agent(
                role="Web Research Specialist",
                goal="Produce comprehensive, accurate, and up-to-date research summaries that align with brand positioning and terminology",
                backstory="You are an expert digital researcher who finds the most relevant, authoritative, and current information on any topic. You have exceptional abilities to evaluate source credibility, synthesize information, and organize findings into clear, structured reports. You prioritize accuracy and always cite sources properly. You're skilled at identifying information that complements the brand's existing knowledge base and terminology, ensuring research findings can be seamlessly integrated into final content.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name="deepseek/deepseek-chat", 
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                ),
                tools=[web_search_tool] if web_search_tool is not None else []
            )
        else:
            # Usa OpenAI per Web Searcher (comportamento predefinito)
            web_searcher = Agent(
                role="Web Research Specialist",
                goal="Produce comprehensive, accurate, and up-to-date research summaries that align with brand positioning and terminology",
                backstory="You are an expert digital researcher who finds the most relevant, authoritative, and current information on any topic. You have exceptional abilities to evaluate source credibility, synthesize information, and organize findings into clear, structured reports. You prioritize accuracy and always cite sources properly. You're skilled at identifying information that complements the brand's existing knowledge base and terminology, ensuring research findings can be seamlessly integrated into final content.",
                verbose=True,
                process_type='sequential',
                llm=ChatOpenAI(
                    temperature=temperature,
                    model_name=model_name,
                    api_key=openai_api_key
                ),
                tools=[web_search_tool] if web_search_tool is not None else []
            )

        # 2. Content Architect
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Content Architect in modalità economica
            architect = Agent(
                role="Content Architect",
                goal="Design strategic content structures that organize complex information according to brand standards and content patterns",
                backstory="You are a strategic content planner with exceptional skills in information architecture. Before designing any structure, you carefully analyze audience needs, key messaging priorities, and the brand's established content patterns. You excel at creating outlines that follow the brand's preferred content structures while adapting to specific topic requirements. Your expertise ensures all content has a solid foundation that serves both audience needs and aligns with the brand's established content formats and section patterns.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name="deepseek/deepseek-chat", 
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                )
            )
        else:
            # Usa OpenAI per Content Architect (comportamento predefinito)
            architect = Agent(
                role="Content Architect",
                goal="Design strategic content structures that organize complex information according to brand standards and content patterns",
                backstory="You are a strategic content planner with exceptional skills in information architecture. Before designing any structure, you carefully analyze audience needs, key messaging priorities, and the brand's established content patterns. You excel at creating outlines that follow the brand's preferred content structures while adapting to specific topic requirements. Your expertise ensures all content has a solid foundation that serves both audience needs and aligns with the brand's established content formats and section patterns.",
                verbose=True,
                process_type='sequential',
                llm=ChatOpenAI(
                    temperature=temperature,
                    model_name=model_name,
                    api_key=openai_api_key
                )
            )

        # 3. Section Writer
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Section Writer in modalità economica
            section_writer = Agent(
                role="Section Writer",
                goal="Create detailed, well-researched content sections that follow brand voice and terminology guidelines",
                backstory="You are a specialized content creator who excels at developing comprehensive content for specific document sections. You have a unique ability to maintain consistency with brand voice while delivering subject matter expertise. You always strive to incorporate the brand's terminology preferences and maintain the established content structure patterns. You excel at working within word count constraints and editorial guidelines while still producing distinctive, high-quality content that feels native to the brand.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name="deepseek/deepseek-chat",
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                )
            )
        else:
            # Usa Anthropic per Section Writer (comportamento predefinito)
            section_writer = Agent(
                role="Section Writer",
                goal="Create detailed, well-researched content sections that follow brand voice and terminology guidelines",
                backstory="You are a specialized content creator who excels at developing comprehensive content for specific document sections. You have a unique ability to maintain consistency with brand voice while delivering subject matter expertise. You always strive to incorporate the brand's terminology preferences and maintain the established content structure patterns. You excel at working within word count constraints and editorial guidelines while still producing distinctive, high-quality content that feels native to the brand.",
                verbose=True,
                process_type='sequential',
                llm=ChatAnthropic(
                    temperature=temperature,
                    model_name=LLM_MODELS['anthropic']['default'],
                    api_key=ANTHROPIC_API_KEY
                )
            )

        # 4. Copywriter
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Copywriter in modalità economica
            copywriter = Agent(
                role="Content Copywriter",
                goal="Transform complex research into compelling, brand-aligned content that engages target audiences",
                backstory="You are a versatile professional writer who transforms technical research into accessible, engaging content that adheres to brand voice and terminology guidelines. You craft content that follows the brand's established structure patterns while bringing topics to life using the brand's distinctive tone and personality. You're skilled at balancing factual accuracy with narrative engagement while incorporating the preferred terminology and avoiding expressions that don't align with the brand's voice. Your writing seamlessly combines research findings with the brand's unique perspective.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name="deepseek/deepseek-chat",
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                )
            )
        else:
            # Usa Anthropic per Copywriter (comportamento predefinito)
            copywriter = Agent(
                role="Content Copywriter",
                goal="Transform complex research into compelling, brand-aligned content that engages target audiences",
                backstory="You are a versatile professional writer who transforms technical research into accessible, engaging content that adheres to brand voice and terminology guidelines. You craft content that follows the brand's established structure patterns while bringing topics to life using the brand's distinctive tone and personality. You're skilled at balancing factual accuracy with narrative engagement while incorporating the preferred terminology and avoiding expressions that don't align with the brand's voice. Your writing seamlessly combines research findings with the brand's unique perspective.",
                verbose=True,
                process_type='sequential',
                llm=ChatAnthropic(
                    temperature=temperature,
                    model_name=LLM_MODELS['anthropic']['default'],
                    api_key=ANTHROPIC_API_KEY
                )
            )

        # 5. Editor
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Editor in modalità economica
            editor = Agent(
                role="Content Editor and Brand Aligner",
                goal="Align content perfectly with brand guidelines in voice, structure, terminology, and formatting",
                backstory="You are an expert editor with exceptional skills in content refinement and brand alignment. Your PRIMARY responsibility is to ALWAYS check reference markdown files using the markdown_tool BEFORE editing any content. Begin by systematically accessing these EXACT sections in this order: 1) 'Brand Voice', 2) 'Style Guide', 3) 'Content Structure', 4) 'Terminology Preferences'. For each section, extract specific guidance and EXPLICITLY cite it when making edits using 'According to [Section Name]: [direct quote]' format. If a section access fails, document the error and try the next section. Review content against ALL brand dimensions: voice/tone alignment, formatting adherence, structural compliance, and terminology usage. Flag content that contradicts competitor positioning or misrepresents company background and products. If ALL reference file access attempts fail, clearly document the errors and apply professional editing standards. Your output MUST be the COMPLETE, publication-ready content with explicit documentation of how brand guidelines were applied.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name="deepseek/deepseek-chat",
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                ),
                tools=[markdown_tool] if markdown_tool is not None else []
            )
        else:
            # Usa OpenAI per Editor (comportamento predefinito)
            editor = Agent(
                role="Content Editor and Brand Aligner",
                goal="Align content perfectly with brand guidelines in voice, structure, terminology, and formatting",
                backstory="You are an expert editor with exceptional skills in content refinement and brand alignment. Your PRIMARY responsibility is to ALWAYS check reference markdown files using the markdown_tool BEFORE editing any content. Begin by systematically accessing these EXACT sections in this order: 1) 'Brand Voice', 2) 'Style Guide', 3) 'Content Structure', 4) 'Terminology Preferences'. For each section, extract specific guidance and EXPLICITLY cite it when making edits using 'According to [Section Name]: [direct quote]' format. If a section access fails, document the error and try the next section. Review content against ALL brand dimensions: voice/tone alignment, formatting adherence, structural compliance, and terminology usage. Flag content that contradicts competitor positioning or misrepresents company background and products. If ALL reference file access attempts fail, clearly document the errors and apply professional editing standards. Your output MUST be the COMPLETE, publication-ready content with explicit documentation of how brand guidelines were applied.",
                verbose=True,
                process_type='sequential',
                llm=ChatOpenAI(
                    temperature=temperature,
                    model_name=model_name,
                    api_key=openai_api_key
                ),
                tools=[markdown_tool] if markdown_tool is not None else []
            )

        # 6. Quality Reviewer
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Quality Reviewer in modalità economica
            quality_reviewer = Agent(
                role="Content Quality Reviewer",
                goal="Ensure content meets all brand standards and quality requirements before publication",
                backstory="You are a meticulous quality assurance specialist responsible for the final verification of content against brand standards. Your review process BEGINS with systematic reference file verification using the markdown_tool, following this EXACT sequence: 1) 'Brand Voice', 2) 'Style Guide', 3) 'Content Structure', 4) 'Terminology Preferences', 5) 'Company Background', 6) 'Product Information', 7) 'Competitor Analysis'. For each successful access, EXPLICITLY cite the guidelines when assessing content. Your quality assessment examines multiple dimensions: brand voice consistency, structural adherence to preferred patterns, correct terminology usage, formatting compliance, factual accuracy regarding company and products, and appropriate competitive positioning. When identifying issues, provide SPECIFIC examples with CLEAR recommendations, citing the exact reference section that's being violated. If reference sections cannot be accessed, document all attempts with exact error messages and proceed using professional standards. Your feedback must be structured, actionable, and evidence-based.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=0.2,  # Temperatura più bassa per valutazioni più precise
                    model_name="deepseek/deepseek-chat",
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                ),
                tools=[markdown_tool] if markdown_tool is not None else []
            )
        else:
            # Usa OpenAI per Quality Reviewer (comportamento predefinito)
            quality_reviewer = Agent(
                role="Content Quality Reviewer",
                goal="Ensure content meets all brand standards and quality requirements before publication",
                backstory="You are a meticulous quality assurance specialist responsible for the final verification of content against brand standards. Your review process BEGINS with systematic reference file verification using the markdown_tool, following this EXACT sequence: 1) 'Brand Voice', 2) 'Style Guide', 3) 'Content Structure', 4) 'Terminology Preferences', 5) 'Company Background', 6) 'Product Information', 7) 'Competitor Analysis'. For each successful access, EXPLICITLY cite the guidelines when assessing content. Your quality assessment examines multiple dimensions: brand voice consistency, structural adherence to preferred patterns, correct terminology usage, formatting compliance, factual accuracy regarding company and products, and appropriate competitive positioning. When identifying issues, provide SPECIFIC examples with CLEAR recommendations, citing the exact reference section that's being violated. If reference sections cannot be accessed, document all attempts with exact error messages and proceed using professional standards. Your feedback must be structured, actionable, and evidence-based.",
                verbose=True,
                process_type='sequential',
                llm=ChatOpenAI(
                    temperature=0.2,  # Temperatura più bassa per valutazioni più precise
                    model_name="gpt-4",  # Usa sempre GPT-4 per la qualità
                    api_key=openai_api_key
                ),
                tools=[markdown_tool] if markdown_tool is not None else []
            )

        agents = {
            "web_searcher": web_searcher,
            "architect": architect,
            "section_writer": section_writer,
            "copywriter": copywriter,
            "editor": editor,
            "quality_reviewer": quality_reviewer
        }

        # Inizializza le metriche per ogni agente
        for agent_name in agents:
            self.calls_per_agent[agent_name] = 0
            self.execution_times[agent_name] = []
            self.errors_per_agent[agent_name] = 0

        return agents

    def get_performance_metrics(self):
        """Restituisce le metriche di performance degli agenti."""
        metrics = {
            "calls_per_agent": self.calls_per_agent,
            "avg_execution_time": {},
            "error_rate": {}
        }

        # Calcola tempo medio di esecuzione e tasso di errore per ogni agente
        for agent_name in self.calls_per_agent:
            if self.execution_times[agent_name]:
                avg_time = sum(self.execution_times[agent_name]) / len(self.execution_times[agent_name])
                metrics["avg_execution_time"][agent_name] = round(avg_time, 2)
            else:
                metrics["avg_execution_time"][agent_name] = 0

            if self.calls_per_agent[agent_name] > 0:
                error_rate = (self.errors_per_agent[agent_name] / self.calls_per_agent[agent_name]) * 100
                metrics["error_rate"][agent_name] = round(error_rate, 2)
            else:
                metrics["error_rate"][agent_name] = 0

        return metrics