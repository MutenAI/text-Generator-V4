
#!/bin/bash
cd $(dirname "$0")
echo "==== Starting Content Generation System ===="
echo "Checking for running Streamlit processes..."
ps aux | grep streamlit | grep -v grep

echo "Killing any existing Streamlit processes..."
pkill -f "streamlit run" || true

echo "Starting Streamlit app on port 8501..."
python -m streamlit run content_generator_app.py \
  --server.port=8501 \
  --server.headless=true \
  --server.enableCORS=true \
  --server.enableWebsocketCompression=false \
  --server.address=0.0.0.0 \
  --browser.serverAddress=0.0.0.0 \
  --browser.gatherUsageStats=false
