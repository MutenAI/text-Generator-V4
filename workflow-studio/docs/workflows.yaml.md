
# File di Configurazione Workflow (workflows.yaml)

```yaml
# Workflow configurations for content generation

workflows:
  standard:
    steps:
      - task: research_and_outline
        description: "Ricerca informazioni e creazione della struttura del contenuto"
      - task: draft_and_edit
        description: "Scrittura e ottimizzazione del contenuto"
      - task: review_and_finalize
        description: "Revisione finale e formattazione del contenuto"

  extended_article:
    steps:
      - task: research
        description: "Ricerca approfondita e analisi delle fonti"
      - task: outline
        description: "Strutturazione dettagliata dei contenuti"
      - task: draft
        description: "Scrittura del contenuto esteso"
      - task: expert_review
        description: "Revisione tecnica e verifica accuratezza"
      - task: edit
        description: "Editing e ottimizzazione del testo"
      - task: finalize
        description: "Finalizzazione e formattazione professionale"

  whitepaper:
    steps:
      - task: research
        description: "Ricerca approfondita e raccolta dati"
      - task: outline
        description: "Strutturazione dettagliata del whitepaper"
      - task: technical_draft
        description: "Scrittura contenuto tecnico"
      - task: expert_review
        description: "Revisione tecnica approfondita"
      - task: edit
        description: "Editing professionale"
      - task: design
        description: "Formattazione e design professionale"
      - task: finalize
        description: "Finalizzazione e controllo qualità"

  social_content:
    steps:
      - task: research
        description: "Analisi trend e target audience"
      - task: brainstorm
        description: "Ideazione contenuti social"
      - task: draft
        description: "Creazione copy e contenuti"
      - task: optimize
        description: "Ottimizzazione per piattaforme social"
      - task: finalize
        description: "Finalizzazione e scheduling"
```

## Spiegazione Dettagliata

Questo file YAML definisce quattro tipi principali di workflow per la generazione di contenuti:

### 1. Workflow Standard

Ottimizzato per articoli di media lunghezza (800-1000 parole), questo workflow riduce i passaggi necessari combinando task complementari:

- **research_and_outline**: Unisce la ricerca delle informazioni e la strutturazione del contenuto in un unico passaggio
- **draft_and_edit**: Combina la scrittura del contenuto e l'editing iniziale
- **review_and_finalize**: Riunisce la revisione finale e la formattazione del contenuto

Questo workflow è stato appositamente ottimizzato per ridurre il numero di passaggi da 5-6 a soli 3, mantenendo alta la qualità del contenuto.

### 2. Workflow Extended Article

Progettato per articoli più lunghi (1500+ parole), questo workflow mantiene passaggi separati per garantire maggiore profondità e qualità:

- **research**: Ricerca approfondita con raccolta di informazioni dettagliate
- **outline**: Sviluppo di una struttura complessa e dettagliata
- **draft**: Scrittura del contenuto principale
- **expert_review**: Revisione da parte di un esperto per garantire precisione tecnica
- **edit**: Editing professionale per migliorare stile e leggibilità
- **finalize**: Finalizzazione e formattazione professionale

### 3. Workflow Whitepaper

Specializzato per documenti tecnici approfonditi (3000+ parole), include passaggi supplementari:

- Aggiunge **technical_draft** per contenuti altamente specializzati
- Include **design** per la formattazione professionale del documento

### 4. Workflow Social Content

Ottimizzato per la creazione di contenuti social media:

- **research**: Analisi dei trend e del pubblico target
- **brainstorm**: Fase creativa per generare idee originali
- **draft**: Scrittura dei contenuti specifici per social
- **optimize**: Ottimizzazione per le diverse piattaforme social
- **finalize**: Finalizzazione e pianificazione della pubblicazione

## Come Modificare questo File

Per modificare i workflow esistenti o crearne di nuovi:

1. Mantenere la struttura YAML esistente
2. Per ogni workflow, definire:
   - Un nome univoco (es. `custom_workflow`)
   - Una lista di `steps` con `task` e `description` per ogni passaggio

### Esempio di Nuovo Workflow

```yaml
podcast_script:
  steps:
    - task: research
      description: "Ricerca approfondita sull'argomento del podcast"
    - task: outline
      description: "Strutturazione della narrazione e dei punti chiave"
    - task: draft_script
      description: "Scrittura dello script del podcast"
    - task: edit_for_audio
      description: "Ottimizzazione dello script per la narrazione audio"
    - task: finalize
      description: "Finalizzazione dello script con note di produzione"
```
