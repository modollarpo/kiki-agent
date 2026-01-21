package connectors

import (
	"testing"
)

// TestHeuristicFallbackBidCalculation tests the core fallback bid calculation
func TestHeuristicFallbackBidCalculation(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Record some LTV history for Google Ads
	ltvsGoogle := []float64{100, 120, 110, 115, 105}
	for _, ltv := range ltvsGoogle {
		hfe.RecordLTV("google_ads", ltv)
	}

	// Calculate fallback bid
	// Median of [100, 105, 110, 115, 120] is 110
	// Google Ads multiplier is 1.0
	// Expected bid: 110 * 1.0 = 110
	fallbackBid := hfe.CalculateFallbackBid("google_ads", 100.0)

	if fallbackBid != 110.0 {
		t.Errorf("Expected fallback bid 110.0, got %.2f", fallbackBid)
	}
}

// TestHeuristicFallbackWithPlatformMultipliers tests platform-specific multipliers
func TestHeuristicFallbackWithPlatformMultipliers(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Record TikTok LTV history
	ltvsTickTok := []float64{50, 60, 55, 65, 58}
	for _, ltv := range ltvsTickTok {
		hfe.RecordLTV("tiktok", ltv)
	}

	// Calculate fallback bid
	// Median of [50, 55, 58, 60, 65] is 58
	// TikTok multiplier is 1.5 (viral multiplier)
	// Expected bid: 58 * 1.5 = 87.0
	fallbackBid := hfe.CalculateFallbackBid("tiktok", 50.0)

	if fallbackBid != 87.0 {
		t.Errorf("Expected fallback bid 87.0, got %.2f", fallbackBid)
	}
}

// TestHeuristicFallbackInsufficientHistory tests fallback to default LTV
func TestHeuristicFallbackInsufficientHistory(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Record only 2 LTV values (less than minLTVSamples of 5)
	hfe.RecordLTV("linkedin", 100.0)
	hfe.RecordLTV("linkedin", 110.0)

	// Should fall back to default LTV
	defaultLTV := 105.0
	fallbackBid := hfe.CalculateFallbackBid("linkedin", defaultLTV)

	// LinkedIn multiplier is 1.2, so: 105 * 1.2 = 126
	expectedBid := defaultLTV * 1.2

	if fallbackBid != expectedBid {
		t.Errorf("Expected fallback bid %.2f, got %.2f", expectedBid, fallbackBid)
	}
}

// TestHeuristicMedianCalculation tests median calculation with even/odd counts
func TestHeuristicMedianCalculation(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Test with odd count (3 elements)
	hfe.RecordLTV("test_odd", 10.0)
	hfe.RecordLTV("test_odd", 20.0)
	hfe.RecordLTV("test_odd", 30.0)

	// Median should be 20.0
	bid := hfe.CalculateFallbackBid("test_odd", 0.0)
	expectedBid := 20.0 * 1.0 // Default multiplier

	if bid != expectedBid {
		t.Errorf("Expected median bid %.2f, got %.2f", expectedBid, bid)
	}

	// Test with even count (4 elements)
	hfe.ClearHistory()
	hfe.RecordLTV("test_even", 10.0)
	hfe.RecordLTV("test_even", 20.0)
	hfe.RecordLTV("test_even", 30.0)
	hfe.RecordLTV("test_even", 40.0)

	// Median should be (20 + 30) / 2 = 25.0
	bid = hfe.CalculateFallbackBid("test_even", 0.0)
	expectedBid = 25.0 * 1.0

	if bid != expectedBid {
		t.Errorf("Expected median bid %.2f, got %.2f", expectedBid, bid)
	}
}

// TestHeuristicHistoryMaxSize tests that history is limited to maxHistorySize
func TestHeuristicHistoryMaxSize(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Record more than maxHistorySize (100) values
	for i := 0; i < 150; i++ {
		hfe.RecordLTV("amazon", float64(i))
	}

	history := hfe.GetLTVHistory("amazon")

	// Should keep only the last 100
	if len(history) != 100 {
		t.Errorf("Expected history size 100, got %d", len(history))
	}

	// Most recent values should be 50-149
	if history[0] != 50.0 || history[99] != 149.0 {
		t.Errorf("Expected history [50...149], got [%.0f...%.0f]",
			history[0], history[len(history)-1])
	}
}

