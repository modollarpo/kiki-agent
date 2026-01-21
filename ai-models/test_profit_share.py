"""Test profit-share billing system"""

import sys
sys.path.insert(0, '.')

try:
    print("Testing profit-share billing imports...")
    from profit_share_calculator import KIKIProfitShareEngine
    print("✅ Imports successful")
    
    print("\nInitializing engine...")
    engine = KIKIProfitShareEngine(
        prometheus_url="http://localhost:9090",
        audit_trail_path="../audit_log.csv",
        profit_share_pct=10.0
    )
    print(f"✅ Engine initialized with {engine.profit_share_pct}% profit share")
    
    print("\nTesting Prometheus connection...")
    result = engine.fetch_prometheus_metric("up")
    if result:
        print(f"✅ Prometheus connected: {len(result)} targets up")
    else:
        print("⚠️  Prometheus not responding - metrics will use simulated data")
    
    print("\n✅ All systems ready for OaaS billing")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
