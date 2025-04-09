# Content Generation System con CrewAI

**PROPRIETÀ DI FYLLE SRL**  
**SVILUPPATO PER SIEBERT FINANCIAL CORP**

Questo sistema è stato sviluppato per la generazione automatica di contenuti finanziari utilizzando un'architettura Multi-Agent. Il sistema utilizza CrewAI con agenti specializzati per generare contenuti allineati allo stile di un brand, ottimizzando al contempo i costi delle API e l'utilizzo dei token.

## Caratteristiche Principali

- **Sistema Multi-Agent**: Utilizza agenti specializzati per ricerca, scrittura e revisione
- **Ottimizzazione dei costi API**: Riduce automaticamente le chiamate API e i costi associati
- **Supporto per multiple LLM**: OpenAI, Anthropic Claude e DeepSeek
- **Modalità economica**: Opzione per utilizzare DeepSeek come provider principale a costi ridotti
- **Caching intelligente**: Memorizza risultati per evitare chiamate API ripetitive
- **Gestione dei token**: Ottimizza l'utilizzo dei token per rispettare i limiti dei modelli
- **Interfaccia Streamlit**: Facile da utilizzare tramite UI web
- **Workflow configurabili**: Personalizza il processo di generazione dei contenuti

## Architettura del Sistema

```
content-generation-system/
├── .env                       # API keys (OpenAI, Anthropic, DeepSeek, Serper)
├── main.py                    # Script principale da riga di comando
├── content_generator_app.py   # Interfaccia Streamlit
├── requirements.txt           # Dipendenze
├── config/                    # Directory per file di configurazione
│   ├── workflows.yaml         # Configurazione dei workflow
│   └── optimization_config.yaml # Configurazione ottimizzazione costi
├── reference/                 # Directory per file markdown di riferimento
├── output/                    # Directory per contenuti generati
└── src/
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

## Prerequisiti

- Python 3.8+
- Account OpenAI con API key
- Account Anthropic con API key 
- Account DeepSeek con API key (opzionale, per modalità economica)
- Account Serper.dev con API key (per ricerche web)

## Installazione

1. Clona questo repository

2. Naviga nella directory del progetto:
   ```bash
   cd content-generation-system
   ```

3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura il file `.env` con le tue API key:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   DEEPSEEK_API_KEY=your-deepseek-api-key
   SERPER_API_KEY=your-serper-api-key
   ```

## Utilizzo

### Interfaccia Web (Consigliata)

Per avviare l'interfaccia Streamlit:

```bash
streamlit run content_generator_app.py
```

**IMPORTANTE**: Assicurati di eseguire il comando dalla directory principale `content-generation-system` e non da una sottodirectory, per evitare problemi di percorso.

L'interfaccia web sarà accessibile all'indirizzo: http://localhost:8501

### Da Riga di Comando

Per generare contenuti da riga di comando:

```bash
python main.py --topic "Strategie di investimento per millennials" --reference "reference/siebert-system-brief-optimized.md"
```

Parametri:
- `--topic`: L'argomento su cui generare il contenuto
- `--type`: Tipo di contenuto (article, extended_article, whitepaper)
- `--reference`: Il percorso del file markdown di riferimento per lo stile del contenuto
- `--output`: Directory dove salvare l'output (default: "output")

## Ottimizzazione dei Costi API

Il sistema include un modulo completo di ottimizzazione dei costi API che:

1. **Riduce le chiamate API** attraverso:
   - Caching intelligente dei risultati
   - Fusione di passaggi compatibili nei workflow
   - Selezione automatica del modello più economico adatto al task

2. **Ottimizza l'utilizzo dei token** tramite:
   - Chunking automatico dei contenuti lunghi
   - Troncatura intelligente dei messaggi
   - Gestione efficiente del contesto

3. **Supporta provider economici** come DeepSeek:
   - Modalità economica che utilizza DeepSeek come provider principale
   - Fallback automatico a provider più potenti quando necessario

Le configurazioni di ottimizzazione possono essere personalizzate nel file `config/optimization_config.yaml`.

## Workflow Disponibili

Il sistema supporta diversi workflow predefiniti:

- **standard**: Workflow base per articoli generici
- **extended_article**: Per articoli più approfonditi e dettagliati
- **whitepaper**: Per contenuti tecnici di alta qualità
- **social_content**: Per la creazione di contenuti per social media

I workflow sono configurabili nel file `config/workflows.yaml`.

## Personalizzazione

### Aggiungere Nuovi File di Riferimento

Puoi aggiungere qualsiasi file markdown nella directory `reference/` e specificarlo come parametro quando esegui lo script o selezionarlo nell'interfaccia web.

### Modificare gli Agenti

Gli agenti possono essere personalizzati modificando il file `src/agents.py`. Puoi:
- Cambiare i modelli LLM utilizzati
- Modificare i role, goal e backstory
- Aggiungere ulteriori strumenti

### Configurare l'Ottimizzazione

Puoi personalizzare le strategie di ottimizzazione modificando il file `config/optimization_config.yaml`:
- Impostare quote di utilizzo per modello
- Configurare la cache
- Definire coppie di passaggi che possono essere uniti
- Specificare preferenze di provider per diversi tipi di task

## Risoluzione Problemi

### Problemi di Path

Se riscontri errori relativi ai percorsi dei file:

1. Assicurati di eseguire i comandi dalla directory principale `content-generation-system`
2. Verifica che i percorsi nei parametri siano corretti (usa percorsi relativi alla directory principale)
3. Controlla che le directory `reference/` e `output/` esistano

### Errori API

Se riscontri errori relativi alle API:

1. Verifica che le API key nel file `.env` siano corrette e attive
2. Controlla i limiti di utilizzo delle API (quota)
3. Verifica la connessione internet

## Note

- Il sistema è progettato per funzionare con API key valide
- Le ricerche web utilizzano l'API di Serper.dev che ha un limite di utilizzo gratuito
- I contenuti generati sono salvati con un timestamp per evitare sovrascritture
- L'utilizzo della modalità economica con DeepSeek può ridurre i costi ma potrebbe influire sulla qualità dei contenuti per task complessi