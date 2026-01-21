package connectors

import (
	"context"
	"log"
	"testing"
	"time"
)

// TestMetaSmartConnectorIntegration tests Meta Smart Connector with budget management
func TestMetaSmartConnectorIntegration(t *testing.T) {
	log.Println("🧪 Starting Meta Smart Connector Integration Test")

	// Initialize connector with $400 budget
	config := ConnectorConfig{
		Type:       MetaSmart,
		APIKey:     "test-access-token",
		BusinessID: "meta-business-123",
		MaxBudget:  400.00,
	}

	connector, err := NewConnector(config)
	if err != nil {
		t.Fatalf("Failed to create connector: %v", err)
	}

	smartConnector, ok := connector.(*MetaSmartConnector)
	if !ok {
		t.Fatalf("Expected MetaSmartConnector, got %T", connector)
	}

	// Enable mock mode
	smartConnector.MockMode = true

	// Connect to platform
	ctx := context.Background()
	if err := smartConnector.Connect(ctx); err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}

	log.Printf("✅ Connected: %s", smartConnector.GetStatus())

	// Test bid scenarios
	testCases := []struct {
		name         string
		customerID   string
		predictedLTV float64
		bidAmount    float64
		explanation  string
		shouldPass   bool
	}{
		{
			name:         "High Value Meta Campaign - $120 bid",
			customerID:   "META_CUST_001",
			predictedLTV: 1200.00,
			bidAmount:    120.00,
			explanation:  `{"spend_contribution": 0.70, "engagement_contribution": 0.30, "confidence": 0.92}`,
			shouldPass:   true,
		},
		{
			name:         "Medium Value Campaign - $100 bid",
			customerID:   "META_CUST_002",
			predictedLTV: 600.00,
			bidAmount:    100.00,
			explanation:  `{"spend_contribution": 0.60, "engagement_contribution": 0.40, "confidence": 0.88}`,
			shouldPass:   true,
		},
		{
			name:         "Budget overflow - $200 bid (should fail)",
			customerID:   "META_CUST_003",
			predictedLTV: 1500.00,
			bidAmount:    200.00,
			explanation:  `{"spend_contribution": 0.75, "engagement_contribution": 0.25, "confidence": 0.95}`,
			shouldPass:   false, // Total would be $420 > $400 limit
		},
	}

	for i, tc := range testCases {
		log.Printf("\n--- Test Case %d: %s ---", i+1, tc.name)

		bidReq := &BidRequest{
			CustomerID:   tc.customerID,
			CampaignID:   "meta-campaign-001",
			PredictedLTV: tc.predictedLTV,
			BidAmount:    tc.bidAmount,
			Explanation:  tc.explanation,
			Timestamp:    time.Now(),
		}

		stats := smartConnector.GetBudgetStats()
		log.Printf("📊 Pre-bid budget: $%.2f/$%.2f (%.1f%% used)",
			stats.CurrentSpend,
			stats.MaxBudget,
			(stats.CurrentSpend/stats.MaxBudget)*100)

		resp, err := smartConnector.PlaceBid(ctx, bidReq)

		if tc.shouldPass {
			if err != nil {
				log.Printf("⚠️ Expected success but got error: %v", err)
			}
			if resp != nil {
				log.Printf("📝 Response: %s (Code: %s)", resp.Message, resp.PlatformCode)
			}
		} else {
			if err == nil {
				t.Errorf("Expected budget overflow error for %s, but bid succeeded", tc.name)
			} else {
				log.Printf("✅ Correctly rejected: %v", err)
			}
		}

		statsAfter := smartConnector.GetBudgetStats()
		log.Printf("📊 Post-bid budget: $%.2f/$%.2f (%.1f%% used)",
			statsAfter.CurrentSpend,
			statsAfter.MaxBudget,
			(statsAfter.CurrentSpend/statsAfter.MaxBudget)*100)
	}

	// Verify final state
	finalStats := smartConnector.GetBudgetStats()
	log.Printf("\n🏁 Meta Final Results:")
	log.Printf("   Total Spend: $%.2f", finalStats.CurrentSpend)
	log.Printf("   Max Budget: $%.2f", finalStats.MaxBudget)
	log.Printf("   Remaining: $%.2f", finalStats.RemainingBudget)

	// Clean up
	if err := smartConnector.Close(); err != nil {
		t.Fatalf("Failed to close connector: %v", err)
	}

	log.Printf("\n✅ Meta integration test complete")
}

