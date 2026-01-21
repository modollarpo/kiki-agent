package connectors

import (
	"context"
	"testing"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// Circuit Breaker Integration Tests
//
// This file contains integration tests validating the circuit breaker's resilience behavior
// under realistic failure scenarios. The tests cover:
//
// 1. Failure Detection: Verify breaker opens after threshold (3 consecutive failures)
// 2. Fallback Calculation: Validate heuristic bids use median LTV × platform multiplier
// 3. Half-Open Recovery: Test state machine transitions OPEN → HALF_OPEN → CLOSED
// 4. Latency Protection: Ensure slow calls (>500ms) trigger circuit opening
// 5. Concurrency Safety: Verify thread-safe operation under concurrent load
// 6. Platform Isolation: Confirm each connector has independent circuit breaker
// 7. Fallback Defaults: Test fallback works with insufficient LTV history
//
// Test Execution:
//   - Quick run (skip slow tests): go test -short -run TestCircuitBreaker
//   - Full run (includes 31s timeout test): go test -run TestCircuitBreaker
//
// All tests pass as of 2026-01-18

// TestCircuitBreakerFailureScenario validates that the circuit breaker opens after 3 consecutive failures
func TestCircuitBreakerFailureScenario(t *testing.T) {
	connector := NewGoogleAdsSmartConnector("test-key", "test-customer", 1000.0)
	connector.MockMode = true
	connector.Connect(context.Background())

	// Simulate 3 consecutive failures by recording them directly
	breaker := connector.CircuitBreaker

	// Record 3 failures to trigger OPEN state
	for i := 0; i < 3; i++ {
		breaker.RecordFailure(100 * time.Millisecond)
	}

	// Verify breaker is now OPEN
	if breaker.CanExecute() {
		t.Errorf("Expected circuit breaker to be OPEN after 3 failures, but CanExecute() returned true")
	}

	state := breaker.GetState()
	if state != shield.OPEN {
		t.Errorf("Expected state OPEN, got %v", state)
	}

	stats := breaker.GetStats()
	if stats.FailureCount != 3 {
		t.Errorf("Expected 3 failures, got %d", stats.FailureCount)
	}

	t.Logf("✅ Circuit breaker opened after %d failures", stats.FailureCount)
}

// TestCircuitBreakerFallbackBidCalculation validates heuristic fallback when breaker is open
func TestCircuitBreakerFallbackBidCalculation(t *testing.T) {
	connector := NewGoogleAdsSmartConnector("test-key", "test-customer", 1000.0)
	connector.MockMode = true
	connector.Connect(context.Background())

	// Build LTV history
	connector.FallbackEngine.RecordLTV("google_ads", 100.0)
	connector.FallbackEngine.RecordLTV("google_ads", 150.0)
	connector.FallbackEngine.RecordLTV("google_ads", 200.0)

	// Force breaker OPEN
	for i := 0; i < 3; i++ {
		connector.CircuitBreaker.RecordFailure(100 * time.Millisecond)
	}

	// Place bid - should use fallback
	req := &BidRequest{
		CustomerID:   "CUST_001",
		CampaignID:   "campaign-123",
		PredictedLTV: 175.0,
		BidAmount:    175.0, // This should be ignored; fallback will use median LTV
		Explanation:  `{"confidence": 0.95}`,
		Timestamp:    time.Now(),
	}

	resp, err := connector.PlaceBid(context.Background(), req)
	if err != nil {
		t.Fatalf("PlaceBid failed: %v", err)
	}

	if !resp.Success {
		t.Errorf("Expected successful bid (using fallback), got: %s", resp.Message)
	}

	// Check fallback was used
	stats := connector.CircuitBreaker.GetStats()
	if stats.FallbackActivations < 1 {
		t.Errorf("Expected at least 1 fallback, got %d", stats.FallbackActivations)
	}

	// Median calculation: For [100, 150, 200], median is average of middle values
	// When the bid is placed, the PlaceBid itself records another LTV (175.0)
	// So history becomes [100, 150, 200, 175], and median is (150+175)/2 = 162.5
	// google_ads multiplier = 1.0, so fallback = 162.5
	expectedFallbackBid := 162.50
	budgetStats := connector.GetBudgetStats()

	// Budget should reflect fallback bid, not AI bid
	if budgetStats.CurrentSpend != expectedFallbackBid {
		t.Errorf("Expected spend of $%.2f (fallback), got $%.2f", expectedFallbackBid, budgetStats.CurrentSpend)
	}

	t.Logf("✅ Fallback bid calculated correctly: $%.2f (median LTV × 1.0)", budgetStats.CurrentSpend)
}

// TestCircuitBreakerHalfOpenRecovery validates recovery from OPEN to CLOSED via HALF_OPEN
// Note: This test uses the real 30s timeout, so it takes 31+ seconds to complete.
// To skip this slow test during quick runs, use: go test -short
func TestCircuitBreakerHalfOpenRecovery(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping slow test in short mode (31+ second wait)")
	}

	connector := NewGoogleAdsSmartConnector("test-key", "test-customer", 1000.0)
	connector.MockMode = true
	connector.Connect(context.Background())

	breaker := connector.CircuitBreaker

	// Force OPEN state
	for i := 0; i < 3; i++ {
		breaker.RecordFailure(100 * time.Millisecond)
	}

	if breaker.GetState() != shield.OPEN {
		t.Fatalf("Expected OPEN state after failures")
	}

	// Wait for reset timeout (30s default, but we can manipulate it for testing)
	// For this test, we'll manually transition to HALF_OPEN by waiting
	t.Logf("Waiting for reset timeout to transition to HALF_OPEN...")
	time.Sleep(31 * time.Second)

	// First call after timeout should transition to HALF_OPEN
	canExecute := breaker.CanExecute()
	state := breaker.GetState()

	if state != shield.HALF_OPEN {
		t.Errorf("Expected HALF_OPEN state after timeout, got %v", state)
	}

	if !canExecute {
		t.Errorf("Expected CanExecute() = true in HALF_OPEN state")
	}

	t.Logf("✅ Transitioned to HALF_OPEN after reset timeout")

	// Record 2 consecutive successes to transition to CLOSED
	breaker.RecordSuccess(50 * time.Millisecond)
	breaker.RecordSuccess(50 * time.Millisecond)

	state = breaker.GetState()
	if state != shield.CLOSED {
		t.Errorf("Expected CLOSED state after 2 successes in HALF_OPEN, got %v", state)
	}

	stats := breaker.GetStats()
	if stats.SuccessfulRequests < 2 {
		t.Errorf("Expected at least 2 successes, got %d", stats.SuccessfulRequests)
	}

	t.Logf("✅ Recovered to CLOSED state after %d consecutive successes", stats.SuccessfulRequests)
}

