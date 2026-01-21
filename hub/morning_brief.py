import sqlite3
from datetime import datetime, timedelta

def generate_briefing():
    def send_slack_briefing(briefing, webhook_url):
        import requests
        text = f"*KIKI Morning Briefing for {briefing['date']}*\n" \
               f"Revenue Recovered: ${briefing['revenue']}\n" \
               f"Shield Interventions: {briefing['safety_blocks']}\n" \
               f"Strategic Insight: {briefing['ai_insight']}"
        payload = {"text": text}
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"[Slack Briefing Error] {e}")

    def send_discord_briefing(briefing, webhook_url):
        import requests
        content = f"**KIKI Morning Briefing for {briefing['date']}**\n" \
                  f"Revenue Recovered: ${briefing['revenue']}\n" \
                  f"Shield Interventions: {briefing['safety_blocks']}\n" \
                  f"Strategic Insight: {briefing['ai_insight']}"
        payload = {"content": content}
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"[Discord Briefing Error] {e}")
    conn = sqlite3.connect('kiki_memory.db')
    cursor = conn.cursor()
    # 1. Query Yesterday's Recovered Margin
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    cursor.execute("SELECT SUM(actual_revenue) FROM CreativePerformance WHERE date=?", (yesterday,))
    total_rev = cursor.fetchone()[0] or 0
    # 2. Query Shield Block Frequency
    cursor.execute("SELECT COUNT(*) FROM ShieldAudit WHERE date=? AND status='BLOCKED'", (yesterday,))
    blocks = cursor.fetchone()[0]
    # 3. Formulate the 'KIKI Lesson' (stubbed for demo)
    insight = "KIKI noticed that TikTok variants with 'Neon' overlays had a 12% higher LTV than Meta variants."
    conn.close()
    return {
        "date": yesterday,
        "revenue": total_rev,
        "safety_blocks": blocks,
        "ai_insight": insight
    }

if __name__ == "__main__":
    briefing = generate_briefing()
    print(f"KIKI Morning Briefing for {briefing['date']}")
    print(f"Revenue Recovered: ${briefing['revenue']}")
    print(f"Shield Interventions: {briefing['safety_blocks']}")
    print(f"Strategic Insight: {briefing['ai_insight']}")
    # Send to Slack/Discord if configured
    import os
    slack_url = os.environ.get('KIKI_SLACK_BRIEFING_URL')
    discord_url = os.environ.get('KIKI_DISCORD_BRIEFING_URL')
    if slack_url:
        send_slack_briefing(briefing, slack_url)
    if discord_url:
        send_discord_briefing(briefing, discord_url)
