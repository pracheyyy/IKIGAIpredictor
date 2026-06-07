"""
IKIGAI — Entry Point
Run: python run.py
"""
import os
from dotenv import load_dotenv
load_dotenv()
from backend.app import app

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    print(f"\n🌸  IKIGAI server starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)