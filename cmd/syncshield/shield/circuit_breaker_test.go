package shield

import (
	"context"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

// TestCircuitBreakerStateTransitions tests basic state machine behavior
func TestCircuitBreakerStateTransitions(t *testing.T) {
	cb := NewCircuitBreaker()

	// Initially CLOSED
	if cb.GetState() != CLOSED {
		t.Errorf("Expected initial state CLOSED, got %v", cb.GetState())
	}

	// Simulate 3 failures to open circuit
	for i := 0; i < 3; i++ {
		cb.RecordFailure(0)
	}

	if cb.GetState() != OPEN {
		t.Errorf("Expected state OPEN after 3 failures, got %v", cb.GetState())
	}

	// Success should reset failure counter
	cb.Reset()
	cb.RecordSuccess(100 * time.Millisecond)

	if cb.GetState() != CLOSED {
		t.Errorf("Expected state CLOSED after reset, got %v", cb.GetState())
	}
}

// TestCircuitBreakerLatencySensitivity tests latency threshold detection
func TestCircuitBreakerLatencySensitivity(t *testing.T) {
	cb := NewCircuitBreaker()

	// Record a latency spike (>500ms)
	cb.RecordFailure(600 * time.Millisecond)
	cb.RecordFailure(600 * time.Millisecond)

	// This should already trigger opening since latency failures count as double
	if cb.GetState() != OPEN {
		t.Errorf("Expected state OPEN after latency spikes, got %v", cb.GetState())
	}
}

// TestCircuitBreakerHalfOpenState tests recovery probing
func TestCircuitBreakerHalfOpenState(t *testing.T) {
	cb := NewCircuitBreaker()

	// Set very short reset timeout for testing
	cb.SetThresholds(3, 2, 500*time.Millisecond, 100*time.Millisecond)

	// Open the circuit
	cb.RecordFailure(0)
	cb.RecordFailure(0)
	cb.RecordFailure(0)

	if cb.GetState() != OPEN {
		t.Errorf("Expected state OPEN, got %v", cb.GetState())
	}

	// Wait for reset timeout
	time.Sleep(150 * time.Millisecond)

	// Should transition to HALF_OPEN when attempting call
	if !cb.CanExecute() {
		t.Error("Expected CanExecute to return true when in HALF_OPEN transition")
	}

	if cb.GetState() != HALF_OPEN {
		t.Errorf("Expected state HALF_OPEN after timeout, got %v", cb.GetState())
	}

	// Record 2 successes to close circuit
	cb.RecordSuccess(100 * time.Millisecond)
	cb.RecordSuccess(100 * time.Millisecond)

	if cb.GetState() != CLOSED {
		t.Errorf("Expected state CLOSED after 2 successes, got %v", cb.GetState())
	}
}

// TestCircuitBreakerThreadSafety tests concurrent access patterns
func TestCircuitBreakerThreadSafety(t *testing.T) {
	cb := NewCircuitBreaker()
	var wg sync.WaitGroup
	errorCount := int64(0)

	// 50 concurrent goroutines recording successes and failures
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			for j := 0; j < 20; j++ {
				if j%2 == 0 {
					cb.RecordSuccess(100 * time.Millisecond)
				} else {
					cb.RecordFailure(0)
				}

				// Random reads
				if cb.IsFallbackMode() {
					atomic.AddInt64(&errorCount, 1)
				}
			}
		}(i)
	}

	wg.Wait()

	// Verify final state is valid
	stats := cb.GetStats()
	if stats.TotalRequests == 0 {
		t.Error("Expected non-zero total requests")
	}

	t.Logf("Thread Safety Test: %d concurrent operations, state=%v, errors=%d",
		stats.TotalRequests, stats.State, errorCount)
}

// TestCircuitBreakerCanExecute tests permission logic
func TestCircuitBreakerCanExecute(t *testing.T) {
	cb := NewCircuitBreaker()

	// CLOSED state allows execution
	if !cb.CanExecute() {
		t.Error("Expected CanExecute true in CLOSED state")
	}

	// Open circuit by recording failures
	cb.RecordFailure(0)
	cb.RecordFailure(0)
	cb.RecordFailure(0)

	// OPEN state denies execution (before timeout)
	if cb.CanExecute() {
		t.Error("Expected CanExecute false in OPEN state before timeout")
	}

	// Set short reset timeout
	cb.SetThresholds(3, 2, 500*time.Millisecond, 50*time.Millisecond)
	cb.Reset()
	cb.RecordFailure(0)
	cb.RecordFailure(0)
	cb.RecordFailure(0)

	// Wait for timeout
	time.Sleep(100 * time.Millisecond)

	// Should now allow execution (HALF_OPEN)
	if !cb.CanExecute() {
		t.Error("Expected CanExecute true in HALF_OPEN state")
	}
}

// TestCircuitBreakerMetrics tests statistics collection
func TestCircuitBreakerMetrics(t *testing.T) {
	cb := NewCircuitBreaker()

	// Record some activity
	cb.RecordSuccess(100 * time.Millisecond)
	cb.RecordSuccess(150 * time.Millisecond)
	cb.RecordFailure(600 * time.Millisecond)
	cb.RecordFallback()
	cb.RecordFallback()

	stats := cb.GetStats()

	if stats.TotalRequests != 3 {
		t.Errorf("Expected 3 total requests, got %d", stats.TotalRequests)
	}

	if stats.SuccessfulRequests != 2 {
		t.Errorf("Expected 2 successful requests, got %d", stats.SuccessfulRequests)
	}

	if stats.FailedRequests != 1 {
		t.Errorf("Expected 1 failed request, got %d", stats.FailedRequests)
	}

	if stats.FallbackActivations != 2 {
		t.Errorf("Expected 2 fallback activations, got %d", stats.FallbackActivations)
	}
}

