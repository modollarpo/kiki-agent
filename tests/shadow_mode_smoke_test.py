import requests
import sys

API = "http://localhost:5001/api/shadow-report"
CLIENTS = [
    "Google Ads Partner",
    "Meta AI Studio",
    "TikTok Growth",
    "Storegrill Inc Ltd",
]


def check_client(client):
    print(f"\nTesting report for: {client}")
    r = requests.get(API, params={"client": client}, timeout=10)
    r.raise_for_status()
    data = r.json()

    # Basic keys
    for key in ["meta", "headline", "predictive_accuracy", "capital_leak", "human_latency", "anomalies", "recommendation"]:
        assert key in data, f"Missing '{key}' in response for {client}"

    # Headline sanity
    headline = data["headline"]
    assert isinstance(headline.get("kiki_accuracy_pct"), (int, float)), "kiki_accuracy_pct must be numeric"
    assert isinstance(headline.get("recoverable_margin_gbp"), (int, float)), "recoverable_margin_gbp must be numeric"
    assert isinstance(headline.get("capital_leak_pct"), (int, float)), "capital_leak_pct must be numeric"

    print(
        f"  ✓ Accuracy: {headline['kiki_accuracy_pct']:.1f}% | Recoverable: £{headline['recoverable_margin_gbp']:.2f} | Leak: {headline['capital_leak_pct']:.1f}%"
    )


if __name__ == "__main__":
    failures = 0
    for c in CLIENTS:
        try:
            check_client(c)
        except Exception as e:
            failures += 1
            print(f"  ✗ Failed for {c}: {e}")
    
    if failures:
        print(f"\nCompleted with {failures} failure(s).")
        sys.exit(1)
    else:
        print("\nAll Shadow Mode API checks passed.")
        sys.exit(0)
