"""Test grafana_alternative startup and catch errors."""
import sys
import traceback

try:
    print("Importing grafana_alternative...")
    from grafana_alternative import app
    print("✓ Import successful")
    
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=8502, debug=True)
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
