
#!/bin/bash
# Script per testare l'editor con debug attivato

# Ferma eventuali processi Streamlit
pkill -f streamlit

# Imposta le variabili di ambiente per il debug
export STREAMLIT_DEBUG=true
export PYTHONPATH=.
export LOG_LEVEL=DEBUG

# Avvia Streamlit con opzioni di debug
cd content-generation-system
python -m streamlit run content_generator_app.py \
  --server.port=8501 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableWebsocketCompression=false \
  --server.address=0.0.0.0 \
  --logger.level=debug
