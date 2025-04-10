import os
import time
import logging
import requests
import json
from typing import Optional, Dict, Any
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from json.decoder import JSONDecodeError
from crewai.tools import BaseTool
from .config import SERPER_API_KEY

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
        class WebSearchCrewAITool(BaseTool):
            name: str = "web_search"
            description: str = "Search the web for comprehensive information on a topic. Returns a structured summary of findings."
            
            def _run(self, query: str):
                return self.search_func(query)
            
        tool = WebSearchCrewAITool()
        tool.search_func = self.search
        return tool


class MarkdownParserTool:
    """Tool per analizzare un file markdown di riferimento."""
    
    def __init__(self, file_path=None):
        self.file_path = file_path
        if not self.file_path:
            raise ValueError("Il percorso del file markdown di riferimento non è stato specificato")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File markdown non trovato: {self.file_path}")
        
    def get_content(self, section=None):
        """Legge il contenuto del file markdown, opzionalmente filtrando per sezione."""
        try:
            print(f"\nLeggendo file markdown: {self.file_path}")
            print(f"Sezione richiesta: {section if section else 'intero documento'}")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Letto file markdown di {len(content)} caratteri")
            
            if not section:
                return content
            
            # Parsing semplice per trovare sezioni nel markdown
            import re
            
            # Cerca sezioni di livello 2 (##)
            pattern = rf"## {re.escape(section)}(.*?)(?=\n## |\Z)"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                result = f"## {section}{match.group(1)}"
                logger.info(f"Trovata sezione '{section}' di livello 2")
                return result
            
            # Cerca sezioni di livello 3 (###)
            pattern = rf"### {re.escape(section)}(.*?)(?=\n### |\n## |\Z)"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                result = f"### {section}{match.group(1)}"
                logger.info(f"Trovata sezione '{section}' di livello 3")
                return result
            
            logger.warning(f"Sezione '{section}' non trovata nel documento")
            return f"Nota: La sezione '{section}' non è stata trovata nel documento. "  \
                   f"Verifica il nome della sezione o consulta il documento completo."
        
        except FileNotFoundError as e:
            logger.error(f"File non trovato: {str(e)}")
            return f"Errore: Il file markdown non è stato trovato. Verifica il percorso del file."
        except UnicodeDecodeError as e:
            logger.error(f"Errore di decodifica del file: {str(e)}")
            return "Errore: Impossibile leggere il file a causa di problemi di codifica. "  \
                   "Il file potrebbe essere danneggiato o utilizzare una codifica non supportata."
        except Exception as e:
            logger.error(f"Errore imprevisto durante la lettura del file: {str(e)}", exc_info=True)
            return f"Si è verificato un errore durante la lettura del file: {str(e)}. "  \
                   "Per favore, verifica che il file sia accessibile e non sia danneggiato."
    
    def get_tool(self):
        """Restituisce un oggetto BaseTool per l'integrazione con CrewAI."""
        class MarkdownReferenceCrewAITool(BaseTool):
            name: str = "markdown_reference"
            description: str = "Get content from the reference markdown file. Optionally specify a section name to get only that part."
            
            def _run(self, section=None):
                return self.get_content_func(section)
            
        tool = MarkdownReferenceCrewAITool()
        tool.get_content_func = self.get_content
        return tool