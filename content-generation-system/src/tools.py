import os
import time
import logging
import requests
import json
from typing import Optional, Dict, Any
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from json.decoder import JSONDecodeError
from langchain.tools import Tool
from .config import SERPER_API_KEY
import re
from .utils import handle_markdown_error

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSearchTool:
    """Tool per la ricerca web via Serper.dev."""

    def __init__(self, api_key=None):
        self.api_key = api_key or SERPER_API_KEY
        if not self.api_key:
            raise ValueError("SERPER_API_KEY non configurata nelle variabili d'ambiente o non fornita come parametro")

    def _make_request(self, query: str, max_retries: int = 2, retry_delay: int = 1) -> Optional[Dict[str, Any]]:
        """Esegue la richiesta HTTP con gestione retry."""
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': 5
        }

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Tentativo {attempt + 1}/{max_retries + 1} di ricerca per: '{query}'")
                response = requests.post(
                    'https://google.serper.dev/search',
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                return response.json()

            except Timeout:
                logger.warning(f"Timeout durante la richiesta (tentativo {attempt + 1})")
            except ConnectionError as e:
                logger.warning(f"Errore di connessione (tentativo {attempt + 1}): {str(e)}")
            except HTTPError as e:
                if response.status_code == 429:  # Rate limit
                    logger.warning("Rate limit raggiunto. Attendere prima di riprovare.")
                    return None
                elif response.status_code in [502, 503, 504]:  # Errori server temporanei
                    logger.warning(f"Errore server temporaneo: {response.status_code}")
                else:
                    logger.error(f"Errore HTTP {response.status_code}: {str(e)}")
                    return None
            except JSONDecodeError as e:
                logger.error(f"Errore nel parsing JSON: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Errore imprevisto: {str(e)}")
                return None

            if attempt < max_retries:
                time.sleep(retry_delay)

        return None

    def search(self, query: str) -> str:
        """Esegue una ricerca web e restituisce un riassunto strutturato."""
        try:
            logger.info(f"Avvio ricerca web per: '{query}'")
            results = self._make_request(query)

            if not results:
                return "Non è stato possibile completare la ricerca. Si prega di riprovare più tardi."

            logger.info(f"Elaborazione risultati della ricerca per: '{query}'")

            # Formatta i risultati in un riassunto strutturato
            summary = f"## Research Summary: {query}\n\n"

            if 'organic' in results and results['organic']:
                summary += "### Key Information:\n\n"

                for item in results['organic'][:5]:
                    title = item.get('title', 'No Title')
                    snippet = item.get('snippet', 'No description')
                    link = item.get('link', '#')

                    summary += f"**{title}**\n"
                    summary += f"{snippet}\n"
                    summary += f"Source: {link}\n\n"
                    logger.debug(f"Aggiunto risultato: {title}")
            else:
                logger.warning("Nessun risultato organico trovato nella ricerca")
                summary += "### Warning: No organic search results found.\n\n"

            if 'knowledgeGraph' in results:
                kg = results['knowledgeGraph']
                if 'description' in kg:
                    summary += f"### Overview:\n{kg['description']}\n\n"
                    logger.debug("Aggiunta descrizione da Knowledge Graph")

            summary += "### Summary of Findings:\n"

            if 'organic' in results and results['organic']:
                summary += "Based on the search results, here are the key insights on this topic:\n\n"

                insights = []
                for i, item in enumerate(results['organic'][:3]):
                    insight = f"{i+1}. {item.get('title', 'Key insight')}: {item.get('snippet', 'Important information from the search')}"
                    insights.append(insight)

                summary += "\n".join(insights)
                logger.debug(f"Generati {len(insights)} insights dai risultati")
            else:
                logger.warning("Generazione insights fallita - nessun risultato disponibile")
                summary += "Non sono stati trovati risultati significativi per questa ricerca.\n"
                summary += "1. [Ricerca non ha prodotto risultati rilevanti]\n"
                summary += "2. [Potrebbe essere necessario riformulare la query]\n"
                summary += "3. [Prova una ricerca più specifica]\n"

            logger.info("Ricerca completata con successo")
            return summary

        except Exception as e:
            logger.error(f"Errore imprevisto durante la ricerca: {str(e)}", exc_info=True)
            return f"Si è verificato un errore durante la ricerca: {str(e)}. Per favore, riprova più tardi."

    def get_tool(self):
        """Restituisce un oggetto BaseTool per l'integrazione con CrewAI."""
        from crewai.tools import BaseTool

        search_function = self.search

        class WebSearchCrewAITool(BaseTool):
            name: str = "web_search"
            description: str = "Search the web for comprehensive information on a topic. Returns a structured summary of findings."

            def _run(self, query: str) -> str:
                return search_function(query)

        return WebSearchCrewAITool()


class MarkdownParserTool:
    """Tool per analizzare un file markdown di riferimento."""

    def __init__(self, file_path=None):
        self.file_path = file_path
        if not self.file_path:
            logger.warning("Il percorso del file markdown di riferimento non è stato specificato")
            self.file_exists = False
            return
        if not os.path.exists(self.file_path):
            logger.warning(f"File markdown non trovato: {self.file_path}")
            self.file_exists = False
            return
        self.file_exists = True

    def get_content(self, section=None):
        """Legge il contenuto del file markdown, opzionalmente filtrando per sezione."""
        try:
            if not hasattr(self, 'file_exists') or not self.file_exists:
                logger.warning("File markdown non disponibile o non trovato")
                return handle_markdown_error("File markdown non disponibile", section or "ALL")

            print(f"\nLeggendo file markdown: {self.file_path}")
            print(f"Sezione richiesta: {section if section else 'intero documento'}")

            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"Letto file markdown di {len(content)} caratteri")

            if not section:
                return content

            # Parsing semplice per trovare sezioni nel markdown
            import re

            # Se richiesta è "brand guidelines", cerchiamo anche "Brand Voice" come fallback
            section_alternatives = [section]
            if section.lower() == "brand guidelines":
                section_alternatives.extend(["Brand Voice", "brand voice", "Style Guide"])

            # Cerca con corrispondenza esatta e poi con ricerca parziale
            for current_section in section_alternatives:
                # Cerca sezioni di livello 2 (##) con corrispondenza esatta
                pattern = rf"## {re.escape(current_section)}(.*?)(?=\n## |\Z)"
                match = re.search(pattern, content, re.DOTALL)

                if match:
                    result = f"## {current_section}{match.group(1)}"
                    logger.info(f"Trovata sezione '{current_section}' di livello 2")
                    return result

                # Cerca sezioni di livello 3 (###) con corrispondenza esatta
                pattern = rf"### {re.escape(current_section)}(.*?)(?=\n### |\n## |\Z)"
                match = re.search(pattern, content, re.DOTALL)

                if match:
                    result = f"### {current_section}{match.group(1)}"
                    logger.info(f"Trovata sezione '{current_section}' di livello 3")
                    return result

            # Ricerca parziale - cerca sezioni che contengano il termine
            search_term = section.lower()
            all_sections = re.findall(r"(#+)\s+(.+)$", content, re.MULTILINE)

            for heading_marks, heading_text in all_sections:
                if search_term in heading_text.lower():
                    # Ha trovato un titolo che contiene il termine cercato
                    logger.info(f"Trovata sezione simile: '{heading_text}'")

                    # Estrai il contenuto di questa sezione
                    pattern = rf"{re.escape(heading_marks)} {re.escape(heading_text)}(.*?)(?=\n{re.escape(heading_marks[0])} |\Z)"
                    section_match = re.search(pattern, content, re.DOTALL)

                    if section_match:
                        return f"{heading_marks} {heading_text}{section_match.group(1)}"

            # Se non trova nulla, restituisci l'intero documento come fallback
            logger.warning(f"Sezione '{section}' non trovata nel documento, restituisco l'intero documento")
            return f"Nota: La sezione '{section}' non è stata trovata nel documento. Di seguito l'intero documento:\n\n{content}"

        except FileNotFoundError as e:
            logger.error(f"File non trovato: {str(e)}")
            return handle_markdown_error(str(e), section)
        except UnicodeDecodeError as e:
            logger.error(f"Errore di decodifica del file: {str(e)}")
            return handle_markdown_error("Problemi di codifica del file", section)
        except Exception as e:
            logger.error(f"Errore imprevisto durante la lettura del file: {str(e)}", exc_info=True)
            return handle_markdown_error(str(e), section)

    def get_tool(self):
        """Restituisce un oggetto BaseTool per l'integrazione con CrewAI."""
        from crewai.tools import BaseTool

        get_content_function = self.get_content

        class MarkdownReferenceCrewAITool(BaseTool):
            name: str = "markdown_reference"
            description: str = "Get content from the reference markdown file. Optionally specify a section name to get only that part."

            def _run(self, section: str = None) -> str:
                return get_content_function(section)

        return MarkdownReferenceCrewAITool()