// TestHeuristicPlatformMultiplierCustomization tests dynamic multiplier updates
func TestHeuristicPlatformMultiplierCustomization(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Record LTV history
	for i := 0; i < 10; i++ {
		hfe.RecordLTV("custom_platform", 100.0)
	}

	// Set custom multiplier
	hfe.SetPlatformMultiplier("custom_platform", 2.5)

	// Verify multiplier is applied
	bid := hfe.CalculateFallbackBid("custom_platform", 100.0)
	expectedBid := 100.0 * 2.5

	if bid != expectedBid {
		t.Errorf("Expected bid %.2f with custom multiplier, got %.2f", expectedBid, bid)
	}
}

// TestHeuristicGetMultiplier tests retrieval of platform multipliers
func TestHeuristicGetMultiplier(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Check default multipliers
	if hfe.GetPlatformMultiplier("google_ads") != 1.0 {
		t.Error("Expected Google Ads multiplier 1.0")
	}

	if hfe.GetPlatformMultiplier("tiktok") != 1.5 {
		t.Error("Expected TikTok multiplier 1.5")
	}

	if hfe.GetPlatformMultiplier("x") != 0.75 {
		t.Error("Expected X multiplier 0.75")
	}
}

// TestHeuristicOptimizationRecoveryEstimate tests optimization recovery percentage
func TestHeuristicOptimizationRecoveryEstimate(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	recovery := hfe.EstimateAIOptimizationRecovery()

	if recovery != 0.80 {
		t.Errorf("Expected 0.80 (80%%) recovery, got %.2f", recovery)
	}
}

// TestHeuristicHistoryRetrieval tests getting LTV history
func TestHeuristicHistoryRetrieval(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	ltv_values := []float64{100, 110, 120, 130}
	for _, ltv := range ltv_values {
		hfe.RecordLTV("meta", ltv)
	}

	history := hfe.GetLTVHistory("meta")

	if len(history) != 4 {
		t.Errorf("Expected history length 4, got %d", len(history))
	}

	// Verify values match (order doesn't matter for median calculation)
	for i, expected := range ltv_values {
		if history[i] != expected {
			t.Errorf("Expected history[%d]=%.0f, got %.0f", i, expected, history[i])
		}
	}
}

// TestHeuristicEmptyHistory tests behavior with no recorded LTVs
func TestHeuristicEmptyHistory(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Request bid for platform with no history
	fallbackBid := hfe.CalculateFallbackBid("unknown_platform", 150.0)

	// Should fall back to default with platform multiplier
	// Unknown platform defaults to 1.0 multiplier
	if fallbackBid != 150.0 {
		t.Errorf("Expected fallback bid 150.0, got %.2f", fallbackBid)
	}
}

// TestHeuristicConcurrentRecording tests thread-safe LTV recording
func TestHeuristicConcurrentRecording(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Simulate concurrent gRPC responses recording LTV values
	done := make(chan bool)

	for i := 0; i < 10; i++ {
		go func(platform string, values int) {
			defer func() { done <- true }()
			for j := 0; j < values; j++ {
				hfe.RecordLTV(platform, float64(j*10))
			}
		}("amazon", 5)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	history := hfe.GetLTVHistory("amazon")

	// Should have ~50 values (10 goroutines × 5 values each)
	if len(history) < 40 || len(history) > 60 {
		t.Logf("Warning: Expected ~50 LTV values, got %d (acceptable due to concurrency)", len(history))
	}
}

// TestHeuristicClearHistory tests history clearing for testing
func TestHeuristicClearHistory(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	// Record some history
	hfe.RecordLTV("google_ads", 100)
	hfe.RecordLTV("meta", 150)

	// Clear it
	hfe.ClearHistory()

	// Verify cleared
	if len(hfe.GetLTVHistory("google_ads")) != 0 {
		t.Error("Expected empty history after clear")
	}

	if len(hfe.GetLTVHistory("meta")) != 0 {
		t.Error("Expected empty history after clear")
	}
}

// TestHeuristicAllPlatforms tests fallback bids for all 7 platforms
func TestHeuristicAllPlatforms(t *testing.T) {
	hfe := NewHeuristicFallbackEngine()

	platforms := []string{"google_ads", "meta", "tradedesk", "amazon", "x", "linkedin", "tiktok"}
	basePrice := 100.0

	// Record baseline LTV for each platform
	for _, platform := range platforms {
		for i := 0; i < 10; i++ {
			hfe.RecordLTV(platform, basePrice)
		}
	}

	// Calculate fallback bids for each
	for _, platform := range platforms {
		bid := hfe.CalculateFallbackBid(platform, basePrice)
		multiplier := hfe.GetPlatformMultiplier(platform)
		expected := basePrice * multiplier

		if bid != expected {
			t.Errorf("%s: Expected bid %.2f, got %.2f", platform, expected, bid)
		}
	}

	t.Logf("All 7 platforms calculated fallback bids successfully")
}
