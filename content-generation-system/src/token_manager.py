\"""Gestore dei token per ottimizzare l'uso dei modelli LLM."""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union
import tiktoken

class TokenManager:
    """Gestisce il conteggio e l'ottimizzazione dei token per i modelli LLM."""
    
    # Limiti di token per modello
    MODEL_TOKEN_LIMITS = {
        # OpenAI
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 16384,
        # Anthropic
        "claude-3-opus-20240229": 200000,
        "claude-3-sonnet-20240229": 200000,
        "claude-3-haiku-20240307": 200000,
        # DeepSeek
        "deepseek-chat": 8192,  # Limite confermato dall'errore
        "deepseek-coder": 8192   # Stesso limite per coerenza
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Inizializza il gestore dei token.
        
        Args:
            logger: Logger opzionale per il logging
        """
        self.logger = logger or logging.getLogger(__name__)
        # Inizializza gli encoder per i diversi modelli
        self.encoders = {}
        try:
            # Carica gli encoder per i modelli OpenAI
            self.encoders["gpt-4"] = tiktoken.encoding_for_model("gpt-4")
            self.encoders["gpt-3.5-turbo"] = tiktoken.encoding_for_model("gpt-3.5-turbo")
            # Per altri modelli, usiamo l'encoder cl100k_base come fallback
            self.encoders["default"] = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            self.logger.warning(f"Errore nell'inizializzazione degli encoder tiktoken: {e}")
            self.logger.info("Utilizzo della stima basata su parole come fallback")
    
    def count_tokens(self, text: Union[str, List[Dict[str, str]]], model: str = "default") -> int:
        """Conta i token in un testo o in una lista di messaggi.
        
        Args:
            text: Testo o lista di messaggi da analizzare
            model: Nome del modello per cui contare i token
            
        Returns:
            Numero di token
        """
        if not text:
            return 0
            
        # Gestisci il caso in cui text è una lista di messaggi (formato OpenAI/DeepSeek)
        if isinstance(text, list):
            total_tokens = 0
            for message in text:
                if "content" in message and isinstance(message["content"], str):
                    total_tokens += self.count_tokens(message["content"], model)
                # Aggiungi token per i metadati del messaggio (ruolo, ecc.)
                total_tokens += 4  # Stima approssimativa per i metadati
            return total_tokens
        
        # Gestisci il caso in cui text è una stringa
        if not isinstance(text, str):
            self.logger.warning(f"Tipo non supportato per il conteggio dei token: {type(text)}")
            return 0
            
        # Usa tiktoken se disponibile per il modello
        encoder_key = model if model in self.encoders else "default"
        if encoder_key in self.encoders and self.encoders[encoder_key]:
            try:
                return len(self.encoders[encoder_key].encode(text))
            except Exception as e:
                self.logger.warning(f"Errore nel conteggio dei token con tiktoken: {e}")
        
        # Fallback: stima basata su parole (approssimativa)
        words = text.split()
        return int(len(words) * 1.3)  # Fattore di conversione approssimativo
    
    def truncate_text(self, text: str, max_tokens: int, model: str = "default") -> str:
        """Tronca un testo per rispettare un limite di token.
        
        Args:
            text: Testo da troncare
            max_tokens: Numero massimo di token
            model: Nome del modello
            
        Returns:
            Testo troncato
        """
        if not text:
            return ""
            
        current_tokens = self.count_tokens(text, model)
        if current_tokens <= max_tokens:
            return text
            
        # Usa tiktoken se disponibile
        encoder_key = model if model in self.encoders else "default"
        if encoder_key in self.encoders and self.encoders[encoder_key]:
            try:
                encoded = self.encoders[encoder_key].encode(text)
                truncated = encoded[:max_tokens]
                return self.encoders[encoder_key].decode(truncated)
            except Exception as e:
                self.logger.warning(f"Errore nella troncatura con tiktoken: {e}")
        
        # Fallback: troncatura basata su parole
        words = text.split()
        estimated_tokens_per_word = current_tokens / len(words)
        estimated_words = int(max_tokens / estimated_tokens_per_word)
        return " ".join(words[:estimated_words])
    
    def chunk_text(self, text: str, chunk_size: int, overlap: int = 100, model: str = "default") -> List[str]:
        """Divide un testo in chunk di dimensione specificata con sovrapposizione.
        
        Args:
            text: Testo da dividere
            chunk_size: Dimensione massima di ciascun chunk in token
            overlap: Sovrapposizione tra chunk in token
            model: Nome del modello
            
        Returns:
            Lista di chunk di testo
        """
        if not text:
            return []
            
        # Se il testo è già abbastanza corto, restituiscilo direttamente
        if self.count_tokens(text, model) <= chunk_size:
            return [text]
            
        chunks = []
        # Usa tiktoken se disponibile
        encoder_key = model if model in self.encoders else "default"
        if encoder_key in self.encoders and self.encoders[encoder_key]:
            try:
                encoded = self.encoders[encoder_key].encode(text)
                
                # Dividi in chunk con sovrapposizione
                i = 0
                while i < len(encoded):
                    chunk_end = min(i + chunk_size, len(encoded))
                    chunk = encoded[i:chunk_end]
                    chunks.append(self.encoders[encoder_key].decode(chunk))
                    i += chunk_size - overlap
                    
                return chunks
            except Exception as e:
                self.logger.warning(f"Errore nel chunking con tiktoken: {e}")
        
        # Fallback: chunking basato su paragrafi
        paragraphs = re.split(r'\n\s*\n', text)
        current_chunk = ""
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para, model)
            
            # Se il paragrafo è troppo grande, dividilo ulteriormente
            if para_tokens > chunk_size:
                if current_chunk:  # Aggiungi il chunk corrente se non è vuoto
                    chunks.append(current_chunk)
                    current_chunk = ""
                    current_tokens = 0
                
                # Dividi il paragrafo in frasi
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence_tokens = self.count_tokens(sentence, model)
                    if current_tokens + sentence_tokens <= chunk_size:
                        if current_chunk:
                            current_chunk += " "
                        current_chunk += sentence
                        current_tokens += sentence_tokens
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                        current_tokens = sentence_tokens
            else:
                # Aggiungi il paragrafo al chunk corrente o inizia un nuovo chunk
                if current_tokens + para_tokens <= chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n"
                    current_chunk += para
                    current_tokens += para_tokens
                else:
                    chunks.append(current_chunk)
                    current_chunk = para
                    current_tokens = para_tokens
        
        # Aggiungi l'ultimo chunk se non è vuoto
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
    
    def optimize_messages(self, messages: List[Dict[str, str]], model: str, max_tokens: Optional[int] = None) -> List[Dict[str, str]]:
        """Ottimizza una lista di messaggi per rispettare il limite di token.
        
        Args:
            messages: Lista di messaggi nel formato OpenAI/DeepSeek
            model: Nome del modello
            max_tokens: Limite massimo di token (se None, usa il limite del modello)
            
        Returns:
            Lista di messaggi ottimizzata
        """
        if not messages:
            return []
            
        # Determina il limite di token
        if max_tokens is None:
            max_tokens = self.MODEL_TOKEN_LIMITS.get(model, 4096)
        
        # Riserva token per la risposta (circa 20% del limite)
        response_tokens = int(max_tokens * 0.2)
        available_tokens = max_tokens - response_tokens
        
        # Conta i token attuali
        current_tokens = self.count_tokens(messages, model)
        
        # Se siamo già sotto il limite, restituisci i messaggi originali
        if current_tokens <= available_tokens:
            return messages
            
        # Strategia di ottimizzazione:
        # 1. Mantieni sempre il messaggio di sistema (se presente)
        # 2. Mantieni sempre l'ultimo messaggio utente
        # 3. Riduci o rimuovi i messaggi intermedi
        
        # Estrai il messaggio di sistema e l'ultimo messaggio utente
        system_message = None
        user_messages = []
        assistant_messages = []
        
        for msg in messages:
            role = msg.get("role", "")
            if role == "system":
                system_message = msg
            elif role == "user":
                user_messages.append(msg)
            elif role == "assistant":
                assistant_messages.append(msg)
        
        # Assicurati di avere almeno un messaggio utente
        if not user_messages:
            self.logger.warning("Nessun messaggio utente trovato")
            return messages[:1] if messages else []
        
        # Inizia con il messaggio di sistema (se presente) e l'ultimo messaggio utente
        optimized_messages = []
        if system_message:
            optimized_messages.append(system_message)
        
        last_user_message = user_messages[-1]
        
        # Calcola i token già utilizzati
        used_tokens = 0
        if system_message:
            used_tokens += self.count_tokens([system_message], model)
        
        # Se il messaggio di sistema è troppo grande, troncalo
        if system_message and used_tokens > available_tokens * 0.3:  # Max 30% per il messaggio di sistema
            content = system_message.get("content", "")
            truncated_content = self.truncate_text(content, int(available_tokens * 0.3), model)
            system_message["content"] = truncated_content
            used_tokens = self.count_tokens([system_message], model)
            optimized_messages = [system_message]
        
        # Aggiungi l'ultimo messaggio utente (potrebbe essere necessario troncarlo)
        last_user_tokens = self.count_tokens([last_user_message], model)
        if used_tokens + last_user_tokens <= available_tokens:
            # Possiamo aggiungere l'ultimo messaggio utente senza modifiche
            optimized_messages.append(last_user_message)
            used_tokens += last_user_tokens
        else:
            # Tronca l'ultimo messaggio utente
            content = last_user_message.get("content", "")
            remaining_tokens = available_tokens - used_tokens
            truncated_content = self.truncate_text(content, remaining_tokens, model)
            truncated_message = last_user_message.copy()
            truncated_message["content"] = truncated_content
            optimized_messages.append(truncated_message)
            used_tokens += self.count_tokens([truncated_message], model)
        
        # Aggiungi messaggi di contesto se c'è spazio
        # Priorità: messaggi recenti dell'assistente, poi messaggi recenti dell'utente
        remaining_tokens = available_tokens - used_tokens
        
        # Aggiungi messaggi dell'assistente recenti (dal più recente al meno recente)
        for msg in reversed(assistant_messages):
            msg_tokens = self.count_tokens([msg], model)
            if remaining_tokens >= msg_tokens:
                optimized_messages.insert(1 if system_message else 0, msg)
                remaining_tokens -= msg_tokens
            else:
                break
        
        # Aggiungi messaggi dell'utente precedenti (dal più recente al meno recente, escludendo l'ultimo)
        for msg in reversed(user_messages[:-1]):
            msg_tokens = self.count_tokens([msg], model)
            if remaining_tokens >= msg_tokens:
                # Inserisci dopo il messaggio di sistema ma prima dei messaggi dell'assistente
                insert_pos = 1 if system_message else 0
                optimized_messages.insert(insert_pos, msg)
                remaining_tokens -= msg_tokens
            else:
                break
        
        # Riordina i messaggi per mantenere la sequenza temporale corretta
        optimized_messages.sort(key=lambda x: messages.index(x) if x in messages else -1)
        
        return optimized_messages
    
    def get_model_token_limit(self, model: str) -> int:
        """Restituisce il limite di token per un modello specifico.
        
        Args:
            model: Nome del modello
            
        Returns:
            Limite di token del modello
        """
        return self.MODEL_TOKEN_LIMITS.get(model, 4096)  # Default a 4096 se non specificato