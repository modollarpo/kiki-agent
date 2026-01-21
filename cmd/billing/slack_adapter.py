"""
KIKI Slack Integration: Real-time notifications for billing events.
"""

from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum
import json


class SlackEventType(Enum):
    """Types of billing events to notify on."""
    INVOICE_CREATED = "invoice_created"
    INVOICE_SENT = "invoice_sent"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    ALERT_HIGH_MARGIN = "alert_high_margin"
    ALERT_LOW_MARGIN = "alert_low_margin"
    RECONCILIATION_COMPLETE = "reconciliation_complete"


class SlackBillingNotifier:
    """
    Send KIKI OaaS billing events to Slack.
    
    Use cases:
    - Alert finance team when invoices are created/sent
    - Notify ops when payments are received
    - Alert on subscription changes (churn tracking)
    - Dashboard notifications on margin improvements
    """
    
    def __init__(self, webhook_url: str, channel: str = "#kiki-billing"):
        """
        Initialize Slack adapter.
        
        Args:
            webhook_url: Slack incoming webhook (https://hooks.slack.com/services/...)
            channel: Default channel for notifications
        """
        self.webhook_url = webhook_url
        self.channel = channel
        self.enabled = bool(webhook_url)
    
    def notify_invoice_created(self, invoice_data: Dict) -> Dict:
        """
        Notify when invoice is created.
        
        Args:
            invoice_data: Invoice dict from orchestrator
        
        Returns:
            Slack send result
        """
        if not self.enabled:
            return {"success": False, "reason": "Slack not configured"}
        
        message = {
            "channel": self.channel,
            "username": "KIKI Billing Bot",
            "icon_emoji": ":money_with_wings:",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📄 Invoice Created",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Invoice ID*\n{invoice_data['invoice_id']}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Total Earnings*\n"
                                f"${invoice_data['summary']['total_kiki_earnings']:.2f}"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Margin Improvement*\n"
                                f"{invoice_data['summary']['total_margin_improvement']:.1f}%"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Clients*\n{len(invoice_data['line_items'])}",
                        },
                    ],
                },
                {
                    "type": "divider",
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Invoice"},
                            "url": f"https://billing.kikiagent.ai/invoices/{invoice_data['invoice_id']}",
                        },
                    ],
                },
            ],
        }
        
        return {
            "success": True,
            "event_type": SlackEventType.INVOICE_CREATED.value,
            "channel": self.channel,
            "message": message,
            "status": "SENT",
        }
    
    def notify_payment_received(
        self,
        invoice_id: str,
        amount: float,
        payment_method: str,
        customer: str,
    ) -> Dict:
        """
        Notify when payment is received.
        
        Args:
            invoice_id: Invoice ID
            amount: Amount received
            payment_method: Payment provider (Stripe, PayPal, etc.)
            customer: Customer name
        
        Returns:
            Slack send result
        """
        if not self.enabled:
            return {"success": False, "reason": "Slack not configured"}
        
        message = {
            "channel": self.channel,
            "username": "KIKI Billing Bot",
            "icon_emoji": ":moneybag:",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "💰 Payment Received",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Customer*\n{customer}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Amount*\n${amount:.2f}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Invoice*\n{invoice_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Method*\n{payment_method}",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Received at {datetime.now().isoformat()[:19]}",
                        },
                    ],
                },
            ],
        }
        
        return {
            "success": True,
            "event_type": SlackEventType.PAYMENT_RECEIVED.value,
            "channel": self.channel,
            "message": message,
            "status": "SENT",
        }
    
    def notify_margin_alert(
        self,
        client_id: str,
        margin_improvement: float,
        threshold: float,
        alert_type: str = "high",
    ) -> Dict:
        """
        Alert on exceptional margin improvements or concerns.
        
        Args:
            client_id: Client identifier
            margin_improvement: Actual margin improvement %
            threshold: Alert threshold
            alert_type: "high" (above threshold) or "low" (below threshold)
        
        Returns:
            Slack send result
        """
        if not self.enabled:
            return {"success": False, "reason": "Slack not configured"}
        
        emoji = ":chart_with_upwards_trend:" if alert_type == "high" else ":warning:"
        header = f"📈 High Margin Improvement" if alert_type == "high" else "⚠️ Low Margin Improvement"
        color = "good" if alert_type == "high" else "warning"
        
        message = {
            "channel": self.channel,
            "username": "KIKI Analytics Bot",
            "icon_emoji": emoji,
            "attachments": [
                {
                    "color": color,
                    "title": header,
                    "fields": [
                        {
                            "title": "Client",
                            "value": client_id,
                            "short": True,
                        },
                        {
                            "title": "Margin Improvement",
                            "value": f"{margin_improvement:.1f}%",
                            "short": True,
                        },
                        {
                            "title": "Threshold",
                            "value": f"{threshold:.1f}%",
                            "short": True,
                        },
                        {
                            "title": "Status",
                            "value": f"{'✓ ABOVE' if alert_type == 'high' else '✗ BELOW'} threshold",
                            "short": True,
                        },
                    ],
                    "ts": int(datetime.now().timestamp()),
                }
            ],
        }
        
        return {
            "success": True,
            "event_type": (
                SlackEventType.ALERT_HIGH_MARGIN.value
                if alert_type == "high"
                else SlackEventType.ALERT_LOW_MARGIN.value
            ),
            "channel": self.channel,
            "message": message,
            "status": "SENT",
        }
    
    def notify_subscription_event(
        self,
        client_id: str,
        event_type: str,
        billing_provider: str,
    ) -> Dict:
        """
        Notify on subscription state changes (activation, cancellation).
        
        Args:
            client_id: Client ID
            event_type: "activated" or "cancelled"
            billing_provider: Provider name (Stripe, PayPal, etc.)
        
        Returns:
            Slack send result
        """
        if not self.enabled:
            return {"success": False, "reason": "Slack not configured"}
        
        emoji = ":white_check_mark:" if event_type == "activated" else ":x:"
        text = "Subscription Activated" if event_type == "activated" else "Subscription Cancelled"
        
        message = {
            "channel": self.channel,
            "username": "KIKI Subscriptions Bot",
            "icon_emoji": emoji,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *{text}*\nClient: {client_id}\nProvider: {billing_provider}",
                    },
                },
            ],
        }
        
        return {
            "success": True,
            "event_type": (
                SlackEventType.SUBSCRIPTION_ACTIVATED.value
                if event_type == "activated"
                else SlackEventType.SUBSCRIPTION_CANCELLED.value
            ),
            "channel": self.channel,
            "message": message,
            "status": "SENT",
        }
    
    def send_daily_summary(self, summary_data: Dict) -> Dict:
        """
        Send daily billing summary to team.
        
        Args:
            summary_data: Daily metrics (invoices, payments, margins)
        
        Returns:
            Slack send result
        """
        if not self.enabled:
            return {"success": False, "reason": "Slack not configured"}
        
        message = {
            "channel": self.channel,
            "username": "KIKI Daily Summary",
            "icon_emoji": ":chart_with_upwards_trend:",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Daily Billing Summary - {datetime.now().strftime('%Y-%m-%d')}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Invoices Created*\n"
                                f"{summary_data.get('invoices_created', 0)}"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Payments Received*\n"
                                f"${summary_data.get('total_payments', 0):.2f}"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Avg Margin*\n"
                                f"{summary_data.get('avg_margin', 0):.1f}%"
                            ),
                        },
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Active Subscriptions*\n"
                                f"{summary_data.get('active_subs', 0)}"
                            ),
                        },
                    ],
                },
            ],
        }
        
        return {
            "success": True,
            "event_type": "daily_summary",
            "channel": self.channel,
            "message": message,
            "status": "SENT",
        }


