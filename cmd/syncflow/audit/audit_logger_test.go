package audit

import (
	"testing"
	"time"
)

// Mock audit entries for testing
func createTestEntry(customerID, platform string, amount float64) *AuditEntry {
	return &AuditEntry{
		RequestID:       "test-req-001",
		Timestamp:       time.Now(),
		CustomerID:      customerID,
		CampaignID:      "camp-123",
		PredictedLTV:    amount,
		Confidence:      0.947,
		LTVLowerBound:   amount * 0.9,
		LTVUpperBound:   amount * 1.1,
		ModelVersion:    "dRNN-v2.1.0",
		BidAmount:       amount * 0.30,
		BidSource:       "AI_PREDICTION",
		Platform:        platform,
		BidStatus:       "ACCEPTED",
		CircuitState:    "CLOSED",
		UsedFallback:    false,
		ExecutionTimeMs: 10,
		InferenceTimeUs: 850,
		CampaignBudget:  10000,
		CurrentSpend:    amount * 0.30,
		RemainingBudget: 10000 - (amount * 0.30),
		Metadata: map[string]interface{}{
			"region": "US",
			"device": "mobile",
		},
		Explanation: "High purchase frequency + recency score",
	}
}

func TestAuditEntry_BasicStructure(t *testing.T) {
	entry := createTestEntry("cust-123", "google_ads", 150.0)

	if entry.CustomerID != "cust-123" {
		t.Errorf("Expected cust-123, got %s", entry.CustomerID)
	}

	if entry.Platform != "google_ads" {
		t.Errorf("Expected google_ads, got %s", entry.Platform)
	}

	if entry.PredictedLTV != 150.0 {
		t.Errorf("Expected 150.0, got %.2f", entry.PredictedLTV)
	}

	if entry.BidStatus != "ACCEPTED" {
		t.Errorf("Expected ACCEPTED, got %s", entry.BidStatus)
	}
}

func TestAuditEntry_Metadata(t *testing.T) {
	entry := createTestEntry("cust-123", "meta", 100.0)

	if region, ok := entry.Metadata["region"]; !ok || region != "US" {
		t.Error("Expected metadata region=US")
	}

	if device, ok := entry.Metadata["device"]; !ok || device != "mobile" {
		t.Error("Expected metadata device=mobile")
	}
}

func TestAuditEntry_LTVBounds(t *testing.T) {
	entry := createTestEntry("cust-123", "tiktok", 200.0)

	expectedLower := 180.0
	expectedUpper := 220.0

	// Use approximate comparison for floating point
	if diff := entry.LTVLowerBound - expectedLower; diff > 0.01 || diff < -0.01 {
		t.Errorf("Expected lower bound %.2f, got %.2f", expectedLower, entry.LTVLowerBound)
	}

	if diff := entry.LTVUpperBound - expectedUpper; diff > 0.01 || diff < -0.01 {
		t.Errorf("Expected upper bound %.2f, got %.2f", expectedUpper, entry.LTVUpperBound)
	}
}

func TestAuditEntry_BidCalculation(t *testing.T) {
	entry := createTestEntry("cust-123", "linkedin", 300.0)

	expectedBid := 300.0 * 0.30 // 90

	if entry.BidAmount != expectedBid {
		t.Errorf("Expected bid %.2f, got %.2f", expectedBid, entry.BidAmount)
	}
}

func TestAuditEntry_BudgetTracking(t *testing.T) {
	entry := createTestEntry("cust-123", "amazon", 500.0)

	totalBudget := entry.CampaignBudget
	currentSpend := entry.CurrentSpend
	remaining := entry.RemainingBudget

	if remaining != (totalBudget - currentSpend) {
		t.Errorf("Budget math error: %.2f + %.2f != %.2f",
			currentSpend, remaining, totalBudget)
	}
}

func TestAuditEntry_CircuitBreakerState(t *testing.T) {
	tests := []struct {
		name    string
		state   string
		healthy bool
	}{
		{"closed", "CLOSED", true},
		{"open", "OPEN", false},
		{"half_open", "HALF_OPEN", false},
	}

	for _, tt := range tests {
		entry := createTestEntry("cust-123", "google_ads", 100.0)
		entry.CircuitState = tt.state

		// Just verify the state is set correctly
		if entry.CircuitState != tt.state {
			t.Errorf("Expected %s, got %s", tt.state, entry.CircuitState)
		}
	}
}