from .utils import handle_markdown_error

class MarkdownReferenceTool:
    """Tool per l'estrazione di contenuti da file markdown di riferimento."""

    def __init__(self, reference_file_path=None, logger=None):
        """
        Inizializza lo strumento con il percorso del file di riferimento.

        Args:
            reference_file_path: Percorso al file markdown di riferimento
            logger: Logger per tracciare operazioni
        """
        self.reference_file_path = reference_file_path
        self.logger = logger or logging.getLogger(__name__)
        self.content = None
        self.loaded_successfully = False

        # Carica il contenuto del file di riferimento se specificato
        if reference_file_path:
            self.loaded_successfully = self.load_reference_file(reference_file_path)

    def load_reference_file(self, file_path):
        """
        Carica il contenuto del file di riferimento.

        Args:
            file_path: Percorso al file markdown

        Returns:
            bool: True se il file è stato caricato con successo, False altrimenti
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.content = file.read()
            self.reference_file_path = file_path
            self.logger.info(f"File di riferimento caricato: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Errore nel caricamento del file di riferimento: {str(e)}")
            self.content = None
            return False

    def get_content(self, section=None):
        """
        Ottiene il contenuto completo o di una sezione specifica.

        Args:
            section: Nome della sezione da estrarre (opzionale)

        Returns:
            Il contenuto estratto o un messaggio di errore strutturato
        """
        if not self.content:
            error_message = "Nessun file di riferimento caricato."
            self.logger.warning(error_message)
            return handle_markdown_error(error_message, section or "ALL")

        if not section:
            self.logger.info("Restituendo l'intero contenuto del file di riferimento")
            return self.content

        # Pattern per trovare le sezioni nel markdown (## Titolo)
        section_pattern = r'(?<=^|\n)##\s+(.+?)(?=\n##|\Z)'
        sections = re.finditer(section_pattern, self.content, re.DOTALL)

        found_sections = []
        for s in sections:
            section_title = s.group(1).strip()
            section_content = s.group(0)
            found_sections.append(section_title)

            # Se la sezione corrisponde a quella richiesta (ignorando case)
            if section.lower() in section_title.lower():
                self.logger.info(f"Sezione trovata: {section_title}")
                return section_content

        # Se si richiede "ALL", restituisce tutte le sezioni
        if section.upper() == "ALL":
            self.logger.info("Restituendo tutte le sezioni del file")
            return self.content

        error_message = f"Sezione '{section}' non trovata nel file di riferimento."
        self.logger.warning(error_message)
        self.logger.info(f"Sezioni disponibili: {', '.join(found_sections)}")
        return handle_markdown_error(error_message, section)

    def get_tool(self):
        """Restituisce un oggetto BaseTool per l'integrazione con CrewAI."""
        from crewai.tools import BaseTool

        get_content_function = self.get_content

        class MarkdownReferenceCrewAITool(BaseTool):
            name: str = "markdown_reference"
            description: str = "Get content from the reference markdown file. Optionally specify a section name to get only that part."

            def _run(self, section: str = None) -> str:
                return get_content_function(section)

        return MarkdownReferenceCrewAITool()

