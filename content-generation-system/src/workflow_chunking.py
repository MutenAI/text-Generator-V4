"""Modulo per la gestione del chunking nei workflow per ottimizzare l'uso dei token."""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from .token_manager import TokenManager

class WorkflowChunking:
    """Gestisce il chunking dei contenuti nei workflow per ottimizzare l'uso dei token."""
    
    def __init__(self, token_manager: TokenManager, logger: Optional[logging.Logger] = None):
        """Inizializza il gestore di chunking.
        
        Args:
            token_manager: Gestore dei token
            logger: Logger opzionale
        """
        self.token_manager = token_manager
        self.logger = logger or logging.getLogger(__name__)
    
    def chunk_workflow_content(self, content: str, model: str, max_chunk_size: Optional[int] = None) -> List[str]:
        """Divide un contenuto in chunk per un workflow.
        
        Args:
            content: Contenuto da dividere
            model: Modello LLM da utilizzare
            max_chunk_size: Dimensione massima di ciascun chunk in token (opzionale)
            
        Returns:
            Lista di chunk di contenuto
        """
        if not content:
            return []
            
        # Determina la dimensione massima del chunk
        if max_chunk_size is None:
            model_limit = self.token_manager.get_model_token_limit(model)
            # Usa il 70% del limite del modello per lasciare spazio per il contesto e la risposta
            max_chunk_size = int(model_limit * 0.7)
        
        # Conta i token nel contenuto originale
        content_tokens = self.token_manager.count_tokens(content, model)
        
        # Se il contenuto è già abbastanza corto, restituiscilo direttamente
        if content_tokens <= max_chunk_size:
            return [content]
            
        # Altrimenti, dividi in chunk
        self.logger.info(f"Dividendo contenuto di {content_tokens} token in chunk di max {max_chunk_size} token")
        return self.token_manager.chunk_text(content, max_chunk_size, overlap=100, model=model)
    
    def process_chunked_workflow(self, chunks: List[str], process_func: callable, **kwargs) -> str:
        """Elabora un workflow in chunk e combina i risultati.
        
        Args:
            chunks: Lista di chunk di contenuto
            process_func: Funzione che elabora un singolo chunk
            **kwargs: Argomenti aggiuntivi da passare alla funzione di elaborazione
            
        Returns:
            Risultato combinato dell'elaborazione
        """
        if not chunks:
            return ""
            
        # Se c'è un solo chunk, elaboralo direttamente
        if len(chunks) == 1:
            return process_func(chunks[0], **kwargs)
            
        # Altrimenti, elabora ogni chunk e combina i risultati
        self.logger.info(f"Elaborazione di {len(chunks)} chunk separati")
        
        results = []
        for i, chunk in enumerate(chunks):
            self.logger.info(f"Elaborazione chunk {i+1}/{len(chunks)}")
            chunk_result = process_func(chunk, is_chunk=True, chunk_index=i, total_chunks=len(chunks), **kwargs)
            results.append(chunk_result)
            
        # Combina i risultati
        return self._combine_chunk_results(results)
    
    def _combine_chunk_results(self, results: List[str]) -> str:
        """Combina i risultati dell'elaborazione dei chunk.
        
        Args:
            results: Lista di risultati dei chunk
            
        Returns:
            Risultato combinato
        """
        if not results:
            return ""
            
        # Semplice concatenazione con separatori
        combined = "\n\n".join(results)
        
        return combined
    
    def optimize_agent_messages(self, messages: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
        """Ottimizza i messaggi tra agenti per rispettare i limiti di token.
        
        Args:
            messages: Lista di messaggi
            model: Modello LLM
            
        Returns:
            Lista di messaggi ottimizzata
        """
        if not messages:
            return []
            
        # Conta i token nei messaggi
        total_tokens = self.token_manager.count_tokens(messages, model)
        model_limit = self.token_manager.get_model_token_limit(model)
        
        # Se siamo già sotto il limite, restituisci i messaggi originali
        if total_tokens <= model_limit * 0.8:  # 80% del limite
            return messages
            
        self.logger.warning(f"Messaggi tra agenti troppo lunghi: {total_tokens} token (limite: {model_limit})")
        
        # Strategia: sostituisci i messaggi lunghi con riassunti
        optimized_messages = []
        for msg in messages:
            if "content" in msg and isinstance(msg["content"], str):
                content = msg["content"]
                content_tokens = self.token_manager.count_tokens(content, model)
                
                # Se il contenuto è lungo, sostituiscilo con un riassunto
                if content_tokens > 1000:  # Soglia arbitraria
                    # Estrai le informazioni chiave
                    # Strategia semplice: mantieni l'inizio e la fine
                    start = self.token_manager.truncate_text(content, 300, model)
                    end = content[-500:] if len(content) > 500 else ""
                    
                    # Crea un riassunto
                    summary = f"{start}\n\n[...contenuto intermedio omesso per ottimizzazione token...]\n\n{end}"
                    
                    # Sostituisci il contenuto con il riassunto
                    new_msg = msg.copy()
                    new_msg["content"] = summary
                    optimized_messages.append(new_msg)
                    
                    # Log della riduzione
                    new_tokens = self.token_manager.count_tokens(summary, model)
                    reduction = (1 - (new_tokens / content_tokens)) * 100
                    self.logger.info(f"Messaggio ridotto da {content_tokens} a {new_tokens} token ({reduction:.1f}% riduzione)")
                else:
                    # Mantieni il messaggio originale
                    optimized_messages.append(msg)
            else:
                # Mantieni il messaggio originale
                optimized_messages.append(msg)
        
        # Verifica finale
        final_tokens = self.token_manager.count_tokens(optimized_messages, model)
        if final_tokens > model_limit * 0.8:
            self.logger.warning(f"Messaggi ancora troppo lunghi dopo ottimizzazione: {final_tokens} token")
            # Riduci ulteriormente mantenendo solo i messaggi essenziali
            return self._reduce_to_essential_messages(optimized_messages, model)
        
        return optimized_messages
    
    def _reduce_to_essential_messages(self, messages: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
        """Riduce i messaggi ai soli essenziali per rispettare i limiti di token.
        
        Args:
            messages: Lista di messaggi
            model: Modello LLM
            
        Returns:
            Lista ridotta di messaggi essenziali
        """
        if not messages:
            return []
            
        model_limit = self.token_manager.get_model_token_limit(model)
        max_tokens = int(model_limit * 0.8)  # 80% del limite
        
        # Mantieni solo il primo e l'ultimo messaggio
        if len(messages) > 2:
            essential = [messages[0], messages[-1]]
            essential_tokens = self.token_manager.count_tokens(essential, model)
            
            if essential_tokens <= max_tokens:
                self.logger.info(f"Riduzione a messaggi essenziali: da {len(messages)} a 2 messaggi")
                return essential
        
        # Se ancora troppo lungo, tronca il contenuto dell'ultimo messaggio
        if len(messages) > 0:
            last_msg = messages[-1].copy()
            if "content" in last_msg and isinstance(last_msg["content"], str):
                # Determina quanti token possiamo usare
                available_tokens = max_tokens
                if len(messages) > 1:
                    first_msg_tokens = self.token_manager.count_tokens([messages[0]], model)
                    available_tokens -= first_msg_tokens
                
                # Tronca il contenuto dell'ultimo messaggio
                last_msg["content"] = self.token_manager.truncate_text(last_msg["content"], available_tokens, model)
                
                if len(messages) > 1:
                    return [messages[0], last_msg]
                else:
                    return [last_msg]
        
        # Fallback: restituisci un messaggio vuoto
        self.logger.warning("Impossibile ridurre i messaggi entro il limite di token")
        return [{"role": "user", "content": "Contenuto troppo lungo, impossibile elaborare la richiesta."}]