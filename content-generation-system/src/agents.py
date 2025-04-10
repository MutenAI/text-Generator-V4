from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.chat_models import ChatOpenAI as LangchainChatOpenAI
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

    def create_agents(
        self, 
        web_search_tool, 
        markdown_tool, 
        use_economic_mode=None, 
        provider_preference=None
    ) -> Dict[str, Agent]:
        """
        Crea tutti gli agenti necessari per il sistema

        Args:
            web_search_tool: Tool per la ricerca web
            markdown_tool: Tool per l'analisi Markdown
            use_economic_mode: Usa modalità economica (modelli più economici)
            provider_preference: Provider preferito ('openai', 'anthropic', 'deepseek')

        Returns:
            Dizionario con tutti gli agenti creati
        """
        # Se use_economic_mode non è specificato, controlla la variabile d'ambiente
        if use_economic_mode is None:
            use_economic_mode = os.getenv('ECONOMIC_MODE', 'false').lower() == 'true'

        # Se la modalità economica è attiva, imposta DeepSeek come provider preferito
        if use_economic_mode and not provider_preference:
            provider_preference = "deepseek"

        self.logger.info(f"Creazione agenti con modalità economica: {use_economic_mode}, provider: {provider_preference}")

        # Usa i parametri dalla configurazione se disponibili
        model_name = self.config.get('model_name', LLM_MODELS['openai']['default']) if self.config else LLM_MODELS['openai']['default']
        temperature = self.config.get('temperature', LLM_MODELS['openai']['temperature']['medium']) if self.config else LLM_MODELS['openai']['temperature']['medium']
        openai_api_key = self.config.get('openai_api_key', OPENAI_API_KEY) if self.config else OPENAI_API_KEY

        # Verifica se è attiva la modalità economica
        

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
                goal="Produce comprehensive, accurate, and up-to-date summaries on requested topics",
                backstory="You are an expert researcher who finds the most relevant and current information on any topic.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name=LLM_MODELS['deepseek']['default'],
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                ),
                tools=[web_search_tool]
            )
        else:
            # Usa OpenAI per Web Searcher (comportamento predefinito)
            web_searcher = Agent(
                role="Web Research Specialist",
                goal="Produce comprehensive, accurate, and up-to-date summaries on requested topics",
                backstory="You are an expert researcher who finds the most relevant and current information on any topic.",
                verbose=True,
                process_type='sequential',
                llm=ChatOpenAI(
                    temperature=temperature,
                    model_name=model_name,
                    api_key=openai_api_key
                ),
                tools=[web_search_tool]
            )

        # 2. Content Architect
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Content Architect in modalità economica
            architect = Agent(
                role="Content Architect",
                goal="Design detailed content structures and outlines for extended documents",
                backstory="You are a strategic content planner who excels at organizing complex information into clear, logical structures.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name=LLM_MODELS['deepseek']['default'],
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                )
            )
        else:
            # Usa OpenAI per Content Architect (comportamento predefinito)
            architect = Agent(
                role="Content Architect",
                goal="Design detailed content structures and outlines for extended documents",
                backstory="You are a strategic content planner who excels at organizing complex information into clear, logical structures.",
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
                goal="Create detailed, well-researched content for specific document sections",
                backstory="You are a specialized writer who excels at developing comprehensive content for individual document sections while maintaining consistency with the overall document structure.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name=LLM_MODELS['deepseek']['default'],
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                )
            )
        else:
            # Usa Anthropic per Section Writer (comportamento predefinito)
            section_writer = Agent(
                role="Section Writer",
                goal="Create detailed, well-researched content for specific document sections",
                backstory="You are a specialized writer who excels at developing comprehensive content for individual document sections while maintaining consistency with the overall document structure.",
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
                goal="Create engaging, informative content based on research summaries",
                backstory="You are a skilled writer who transforms research into compelling articles.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name=LLM_MODELS['deepseek']['default'],
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                )
            )
        else:
            # Usa Anthropic per Copywriter (comportamento predefinito)
            copywriter = Agent(
                role="Content Copywriter",
                goal="Create engaging, informative content based on research summaries",
                backstory="You are a skilled writer who transforms research into compelling articles.",
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
                goal="Optimize content to match brand voice and style from reference documents",
                backstory="You are an expert editor who ensures content aligns perfectly with brand guidelines.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=temperature,
                    model_name=LLM_MODELS['deepseek']['default'],
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                ),
                tools=[markdown_tool]
            )
        else:
            # Usa OpenAI per Editor (comportamento predefinito)
            editor = Agent(
                role="Content Editor and Brand Aligner",
                goal="Optimize content to match brand voice and style from reference documents",
                backstory="You are an expert editor who ensures content aligns perfectly with brand guidelines.",
                verbose=True,
                process_type='sequential',
                llm=ChatOpenAI(
                    temperature=temperature,
                    model_name=model_name,
                    api_key=openai_api_key
                ),
                tools=[markdown_tool]
            )

        # 6. Quality Reviewer
        if use_economic_mode and provider_preference == "deepseek":
            # Usa DeepSeek per Quality Reviewer in modalità economica
            quality_reviewer = Agent(
                role="Content Quality Reviewer",
                goal="Ensure content meets high standards of quality, accuracy, and relevance",
                backstory="You are a meticulous quality control specialist who ensures all content meets the highest standards before publication.",
                verbose=True,
                process_type='sequential',
                llm=LangchainChatOpenAI(
                    temperature=0.2,  # Temperatura più bassa per valutazioni più precise
                    model_name=LLM_MODELS['deepseek']['default'],
                    openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                    openai_api_base="https://api.deepseek.com/v1"
                ),
                tools=[markdown_tool]
            )
        else:
            # Usa OpenAI per Quality Reviewer (comportamento predefinito)
            quality_reviewer = Agent(
                role="Content Quality Reviewer",
                goal="Ensure content meets high standards of quality, accuracy, and relevance",
                backstory="You are a meticulous quality control specialist who ensures all content meets the highest standards before publication.",
                verbose=True,
                process_type='sequential',
                llm=ChatOpenAI(
                    temperature=0.2,  # Temperatura più bassa per valutazioni più precise
                    model_name="gpt-4",  # Usa sempre GPT-4 per la qualità
                    api_key=openai_api_key
                ),
                tools=[markdown_tool]
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