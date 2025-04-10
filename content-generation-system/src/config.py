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
        'powerful': 'gpt-4',
        'balanced': 'gpt-4',
        'economic': 'gpt-3.5-turbo'
    },
    'anthropic': {
        'default': 'claude-3-sonnet-20240229',
        'powerful': 'claude-3-opus-20240229',
        'balanced': 'claude-3-sonnet-20240229',
        'economic': 'claude-3-haiku-20240307'
    },
    'deepseek': {
        'default': 'deepseek-coder',
        'powerful': 'deepseek-chat',
        'balanced': 'deepseek-coder',
        'economic': 'deepseek-lite'
    },
    'cohere': {
        'default': 'command-r-plus',
        'powerful': 'command-r-plus',
        'balanced': 'command-r',
        'economic': 'command'
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