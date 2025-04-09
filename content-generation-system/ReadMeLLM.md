# ReadMeLLM - Content Generation System

Questo documento è strutturato specificamente per assistere un LLM di codice a comprendere, lanciare e migliorare il sistema di generazione di contenuti. Contiene informazioni tecniche dettagliate sull'architettura, i componenti, i flussi di lavoro e le istruzioni per l'esecuzione.

## Struttura del Progetto

```
content-generation-system/
├── .env                       # API keys (OpenAI, Anthropic, DeepSeek, Serper)
├── main.py                    # Script principale da riga di comando
├── content_generator_app.py   # Interfaccia Streamlit
├── requirements.txt           # Dipendenze Python
├── config/                    # Directory per file di configurazione
│   ├── workflows.yaml         # Configurazione dei workflow
│   └── optimization_config.yaml # Configurazione ottimizzazione costi
├── reference/                 # Directory per file markdown di riferimento
├── output/                    # Directory per contenuti generati
└── src/                       # Codice sorgente
    ├── __init__.py
    ├── agents.py              # Definizione degli agenti
    ├── api_cost_optimizer.py  # Sistema di ottimizzazione costi API
    ├── cache_manager.py       # Gestione della cache
    ├── config.py              # Configurazioni di base
    ├── config_manager.py      # Gestione configurazioni
    ├── llm_optimizer.py       # Ottimizzazione modelli LLM
    ├── quality.py             # Controllo qualità contenuti
    ├── tasks.py               # Definizione sequenza task
    ├── token_manager.py       # Gestione dei token
    ├── tools.py               # Web search e markdown parser
    ├── utils.py               # Funzioni di utilità
    ├── workflow_chunking.py   # Gestione chunking contenuti
    └── workflow_optimizer.py  # Ottimizzazione workflow
```

## Componenti Principali

### 1. Sistema Multi-Agent (CrewAI)

Il sistema utilizza CrewAI per orchestrare agenti specializzati:

- **WebSearcher**: Esegue ricerche web e raccoglie informazioni
- **ContentArchitect**: Crea la struttura del contenuto
- **Copywriter**: Genera il contenuto principale
- **Editor**: Ottimizza e allinea il contenuto allo stile desiderato
- **QualityReviewer**: Verifica la qualità del contenuto finale

Implementazione in `src/agents.py`.

### 2. Sistema di Ottimizzazione Costi API

Componenti per l'ottimizzazione dei costi:

- **APICostOptimizer** (`src/api_cost_optimizer.py`): Sistema integrato di ottimizzazione
- **CacheManager** (`src/cache_manager.py`): Gestisce la cache delle chiamate API
- **LLMOptimizer** (`src/llm_optimizer.py`): Ottimizza l'uso dei modelli LLM
- **TokenManager** (`src/token_manager.py`): Gestisce il conteggio e l'ottimizzazione dei token
- **WorkflowOptimizer** (`src/workflow_optimizer.py`): Ottimizza i workflow per ridurre le chiamate API
- **WorkflowChunking** (`src/workflow_chunking.py`): Gestisce il chunking dei contenuti lunghi

### 3. Gestione Workflow

Il sistema supporta workflow configurabili definiti in `config/workflows.yaml`:

- **WorkflowManager** (`src/tasks.py`): Crea e gestisce i task in base al workflow selezionato

### 4. Interfaccia Utente

- **Streamlit App** (`content_generator_app.py`): Interfaccia web per l'interazione con il sistema
- **CLI** (`main.py`): Interfaccia a riga di comando

## Flussi di Dati e Dipendenze

1. **Inizializzazione**:
   - Caricamento configurazioni da `config/`
   - Inizializzazione componenti di ottimizzazione
   - Creazione agenti e strumenti

2. **Generazione Contenuti**:
   - Selezione workflow e topic
   - Esecuzione sequenziale o ottimizzata dei task
   - Ottimizzazione automatica delle chiamate API
   - Salvataggio output nella directory `output/`

3. **Ottimizzazione Costi**:
   - Caching risultati per riutilizzo
   - Fusione di passaggi compatibili nei workflow
   - Selezione automatica del modello più economico per ogni task
   - Chunking contenuti lunghi per rispettare limiti di token

