package shield

import (
	"testing"
	"time"
)

func TestMetricsCollectorBasicOperations(t *testing.T) {
	collector := NewMetricsCollector()

	// Record some requests
	collector.RecordRequest()
	collector.RecordSuccess(50 * time.Millisecond)

	collector.RecordRequest()
	collector.RecordFailure(100*time.Millisecond, "timeout")

	collector.RecordRequest()
	collector.RecordFallback()

	// Get summary
	summary := collector.GetMetricsSummary()

	if summary.TotalRequests != 3 {
		t.Errorf("Expected 3 total requests, got %d", summary.TotalRequests)
	}

	if summary.SuccessfulRequests != 1 {
		t.Errorf("Expected 1 successful request, got %d", summary.SuccessfulRequests)
	}

	if summary.FailedRequests != 1 {
		t.Errorf("Expected 1 failed request, got %d", summary.FailedRequests)
	}

	if summary.FallbackRequests != 1 {
		t.Errorf("Expected 1 fallback request, got %d", summary.FallbackRequests)
	}

	// Check error tracking
	if summary.ErrorsByType["timeout"] != 1 {
		t.Errorf("Expected 1 timeout error, got %d", summary.ErrorsByType["timeout"])
	}
}

func TestMetricsCollectorLatencyPercentiles(t *testing.T) {
	collector := NewMetricsCollector()

	// Record latencies: 10, 50, 100, 150, 200ms
	latencies := []time.Duration{10, 50, 100, 150, 200}
	for _, latency := range latencies {
		collector.RecordSuccess(latency * time.Millisecond)
	}

	percentiles := collector.GetLatencyPercentiles()

	// p50 should be around 100ms
	if percentiles["p50"] < 90 || percentiles["p50"] > 110 {
		t.Errorf("Expected p50 around 100ms, got %.2f", percentiles["p50"])
	}

	// p99 should be around 200ms
	if percentiles["p99"] < 190 || percentiles["p99"] > 210 {
		t.Errorf("Expected p99 around 200ms, got %.2f", percentiles["p99"])
	}
}

func TestMetricsCollectorStateTransitions(t *testing.T) {
	collector := NewMetricsCollector()

	// Record state transitions
	collector.RecordStateTransition(CLOSED, OPEN)
	collector.RecordStateTransition(OPEN, HALF_OPEN)
	collector.RecordStateTransition(HALF_OPEN, CLOSED)

	summary := collector.GetMetricsSummary()

	if summary.StateTransitions != 3 {
		t.Errorf("Expected 3 state transitions, got %d", summary.StateTransitions)
	}

	// Check state counters (each transition increments the "to" state)
	if summary.BreakerStateOpen != 1 {
		t.Errorf("Expected 1 OPEN state, got %d", summary.BreakerStateOpen)
	}

	if summary.BreakerStateHalfOpen != 1 {
		t.Errorf("Expected 1 HALF_OPEN state, got %d", summary.BreakerStateHalfOpen)
	}

	if summary.BreakerStateClosed != 1 {
		t.Errorf("Expected 1 CLOSED state, got %d", summary.BreakerStateClosed)
	}
}

func TestCircuitBreakerMetricsIntegration(t *testing.T) {
	breaker := NewCircuitBreaker()
	collector := breaker.EnableMetrics()

	// Successful request
	breaker.RecordSuccess(50 * time.Millisecond)

	// Failed request
	breaker.RecordFailure(100 * time.Millisecond)

	// Get metrics
	summary := collector.GetMetricsSummary()

	if summary.TotalRequests != 2 {
		t.Errorf("Expected 2 total requests, got %d", summary.TotalRequests)
	}

	if summary.SuccessfulRequests != 1 {
		t.Errorf("Expected 1 successful request, got %d", summary.SuccessfulRequests)
	}

	if summary.FailedRequests != 1 {
		t.Errorf("Expected 1 failed request, got %d", summary.FailedRequests)
	}

	// Verify latencies were recorded
	percentiles := collector.GetLatencyPercentiles()
	if percentiles["p50"] <= 0 {
		t.Errorf("Expected positive p50 latency, got %.2f", percentiles["p50"])
	}
}

func TestCircuitBreakerMetricsStateTransitions(t *testing.T) {
	breaker := NewCircuitBreaker()
	collector := breaker.EnableMetrics()

	// Trigger CLOSED → OPEN transition
	for i := 0; i < 3; i++ {
		breaker.RecordFailure(100 * time.Millisecond)
	}

	summary := collector.GetMetricsSummary()

	if summary.StateTransitions != 1 {
		t.Errorf("Expected 1 state transition (CLOSED → OPEN), got %d", summary.StateTransitions)
	}

	if summary.BreakerStateOpen != 1 {
		t.Errorf("Expected 1 OPEN state count, got %d", summary.BreakerStateOpen)
	}
}

func TestCircuitBreakerMetricsDisabledByDefault(t *testing.T) {
	breaker := NewCircuitBreaker()

	// Metrics should be nil by default
	if breaker.GetMetricsCollector() != nil {
		t.Error("Expected metrics collector to be nil by default")
	}

	// Operations should still work without metrics
	breaker.RecordSuccess(50 * time.Millisecond)
	breaker.RecordFailure(100 * time.Millisecond)

	stats := breaker.GetStats()
	if stats.TotalRequests != 2 {
		t.Errorf("Expected 2 total requests, got %d", stats.TotalRequests)
	}
}