from .utils import handle_markdown_error

class MarkdownParserTool(Tool):
    """
    Strumento che consente di analizzare file markdown e estrarre sezioni.
    """

    def __init__(self, reference_file=None, logger=None):
        """
        Inizializza lo strumento di parsing markdown.

        Args:
            reference_file: Percorso al file markdown di riferimento
            logger: Logger opzionale
        """
        super().__init__(
            name="markdown_reference",
            description="Accede a una sezione specifica del file markdown di riferimento. "+
                       "Fornisci il nome della sezione (ad es. 'Brand Voice') per estrarre il contenuto corrispondente. "+
                       "Se la sezione non è trovata, verranno tentate sezioni alternative come fallback.",
            func=self._extract_markdown_section,
            logger=logger
        )
        self.reference_file = reference_file

        # Importa eventuali utilità aggiuntive
        try:
            from .utils import handle_markdown_reference
            self.handle_markdown_reference = handle_markdown_reference
        except ImportError:
            self.handle_markdown_reference = None

    def _extract_markdown_section(self, params):
        """
        Estrae una sezione specifica da un file markdown con gestione avanzata degli errori.

        Args:
            params: Dizionario con 'section' come chiave per specificare la sezione da estrarre

        Returns:
            Il contenuto della sezione specificata
        """
        section_name = params.get('section')

        # Se è disponibile l'helper avanzato di gestione markdown e il parametro section
        # non è specificato, usa l'helper per una gestione più robusta
        if not section_name and self.handle_markdown_reference:
            try:
                # Tenta di leggere l'intero file come fallback
                with open(self.reference_file, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if self.logger:
                        self.logger.info(f"Letto intero file markdown di {len(content)} caratteri")
                    print(f"Leggendo file markdown completo: {self.reference_file}")
                    return content
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Errore nella lettura completa del file: {str(e)}")
                raise ValueError(f"Errore nella lettura completa del file: {str(e)}")

        # Se è richiesta una sezione specifica
        if not section_name:
            raise ValueError("È necessario specificare una sezione da estrarre")

        if not self.reference_file:
            if self.logger:
                self.logger.error("File di riferimento non specificato")
            raise ValueError("File di riferimento non specificato")

        try:
            with open(self.reference_file, 'r', encoding='utf-8') as file:
                content = file.read()
                if self.logger:
                    self.logger.info(f"Letto file markdown di {len(content)} caratteri")

                # Cerca sezioni di livello 1 e 2 (# e ##)
                section_patterns = [
                    # Sezione di livello 1
                    r'# ' + re.escape(section_name) + r'\s*\n(.*?)(?:\n# |\Z)',
                    # Sezione di livello 2
                    r'## ' + re.escape(section_name) + r'\s*\n(.*?)(?:\n## |\n# |\Z)'
                ]

                for pattern in section_patterns:
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        section_content = match.group(1).strip()
                        if self.logger:
                            self.logger.info(f"Trovata sezione '{section_name}' di livello {section_patterns.index(pattern) + 1}")

                        # Stampa a riga di comando per debug
                        print(f"Leggendo file markdown: {self.reference_file}")
                        print(f"Sezione richiesta: {section_name}")

                        return section_content

                # Se non troviamo la sezione con il pattern specifico, 
                # cerchiamo in modo più flessibile
                headers = re.findall(r'(#+)\s+(.*?)\s*\n', content)
                for header_level, header_text in headers:
                    if section_name.lower() in header_text.lower():
                        # Trovato un'intestazione che contiene il nome della sezione
                        header_pattern = re.escape(header_level) + r'\s+' + re.escape(header_text) + r'\s*\n(.*?)(?:\n' + re.escape(header_level[0]) + r'{1,' + str(len(header_level)) + r'}\s+|\Z)'
                        match = re.search(header_pattern, content, re.DOTALL)
                        if match:
                            section_content = match.group(1).strip()
                            if self.logger:
                                self.logger.info(f"Trovata sezione simile a '{section_name}': '{header_text}'")
                            return section_content

                # Se ancora non troviamo nulla, tentiamo un approccio più flessibile cercando contenuti rilevanti
                # Questo è utile quando le sezioni non hanno esattamente il nome richiesto
                section_keywords = section_name.lower().split()
                potential_sections = []

                for header_level, header_text in headers:
                    header_keywords = header_text.lower().split()
                    # Calcola quante parole chiave corrispondono
                    matches = sum(1 for keyword in section_keywords if keyword in header_keywords)
                    if matches > 0:
                        relevance = matches / len(section_keywords)
                        # Se la rilevanza è sufficiente, aggiungi alla lista dei potenziali
                        if relevance >= 0.5:  # Almeno metà delle parole chiave devono corrispondere
                            header_pattern = re.escape(header_level) + r'\s+' + re.escape(header_text) + r'\s*\n(.*?)(?:\n' + re.escape(header_level[0]) + r'{1,' + str(len(header_level)) + r'}\s+|\Z)'
                            match = re.search(header_pattern, content, re.DOTALL)
                            if match:
                                section_content = match.group(1).strip()
                                potential_sections.append((relevance, header_text, section_content))

                # Se abbiamo trovato sezioni potenzialmente rilevanti, restituisci la più rilevante
                if potential_sections:
                    # Ordina per rilevanza (decrescente)
                    potential_sections.sort(reverse=True)
                    best_match = potential_sections[0]
                    if self.logger:
                        self.logger.info(f"Utilizzata sezione alternativa '{best_match[1]}' con rilevanza {best_match[0]:.2f}")
                    return best_match[2]

                # Se ancora non troviamo nulla, restituiamo un errore
                if self.logger:
                    self.logger.warning(f"Sezione '{section_name}' non trovata nel file markdown")
                raise ValueError(f"Sezione '{section_name}' non trovata nel file markdown")

        except FileNotFoundError:
            if self.logger:
                self.logger.error(f"File di riferimento non trovato: {self.reference_file}")
            raise ValueError(f"File di riferimento non trovato: {self.reference_file}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Errore nell'analisi del file markdown: {str(e)}")
            raise ValueError(f"Errore nell'analisi del file markdown: {str(e)}")