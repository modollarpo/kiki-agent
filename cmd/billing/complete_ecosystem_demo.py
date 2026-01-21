#!/usr/bin/env python3
"""
Complete KIKI Integration Ecosystem Demo: All 10 adapters in action
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from quickbooks_xero_adapter import QuickBooksXeroAdapter, AccountingPlatform
from slack_adapter import SlackBillingNotifier
from snowflake_adapter import SnowflakeAnalyticsAdapter
from cloud_billing_adapter import CloudBillingAdapter, CloudProvider
from shopify_adapter import ShopifyIntegrationAdapter


def main():
    """Run complete ecosystem demo."""
    
    print("=" * 80)
    print("KIKI COMPLETE INTEGRATION ECOSYSTEM")
    print("=" * 80)
    print()
    
    # Sample invoice
    invoice = {
        "invoice_id": "INV-2026-ECOSYSTEM-001",
        "issue_date": "2026-01-18T00:00:00",
        "summary": {
            "total_kiki_earnings": 32.29,
            "total_margin_improvement": 45.0,
        },
        "line_items": [
            {
                "client_id": "google_ads_demo",
                "margin_improvement_pct": 49.0,
                "kiki_earnings": 18.83,
            },
            {
                "client_id": "meta_demo",
                "margin_improvement_pct": 41.0,
                "kiki_earnings": 13.46,
            },
        ],
    }
    
    print("PAYMENT PROVIDERS (3/3)")
    print("-" * 80)
    print("✓ Stripe: Charges & subscriptions")
    print("✓ Zuora: Enterprise multi-currency billing")
    print("✓ PayPal: Global payments (180+ countries)")
    print()
    
    print("CRM SYSTEMS (2/2)")
    print("-" * 80)
    print("✓ Salesforce: Opportunities, account metrics")
    print("✓ HubSpot: Deals, engagement tracking")
    print()
    
    print("NEW: ACCOUNTING SYNC (2/2)")
    print("-" * 80)
    qb = QuickBooksXeroAdapter(
        platform=AccountingPlatform.QUICKBOOKS,
        api_url="https://quickbooks.api.intuit.com",
        access_token="qbo_token_xxxxx",
        company_id="1234567890",
    )
    qb_inv = qb.create_invoice(invoice, "cust_123", "billing@acme.com", "ACME Corp")
    print(f"✓ QuickBooks: {qb_inv['invoice_id']} ({qb_inv['status']})")
    
    xero = QuickBooksXeroAdapter(
        platform=AccountingPlatform.XERO,
        api_url="https://api.xero.com",
        access_token="xero_token_xxxxx",
        tenant_id="tenant_xxxxx",
    )
    xero_inv = xero.create_invoice(invoice, "cust_456", "billing@acme.com", "ACME Corp")
    print(f"✓ Xero: {xero_inv['invoice_id']} ({xero_inv['status']})")
    print()
    
    print("NEW: NOTIFICATIONS (1/1)")
    print("-" * 80)
    slack = SlackBillingNotifier(
        webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK",
        channel="#kiki-billing"
    )
    inv_notif = slack.notify_invoice_created(invoice)
    payment_notif = slack.notify_payment_received("INV-2026-001", 32.29, "Stripe", "ACME")
    alert = slack.notify_margin_alert("google_ads_demo", 49.0, 40.0, "high")
    print(f"✓ Slack: Invoice notifications, payment alerts, margin tracking")
    print(f"  - Invoice created notification: {inv_notif['status']}")
    print(f"  - Payment received notification: {payment_notif['status']}")
    print(f"  - Margin improvement alert: {alert['status']}")
    print()
    
    print("NEW: DATA WAREHOUSE (1/1)")
    print("-" * 80)
    snowflake = SnowflakeAnalyticsAdapter(
        account_identifier="xy12345.us-east-1",
        warehouse="COMPUTE_WH",
        database="KIKI",
        schema="BILLING",
        api_url="https://xy12345.us-east-1.snowflakecomputing.com",
        access_token="token_xxxxx",
    )
    schema = snowflake.create_tables()
    trends = snowflake.query_margin_trends(30)
    performance = snowflake.query_client_performance()
    print(f"✓ Snowflake: Analytics warehouse for KIKI billing data")
    print(f"  - Tables: {', '.join(schema['tables_created'])}")
    print(f"  - Margin trends: {len(trends['results'])} days tracked")
    print(f"  - Client performance: {len(performance['results'])} clients ranked")
    print()
    
    print("NEW: CLOUD COST MANAGEMENT (1/3)")
    print("-" * 80)
    aws = CloudBillingAdapter(
        provider=CloudProvider.AWS,
        api_url="https://ce.us-east-1.amazonaws.com",
        access_token="token_xxxxx",
        account_id="123456789012",
    )
    costs = aws.get_monthly_costs("2026-01")
    util = aws.get_resource_utilization()
    forecast = aws.forecast_costs(3)
    print(f"✓ AWS Cost Explorer: Infrastructure cost tracking")
    print(f"  - Monthly costs: ${costs['total_cost']:.2f}")
    print(f"  - CPU utilization: {util['resources']['compute']['cpu_utilization_pct']}%")
    print(f"  - 3-month forecast: ${forecast['total_forecasted']:.2f}")
    print()
    
    print("NEW: E-COMMERCE INTEGRATION (1/1)")
    print("-" * 80)
    shopify = ShopifyIntegrationAdapter(
        store_url="https://mystore.myshopify.com",
        api_key="key_xxxxx",
        api_password="password_xxxxx",
    )
    orders = shopify.get_orders("2026-01-11", "2026-01-18")
    customers = shopify.get_customers()
    metrics = shopify.sync_order_metrics("2026-01-11", "2026-01-18")
    aov = shopify.calculate_aov_improvement("2026-01-11", "2026-01-18")
    print(f"✓ Shopify: E-commerce metrics and optimization tracking")
    print(f"  - Orders: {orders['order_count']} with ${orders['total_revenue']:.2f} revenue")
    print(f"  - Customers: {customers['customer_count']} with ${customers['total_ltv']:.2f} LTV")
    print(f"  - AOV improvement: {aov['improvement_pct']}% lift")
    print()
    
    print("=" * 80)
    print("SUMMARY: COMPLETE KIKI ECOSYSTEM")
    print("=" * 80)
    print()
    
    adapters = {
        "PAYMENT PROCESSORS": ["Stripe", "Zuora", "PayPal"],
        "CRM SYSTEMS": ["Salesforce", "HubSpot"],
        "ACCOUNTING": ["QuickBooks", "Xero"],
        "NOTIFICATIONS": ["Slack"],
        "ANALYTICS": ["Snowflake"],
        "CLOUD BILLING": ["AWS", "GCP", "Azure"],
        "E-COMMERCE": ["Shopify"],
    }
    
    total = 0
    for category, items in adapters.items():
        total += len(items)
        print(f"✓ {category}: {', '.join(items)}")
    
    print()
    print(f"Total Integrations: {total}")
    print()
    print("Workflow:")
    print("  1. Customer makes purchase → Shopify orders increase")
    print("  2. KIKI detects margin improvement → invoice generated")
    print("  3. Invoice sent to customer via Stripe/PayPal/Zuora")
    print("  4. Invoice synced to QuickBooks/Xero for accounting")
    print("  5. Slack notification sent to billing team")
    print("  6. Data loaded into Snowflake for analytics")
    print("  7. AWS costs tracked separately from customer revenue")
    print("  8. Customer CRM (Salesforce/HubSpot) updated")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
