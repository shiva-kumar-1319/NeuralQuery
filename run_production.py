from waitress import serve
from wsgi import app
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')

def run_server():
    port = int(os.environ.get('PORT', 5000))
    print(f"\n" + "="*60)
    print("🚀 NeuralQuery - Production Server")
    print("="*60)
    print(f"📍 Listening on: http://0.0.0.0:{port}")
    print("🔧 Server: Waitress (WSGI)")
    print("="*60 + "\n")
    
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    run_server()
