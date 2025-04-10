"""Configurazione centralizzata per il sistema di generazione contenuti."""

import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

# Configurazione Modelli LLM
LLM_MODELS = {
    'openai': {
        'default': 'gpt-4',
        'temperature': {
            'low': 0.0,
            'medium': 0.2,
            'high': 0.7
        }
    },
    'anthropic': {
        'default': 'claude-3-opus-20240229',
        'temperature': {
            'low': 0.0,
            'medium': 0.2,
            'high': 0.7
        }
    },
    'deepseek': {
        'default': 'deepseek/deepseek-chat',
        'temperature': {
            'low': 0.0,
            'medium': 0.2,
            'high': 0.7
        }
    }
}

# Configurazione Percorsi
DEFAULT_OUTPUT_DIR = 'output'
DEFAULT_REFERENCE_FILE = os.path.join('reference', 'fylle-knowledge-base.md')

def validate_environment():
    """Valida la presenza delle variabili d'ambiente necessarie."""
    missing_vars = []
    required_vars = {
        'OPENAI_API_KEY': OPENAI_API_KEY,
        'ANTHROPIC_API_KEY': ANTHROPIC_API_KEY,
        'SERPER_API_KEY': SERPER_API_KEY
    }
    
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        raise EnvironmentError(
            f"Variabili d'ambiente mancanti: {', '.join(missing_vars)}. "
            "Assicurati di configurare queste variabili nel file .env"
        )