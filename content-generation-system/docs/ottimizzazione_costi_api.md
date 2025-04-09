# Guida all'Ottimizzazione dei Costi API

Questo documento fornisce una panoramica delle strategie implementate per ridurre i costi delle chiamate API nel sistema di generazione contenuti.

## Panoramica delle Soluzioni

Abbiamo implementato diverse strategie per ottimizzare i costi delle chiamate API, con un focus su soluzioni ad alto impatto e facili da implementare:

1. **Sistema di Caching Avanzato**: Memorizza i risultati delle chiamate API per riutilizzarli in richieste simili
2. **Ottimizzazione dei Modelli LLM**: Seleziona automaticamente il modello più economico adatto alla complessità del task
3. **Ottimizzazione dei Workflow**: Riduce il numero di passaggi combinando task compatibili
4. **Ottimizzazione dei Prompt**: Riduce il numero di token utilizzati nelle richieste
5. **Sistema di Quote**: Gestisce i limiti di utilizzo per ogni modello

## Componenti Principali

### 1. Cache Manager (`cache_manager.py`)

Gestisce il caching dei risultati delle chiamate API per evitare chiamate ripetute.

**Caratteristiche principali:**
- Cache su disco e in memoria per prestazioni ottimali
- Gestione della scadenza della cache
- Statistiche di utilizzo e risparmio

**Esempio di utilizzo:**
```python
from src.cache_manager import CacheManager

# Inizializza il cache manager
cache_manager = CacheManager(cache_dir="./cache")

# Utilizza la cache per una chiamata API
result = cache_manager.cached_api_call(
    prefix="search",
    func=search_function,
    params={"query": "strategie di investimento"},
    max_age=86400  # 24 ore
)
```

### 2. LLM Optimizer (`llm_optimizer.py`)

Ottimizza l'utilizzo dei modelli LLM selezionando automaticamente il modello più adatto in base alla complessità del task.

**Caratteristiche principali:**
- Selezione automatica del modello in base alla complessità del task
- Ottimizzazione dei prompt per ridurre i token
- Gestione delle quote di utilizzo
- Monitoraggio dei costi

**Esempio di utilizzo:**
```python
from src.llm_optimizer import LLMOptimizer

# Inizializza l'ottimizzatore
llm_optimizer = LLMOptimizer()

# Imposta limiti di quota
llm_optimizer.set_quota_limit("gpt-4", 50, reset_interval=3600)  # 50 chiamate/ora

# Ottimizza una chiamata LLM
@llm_optimizer.optimize_llm_call
def generate_content(prompt, model="gpt-4"):
    # Implementazione della chiamata API
    pass
```

### 3. Workflow Optimizer (`workflow_optimizer.py`)

Ottimizza i workflow degli agenti combinando passaggi compatibili per ridurre il numero totale di chiamate API.

**Caratteristiche principali:**
- Unione di passaggi compatibili
- Assegnazione ottimale dei modelli per ogni passaggio
- Statistiche di ottimizzazione

**Esempio di utilizzo:**
```python
from src.workflow_optimizer import WorkflowOptimizer

# Inizializza l'ottimizzatore
workflow_optimizer = WorkflowOptimizer(cache_manager, llm_optimizer)

# Ottimizza un workflow
optimized_workflow = workflow_optimizer.optimize_workflow(workflow_config)
```

### 4. API Cost Optimizer (`api_cost_optimizer.py`)

Sistema integrato che combina tutti i componenti di ottimizzazione.

**Caratteristiche principali:**
- Interfaccia unificata per tutte le ottimizzazioni
- Statistiche globali di utilizzo e risparmio
- Gestione centralizzata delle configurazioni

**Esempio di utilizzo:**
```python
from src.api_cost_optimizer import APICostOptimizer

# Inizializza l'ottimizzatore
optimizer = APICostOptimizer(cache_dir="./cache")

# Ottimizza i workflow
optimized_workflows = optimizer.optimize_workflows(workflows_config)

# Ottimizza una chiamata API con caching
result = optimizer.cached_api_call(
    prefix="completion",
    func=completion_function,
    params={"prompt": "Genera un articolo su..."},
    max_age=3600  # 1 ora
)

# Ottimizza una chiamata LLM
@optimizer.optimize_llm_call
def generate_text(prompt, model="gpt-4"):
    # Implementazione della chiamata API
    pass

# Ottieni statistiche
stats = optimizer.get_optimization_stats()
print(f"Risparmio stimato: ${stats['total_saved_cost']:.2f}")
```

## Implementazione nel Sistema Esistente

Per integrare queste ottimizzazioni nel sistema esistente:

1. **Inizializzazione**: Crea un'istanza di `APICostOptimizer` all'avvio dell'applicazione
2. **Ottimizzazione Workflow**: Applica l'ottimizzazione ai workflow prima di creare i task
3. **Decorazione Chiamate LLM**: Utilizza il decoratore `optimize_llm_call` per le funzioni che effettuano chiamate LLM
4. **Caching**: Utilizza `cached_api_call` per le chiamate API ripetitive

Vedi il file `src/optimization_example.py` per un esempio completo di integrazione.

## Benefici Attesi

In base ai test preliminari, ci aspettiamo i seguenti benefici:

- **Riduzione dei Costi**: 30-50% di riduzione dei costi API complessivi
- **Miglioramento delle Prestazioni**: Tempi di risposta più rapidi grazie al caching
- **Maggiore Resilienza**: Gestione intelligente delle quote e fallback automatico a modelli alternativi

## Monitoraggio e Ottimizzazione Continua

Il sistema genera statistiche dettagliate che possono essere utilizzate per monitorare l'efficacia delle ottimizzazioni e identificare ulteriori opportunità di miglioramento.

Per visualizzare le statistiche:

```python
stats = optimizer.get_optimization_stats()
print(stats)

# Salva le statistiche su file
optimizer.save_stats_to_file("stats.json")
```

## Prossimi Passi

1. **Ottimizzazione Batch**: Implementare un sistema per combinare più richieste in un'unica chiamata API
2. **Analisi Semantica**: Migliorare il sistema di caching con analisi semantica per identificare richieste simili
3. **Apprendimento Automatico**: Implementare un sistema di apprendimento per ottimizzare automaticamente la selezione dei modelli in base ai risultati precedenti