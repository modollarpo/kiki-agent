package budget

import (
	"testing"
	"time"
)

func TestSlidingWindowBudget_BasicSpend(t *testing.T) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000.0)

	// Record a spend
	err := budgeter.RecordSpend(100.0, "google_ads", "req-001")
	if err != nil {
		t.Fatalf("Expected no error, got: %v", err)
	}

	// Check current spend
	currentSpend := budgeter.GetCurrentSpend()
	if currentSpend != 100.0 {
		t.Errorf("Expected current spend 100.0, got: %.2f", currentSpend)
	}
}

func TestSlidingWindowBudget_BurstLimit(t *testing.T) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000.0)

	// Fill up to 900
	err := budgeter.RecordSpend(900.0, "google_ads", "req-001")
	if err != nil {
		t.Fatalf("Expected no error, got: %v", err)
	}

	// Should succeed (within limit)
	err = budgeter.RecordSpend(50.0, "meta", "req-002")
	if err != nil {
		t.Errorf("Expected no error, got: %v", err)
	}

	// Should fail (exceeds limit)
	err = budgeter.RecordSpend(100.0, "tiktok", "req-003")
	if err == nil {
		t.Error("Expected budget exceeded error, got nil")
	}

	// Verify error type
	if _, ok := err.(*BudgetExceededError); !ok {
		t.Errorf("Expected BudgetExceededError, got: %T", err)
	}
}

func TestSlidingWindowBudget_CanSpend(t *testing.T) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000.0)

	// Record 800
	budgeter.RecordSpend(800.0, "google_ads", "req-001")

	// Should be able to spend 150
	if !budgeter.CanSpend(150.0) {
		t.Error("Expected CanSpend(150.0) to be true")
	}

	// Should NOT be able to spend 250
	if budgeter.CanSpend(250.0) {
		t.Error("Expected CanSpend(250.0) to be false")
	}
}

func TestSlidingWindowBudget_WindowEviction(t *testing.T) {
	// Short window for testing: 2 seconds
	budgeter := NewSlidingWindowBudget(2*time.Second, 1000.0)

	// Record a spend
	budgeter.RecordSpend(500.0, "google_ads", "req-001")

	// Immediately check (should be 500)
	if budgeter.GetCurrentSpend() != 500.0 {
		t.Errorf("Expected 500.0, got: %.2f", budgeter.GetCurrentSpend())
	}

	// Wait 3 seconds (beyond window)
	time.Sleep(3 * time.Second)

	// Record another spend (should evict old event)
	budgeter.RecordSpend(200.0, "meta", "req-002")

	// Current spend should be 200 (old event evicted)
	currentSpend := budgeter.GetCurrentSpend()
	if currentSpend != 200.0 {
		t.Errorf("Expected 200.0 (old event evicted), got: %.2f", currentSpend)
	}
}

func TestSlidingWindowBudget_ConcurrentAccess(t *testing.T) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 10000.0)

	// Simulate concurrent bids
	done := make(chan bool)
	for i := 0; i < 100; i++ {
		go func(id int) {
			budgeter.RecordSpend(50.0, "google_ads", "concurrent")
			budgeter.CanSpend(100.0)
			budgeter.GetCurrentSpend()
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 100; i++ {
		<-done
	}

	// Total spend should be 100 * 50 = 5000
	currentSpend := budgeter.GetCurrentSpend()
	if currentSpend != 5000.0 {
		t.Errorf("Expected 5000.0, got: %.2f", currentSpend)
	}
}

func TestSlidingWindowBudget_GetBudgetStatus(t *testing.T) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000.0)

	budgeter.RecordSpend(600.0, "google_ads", "req-001")

	status := budgeter.GetBudgetStatus()

	if status.TotalBudget != 1000.0 {
		t.Errorf("Expected TotalBudget 1000.0, got: %.2f", status.TotalBudget)
	}

	if status.CurrentSpend != 600.0 {
		t.Errorf("Expected CurrentSpend 600.0, got: %.2f", status.CurrentSpend)
	}

	if status.RemainingBudget != 400.0 {
		t.Errorf("Expected RemainingBudget 400.0, got: %.2f", status.RemainingBudget)
	}

	if status.UtilizationPct != 60.0 {
		t.Errorf("Expected UtilizationPct 60.0, got: %.2f", status.UtilizationPct)
	}

	if status.BudgetExceeded {
		t.Error("Expected BudgetExceeded to be false")
	}

	// Calculate spend rate (600 / 10 minutes = 60 per minute)
	expectedRate := 60.0
	if status.SpendRatePerMin != expectedRate {
		t.Errorf("Expected SpendRatePerMin %.2f, got: %.2f", expectedRate, status.SpendRatePerMin)
	}
}

func TestSlidingWindowBudget_GetSpendByPlatform(t *testing.T) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000.0)

	budgeter.RecordSpend(300.0, "google_ads", "req-001")
	budgeter.RecordSpend(200.0, "meta", "req-002")
	budgeter.RecordSpend(150.0, "google_ads", "req-003")

	spendByPlatform := budgeter.GetSpendByPlatform()

	if spendByPlatform["google_ads"] != 450.0 {
		t.Errorf("Expected google_ads 450.0, got: %.2f", spendByPlatform["google_ads"])
	}

	if spendByPlatform["meta"] != 200.0 {
		t.Errorf("Expected meta 200.0, got: %.2f", spendByPlatform["meta"])
	}
}

func TestSlidingWindowBudget_Reset(t *testing.T) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000.0)

	budgeter.RecordSpend(500.0, "google_ads", "req-001")

	// Current spend should be 500
	if budgeter.GetCurrentSpend() != 500.0 {
		t.Errorf("Expected 500.0, got: %.2f", budgeter.GetCurrentSpend())
	}

	// Reset
	budgeter.Reset()

	// Current spend should be 0
	if budgeter.GetCurrentSpend() != 0.0 {
		t.Errorf("Expected 0.0 after reset, got: %.2f", budgeter.GetCurrentSpend())
	}
}

// Benchmark concurrent access
func BenchmarkSlidingWindowBudget_ConcurrentRecordSpend(b *testing.B) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000000.0)

	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			budgeter.RecordSpend(10.0, "google_ads", "bench")
		}
	})
}

func BenchmarkSlidingWindowBudget_ConcurrentCanSpend(b *testing.B) {
	budgeter := NewSlidingWindowBudget(10*time.Minute, 1000000.0)

	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			budgeter.CanSpend(10.0)
		}
	})
}
