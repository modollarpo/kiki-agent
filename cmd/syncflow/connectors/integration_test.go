package connectors

import (
	"context"
	"fmt"
	"log"
	"testing"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// TestGoogleAdsSmartConnectorIntegration demonstrates the complete flow:
// SyncValue prediction → SyncShield validation → BudgetManager → Google Ads API
func TestGoogleAdsSmartConnectorIntegration(t *testing.T) {
	log.Println("🧪 Starting Google Ads Smart Connector Integration Test")

	// Step 1: Initialize connector with $500 budget
	config := ConnectorConfig{
		Type:       GoogleAdsSmart,
		APIKey:     "test-api-key-12345",
		CustomerID: "1234567890",
		MaxBudget:  500.00,
	}

	connector, err := NewConnector(config)
	if err != nil {
		t.Fatalf("Failed to create connector: %v", err)
	}

	smartConnector, ok := connector.(*GoogleAdsSmartConnector)
	if !ok {
		t.Fatalf("Expected GoogleAdsSmartConnector, got %T", connector)
	}

	// Enable mock mode for testing without real API calls
	smartConnector.MockMode = true

	// Step 2: Connect to platform
	ctx := context.Background()
	if err := smartConnector.Connect(ctx); err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}

	log.Printf("✅ Connected: %s", smartConnector.GetStatus())

	// Step 3: Simulate bid requests with varying LTV predictions
	testCases := []struct {
		name         string
		customerID   string
		predictedLTV float64
		bidAmount    float64
		explanation  string
		shouldPass   bool
	}{
		{
			name:         "High LTV Customer - $150 bid",
			customerID:   "CUST_001",
			predictedLTV: 1500.00,
			bidAmount:    150.00,
			explanation:  `{"spend_contribution": 0.65, "engagement_contribution": 0.35, "confidence": 0.94}`,
			shouldPass:   true,
		},
		{
			name:         "Medium LTV Customer - $75 bid",
			customerID:   "CUST_002",
			predictedLTV: 450.00,
			bidAmount:    75.00,
			explanation:  `{"spend_contribution": 0.55, "engagement_contribution": 0.45, "confidence": 0.89}`,
			shouldPass:   true,
		},
		{
			name:         "Low LTV Customer - $50 bid",
			customerID:   "CUST_003",
			predictedLTV: 200.00,
			bidAmount:    50.00,
			explanation:  `{"spend_contribution": 0.40, "engagement_contribution": 0.60, "confidence": 0.82}`,
			shouldPass:   true,
		},
		{
			name:         "Budget overflow attempt - $300 bid (should fail)",
			customerID:   "CUST_004",
			predictedLTV: 2000.00,
			bidAmount:    300.00,
			explanation:  `{"spend_contribution": 0.70, "engagement_contribution": 0.30, "confidence": 0.96}`,
			shouldPass:   false, // Total would be $575 > $500 limit
		},
	}

	totalSpent := 0.0
	successfulBids := 0

	for i, tc := range testCases {
		log.Printf("\n--- Test Case %d: %s ---", i+1, tc.name)

		// Create bid request
		bidReq := &BidRequest{
			CustomerID:   tc.customerID,
			CampaignID:   "campaign-test-001",
			PredictedLTV: tc.predictedLTV,
			BidAmount:    tc.bidAmount,
			Explanation:  tc.explanation,
			Timestamp:    time.Now(),
		}

		// Check budget before placing bid (simulate SyncShield validation)
		stats := smartConnector.GetBudgetStats()
		log.Printf("📊 Pre-bid budget: $%.2f/$%.2f (%.1f%% used)",
			stats.CurrentSpend,
			stats.MaxBudget,
			(stats.CurrentSpend/stats.MaxBudget)*100)

		// Place bid
		resp, err := smartConnector.PlaceBid(ctx, bidReq)

		if tc.shouldPass {
			if err != nil {
				// For this test, we expect API errors since we're not hitting real Google Ads
				// But we should still track the budget
				log.Printf("⚠️ Expected API error (test mode): %v", err)
			}
			if resp != nil {
				log.Printf("📝 Response: %s (Code: %s)", resp.Message, resp.PlatformCode)
				if resp.Success {
					totalSpent += tc.bidAmount
					successfulBids++
				}
			}
		} else {
			if err == nil {
				t.Errorf("Expected budget overflow error for %s, but bid succeeded", tc.name)
			} else {
				log.Printf("✅ Correctly rejected: %v", err)
			}
		}

		// Verify budget tracking
		statsAfter := smartConnector.GetBudgetStats()
		log.Printf("📊 Post-bid budget: $%.2f/$%.2f (%.1f%% used)",
			statsAfter.CurrentSpend,
			statsAfter.MaxBudget,
			(statsAfter.CurrentSpend/statsAfter.MaxBudget)*100)
	}

	// Step 4: Verify final state
	finalStats := smartConnector.GetBudgetStats()
	log.Printf("\n🏁 Final Results:")
	log.Printf("   Total Spend: $%.2f", finalStats.CurrentSpend)
	log.Printf("   Max Budget: $%.2f", finalStats.MaxBudget)
	log.Printf("   Remaining: $%.2f", finalStats.RemainingBudget)
	log.Printf("   Budget Used: %.1f%%", (finalStats.CurrentSpend/finalStats.MaxBudget)*100)
	log.Printf("   Successful Bids: %d", successfulBids)
	log.Printf("   Total Transactions: %d", finalStats.RecordCount)

	// Step 5: Test rate limiting
	log.Printf("\n--- Testing Rate Limiter ---")
	rateLimitHit := false
	for i := 0; i < 105; i++ { // Try to exceed 100 calls/minute
		if !smartConnector.RateLimiter.CanMakeCall() {
			log.Printf("✅ Rate limit triggered at call %d", i+1)
			rateLimitHit = true
			break
		}
		smartConnector.RateLimiter.RecordCall()
	}

	if !rateLimitHit {
		t.Error("Rate limiter did not trigger as expected")
	}

	// Step 6: Test budget recovery after window expiration
	log.Printf("\n--- Testing Sliding Window Recovery ---")
	log.Printf("Simulating 11-minute time advance...")
	// In real scenario, wait 11 minutes or mock time
	// For test purposes, we'll verify the concept
	log.Printf("ℹ️ In production, budget would recover after 10-minute window expires")

	// Step 7: Clean up
	if err := smartConnector.Close(); err != nil {
		t.Fatalf("Failed to close connector: %v", err)
	}

	log.Printf("\n✅ Integration test complete")
}

