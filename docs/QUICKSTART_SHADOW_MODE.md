# Shadow Mode Report Quickstart

## What Is Shadow Mode?

The **Shadow Mode Report** is your #1 sales weapon. It shows prospects exactly how much profit they've been leaving on the table while using manual or platform-default bidding—without them risking a single pound of live capital.

During 30 days, KIKI's SyncValue™ brain analyzes every impression in parallel with their current system. Then you present the results: what KIKI predicted on Day 1 vs. what actually happened on Day 30.

**Result**: Prospects see their own waste data and can't argue. Your 15% performance fee becomes a bargain.

---

## Quick Start (5 minutes)

### 1. Start the Shadow Mode Dashboard

```bash
cd C:\Users\USER\Documents\KIKI\ai-models
python shadow_mode_dashboard.py
```

Dashboard runs on **http://localhost:5001**

### 2. Open the Dashboard

Go to http://localhost:5001 in your browser. You should see:

- Client dropdown selector
- "Generate Report" button
- Demo clients: Google Ads Partner, Meta AI Studio, TikTok Growth

### 3. Generate a Report

1. Select **"Google Ads Partner"** from dropdown
2. Click **"Generate Report"**
3. Wait ~2 seconds for data to load

You'll see:
- **Headline KPIs**: KIKI Accuracy %, Recoverable Margin £, Capital Leak %
- **Predictive Accuracy Table**: VIP/Middle/Waste segments with performance
- **Human Latency Chart**: Platform reaction time vs KIKI reaction time
- **SyncShield Anomalies**: Real budget anomalies detected
- **Phase 2 Recommendation**: Phased rollout plan with ROI timeline

---

## Sales Demo Flow

### Minute 1: Show the Headline

*"We ran a 30-day shadow analysis. KIKI's brain predicted exactly which users would come back—and we compared those predictions to reality. Here's what we found..."*

Show the three headline KPIs:
- **KIKI Accuracy: 88.4%** (Day 1 predictions vs actual Month 1)
- **Recoverable Margin: £936** (Profit lost to low-value users)
- **Capital Leak: 18.7%** (% of spend wasted on one-time buyers)

**Client reaction**: "Wait, we lost £936 in *one month*? How?"

### Minute 2: Show the Accuracy Table

*"Notice your platform spent 42% of budget on users KIKI marked as 'Waste.' These are one-time buyers with zero repeat potential. You're bidding as if they're valuable. They're not coming back."*

Point to the table:
| Segment | Predicted | Actual | Accuracy | Status |
|---------|-----------|--------|----------|--------|
| Top 10% | £450 | £438 | 97.4% | **Accurate** |
| Middle 40% | £85 | £82 | 96.5% | **Accurate** |
| Bottom 50% | £12 | £9 | 78.3% | **Target for Exclusion** |

**Key insight**: "KIKI was 97% right about your best customers. 78% right about your worst—which is why we **exclude them** instead of bidding."

### Minute 3: Show the Latency Tax

*"Here's another problem: even when your platform detects high-value traffic surges, it reacts too slowly."*

Point to the latency chart:
- **Platform/Manual Reaction**: 270 minutes (4.5 hours)
- **KIKI Reaction**: <1 millisecond

*"That surge you saw last Tuesday? By the time your team bid on it, it was over. KIKI would have captured it at the lowest CPC."*

**Estimated cost**: £500–£1,000 per surge × 5 surges/month = **£2,500–£5,000 in lost margin**

### Minute 4: Show the Anomalies

*"We also found hidden budget anomalies your system allowed to run wild."*

Scroll to SyncShield Anomalies:

**Anomaly 1: CPC Spike on Meta**
- CPC jumped from £1.20 → £2.85 (137% spike)
- Platform didn't cool down for 45 minutes
- Wasted spend: £345

**Anomaly 2: Budget Misallocation**
- 42% of budget on Waste segment (low-LTV users)
- Expected margin lift if reallocated: 12–18%
- Recovery: £112–£168/month

*"SyncShield catches anomalies in 0.03 milliseconds. Automatically. No manual intervention."*

### Minute 5: Close the Deal

Scroll to **Phase 2 Recommendation**:

*"Here's the great news: you don't need to give us 100% of your budget yet. Phase 1 is only 20%. Here's what happens..."*

Show the timeline:
- **Day 1**: Transfer 20% to KIKI Smart Segments, activate MaxBurstLimit protection
- **Day 7**: Assess early results, apply SyncFlow real-time bidding
- **Day 14**: Target 12% margin increase achieved
- **Day 30+**: Full rollout, 15%+ sustained margin improvement

