# Analisi e Ottimizzazione dei Workflow per TextGenerator

## Indice
1. [Introduzione](#introduzione)
2. [Analisi della Situazione Attuale](#analisi-della-situazione-attuale)
3. [Problematiche Identificate](#problematiche-identificate)
4. [Strategie di Ottimizzazione](#strategie-di-ottimizzazione)
5. [Implementazione Proposta](#implementazione-proposta)
6. [Metriche di Valutazione](#metriche-di-valutazione)

## Introduzione

Questo documento analizza i workflow attualmente implementati nel sistema TextGenerator e propone strategie di ottimizzazione per ridurre i costi delle API e migliorare l'efficienza complessiva del sistema. L'analisi si concentra sui diversi tipi di contenuti supportati (standard, extended_article, whitepaper, social_content) e su come ottimizzare l'uso dei modelli LLM per ciascun tipo di contenuto.

## Analisi della Situazione Attuale

### Workflow Esistenti

Attualmente, il sistema supporta quattro tipi di workflow:

1. **Standard** (articolo di 800-1000 parole)
   - 5 passaggi: research, outline, draft, review, finalize
   - Utilizzo di modelli potenti per tutti i passaggi

2. **Extended Article** (articolo di 1500+ parole)
   - 6 passaggi: research, outline, draft, expert_review, edit, finalize
   - Utilizzo di modelli potenti per tutti i passaggi
   - Generazione di sezioni in parallelo

3. **Whitepaper** (documento di 3000+ parole)
   - 7 passaggi: research, outline, technical_draft, expert_review, edit, design, finalize
   - Utilizzo di modelli potenti per tutti i passaggi
   - Generazione di sezioni in parallelo

4. **Social Content** (contenuti per social media)
   - 5 passaggi: research, brainstorm, draft, optimize, finalize
   - Utilizzo di modelli potenti per tutti i passaggi

### Sistema di Ottimizzazione Attuale

Il sistema attuale include già alcuni componenti di ottimizzazione:

1. **LLMOptimizer**: Seleziona automaticamente il modello più adatto in base alla complessità del task
2. **CacheManager**: Memorizza i risultati delle chiamate API per evitare chiamate ripetute
3. **WorkflowOptimizer**: Ottimizza i workflow unendo passaggi compatibili

## Problematiche Identificate

1. **Utilizzo eccessivo di modelli potenti**: Tutti i passaggi utilizzano modelli di alto livello (GPT-4, Claude-3-Opus) anche quando non necessario
2. **Passaggi ridondanti**: Alcuni passaggi potrebbero essere combinati senza perdita di qualità
3. **Mancanza di differenziazione per complessità**: Non c'è una chiara assegnazione di complessità ai diversi passaggi
4. **Ottimizzazione dei prompt insufficiente**: I prompt potrebbero essere ottimizzati per ridurre il numero di token
5. **Caching non ottimizzato**: Il sistema di caching potrebbe essere migliorato per aumentare il tasso di hit

## Strategie di Ottimizzazione

### 1. Ottimizzazione dei Modelli per Tipo di Task

Proponiamo una mappatura più precisa tra complessità del task e modello utilizzato:

| Tipo di Task | Complessità | Modello Consigliato |
|--------------|-------------|---------------------|
| Research | Alta | GPT-4 / Claude-3-Opus |
| Technical Draft | Alta | GPT-4 / Claude-3-Opus |
| Expert Review | Alta | GPT-4 / Claude-3-Opus |
| Outline | Media | GPT-4-Turbo / Claude-3-Sonnet |
| Draft | Media | GPT-4-Turbo / Claude-3-Sonnet |
| Edit | Media | GPT-4-Turbo / Claude-3-Sonnet |
| Review | Media | GPT-4-Turbo / Claude-3-Sonnet |
| Finalize | Bassa | GPT-3.5-Turbo / Claude-3-Haiku |
| Optimize | Bassa | GPT-3.5-Turbo / Claude-3-Haiku |
| Brainstorm | Bassa | GPT-3.5-Turbo / Claude-3-Haiku |

### 2. Fusione di Passaggi Compatibili

Proponiamo di unire i seguenti passaggi per ridurre il numero di chiamate API:

- **Research + Outline**: Combinare la ricerca con la creazione della struttura
- **Draft + Review**: Combinare la scrittura con la revisione iniziale
- **Edit + Finalize**: Combinare l'editing con la finalizzazione
- **Brainstorm + Draft**: Per contenuti social, combinare l'ideazione con la scrittura

### 3. Ottimizzazione dei Prompt

Proponiamo le seguenti strategie per ottimizzare i prompt:

- **Riduzione delle istruzioni ridondanti**: Eliminare frasi ripetitive e istruzioni ovvie
- **Compressione degli esempi**: Ridurre la lunghezza degli esempi mantenendo l'informazione essenziale
- **Utilizzo di formati strutturati**: Utilizzare JSON o formati strutturati per ridurre la verbosità
- **Istruzioni progressive**: Fornire istruzioni solo quando necessarie, non tutte all'inizio

### 4. Miglioramento del Caching

Proponiamo le seguenti strategie per migliorare il sistema di caching:

- **Caching semantico**: Implementare un sistema di caching che riconosca query semanticamente simili
- **Caching parziale**: Memorizzare risultati parziali che possono essere riutilizzati
- **Precaricamento**: Precaricare risultati comuni per argomenti popolari
- **Gestione intelligente della scadenza**: Scadenza differenziata in base al tipo di contenuto

## Implementazione Proposta

### Modifiche al File di Configurazione

Proponiamo di aggiornare il file `optimization_config.yaml` con le seguenti modifiche:

```yaml
# Mappatura della complessità dei task (aggiornata)
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

# Coppie di passaggi che possono essere uniti (aggiornate)
mergeable_pairs:
  - ["research", "outline"]
  - ["draft", "review"]
  - ["edit", "finalize"]
  - ["brainstorm", "draft"]
  - ["optimize", "finalize"]
```

### Workflow Ottimizzati

Proponiamo i seguenti workflow ottimizzati:

1. **Standard Ottimizzato**
   - 3 passaggi: research_and_outline, draft_and_review, edit_and_finalize
   - Riduzione da 5 a 3 passaggi (40% di riduzione)

2. **Extended Article Ottimizzato**
   - 4 passaggi: research_and_outline, draft, expert_review, edit_and_finalize
   - Riduzione da 6 a 4 passaggi (33% di riduzione)

3. **Whitepaper Ottimizzato**
   - 5 passaggi: research_and_outline, technical_draft, expert_review, edit, design_and_finalize
   - Riduzione da 7 a 5 passaggi (29% di riduzione)

4. **Social Content Ottimizzato**
   - 3 passaggi: research, brainstorm_and_draft, optimize_and_finalize
   - Riduzione da 5 a 3 passaggi (40% di riduzione)

### Ottimizzazione dei Prompt

Proponiamo di migliorare la funzione `optimize_prompt` nel file `llm_optimizer.py` per implementare strategie più avanzate di ottimizzazione dei prompt:

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
```

## Metriche di Valutazione

Per valutare l'efficacia delle ottimizzazioni proposte, suggeriamo di monitorare le seguenti metriche:

1. **Riduzione del numero di chiamate API**: Confronto tra il numero di chiamate prima e dopo l'ottimizzazione
2. **Riduzione dei costi**: Confronto tra i costi stimati prima e dopo l'ottimizzazione
3. **Riduzione del numero di token**: Confronto tra il numero di token utilizzati prima e dopo l'ottimizzazione
4. **Tempo di esecuzione**: Confronto tra i tempi di esecuzione prima e dopo l'ottimizzazione
5. **Qualità del contenuto**: Valutazione della qualità del contenuto generato prima e dopo l'ottimizzazione

Si consiglia di implementare un sistema di monitoraggio continuo per queste metriche e di effettuare aggiustamenti periodici in base ai risultati ottenuti.