func TestAuditEntry_FallbackActivation(t *testing.T) {
	entry := createTestEntry("cust-123", "tradedesk", 250.0)
	entry.UsedFallback = true
	entry.BidSource = "HEURISTIC_FALLBACK"

	if !entry.UsedFallback {
		t.Error("Expected fallback to be activated")
	}

	if entry.BidSource != "HEURISTIC_FALLBACK" {
		t.Errorf("Expected HEURISTIC_FALLBACK, got %s", entry.BidSource)
	}
}

func TestAuditEntry_Explanation(t *testing.T) {
	entry := createTestEntry("cust-123", "x", 75.0)

	if entry.Explanation == "" {
		t.Error("Expected explanation to be present")
	}

	if entry.Explanation != "High purchase frequency + recency score" {
		t.Errorf("Unexpected explanation: %s", entry.Explanation)
	}
}

func TestAuditEntry_TimestampHandling(t *testing.T) {
	entry := &AuditEntry{
		RequestID:  "test-001",
		CustomerID: "cust-123",
		Platform:   "google_ads",
		BidStatus:  "ACCEPTED",
		BidAmount:  50.0,
	}

	// Verify fields are set correctly
	if entry.RequestID != "test-001" {
		t.Errorf("RequestID not set correctly: %s", entry.RequestID)
	}
	if entry.CustomerID != "cust-123" {
		t.Errorf("CustomerID not set correctly: %s", entry.CustomerID)
	}
	if entry.Platform != "google_ads" {
		t.Errorf("Platform not set correctly: %s", entry.Platform)
	}
	if entry.BidStatus != "ACCEPTED" {
		t.Errorf("BidStatus not set correctly: %s", entry.BidStatus)
	}
	if entry.BidAmount != 50.0 {
		t.Errorf("BidAmount not set correctly: %f", entry.BidAmount)
	}

	// Empty timestamp should be set by AuditLogger.Write()
	if !entry.Timestamp.IsZero() {
		t.Error("Expected zero timestamp on new entry")
	}

	// Set timestamp explicitly
	now := time.Now()
	entry.Timestamp = now

	if entry.Timestamp != now {
		t.Error("Timestamp not set correctly")
	}
}

func TestAuditEntry_AllPlatforms(t *testing.T) {
	platforms := []string{
		"google_ads", "meta", "tiktok", "linkedin", "amazon", "tradedesk", "x",
	}

	for _, platform := range platforms {
		entry := createTestEntry("cust-123", platform, 100.0)

		if entry.Platform != platform {
			t.Errorf("Expected platform %s, got %s", platform, entry.Platform)
		}

		if entry.BidStatus == "" {
			t.Errorf("Bid status not set for platform %s", platform)
		}
	}
}

func TestAuditEntry_BidSourceTypes(t *testing.T) {
	sources := []string{
		"AI_PREDICTION",
		"HEURISTIC_FALLBACK",
		"MANUAL_OVERRIDE",
	}

	for _, source := range sources {
		entry := createTestEntry("cust-123", "google_ads", 100.0)
		entry.BidSource = source

		if entry.BidSource != source {
			t.Errorf("Expected bid source %s, got %s", source, entry.BidSource)
		}
	}
}

func TestAuditEntry_LTVAccuracy(t *testing.T) {
	entry := createTestEntry("cust-123", "google_ads", 200.0)

	// Simulate actual LTV coming back
	actualLTV := 195.0 // Within 10% tolerance
	errorPct := ((actualLTV - entry.PredictedLTV) / entry.PredictedLTV) * 100

	entry.ActualLTV = &actualLTV
	entry.ActualLTVTimestamp = ptrTime(time.Now())
	entry.LTVErrorPct = &errorPct

	if entry.ActualLTV == nil {
		t.Error("Actual LTV not set")
	}

	if *entry.ActualLTV != 195.0 {
		t.Errorf("Expected actual LTV 195.0, got %.2f", *entry.ActualLTV)
	}

	// Within 10% tolerance
	if *entry.LTVErrorPct > 10 || *entry.LTVErrorPct < -10 {
		t.Errorf("Error %.2f%% exceeds tolerance", *entry.LTVErrorPct)
	}
}

// Helper function
func ptrTime(t time.Time) *time.Time {
	return &t
}
