"""Interfaccia utente Streamlit per content generator basato su CrewAI.
Permette di selezionare topic, reference file e workflow, e visualizzare l'output in markdown.
"""
import streamlit as st
import os
import yaml
import time
import logging
from datetime import datetime
import glob

# Importa i componenti del sistema
from src.config_manager import ConfigManager
from src.utils import ensure_directory_exists, generate_output_filename, sanitize_filename
from src.tools import WebSearchTool, MarkdownParserTool
from src.agents import AgentsFactory
from src.tasks import WorkflowManager
from src.quality import ContentQualityChecker
from src.config import SERPER_API_KEY
from langchain_community.chat_models import ChatOpenAI
from src.config import SERPER_API_KEY, LLM_MODELS, OPENAI_API_KEY

# Importa CrewAI
from crewai import Crew, Process

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("content_generator_app")

# Titolo e descrizione dell'app
st.set_page_config(
    page_title="Content Generator",
    page_icon="📝",
    layout="wide"
)

st.title("🤖 Content Generator con CrewAI")
st.subheader("Genera contenuti di alta qualità utilizzando agenti AI specializzati")

# Sidebar per le impostazioni e il controllo
with st.sidebar:
    st.header("⚙️ Impostazioni")

    # Selezione file di configurazione
    base_dir = os.path.dirname(__file__)
    config_files = (
        glob.glob(os.path.join(base_dir, "*.yaml")) +
        glob.glob(os.path.join(base_dir, "*.yml")) +
        glob.glob(os.path.join(base_dir, "config", "*.yaml")) +
        glob.glob(os.path.join(base_dir, "config", "*.yml"))
    )

    # Verifica esistenza directory config
    if not os.path.exists('config'):
        os.makedirs('config')

    # Controlla se ci sono file di configurazione
    if not config_files:
        st.error(f"Nessun file di configurazione trovato nelle seguenti posizioni:\n" +
                f"- {os.path.join(base_dir, '*.yaml/yml')}\n" +
                f"- {os.path.join(base_dir, 'config', '*.yaml/yml')}\n\n" +
                "Assicurati che esista almeno un file YAML valido in una di queste directory.")

    config_file = st.selectbox(
        "File di configurazione",
        options=config_files,
        index=0 if config_files else None,
        help="Seleziona il file di configurazione YAML contenente le impostazioni del sistema"
    )

    if config_files:
        st.info(f"File di configurazione trovati: {len(config_files)}")
        if st.checkbox("Mostra percorsi dei file di configurazione"):
            for f in config_files:
                st.code(f"📄 {f}")

    # Verifica che il file selezionato esista
    if config_file:
        try:
            if not os.path.exists(config_file):
                st.error(f"File di configurazione '{config_file}' non trovato. Selezionare un file valido.")
                st.info(f"File cercato in: {os.path.abspath(config_file)}")
                config_file = None
            elif not config_file.endswith(('.yaml', '.yml')):
                st.error(f"Il file selezionato '{config_file}' non è un file YAML valido.")
                config_file = None
        except Exception as e:
            st.error(f"Errore durante la verifica del file: {str(e)}")
            config_file = None

    # Opzioni di generazione
    st.subheader("Opzioni di generazione")

    # Reference file
    reference_files = glob.glob("*.md") + glob.glob("**/*.md")
    reference_file = st.selectbox(
        "File di riferimento (brand guidelines)",
        options=["Nessuno"] + reference_files,
        index=0,
        help="Seleziona un file Markdown con linee guida del brand"
    )

    if reference_file == "Nessuno":
        reference_file = None

    # Pulsante per caricare il proprio file MD
    uploaded_file = st.file_uploader("...o carica un file di riferimento", type=["md"])
    if uploaded_file is not None:
        # Salva il file caricato
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())
        reference_file = uploaded_file.name
        st.success(f"File caricato: {uploaded_file.name}")

    # Opzioni avanzate
    with st.expander("Opzioni avanzate"):
        col1, col2 = st.columns(2)
        with col1:
            use_cache = st.checkbox("Usa cache (riduce chiamate API)", value=True)
            use_economic_mode = st.checkbox("Modalità economica (modelli più economici)", value=False)
            check_adherence = st.checkbox("Verifica aderenza alle linee guida (riduce back and forth)", value=True)
        with col2:
            provider_preference = st.selectbox(
                "Provider preferito",
                ["Auto (ottimale)", "OpenAI", "Anthropic", "DeepSeek"],
                index=0
            )

        show_logs = st.checkbox("Mostra logs", value=True, help="Visualizza log durante la generazione")
        save_to_file = st.checkbox("Salva su file", value=True, help="Salva il contenuto generato su file")
        output_dir = st.text_input("Directory di output", value="./output", help="Directory dove salvare i file generati")
        
        # Aggiungi opzione per log dettagliati
        detailed_logs = st.checkbox("Log dettagliati agenti", value=True, help="Mostra comunicazioni dettagliate tra gli agenti")

    # Modalità economica con DeepSeek
    use_deepseek_mode = st.checkbox("Modalità economica (DeepSeek)", value=False, help="Utilizza DeepSeek come provider principale per ridurre i costi")