// TestTradeDeskSmartConnectorIntegration tests Trade Desk Smart Connector with budget management
func TestTradeDeskSmartConnectorIntegration(t *testing.T) {
	log.Println("🧪 Starting Trade Desk Smart Connector Integration Test")

	// Initialize connector with $600 budget
	config := ConnectorConfig{
		Type:      TradeDeskSmart,
		APIKey:    "test-ttd-api-key",
		PartnerID: "ttd-partner-789",
		MaxBudget: 600.00,
	}

	connector, err := NewConnector(config)
	if err != nil {
		t.Fatalf("Failed to create connector: %v", err)
	}

	smartConnector, ok := connector.(*TradeDeskSmartConnector)
	if !ok {
		t.Fatalf("Expected TradeDeskSmartConnector, got %T", connector)
	}

	// Enable mock mode
	smartConnector.MockMode = true

	// Connect to platform
	ctx := context.Background()
	if err := smartConnector.Connect(ctx); err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}

	log.Printf("✅ Connected: %s", smartConnector.GetStatus())

	// Test bid scenarios for programmatic RTB
	testCases := []struct {
		name         string
		customerID   string
		predictedLTV float64
		bidAmount    float64
		explanation  string
		shouldPass   bool
	}{
		{
			name:         "Premium Programmatic Bid - $200",
			customerID:   "TTD_IMP_001",
			predictedLTV: 2500.00,
			bidAmount:    200.00,
			explanation:  `{"spend_contribution": 0.80, "engagement_contribution": 0.20, "confidence": 0.96}`,
			shouldPass:   true,
		},
		{
			name:         "Standard Programmatic Bid - $150",
			customerID:   "TTD_IMP_002",
			predictedLTV: 1000.00,
			bidAmount:    150.00,
			explanation:  `{"spend_contribution": 0.65, "engagement_contribution": 0.35, "confidence": 0.90}`,
			shouldPass:   true,
		},
		{
			name:         "Low Competition Bid - $100",
			customerID:   "TTD_IMP_003",
			predictedLTV: 500.00,
			bidAmount:    100.00,
			explanation:  `{"spend_contribution": 0.50, "engagement_contribution": 0.50, "confidence": 0.85}`,
			shouldPass:   true,
		},
		{
			name:         "Budget overflow - $200 bid (should fail)",
			customerID:   "TTD_IMP_004",
			predictedLTV: 3000.00,
			bidAmount:    200.00,
			explanation:  `{"spend_contribution": 0.85, "engagement_contribution": 0.15, "confidence": 0.97}`,
			shouldPass:   false, // Total would be $650 > $600 limit
		},
	}

	for i, tc := range testCases {
		log.Printf("\n--- Test Case %d: %s ---", i+1, tc.name)

		bidReq := &BidRequest{
			CustomerID:   tc.customerID,
			CampaignID:   "ttd-campaign-rtb-001",
			PredictedLTV: tc.predictedLTV,
			BidAmount:    tc.bidAmount,
			Explanation:  tc.explanation,
			Timestamp:    time.Now(),
		}

		stats := smartConnector.GetBudgetStats()
		log.Printf("📊 Pre-bid budget: $%.2f/$%.2f (%.1f%% used)",
			stats.CurrentSpend,
			stats.MaxBudget,
			(stats.CurrentSpend/stats.MaxBudget)*100)

		resp, err := smartConnector.PlaceBid(ctx, bidReq)

		if tc.shouldPass {
			if err != nil {
				log.Printf("⚠️ Expected success but got error: %v", err)
			}
			if resp != nil {
				log.Printf("📝 Response: %s (Code: %s)", resp.Message, resp.PlatformCode)
			}
		} else {
			if err == nil {
				t.Errorf("Expected budget overflow error for %s, but bid succeeded", tc.name)
			} else {
				log.Printf("✅ Correctly rejected: %v", err)
			}
		}

		statsAfter := smartConnector.GetBudgetStats()
		log.Printf("📊 Post-bid budget: $%.2f/$%.2f (%.1f%% used)",
			statsAfter.CurrentSpend,
			statsAfter.MaxBudget,
			(statsAfter.CurrentSpend/statsAfter.MaxBudget)*100)
	}

	// Verify final state
	finalStats := smartConnector.GetBudgetStats()
	log.Printf("\n🏁 Trade Desk Final Results:")
	log.Printf("   Total Spend: $%.2f", finalStats.CurrentSpend)
	log.Printf("   Max Budget: $%.2f", finalStats.MaxBudget)
	log.Printf("   Remaining: $%.2f", finalStats.RemainingBudget)
	log.Printf("   Budget Used: %.1f%%", (finalStats.CurrentSpend/finalStats.MaxBudget)*100)

	// Clean up
	if err := smartConnector.Close(); err != nil {
		t.Fatalf("Failed to close connector: %v", err)
	}

	log.Printf("\n✅ Trade Desk integration test complete")
}