## Istruzioni per l'Esecuzione

### Prerequisiti

```python
# Verifica che Python 3.8+ sia installato
import sys
assert sys.version_info >= (3, 8), "Richiesto Python 3.8 o superiore"

# Verifica che le dipendenze siano installate
import pkg_resources
required_packages = [
    'python-dotenv', 'crewai', 'langchain', 'langchain_openai',
    'langchain_anthropic', 'requests', 'streamlit', 'pydantic',
    'pyyaml', 'diskcache', 'funcy'
]
for package in required_packages:
    try:
        pkg_resources.get_distribution(package)
    except pkg_resources.DistributionNotFound:
        print(f"Pacchetto {package} non trovato. Installalo con 'pip install -r requirements.txt'")
        sys.exit(1)
```

### Verifica Configurazione

```python
# Verifica che il file .env esista e contenga le API key necessarie
import os
from dotenv import load_dotenv

load_dotenv()
required_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'SERPER_API_KEY']
for key in required_keys:
    if not os.getenv(key):
        print(f"API key {key} non trovata nel file .env")

# Verifica che le directory necessarie esistano
required_dirs = ['reference', 'output', 'config']
for dir_name in required_dirs:
    if not os.path.isdir(dir_name):
        print(f"Directory {dir_name} non trovata. Creazione...")
        os.makedirs(dir_name)
```

### Avvio dell'Applicazione Streamlit

```python
# Assicurati di essere nella directory principale del progetto
import os
if not os.path.exists('content_generator_app.py'):
    print("Errore: Assicurati di essere nella directory principale 'content-generation-system'")
    sys.exit(1)

# Avvia l'applicazione Streamlit
import subprocess
process = subprocess.Popen(['streamlit', 'run', 'content_generator_app.py'])

# L'applicazione sarà accessibile all'indirizzo http://localhost:8501
print("Applicazione avviata all'indirizzo http://localhost:8501")
```

### Esecuzione da Riga di Comando

```python
# Esempio di esecuzione da script Python
import subprocess

# Genera contenuto su un argomento specifico
topic = "Strategie di investimento per millennials"
reference_file = "reference/siebert-system-brief-optimized.md"

command = [
    'python', 'main.py',
    '--topic', topic,
    '--reference', reference_file
]

result = subprocess.run(command, capture_output=True, text=True)
print(result.stdout)
```

## Risoluzione Problemi Comuni

### Problemi di Path

```python
# Funzione per diagnosticare problemi di path
def diagnose_path_issues():
    import os
    
    # Verifica directory corrente
    current_dir = os.getcwd()
    print(f"Directory corrente: {current_dir}")
    
    # Verifica esistenza file principali
    main_files = ['main.py', 'content_generator_app.py', 'requirements.txt']
    for file in main_files:
        print(f"File {file} esiste: {os.path.exists(file)}")
    
    # Verifica struttura directory
    dirs = ['src', 'config', 'reference', 'output']
    for dir_name in dirs:
        print(f"Directory {dir_name} esiste: {os.path.isdir(dir_name)}")
        if os.path.isdir(dir_name):
            print(f"Contenuto di {dir_name}/: {os.listdir(dir_name)}")
```

### Problemi con le API

```python
# Funzione per testare le connessioni API
def test_api_connections():
    import os
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Test OpenAI API
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        try:
            headers = {"Authorization": f"Bearer {openai_key}"}
            response = requests.get("https://api.openai.com/v1/models", headers=headers)
            print(f"OpenAI API: {response.status_code}")
        except Exception as e:
            print(f"Errore OpenAI API: {e}")
    
    # Test Anthropic API
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if anthropic_key:
        try:
            headers = {"x-api-key": anthropic_key}
            response = requests.get("https://api.anthropic.com/v1/models", headers=headers)
            print(f"Anthropic API: {response.status_code}")
        except Exception as e:
            print(f"Errore Anthropic API: {e}")
```

## Estensione e Miglioramento

### Aggiungere un Nuovo Modello LLM