# Form per l'inserimento dei parametri
with st.form("generation_form"):
    col1, col2 = st.columns(2)

    with col1:
        # Campo topic
        topic = st.text_input(
            "Topic da generare",
            placeholder="Es: Intelligenza Artificiale per il marketing",
            help="Inserisci l'argomento del contenuto da generare"
        )

    with col2:
        # Selezione workflow
        content_types = {
            "standard": "Articolo Standard (800-1000 parole)",
            "whitepaper": "White Paper (3000+ parole)"
        }

        content_type = st.selectbox(
            "Tipo di contenuto",
            options=list(content_types.keys()),
            format_func=lambda x: content_types[x],
            help="Seleziona il tipo di contenuto da generare"
        )

    # Pulsante di generazione
    generate_button = st.form_submit_button("🚀 Genera Contenuto")

# Gestione della generazione del contenuto
if generate_button:
    if not topic:
        st.error("Per favore inserisci un topic per la generazione.")
    elif not config_file or not os.path.exists(config_file):
        st.error("File di configurazione non trovato.")
    else:
        try:
            # Mostra il pannello di generazione
            generation_container = st.empty()
            with generation_container.container():
                st.info("⏳ Inizializzazione del sistema in corso...")

                # Inizializza la configurazione
                config_manager = ConfigManager(logger=logger)
                config = config_manager.load_config(config_path=config_file)

                # Override delle opzioni
                if reference_file:
                    config.brand_reference_file = reference_file

                # Crea la directory di output
                ensure_directory_exists(output_dir)

                # Inizializza tools
                st.write("🔍 Inizializzazione tools...")
                web_search_tool = WebSearchTool(
                    api_key=config.serper_api_key
                ).get_tool()

                markdown_tool = None
                if config.brand_reference_file and os.path.exists(config.brand_reference_file):
                    markdown_tool = MarkdownParserTool(
                        file_path=config.brand_reference_file
                    ).get_tool()
                    st.write(f"📚 Tool markdown inizializzato con {config.brand_reference_file}")

                # Inizializza agenti
                st.write("🤖 Creazione agenti specializzati...")

                # Applica modalità economica se selezionata
                if use_deepseek_mode:
                    st.write("💰 Modalità economica (DeepSeek) attivata")
                    config_dict = config.dict()
                    config_dict["provider_preference"] = "deepseek"
                    config_dict["use_economic_mode"] = True
                else:
                    config_dict = config.dict()

                agents_factory = AgentsFactory(
                    config=config_dict,
                    logger=logger
                )

                agents = agents_factory.create_agents(
                    web_search_tool=web_search_tool,
                    markdown_tool=markdown_tool
                )

                # Inizializza workflow manager
                st.write("🔄 Inizializzazione workflow manager...")
                workflow_manager = WorkflowManager(agents, logger=logger)

                #Imposta la verifica dell'aderenza alle linee guida
                workflow_manager.adherence_check_enabled = check_adherence

                # Genera nome file output
                output_filename = generate_output_filename(topic, output_dir)

                # Ottieni i task per il workflow specificato
                if not config.workflows or content_type not in config.workflows:
                    st.error(f"Workflow '{content_type}' non trovato nella configurazione. Verificare il file workflows.yaml.")
                    st.stop()

                workflow_steps = config.workflows[content_type]['steps']
                st.write(f"📋 Workflow selezionato: {content_types[content_type]}")
                st.write(f"🔄 Passi da eseguire: {len(workflow_steps)}")

                # Mostra i passi del workflow
                for step in workflow_steps:
                    st.write(f"- {step['task']}: {step['description']}")
                
                # Verifica se il file di riferimento esiste
                if markdown_tool is None and reference_file:
                    st.warning(f"⚠️ Attenzione: File di riferimento '{reference_file}' non trovato o non accessibile. Il controllo dell'aderenza al brand potrebbe essere compromesso.")
                
                st.write(f"📋 Creazione task per workflow {content_type}...")
                tasks = workflow_manager.create_tasks(topic, content_type)

                if not tasks:
                    st.error(f"Nessun task generato per il tipo di contenuto: {content_type}")
                    st.stop()

                st.write(f"✅ Creati {len(tasks)} task per il workflow")

                # Definisci se usare elaborazione parallela
                use_parallel = False  # Impostato a False di default per maggiore stabilità

                # Crea il crew
                crew_config = {
                    'agents': list(agents.values()),
                    'tasks': tasks,
                    'verbose': True if show_logs or detailed_logs else False,
                    'process': Process.hierarchical if use_parallel else Process.sequential
                }
                
                if detailed_logs:
                    st.info("🔍 Modalità log dettagliati attivata: vedrai tutte le comunicazioni tra gli agenti")

                # Add manager_llm when using hierarchical process
                if use_parallel:
                    crew_config['manager_llm'] = ChatOpenAI(
                        temperature=0.7,
                        model_name=LLM_MODELS['openai']['default'],
                        api_key=OPENAI_API_KEY
                    )

                crew = Crew(**crew_config)

                # Mostra progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Area per visualizzare i log dettagliati
                if detailed_logs:
                    st.subheader("📋 Log dettagliati comunicazioni agenti")
                    log_area = st.empty()
                    
                    # Configura handler per visualizzare log in Streamlit
                    class StreamlitLogHandler(logging.Handler):
                        def __init__(self, log_area):
                            super().__init__()
                            self.log_area = log_area
                            self.log_buffer = []
                            
                        def emit(self, record):
                            log_entry = self.format(record)
                            self.log_buffer.append(log_entry)
                            # Mantieni solo gli ultimi 100 log per evitare sovraccarichi
                            if len(self.log_buffer) > 100:
                                self.log_buffer = self.log_buffer[-100:]
                            self.log_area.code("\n".join(self.log_buffer))
                    
                    # Aggiungi handler per Streamlit
                    streamlit_handler = StreamlitLogHandler(log_area)
                    streamlit_handler.setLevel(logging.INFO)
                    streamlit_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                    logger.addHandler(streamlit_handler)
                    
                    # Configura anche i logger delle librerie utilizzate
                    for lib_logger in ["crewai", "langchain"]:
                        logging.getLogger(lib_logger).setLevel(logging.INFO)
                        logging.getLogger(lib_logger).addHandler(streamlit_handler)

                # Funzione per aggiornare lo stato (simulato perché CrewAI non fornisce callback di progresso)
                def update_progress():
                    stages = ["Ricerca", "Architettura", "Scrittura", "Editing", "Controllo Qualità"]
                    total_stages = len(stages)

                    for i, stage in enumerate(stages):
                        status_text.write(f"⏳ {stage} in corso...")
                        progress_bar.progress((i) / total_stages)
                        time.sleep(0.5)  # In una implementazione reale, questo sarebbe basato su eventi reali

                # Avvia l'esecuzione
                st.write("🚀 Avvio generazione contenuto...")
                status_text.write("⏳ Inizializzazione della generazione...")

                # Qui dovremmo avere una versione di Crew.kickoff che supporta callback di progresso
                # Per ora simuliamo il progresso
                import threading
                progress_thread = threading.Thread(target=update_progress)
                progress_thread.start()

                # Esegui la generazione
                start_time = time.time()
                result = crew.kickoff()
                execution_time = time.time() - start_time

                # Converti il risultato in una stringa se è un oggetto CrewOutput
                if hasattr(result, 'raw_output'):
                    result_text = result.raw_output
                else:
                    result_text = str(result)

                # Aggiorna la progress bar al completamento
                progress_bar.progress(1.0)
                status_text.write("✅ Generazione completata!")

                # Salva il risultato
                if save_to_file:
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        f.write(result_text)
                    st.write(f"💾 Contenuto salvato in: {output_filename}")

                st.write(f"⏱️ Tempo di esecuzione: {execution_time:.2f} secondi")

                # Pulisci il container
                generation_container.empty()

            # Mostra il risultato in una scheda dedicata
            tab1, tab2 = st.tabs(["📝 Contenuto Generato", "⚙️ Dettagli"])

            with tab1:
                st.markdown("## Contenuto Generato")
                st.markdown(result_text)

            with tab2:
                st.markdown("## Dettagli di Generazione")
                st.write(f"**Topic:** {topic}")
                st.write(f"**Tipo di contenuto:** {content_types[content_type]}")
                st.write(f"**Reference file:** {reference_file or 'Nessuno'}")
                st.write(f"**Numero di task:** {len(tasks)}")
                st.write(f"**Tempo di esecuzione:** {execution_time:.2f} secondi")

                if save_to_file:
                    st.write(f"**File salvato in:** {output_filename}")

                    # Pulsante per scaricare il file
                    with open(output_filename, "r", encoding="utf-8") as f:
                        content = f.read()

                    st.download_button(
                        label="📥 Scarica file Markdown",
                        data=content,
                        file_name=os.path.basename(output_filename),
                        mime="text/markdown"
                    )

                # Mostra metriche degli agenti
                st.subheader("Metriche di Performance Agenti")
                agent_metrics = agents_factory.get_performance_metrics()

                for agent, calls in agent_metrics["calls_per_agent"].items():
                    avg_time = agent_metrics["avg_execution_time"].get(agent, 0)
                    error_rate = agent_metrics["error_rate"].get(agent, 0)

                    st.write(f"**{agent}:** {calls} chiamate, tempo medio: {avg_time:.2f}s, tasso errori: {error_rate}%")

        except Exception as e:
            st.error(f"Errore durante la generazione: {str(e)}")
            logger.error(f"Error during content generation: {str(e)}", exc_info=True)

# Informazioni aggiuntive
with st.expander("ℹ️ Informazioni sul sistema"):
    st.markdown("""
    ### Content Generator con CrewAI

    Questo sistema utilizza agenti AI specializzati per generare contenuti di alta qualità su qualsiasi topic.

    **Workflow disponibili:**
    - **Articolo Standard**: 800-1000 parole, struttura base con introduzione, 2-3 sezioni e conclusione

    **Agenti specializzati:**
    - Web Searcher: Ricerca informazioni aggiornate
    - Content Architect: Progetta la struttura del contenuto
    - Section Writer: Scrive sezioni specifiche
    - Copywriter: Crea contenuti coinvolgenti
    - Editor: Ottimizza e allinea con il brand
    - Quality Checker: Verifica la qualità del contenuto

    **Per iniziare:**
    1. Inserisci un topic
    2. Seleziona un file di riferimento (opzionale)
    3. Scegli il tipo di contenuto
    4. Clicca su "Genera Contenuto"
    """)

# Inizializzazione sessione e controllo stato
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False