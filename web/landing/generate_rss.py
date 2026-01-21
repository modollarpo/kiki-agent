import datetime
from pathlib import Path
from typing import List, Dict

# Static metadata for blog posts. Update this list when adding new posts.
POSTS: List[Dict[str, str]] = [
    {
        "title": "Building a 94.7% Accurate LTV Prediction Model with TensorFlow and gRPC",
        "link": "https://kiki.example.com/blog-ltv-prediction.html",
        "description": "How we engineered SyncValue's lifetime value model for sub-100ms latency and 94.7% accuracy using TensorFlow, Feast, and gRPC.",
        "pub_date": "2026-01-15",
    },
    {
        "title": "Scaling to 10M Messages/Hour: Our Go Microservices Architecture",
        "link": "https://kiki.example.com/blog-microservices-scale.html",
        "description": "How SyncEngage processes 10M+ retention messages per hour with Go, Kafka, and Kubernetes autoscaling.",
        "pub_date": "2026-01-10",
    },
    {
        "title": "GDPR Article 7 Consent: Implementation Guide for SaaS Platforms",
        "link": "https://kiki.example.com/blog-gdpr-consent.html",
        "description": "Practical patterns for consent capture, proofs, and revocation backed by blockchain-grade audit trails.",
        "pub_date": "2026-01-08",
    },
    {
        "title": "Introducing Multi-Variant Creative Generation with SyncCreate",
        "link": "https://kiki.example.com/blog-synccreate-multivariant.html",
        "description": "Generate five TikTok-ready video variants in minutes using scene-aware prompts, motion guardrails, and TTS alignment.",
        "pub_date": "2026-01-05",
    },
    {
        "title": "Zero-Trust Security Architecture: Our Journey to SOC 2 Type II",
        "link": "https://kiki.example.com/blog-zero-trust-soc2.html",
        "description": "Lessons from achieving SOC 2 Type II: mTLS everywhere, OPA sidecars, audit logging, and incident response.",
        "pub_date": "2025-12-28",
    },
    {
        "title": "Feature Engineering for Churn Prediction: 50+ Behavioral Signals",
        "link": "https://kiki.example.com/blog-feature-engineering-churn.html",
        "description": "Behavioral, financial, and adoption signals that improve churn prediction recall and lead time.",
        "pub_date": "2025-12-22",
    },
    {
        "title": "How We Helped a FinTech Reduce Churn by 38% in 90 Days",
        "link": "https://kiki.example.com/blog-fintech-churn-38.html",
        "description": "PayFlow Financial case study: LTV scoring, risk alerts, and multi-channel retention plays that cut churn by 38%.",
        "pub_date": "2025-12-18",
    },
]

CHANNEL = {
    "title": "KIKI Engineering Blog",
    "link": "https://kiki.example.com/blog",
    "description": "AI, ML, compliance, and product engineering insights from KIKI.",
    "language": "en-us",
}


def rfc2822(date_str: str) -> str:
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    # Use UTC midnight as publication time
    return dt.strftime("%a, %d %b %Y 00:00:00 +0000")


def render_item(item: Dict[str, str]) -> str:
    return f"""
    <item>
      <title>{item['title']}</title>
      <link>{item['link']}</link>
      <guid isPermaLink=\"true\">{item['link']}</guid>
      <pubDate>{rfc2822(item['pub_date'])}</pubDate>
      <description>{item['description']}</description>
    </item>"""


def build_rss(items: List[Dict[str, str]]) -> str:
    last_build = rfc2822(max(p["pub_date"] for p in items))
    rendered_items = "\n".join(render_item(item) for item in items)
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <title>{CHANNEL['title']}</title>
    <link>{CHANNEL['link']}</link>
    <description>{CHANNEL['description']}</description>
    <language>{CHANNEL['language']}</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <ttl>720</ttl>
{rendered_items}
  </channel>
</rss>
"""


def main() -> None:
    rss_content = build_rss(POSTS)
    output_path = Path(__file__).with_name("rss.xml")
    output_path.write_text(rss_content, encoding="utf-8")
    print(f"Wrote RSS with {len(POSTS)} items to {output_path}")


if __name__ == "__main__":
    main()