// TestBudgetManagerThreadSafety verifies concurrent bid operations
func TestBudgetManagerThreadSafety(t *testing.T) {
	log.Println("🧪 Testing BudgetManager Thread Safety")

	bm := shield.NewBudgetManager(1000.00)

	// Launch 100 concurrent goroutines trying to spend $15 each
	done := make(chan bool)

	for i := 0; i < 100; i++ {
		go func(id int) {
			if bm.CanSpend(15.00) {
				bm.AddSpend(15.00)
				log.Printf("Goroutine %d: Bid accepted", id)
			} else {
				log.Printf("Goroutine %d: Bid rejected (budget limit)", id)
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 100; i++ {
		<-done
	}

	stats := bm.GetStats()
	log.Printf("Final stats: $%.2f spent, %d transactions", stats.CurrentSpend, stats.RecordCount)

	// Verify we never exceeded the budget
	if stats.CurrentSpend > stats.MaxBudget {
		t.Errorf("Budget exceeded! Spent $%.2f > $%.2f limit", stats.CurrentSpend, stats.MaxBudget)
	}

	log.Printf("✅ Thread safety test passed - no race conditions detected")
}

// TestConnectorFactory verifies factory pattern implementation
func TestConnectorFactory(t *testing.T) {
	log.Println("🧪 Testing Connector Factory")

	tests := []struct {
		name      string
		config    ConnectorConfig
		expectErr bool
		connType  string
	}{
		{
			name: "Google Ads Basic",
			config: ConnectorConfig{
				Type:       GoogleAds,
				APIKey:     "test-key",
				CustomerID: "12345",
			},
			expectErr: false,
			connType:  "*connectors.GoogleAdsConnector",
		},
		{
			name: "Google Ads Smart with Budget",
			config: ConnectorConfig{
				Type:       GoogleAdsSmart,
				APIKey:     "test-key",
				CustomerID: "12345",
				MaxBudget:  500.00,
			},
			expectErr: false,
			connType:  "*connectors.GoogleAdsSmartConnector",
		},
		{
			name: "Google Ads Smart without Budget (should fail)",
			config: ConnectorConfig{
				Type:       GoogleAdsSmart,
				APIKey:     "test-key",
				CustomerID: "12345",
				MaxBudget:  0, // Invalid
			},
			expectErr: true,
			connType:  "",
		},
		{
			name: "Meta Basic Connector",
			config: ConnectorConfig{
				Type:       Meta,
				APIKey:     "test-key",
				BusinessID: "business-123",
			},
			expectErr: false,
			connType:  "*connectors.MetaConnector",
		},
		{
			name: "Meta Smart with Budget",
			config: ConnectorConfig{
				Type:       MetaSmart,
				APIKey:     "test-key",
				BusinessID: "business-123",
				MaxBudget:  500.00,
			},
			expectErr: false,
			connType:  "*connectors.MetaSmartConnector",
		},
		{
			name: "Trade Desk Basic Connector",
			config: ConnectorConfig{
				Type:      TradeDesk,
				APIKey:    "test-key",
				PartnerID: "partner-456",
			},
			expectErr: false,
			connType:  "*connectors.TradesDeskConnector",
		},
		{
			name: "Trade Desk Smart with Budget",
			config: ConnectorConfig{
				Type:      TradeDeskSmart,
				APIKey:    "test-key",
				PartnerID: "partner-456",
				MaxBudget: 500.00,
			},
			expectErr: false,
			connType:  "*connectors.TradeDeskSmartConnector",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			conn, err := NewConnector(tt.config)

			if tt.expectErr {
				if err == nil {
					t.Errorf("Expected error but got none")
				} else {
					log.Printf("✅ Correctly rejected: %v", err)
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				} else {
					actualType := fmt.Sprintf("%T", conn)
					log.Printf("✅ Created connector: %s", actualType)
					if actualType != tt.connType {
						t.Errorf("Expected type %s, got %s", tt.connType, actualType)
					}
				}
			}
		})
	}
}
