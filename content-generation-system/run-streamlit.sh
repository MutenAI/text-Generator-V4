
#!/bin/bash
cd $(dirname "$0")
echo "Starting Streamlit app with logging..."
python -m streamlit run content_generator_app.py --server.port=8501 --server.headless=true --server.enableCORS=true --server.enableWebsocketCompression=false --server.address=0.0.0.0 > streamlit.log 2>&1 &
echo "Streamlit process started with PID: $!"
echo "Waiting for the app to initialize..."
sleep 3
echo "Log output from Streamlit:"
tail -f streamlit.log