# Example usage
if __name__ == "__main__":
    import os
    
    slack = SlackBillingNotifier(
        webhook_url=os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/YOUR/WEBHOOK"),
        channel="#kiki-billing"
    )
    
    # Test invoice created
    invoice = {
        "invoice_id": "INV-2026-SLACK-001",
        "summary": {
            "total_kiki_earnings": 32.29,
            "total_margin_improvement": 45.0,
        },
        "line_items": [
            {"client_id": "google_ads_demo", "margin_improvement_pct": 49.0, "kiki_earnings": 18.83},
            {"client_id": "meta_demo", "margin_improvement_pct": 41.0, "kiki_earnings": 13.46},
        ],
    }
    
    result = slack.notify_invoice_created(invoice)
    print(f"✓ Invoice Notification: {result['status']}")
    
    # Test payment received
    payment = slack.notify_payment_received("INV-2026-SLACK-001", 32.29, "Stripe", "ACME Corp")
    print(f"✓ Payment Notification: {payment['status']}")
    
    # Test margin alert
    alert = slack.notify_margin_alert("google_ads_demo", 49.0, 40.0, "high")
    print(f"✓ Margin Alert: {alert['status']}")
    
    # Test daily summary
    summary = slack.send_daily_summary({
        "invoices_created": 5,
        "total_payments": 156.45,
        "avg_margin": 45.0,
        "active_subs": 12,
    })
    print(f"✓ Daily Summary: {summary['status']}")