```python
# Passi per aggiungere supporto per un nuovo modello LLM

# 1. Aggiorna src/config.py per includere il nuovo modello
def update_config_with_new_model(model_provider, model_name):
    # Esempio di codice da aggiungere a config.py
    new_config = f"""
    # Aggiungi il nuovo provider e modello
    '{model_provider}': {{
        'default': '{model_name}',
    }},
    """
    print(f"Aggiungi questo al dizionario LLM_MODELS in src/config.py:\n{new_config}")

# 2. Aggiorna src/llm_optimizer.py per includere i costi del nuovo modello
def update_llm_optimizer_with_new_model(model_name, cost_per_1k_tokens):
    # Esempio di codice da aggiungere a llm_optimizer.py
    new_cost_entry = f"""
    # Aggiungi il costo del nuovo modello
    "{model_name}": {cost_per_1k_tokens},  # Costo stimato per 1000 token
    """
    print(f"Aggiungi questo al dizionario MODEL_COSTS in src/llm_optimizer.py:\n{new_cost_entry}")

# 3. Aggiorna src/token_manager.py per includere i limiti di token del nuovo modello
def update_token_manager_with_new_model(model_name, token_limit):
    # Esempio di codice da aggiungere a token_manager.py
    new_limit_entry = f"""
    # Aggiungi il limite di token del nuovo modello
    "{model_name}": {token_limit},
    """
    print(f"Aggiungi questo al dizionario MODEL_TOKEN_LIMITS in src/token_manager.py:\n{new_limit_entry}")
```

### Aggiungere un Nuovo Workflow

```python
# Esempio di come aggiungere un nuovo workflow in config/workflows.yaml
new_workflow = """
  newsletter:
    steps:
      - task: research
        description: "Ricerca e analisi del tema della newsletter"
      - task: outline
        description: "Strutturazione delle sezioni della newsletter"
      - task: draft
        description: "Scrittura del contenuto principale"
      - task: optimize
        description: "Ottimizzazione per formato email"
      - task: finalize
        description: "Finalizzazione e formattazione per invio"
"""

print(f"Aggiungi questo a config/workflows.yaml sotto la chiave 'workflows':\n{new_workflow}")
```

### Ottimizzazione delle Prestazioni

```python
# Suggerimenti per ottimizzare le prestazioni del sistema

# 1. Aumenta il caching per ridurre le chiamate API
def optimize_caching():
    # Modifica da apportare a config/optimization_config.yaml
    cache_config = """
cache:
  enabled: true
  directory: "./cache"
  # Aumenta la durata della cache per risultati più stabili
  default_max_age: 604800  # 7 giorni
  # Riduce la frequenza di pulizia
  cleanup_interval: 2592000  # 30 giorni
"""
    print(f"Aggiorna la configurazione della cache in config/optimization_config.yaml:\n{cache_config}")

# 2. Ottimizza la selezione dei modelli per bilanciare costi e qualità
def optimize_model_selection():
    # Modifica da apportare a src/llm_optimizer.py
    model_tier_config = """
    # Modelli in ordine di capacità (dal più potente al meno potente)
    MODEL_TIERS = [
        ["gpt-4", "claude-3-opus-20240229"],  # Tier 1 (più potente)
        ["gpt-4-turbo", "claude-3-sonnet-20240229", "deepseek-coder"],  # Tier 2
        ["gpt-3.5-turbo", "claude-3-haiku-20240307", "deepseek-chat"]  # Tier 3 (meno potente)
    ]
"""
    print(f"Aggiorna la configurazione dei tier di modelli in src/llm_optimizer.py:\n{model_tier_config}")
```

## Debugging e Logging

```python
# Configurazione avanzata del logging per il debugging
def setup_advanced_logging():
    logging_config = """
import logging
import os
from datetime import datetime

# Crea directory per i log se non esiste
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Crea un nome file con timestamp
log_filename = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configurazione del logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

# Ottieni il logger principale
logger = logging.getLogger("content_generator")

# Imposta livelli di logging specifici per moduli
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.INFO)
"""
    print(f"Aggiungi questo codice all'inizio di main.py e content_generator_app.py:\n{logging_config}")
```

Questo documento è progettato per fornire tutte le informazioni necessarie a un LLM di codice per comprendere, eseguire e migliorare il sistema di generazione di contenuti.