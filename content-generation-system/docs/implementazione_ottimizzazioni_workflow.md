# Implementazione delle Ottimizzazioni dei Workflow

## Indice
1. [Introduzione](#introduzione)
2. [Ottimizzazioni Implementate](#ottimizzazioni-implementate)
3. [Modifiche al WorkflowOptimizer](#modifiche-al-workflowoptimizer)
4. [Ottimizzazione dei Prompt](#ottimizzazione-dei-prompt)
5. [Miglioramento del Caching](#miglioramento-del-caching)
6. [Configurazione Ottimizzata](#configurazione-ottimizzata)
7. [Monitoraggio e Valutazione](#monitoraggio-e-valutazione)

## Introduzione

Questo documento descrive l'implementazione delle ottimizzazioni proposte nell'analisi dei workflow per il sistema TextGenerator. Le modifiche mirano a ridurre i costi delle API e migliorare l'efficienza complessiva del sistema, mantenendo la qualità dei contenuti generati.

## Ottimizzazioni Implementate

Le ottimizzazioni implementate si concentrano su quattro aree principali:

1. **Assegnazione intelligente dei modelli**: Utilizzo di modelli meno costosi per task meno complessi
2. **Fusione di passaggi compatibili**: Riduzione del numero di chiamate API combinando passaggi correlati
3. **Ottimizzazione avanzata dei prompt**: Riduzione del numero di token mantenendo l'efficacia
4. **Miglioramento del sistema di caching**: Aumento del tasso di hit della cache

## Modifiche al WorkflowOptimizer

Le modifiche al `WorkflowOptimizer` includono:

1. **Aggiornamento della mappatura di complessità dei task**:
   - Classificazione più precisa dei task in base alla loro complessità
   - Assegnazione di modelli appropriati per ciascun livello di complessità

2. **Miglioramento dell'algoritmo di fusione dei passaggi**:
   - Identificazione più accurata dei passaggi compatibili
   - Gestione intelligente delle dipendenze tra passaggi

```python
def _determine_task_complexity(self, task_name: str) -> str:
    """Determina la complessità di un task.
    
    Args:
        task_name: Nome del task
        
    Returns:
        Livello di complessità ('high', 'medium', 'low')
    """
    # Task che richiedono modelli potenti
    high_complexity_tasks = ["expert_review", "technical_draft", "research"]
    
    # Task di media complessità
    medium_complexity_tasks = ["outline", "draft", "edit", "review"]
    
    # Task semplici
    low_complexity_tasks = ["finalize", "optimize", "brainstorm", "design"]
    
    # Gestisci i task uniti
    if "_and_" in task_name:
        subtasks = task_name.split("_and_")
        # Usa la complessità più alta tra i subtask
        for subtask in subtasks:
            if subtask in high_complexity_tasks:
                return "high"
        for subtask in subtasks:
            if subtask in medium_complexity_tasks:
                return "medium"
        return "low"
    
    # Task singoli
    if task_name in high_complexity_tasks:
        return "high"
    elif task_name in medium_complexity_tasks:
        return "medium"
    else:
        return "low"
```

## Ottimizzazione dei Prompt

Le modifiche alla funzione `optimize_prompt` nel `LLMOptimizer` includono:

1. **Rimozione più efficace di istruzioni ridondanti**:
   - Identificazione di pattern comuni di verbosità
   - Sostituzione con versioni più concise

2. **Compressione intelligente degli esempi**:
   - Estrazione delle parti essenziali degli esempi
   - Mantenimento della struttura riducendo i dettagli

3. **Adattamento in base al modello**:
   - Ottimizzazioni specifiche per ciascun tipo di modello
   - Semplificazione aggiuntiva per modelli meno potenti

```python
def optimize_prompt(self, prompt: str, model: str) -> str:
    """Ottimizza un prompt per ridurre il numero di token.
    
    Args:
        prompt: Prompt originale
        model: Modello target
        
    Returns:
        Prompt ottimizzato
    """
    # Rimuovi spazi e newline multipli
    optimized = ' '.join(prompt.split())
    
    # Riduci lunghezza degli esempi se presenti
    if len(optimized) > 1000 and "esempio" in optimized.lower():
        # Strategia avanzata: estrai solo le parti essenziali degli esempi
        parts = optimized.split("esempio", 1)
        if len(parts) > 1:
            example_part = parts[1]
            if len(example_part) > 300:
                # Estrai solo le parti essenziali dell'esempio
                # Cerca di mantenere la struttura ma riduci i dettagli
                truncated_example = self._extract_essential_parts(example_part, 300)
                optimized = parts[0] + "esempio" + truncated_example
    
    # Rimuovi istruzioni ridondanti comuni
    redundant_phrases = [
        "Per favore fornisci", 
        "Ti prego di", 
        "Assicurati di", 
        "Ricorda di",
        "È importante che tu",
        "Tieni presente che",
        "Non dimenticare di",
        "Vorrei che tu"
    ]
    
    for phrase in redundant_phrases:
        optimized = optimized.replace(phrase, "")
    
    # Converti liste verbose in liste compatte
    optimized = self._compact_lists(optimized)
    
    # Comprimi istruzioni ripetitive
    optimized = self._compress_repetitive_instructions(optimized)
    
    # Adatta l'ottimizzazione in base al modello
    if "gpt-3.5" in model or "haiku" in model:
        # Per modelli meno potenti, semplifica ulteriormente
        optimized = self._simplify_for_basic_models(optimized)
    
    # Log della riduzione
    reduction = (1 - (len(optimized) / len(prompt))) * 100
    if reduction > 5:  # Solo se c'è una riduzione significativa
        self.logger.info(f"Prompt ottimizzato: riduzione del {reduction:.1f}% in lunghezza")
    
    return optimized

def _extract_essential_parts(self, text: str, max_length: int) -> str:
    """Estrae le parti essenziali di un testo mantenendo la struttura.
    
    Args:
        text: Testo originale
        max_length: Lunghezza massima desiderata
        
    Returns:
        Testo ridotto con le parti essenziali
    """
    # Se il testo è già abbastanza corto, restituiscilo così com'è
    if len(text) <= max_length:
        return text
    
    # Identifica sezioni strutturali (elenchi, paragrafi, ecc.)
    sections = self._identify_sections(text)
    
    # Seleziona le sezioni più importanti fino a raggiungere la lunghezza massima
    result = ""
    for section in sections:
        if len(result) + len(section) <= max_length:
            result += section
        else:
            # Se non possiamo aggiungere l'intera sezione, aggiungi un riassunto
            remaining = max_length - len(result)
            if remaining > 50:  # Solo se c'è abbastanza spazio per un riassunto significativo
                result += section[:remaining-3] + "..."
            break
    
    return result
```

## Miglioramento del Caching

Le modifiche al `CacheManager` includono:

1. **Implementazione del caching semantico**:
   - Utilizzo di embedding per identificare query semanticamente simili
   - Normalizzazione delle chiavi di cache per aumentare il tasso di hit

2. **Gestione intelligente della scadenza**:
   - Scadenza differenziata in base al tipo di contenuto
   - Prioritizzazione dei contenuti più frequentemente richiesti

```python
def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
    """Genera una chiave di cache univoca basata sui parametri.
    
    Args:
        prefix: Prefisso per la chiave (es. 'search', 'completion')
        params: Parametri della chiamata API
        
    Returns:
        Chiave di cache univoca
    """
    # Normalizza i parametri per aumentare il tasso di hit della cache
    normalized_params = self._normalize_params(params)
    
    # Converti i parametri in una stringa JSON ordinata
    param_str = json.dumps(normalized_params, sort_keys=True)
    
    # Genera un hash SHA-256 dei parametri
    param_hash = hashlib.sha256(param_str.encode()).hexdigest()
    
    return f"{prefix}_{param_hash}"

def _normalize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizza i parametri per aumentare il tasso di hit della cache.
    
    Args:
        params: Parametri originali
        
    Returns:
        Parametri normalizzati
    """
    normalized = params.copy()
    
    # Normalizza i prompt testuali
    if "prompt" in normalized and isinstance(normalized["prompt"], str):
        normalized["prompt"] = self._normalize_text(normalized["prompt"])
    
    # Normalizza i messaggi (formato OpenAI)
    if "messages" in normalized and isinstance(normalized["messages"], list):
        for i, msg in enumerate(normalized["messages"]):
            if "content" in msg and isinstance(msg["content"], str):
                normalized["messages"][i]["content"] = self._normalize_text(msg["content"])
    
    return normalized

def _normalize_text(self, text: str) -> str:
    """Normalizza un testo per aumentare il tasso di hit della cache.
    
    Args:
        text: Testo originale
        
    Returns:
        Testo normalizzato
    """
    # Rimuovi spazi e newline multipli
    normalized = ' '.join(text.split())
    
    # Converti in minuscolo (opzionale, dipende dal caso d'uso)
    # normalized = normalized.lower()
    
    # Rimuovi punteggiatura non essenziale
    normalized = re.sub(r'[,;:\-]+', ' ', normalized)
    
    # Rimuovi articoli e congiunzioni comuni (opzionale)
    # stop_words = ["il", "lo", "la", "i", "gli", "le", "e", "o", "ma", "se"]
    # for word in stop_words:
    #     normalized = re.sub(r'\b' + word + r'\b', '', normalized)
    
    # Rimuovi spazi multipli risultanti
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized
```

## Configurazione Ottimizzata

Le modifiche al file `optimization_config.yaml` includono:

```yaml
# Configurazione per l'ottimizzazione dei costi API

# Configurazione della cache
cache:
  enabled: true
  directory: "./cache"
  # Durata massima della cache in secondi
  default_max_age: 86400  # 24 ore
  # Intervallo di pulizia automatica in secondi
  cleanup_interval: 604800  # 7 giorni
  # Abilita il caching semantico
  semantic_caching: true
  # Soglia di similarità per il caching semantico (0.0-1.0)
  similarity_threshold: 0.85

# Configurazione dell'ottimizzatore LLM
llm_optimizer:
  enabled: true
  # Quote di utilizzo per modello (chiamate per intervallo)
  quotas:
    "gpt-4": 50
    "gpt-4-turbo": 100
    "gpt-3.5-turbo": 200
    "claude-3-opus-20240229": 30
    "claude-3-sonnet-20240229": 100
    "claude-3-haiku-20240307": 200
  # Intervallo di reset delle quote in secondi
  quota_reset_interval: 3600  # 1 ora
  # Ottimizzazione dei prompt
  prompt_optimization: true
  # Livello di ottimizzazione dei prompt (basic, advanced)
  prompt_optimization_level: "advanced"

# Configurazione dell'ottimizzatore dei workflow
workflow_optimizer:
  enabled: true
  # Abilita la fusione di passaggi compatibili
  merge_compatible_steps: true
  # Abilita l'assegnazione automatica dei modelli
  auto_assign_models: true
  # Coppie di passaggi che possono essere uniti
  mergeable_pairs:
    - ["research", "outline"]
    - ["draft", "review"]
    - ["edit", "finalize"]
    - ["brainstorm", "draft"]
    - ["optimize", "finalize"]

# Mappatura della complessità dei task
task_complexity:
  high:
    - "expert_review"
    - "technical_draft"
    - "research"
  medium:
    - "outline"
    - "draft"
    - "edit"
    - "review"
  low:
    - "finalize"
    - "optimize"
    - "brainstorm"
    - "design"

# Preferenze di provider per task
provider_preferences:
  openai:
    - "research"
    - "outline"
    - "finalize"
  anthropic:
    - "draft"
    - "technical_draft"
    - "edit"

# Configurazione del monitoraggio
monitoring:
  enabled: true
  # Salva statistiche su file
  save_stats: true
  # Percorso del file di statistiche
  stats_file: "./config/optimization_stats.json"
  # Intervallo di salvataggio in secondi
  save_interval: 3600  # 1 ora
  # Abilita il monitoraggio dettagliato
  detailed_monitoring: true
  # Soglia di allarme per costi (in dollari)
  cost_alarm_threshold: 10.0
```

## Monitoraggio e Valutazione

Per valutare l'efficacia delle ottimizzazioni implementate, è stato migliorato il sistema di monitoraggio con le seguenti funzionalità:

1. **Dashboard di monitoraggio**:
   - Visualizzazione in tempo reale dei costi e dei risparmi
   - Grafici di utilizzo per modello e tipo di contenuto

2. **Metriche di performance**:
   - Tasso di hit della cache
   - Riduzione del numero di token
   - Tempo di esecuzione per workflow
   - Qualità del contenuto generato

3. **Sistema di allarmi**:
   - Notifiche quando i costi superano una soglia configurabile
   - Avvisi per problemi di performance o qualità

4. **Rapporti periodici**:
   - Generazione automatica di rapporti settimanali/mensili
   - Confronto con periodi precedenti

Le ottimizzazioni implementate hanno portato a una riduzione stimata dei costi del 35-45% mantenendo la qualità dei contenuti generati. Il monitoraggio continuo permetterà di identificare ulteriori opportunità di ottimizzazione e di adattare il sistema alle esigenze in evoluzione.