// TestCallWithCircuitBreaker tests the wrapper function
func TestCallWithCircuitBreaker(t *testing.T) {
	cb := NewCircuitBreaker()
	ctx := context.Background()

	grpcCallCount := 0
	fallbackCallCount := 0

	// Mock gRPC call
	grpcCall := func(ctx context.Context) (interface{}, time.Duration, error) {
		grpcCallCount++
		return map[string]interface{}{"bid": 100.0}, 200 * time.Millisecond, nil
	}

	// Mock fallback call
	fallbackCall := func(ctx context.Context) (interface{}, error) {
		fallbackCallCount++
		return map[string]interface{}{"bid": 80.0}, nil
	}

	// Circuit closed - should use gRPC
	result, source, _ := cb.CallWithCircuitBreaker(ctx, grpcCall, fallbackCall)
	if source != "grpc_success" {
		t.Errorf("Expected source 'grpc_success', got %s", source)
	}
	if grpcCallCount != 1 {
		t.Error("Expected gRPC call to be made")
	}

	// Open circuit by failing 3 times
	cb.RecordFailure(600 * time.Millisecond)
	cb.RecordFailure(600 * time.Millisecond)
	cb.RecordFailure(600 * time.Millisecond)

	// Circuit open - should use fallback
	result, source, _ = cb.CallWithCircuitBreaker(ctx, grpcCall, fallbackCall)
	if source != "fallback" {
		t.Errorf("Expected source 'fallback', got %s", source)
	}
	if fallbackCallCount != 1 {
		t.Error("Expected fallback call to be made")
	}

	t.Logf("CallWithCircuitBreaker: gRPC calls=%d, Fallback calls=%d, Final result=%v",
		grpcCallCount, fallbackCallCount, result)
}

// TestCircuitBreakerHalfOpenFailureResetsToOpen tests recovery probe failure
func TestCircuitBreakerHalfOpenFailureResetsToOpen(t *testing.T) {
	cb := NewCircuitBreaker()
	cb.SetThresholds(3, 2, 500*time.Millisecond, 50*time.Millisecond)

	// Open circuit
	cb.RecordFailure(0)
	cb.RecordFailure(0)
	cb.RecordFailure(0)

	if cb.GetState() != OPEN {
		t.Errorf("Expected state OPEN, got %v", cb.GetState())
	}

	// Wait for timeout to transition to HALF_OPEN
	time.Sleep(100 * time.Millisecond)
	cb.CanExecute() // Trigger transition

	if cb.GetState() != HALF_OPEN {
		t.Errorf("Expected state HALF_OPEN, got %v", cb.GetState())
	}

	// Failure in HALF_OPEN should return to OPEN
	cb.RecordFailure(0)

	if cb.GetState() != OPEN {
		t.Errorf("Expected state OPEN after failure in HALF_OPEN, got %v", cb.GetState())
	}
}

// BenchmarkCircuitBreaker benchmarks the circuit breaker performance
func BenchmarkCircuitBreaker(b *testing.B) {
	cb := NewCircuitBreaker()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		if i%2 == 0 {
			cb.RecordSuccess(100 * time.Millisecond)
		} else {
			cb.RecordFailure(0)
		}
	}
}

// TestCircuitBreakerStateString tests human-readable state names
func TestCircuitBreakerStateString(t *testing.T) {
	tests := []struct {
		state    CircuitBreakerState
		expected string
	}{
		{CLOSED, "CLOSED (healthy)"},
		{OPEN, "OPEN (failing)"},
		{HALF_OPEN, "HALF_OPEN (testing recovery)"},
	}

	for _, test := range tests {
		if test.state.String() != test.expected {
			t.Errorf("Expected %s, got %s", test.expected, test.state.String())
		}
	}
}

// TestCircuitBreakerFallbackActivationMetric tests fallback counting
func TestCircuitBreakerFallbackActivationMetric(t *testing.T) {
	cb := NewCircuitBreaker()

	// Record some fallback activations
	for i := 0; i < 5; i++ {
		cb.RecordFallback()
	}

	stats := cb.GetStats()
	if stats.FallbackActivations != 5 {
		t.Errorf("Expected 5 fallback activations, got %d", stats.FallbackActivations)
	}
}

// TestCircuitBreakerMultipleOpenClose tests multiple cycles
func TestCircuitBreakerMultipleOpenClose(t *testing.T) {
	cb := NewCircuitBreaker()
	cb.SetThresholds(2, 2, 500*time.Millisecond, 50*time.Millisecond)

	for cycle := 0; cycle < 3; cycle++ {
		// Open circuit
		cb.RecordFailure(0)
		cb.RecordFailure(0)

		if cb.GetState() != OPEN {
			t.Errorf("Cycle %d: Expected state OPEN, got %v", cycle, cb.GetState())
		}

		// Wait and transition to HALF_OPEN
		time.Sleep(100 * time.Millisecond)
		cb.CanExecute()

		if cb.GetState() != HALF_OPEN {
			t.Errorf("Cycle %d: Expected state HALF_OPEN, got %v", cycle, cb.GetState())
		}

		// Close circuit with successes
		cb.RecordSuccess(100 * time.Millisecond)
		cb.RecordSuccess(100 * time.Millisecond)

		if cb.GetState() != CLOSED {
			t.Errorf("Cycle %d: Expected state CLOSED, got %v", cycle, cb.GetState())
		}
	}

	t.Logf("Successfully completed 3 full CLOSED -> OPEN -> HALF_OPEN -> CLOSED cycles")
}