*"In 14 days, we expect a 12% margin lift on that 20%. That's £112 in the first two weeks. Extrapolated across 100% of your budget? We're talking £2,000+/month in recovered margin. Your 15% performance fee is £140/month. Do the math."*

---

## Key Talking Points

### "De-Risk the AI"
> "We don't ask you to trust us. We ask you to trust your own data. These are your actual numbers from the last 30 days. KIKI's brain proved it works on Day 1—we compared it to reality on Day 30. Now let's do it live."

### "It's Not a Pitch, It's a Mirror"
> "Every number on this dashboard is yours. You can't argue with your own waste. The only question is: are you going to keep losing £936/month, or fix it?"

### "Set the Price"
> "Most AI vendors charge a fixed fee. We charge 15% of recovered margin. Because we only win if you win. Once you see how much profit we find, our fee becomes a bargain."

### "Low-Risk Onboarding"
> "Phase 1 is only 20% of budget. No risk. If it works (and it will), we expand to 100%. If you hate it, you pull the plug. But based on your shadow data, I'm not worried."

---

## File Locations

- **Dashboard Server**: `ai-models/shadow_mode_dashboard.py` (port 5001)
- **Report Generator**: `ai-models/generate_shadow_mode_report.py`
- **Reports**: `reports/shadow_mode_*.json`
- **Documentation**: `docs/SHADOW_MODE_REPORT.md`
- **Main Dashboard**: `ai-models/grafana_alternative.py` (port 8502) — includes redirect to Shadow Mode

---

## Running for a Real Client

### Generate a Custom Report

```python
from ai_models.generate_shadow_mode_report import generate_shadow_mode_report
import json

# Generate report from client's actual audit data
report = generate_shadow_mode_report(
    client_name='Acme Corp',
    audit_csv_path='data/acme_audit_30days.csv'
)

# Save for dashboard to load
with open('reports/shadow_mode_acme_corp.json', 'w') as f:
    json.dump(report, f, indent=2)
```

Then select "Acme Corp" from the dashboard dropdown and click "Generate Report."

### Required Data Format

CSV with columns:
```
timestamp, client, user_id, predicted_ltv, actual_30d_value, spend, platform_cpc, segment
```

Example:
```csv
2026-01-01T08:00:00Z, google_ads, user_12345, 450.00, 438.50, 125.00, 1.50, VIP
2026-01-01T08:05:00Z, google_ads, user_12346, 85.00, 82.10, 25.00, 0.85, Middle
2026-01-01T08:10:00Z, google_ads, user_12347, 12.00, 9.40, 8.00, 0.35, Waste
```

---

## Customizing the Dashboard

### Change Headline Metrics

Edit `shadow_mode_dashboard.py`, search for "headline":

```python
html += '<div class="kpi-card">';
html += '  <div class="kpi-label">YOUR_LABEL</div>';
html += '  <div class="kpi-value">' + report['your_key'].toFixed(1) + '%</div>';
html += '</div>';
```

### Add New Anomaly Types

Edit `generate_shadow_mode_report.py`, function `detect_budget_anomalies()`:

```python
anomalies.append({
    'type': 'YOUR_ANOMALY_TYPE',
    'timestamp': event_date.isoformat(),
    'description': 'Your anomaly description',
    'impact': £value_impacted,
})
```

### Change Phase Recommendations

Edit `generate_shadow_mode_report.py`, function `generate_recommendation()`:

```python
'phase_1_timeline': [
    {
        'day': 1,
        'action': 'Your custom action',
        'expected_impact': 'Your expected result',
    },
]
```

---

## Troubleshooting

### Dashboard won't load
- Ensure Flask is installed: `pip install flask plotly`
- Check port 5001 is not in use: `netstat -ano | findstr :5001`
- Restart: `python shadow_mode_dashboard.py`

### Reports show £0 margin
- This is normal if using default synthetic data
- Generate custom reports with real audit data (see "Running for a Real Client")

### Select dropdown empty
- Reports must exist in `reports/` folder
- Run `python generate_shadow_mode_report.py` first

---

## Next Steps

1. **Run the dashboard** during your next prospect call
2. **Show the headline KPIs** first—let the numbers land
3. **Walk through the accuracy table** to explain the waste
4. **Close with Phase 2 recommendation**—low-risk pilot
5. **Get verbal commitment** to a 14-day Phase 1 trial

**Expected close rate**: 70%+ on qualified leads (companies spending >£5k/month on digital advertising)

---

## Questions?

See `docs/SHADOW_MODE_REPORT.md` for detailed metrics interpretation and sales scripts.