// TestMultiPlatformBudgetManagement tests using all three platforms simultaneously
func TestMultiPlatformBudgetManagement(t *testing.T) {
	log.Println("🧪 Starting Multi-Platform Budget Management Test")

	ctx := context.Background()

	// Create all three smart connectors with separate budgets
	googleConfig := ConnectorConfig{
		Type:       GoogleAdsSmart,
		APIKey:     "google-test-key",
		CustomerID: "google-123",
		MaxBudget:  300.00,
	}

	metaConfig := ConnectorConfig{
		Type:       MetaSmart,
		APIKey:     "meta-test-key",
		BusinessID: "meta-456",
		MaxBudget:  200.00,
	}

	tradeDeskConfig := ConnectorConfig{
		Type:      TradeDeskSmart,
		APIKey:    "ttd-test-key",
		PartnerID: "ttd-789",
		MaxBudget: 250.00,
	}

	googleConn, _ := NewConnector(googleConfig)
	metaConn, _ := NewConnector(metaConfig)
	tradeDeskConn, _ := NewConnector(tradeDeskConfig)

	googleSmart := googleConn.(*GoogleAdsSmartConnector)
	metaSmart := metaConn.(*MetaSmartConnector)
	tradeDeskSmart := tradeDeskConn.(*TradeDeskSmartConnector)

	// Enable mock mode for all
	googleSmart.MockMode = true
	metaSmart.MockMode = true
	tradeDeskSmart.MockMode = true

	// Connect all
	googleSmart.Connect(ctx)
	metaSmart.Connect(ctx)
	tradeDeskSmart.Connect(ctx)

	log.Printf("✅ All platforms connected")

	// Place bids on each platform
	bidReq := &BidRequest{
		CustomerID:   "MULTI_CUST_001",
		CampaignID:   "multi-campaign",
		PredictedLTV: 1000.00,
		BidAmount:    100.00,
		Explanation:  `{"confidence": 0.90}`,
		Timestamp:    time.Now(),
	}

	log.Printf("\n--- Placing $100 bid on Google Ads ---")
	googleSmart.PlaceBid(ctx, bidReq)

	log.Printf("\n--- Placing $100 bid on Meta ---")
	metaSmart.PlaceBid(ctx, bidReq)

	log.Printf("\n--- Placing $100 bid on Trade Desk ---")
	tradeDeskSmart.PlaceBid(ctx, bidReq)

	// Verify each platform has independent budget tracking
	googleStats := googleSmart.GetBudgetStats()
	metaStats := metaSmart.GetBudgetStats()
	tradeDeskStats := tradeDeskSmart.GetBudgetStats()

	log.Printf("\n🏁 Multi-Platform Final Stats:")
	log.Printf("   Google Ads: $%.2f/$%.2f", googleStats.CurrentSpend, googleStats.MaxBudget)
	log.Printf("   Meta: $%.2f/$%.2f", metaStats.CurrentSpend, metaStats.MaxBudget)
	log.Printf("   Trade Desk: $%.2f/$%.2f", tradeDeskStats.CurrentSpend, tradeDeskStats.MaxBudget)
	log.Printf("   Total Spend: $%.2f", googleStats.CurrentSpend+metaStats.CurrentSpend+tradeDeskStats.CurrentSpend)

	// Close all
	googleSmart.Close()
	metaSmart.Close()
	tradeDeskSmart.Close()

	log.Printf("\n✅ Multi-platform test complete")
}
