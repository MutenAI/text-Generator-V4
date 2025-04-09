# Ottimizzazione Avanzata dei Costi API

Questo documento descrive le ottimizzazioni avanzate implementate per ridurre significativamente i costi delle API nel sistema TextGenerator.

## Problematica

Il sistema originale utilizzava un approccio che generava costi eccessivi (circa 10€ per workflow standard) a causa di:

1. Utilizzo di modelli potenti (GPT-4, Claude-3-Opus) per tutti i passaggi del workflow
2. Caching insufficiente per contenuti simili
3. Workflow con troppi passaggi separati
4. Mancanza di controlli di budget

## Soluzioni Implementate

### 1. Selezione Intelligente dei Modelli

Abbiamo modificato `llm_optimizer.py` per implementare una strategia più aggressiva di selezione dei modelli:

- **Mappatura diretta task-modello**: Ogni task è ora associato direttamente a un tier di modello specifico
- **Downgrade della complessità**: Alcuni task sono stati spostati a tier inferiori (es. "research" da alta a media complessità)
- **Modelli economici per fasi iniziali**: Utilizziamo GPT-3.5-Turbo per outline e ricerca iniziale
- **Modelli potenti solo per revisione finale**: GPT-4 viene utilizzato solo per revisione esperta e contenuti tecnici

```python
# Mappatura diretta dei task ai tier di modelli (0=Tier1, 1=Tier2, 2=Tier3)
TASK_MODEL_MAPPING = {
    # Solo i task più critici usano Tier 1
    "expert_review": 0,
    "technical_draft": 0,
    
    # La maggior parte dei task usa Tier 2
    "research": 1,
    "draft": 1,
    "edit": 1,
    "review": 1,
    
    # Task semplici usano Tier 3
    "outline": 2,
    "finalize": 2,
    "optimize": 2,
    "brainstorm": 2
}
```

### 2. Caching Semantico Avanzato

Abbiamo potenziato il sistema di cache in `cache_manager.py` per ridurre drasticamente le chiamate API:

- **Normalizzazione dei prompt**: Rimuove spazi, punteggiatura e converte in minuscolo per aumentare le hit della cache
- **Ricerca fuzzy**: Trova risultati simili nella cache anche quando i prompt non sono identici
- **Similarità semantica**: Implementa un algoritmo che identifica prompt con significato simile (70% di parole in comune)
- **Cache in memoria**: Mantiene i risultati recenti in memoria per accesso più veloce

### 3. Ottimizzazione Aggressiva dei Workflow

Abbiamo migliorato `workflow_optimizer.py` per combinare più passaggi compatibili:

- **Più coppie unibili**: Aggiunte nuove combinazioni di passaggi compatibili
- **Unione automatica di task semplici**: I task di bassa complessità vengono uniti automaticamente
- **Riduzione dei passaggi**: Il workflow standard può ora essere completato in 2-3 passaggi invece di 5

### 4. Sistema di Controllo del Budget

Abbiamo implementato in `api_cost_optimizer.py` un sistema di controllo del budget:

- **Budget giornaliero**: Limite massimo di spesa giornaliera configurabile
- **Fallback automatico**: Passa automaticamente a modelli più economici quando si avvicina al limite
- **Monitoraggio in tempo reale**: Avvisi quando il budget è al 75%, 90% e 100%
- **Reset automatico**: Il budget si resetta automaticamente ogni giorno

## Risultati Attesi

Con queste ottimizzazioni, ci aspettiamo:

- **Riduzione dei costi del 70-80%**: Da 10€ a 2-3€ per workflow standard
- **Aumento delle hit di cache del 40-50%**: Grazie al matching semantico
- **Riduzione del 50% delle chiamate API**: Grazie all'unione dei passaggi del workflow
- **Controllo predittivo dei costi**: Prevenzione di spese eccessive grazie al sistema di budget

## Configurazione Consigliata

```yaml
# Configurazione ottimizzata
llm_optimizer:
  enabled: true
  quotas:
    "gpt-4": 20  # Ridotto da 50
    "gpt-4-turbo": 50  # Ridotto da 100
    "gpt-3.5-turbo": 300  # Aumentato da 200
    "claude-3-opus-20240229": 15  # Ridotto da 30
    "claude-3-sonnet-20240229": 50  # Ridotto da 100
    "claude-3-haiku-20240307": 300  # Aumentato da 200

api_cost_optimizer:
  daily_budget: 10.0  # Budget giornaliero in euro

cache_manager:
  enabled: true
  semantic_matching: true
  similarity_threshold: 0.7
```

## Monitoraggio e Ottimizzazione Continua

Per garantire che le ottimizzazioni funzionino come previsto:

1. Monitora il file di log per avvisi relativi al budget
2. Controlla le statistiche di ottimizzazione dopo ogni esecuzione
3. Regola le soglie di similarità semantica in base alle esigenze
4. Adatta il budget giornaliero in base all'utilizzo effettivo

## Conclusione

Queste ottimizzazioni avanzate dovrebbero ridurre significativamente i costi delle API mantenendo la qualità dei contenuti generati. Il sistema è ora più intelligente nell'allocazione delle risorse, utilizzando modelli potenti solo dove necessario e sfruttando al massimo la cache per contenuti simili.