// TestCircuitBreakerLatencyThreshold validates that slow calls trigger OPEN state
func TestCircuitBreakerLatencyThreshold(t *testing.T) {
	connector := NewGoogleAdsSmartConnector("test-key", "test-customer", 1000.0)
	connector.MockMode = true
	connector.Connect(context.Background())

	breaker := connector.CircuitBreaker

	// Record 3 slow calls (>500ms threshold)
	// Note: RecordFailure with latency > latencyThreshold counts as 2 failures (one for error, one for latency)
	// So 3 calls × 2 failures = 6 total failures
	for i := 0; i < 3; i++ {
		breaker.RecordFailure(600 * time.Millisecond) // Above 500ms threshold
	}

	state := breaker.GetState()
	if state != shield.OPEN {
		t.Errorf("Expected OPEN state after 3 slow calls, got %v", state)
	}

	stats := breaker.GetStats()
	// Each slow call increments failureCount twice (once for failure, once for latency)
	expectedFailures := 6
	if stats.FailureCount != expectedFailures {
		t.Errorf("Expected %d failures (3 calls × 2 per slow call), got %d", expectedFailures, stats.FailureCount)
	}

	t.Logf("✅ Circuit breaker opened after %d slow calls (>500ms)", stats.FailureCount)
}

// TestCircuitBreakerConcurrentFailures validates thread-safety during concurrent failures
func TestCircuitBreakerConcurrentFailures(t *testing.T) {
	connector := NewGoogleAdsSmartConnector("test-key", "test-customer", 5000.0)
	connector.MockMode = true
	connector.Connect(context.Background())

	breaker := connector.CircuitBreaker

	// Simulate 10 concurrent requests, mix of success and failure
	done := make(chan bool, 10)

	for i := 0; i < 10; i++ {
		go func(idx int) {
			defer func() { done <- true }()

			if idx%2 == 0 {
				// Even: success
				breaker.RecordSuccess(50 * time.Millisecond)
			} else {
				// Odd: failure
				breaker.RecordFailure(100 * time.Millisecond)
			}
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	stats := breaker.GetStats()
	totalCalls := stats.SuccessfulRequests + stats.FailedRequests

	if totalCalls != 10 {
		t.Errorf("Expected 10 total calls, got %d", totalCalls)
	}

	t.Logf("✅ Concurrent calls handled safely: %d successes, %d failures",
		stats.SuccessfulRequests, stats.FailedRequests)
}

// TestCircuitBreakerMultiPlatformIsolation validates that each platform has independent circuit breaker
func TestCircuitBreakerMultiPlatformIsolation(t *testing.T) {
	googleAds := NewGoogleAdsSmartConnector("ga-key", "ga-customer", 1000.0)
	meta := NewMetaSmartConnector("meta-token", "meta-business", 1000.0)
	tradeDesk := NewTradeDeskSmartConnector("ttd-key", "ttd-partner", 1000.0)

	// Force Google Ads breaker OPEN
	for i := 0; i < 3; i++ {
		googleAds.CircuitBreaker.RecordFailure(100 * time.Millisecond)
	}

	// Meta and TradeDesk should still be CLOSED
	if googleAds.CircuitBreaker.GetState() != shield.OPEN {
		t.Errorf("Expected Google Ads breaker to be OPEN")
	}

	if meta.CircuitBreaker.GetState() != shield.CLOSED {
		t.Errorf("Expected Meta breaker to remain CLOSED")
	}

	if tradeDesk.CircuitBreaker.GetState() != shield.CLOSED {
		t.Errorf("Expected TradeDesk breaker to remain CLOSED")
	}

	t.Logf("✅ Platform circuit breakers are independent")
	t.Logf("   Google Ads: %v", googleAds.CircuitBreaker.GetState())
	t.Logf("   Meta: %v", meta.CircuitBreaker.GetState())
	t.Logf("   TradeDesk: %v", tradeDesk.CircuitBreaker.GetState())
}

// TestCircuitBreakerFallbackWithInsufficientHistory validates fallback uses default LTV when history is empty
func TestCircuitBreakerFallbackWithInsufficientHistory(t *testing.T) {
	connector := NewGoogleAdsSmartConnector("test-key", "test-customer", 1000.0)
	connector.MockMode = true
	connector.Connect(context.Background())

	// Force breaker OPEN without building LTV history
	for i := 0; i < 3; i++ {
		connector.CircuitBreaker.RecordFailure(100 * time.Millisecond)
	}

	// Place bid with no history - should use default LTV
	req := &BidRequest{
		CustomerID:   "CUST_001",
		CampaignID:   "campaign-123",
		PredictedLTV: 250.0, // This is the default/incoming LTV
		BidAmount:    250.0,
		Explanation:  `{"confidence": 0.90}`,
		Timestamp:    time.Now(),
	}

	resp, err := connector.PlaceBid(context.Background(), req)
	if err != nil {
		t.Fatalf("PlaceBid failed: %v", err)
	}

	if !resp.Success {
		t.Errorf("Expected successful bid (using fallback with default LTV)")
	}

	// Fallback should use default LTV (250.0) × multiplier (1.0) = 250.0
	budgetStats := connector.GetBudgetStats()
	expectedSpend := 250.0

	if budgetStats.CurrentSpend != expectedSpend {
		t.Errorf("Expected spend of $%.2f (default LTV), got $%.2f", expectedSpend, budgetStats.CurrentSpend)
	}

	t.Logf("✅ Fallback with no history uses default LTV: $%.2f", budgetStats.CurrentSpend)
}
