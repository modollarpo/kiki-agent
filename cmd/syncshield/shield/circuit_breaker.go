package shield

import (
	"context"
	"sync"
	"time"
)

// CircuitBreakerState defines the state of the circuit
// CLOSED: healthy; OPEN: failing (use fallback); HALF_OPEN: probing recovery
// Half-open allows limited calls to test if service recovered.
type CircuitBreakerState int

const (
	CLOSED CircuitBreakerState = iota
	OPEN
	HALF_OPEN
)

// CircuitBreaker implements resilience for SyncValue™ (gRPC) calls
// It protects connectors from latency spikes or outages by switching to fallback.
type CircuitBreaker struct {
	mu                  sync.RWMutex
	state               CircuitBreakerState
	failureCount        int
	halfOpenSuccesses   int
	lastFailureTime     time.Time
	lastStateChangeTime time.Time

	// Configuration
	failureThreshold int           // failures before opening circuit
	successThreshold int           // successes in HALF_OPEN before closing
	latencyThreshold time.Duration // latency considered a failure
	resetTimeout     time.Duration // time before allowing HALF_OPEN probe

	// Metrics
	totalRequests       int64
	successfulRequests  int64
	failedRequests      int64
	fallbackActivations int64

	// Observability
	metricsCollector *MetricsCollector // Optional: nil if metrics disabled
}

// CircuitBreakerStats exposes circuit state and counters
type CircuitBreakerStats struct {
	State                CircuitBreakerState
	FailureCount         int
	TotalRequests        int64
	SuccessfulRequests   int64
	FailedRequests       int64
	FallbackActivations  int64
	LastFailureTime      time.Time
	TimeSinceLastFailure time.Duration
}

// NewCircuitBreaker returns a breaker with sensible defaults
func NewCircuitBreaker() *CircuitBreaker {
	return &CircuitBreaker{
		state:               CLOSED,
		failureThreshold:    3,
		successThreshold:    2,
		latencyThreshold:    500 * time.Millisecond,
		resetTimeout:        30 * time.Second,
		lastStateChangeTime: time.Now(),
		metricsCollector:    nil, // Metrics disabled by default; enable via EnableMetrics()
	}
}

// EnableMetrics activates observability metrics collection
func (cb *CircuitBreaker) EnableMetrics() *MetricsCollector {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if cb.metricsCollector == nil {
		cb.metricsCollector = NewMetricsCollector()
	}
	return cb.metricsCollector
}

// GetMetricsCollector returns the metrics collector (nil if disabled)
func (cb *CircuitBreaker) GetMetricsCollector() *MetricsCollector {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.metricsCollector
}

// RecordSuccess registers a successful call and handles HALF_OPEN recovery
func (cb *CircuitBreaker) RecordSuccess(latency time.Duration) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.totalRequests++
	cb.successfulRequests++
	cb.failureCount = 0

	// Emit metrics if enabled
	if cb.metricsCollector != nil {
		cb.metricsCollector.RecordRequest()
		cb.metricsCollector.RecordSuccess(latency)
	}

	oldState := cb.state
	switch cb.state {
	case CLOSED:
		// nothing extra
	case HALF_OPEN:
		cb.halfOpenSuccesses++
		if cb.halfOpenSuccesses >= cb.successThreshold {
			cb.state = CLOSED
			cb.failureCount = 0
			cb.halfOpenSuccesses = 0
			cb.lastStateChangeTime = time.Now()

			// Record state transition
			if cb.metricsCollector != nil {
				cb.metricsCollector.RecordStateTransition(oldState, CLOSED)
			}
		}
	}
}

// RecordFailure registers a failed call or latency spike
func (cb *CircuitBreaker) RecordFailure(latency time.Duration) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.totalRequests++
	cb.failedRequests++
	cb.failureCount++
	cb.lastFailureTime = time.Now()

	// Emit metrics if enabled
	errorType := "generic"
	if latency > cb.latencyThreshold {
		errorType = "latency_spike"
		cb.failureCount++ // Latency spike counts as an extra failure
	}

	if cb.metricsCollector != nil {
		cb.metricsCollector.RecordRequest()
		cb.metricsCollector.RecordFailure(latency, errorType)
	}

	oldState := cb.state

	// In HALF_OPEN any failure re-opens the circuit
	if cb.state == HALF_OPEN {
		cb.state = OPEN
		cb.halfOpenSuccesses = 0
		cb.lastStateChangeTime = time.Now()

		if cb.metricsCollector != nil {
			cb.metricsCollector.RecordStateTransition(oldState, OPEN)
		}
		return
	}

	// If not already open and threshold exceeded, open the circuit
	if cb.state != OPEN && cb.failureCount >= cb.failureThreshold {
		cb.state = OPEN
		cb.lastStateChangeTime = time.Now()

		if cb.metricsCollector != nil {
			cb.metricsCollector.RecordStateTransition(oldState, OPEN)
		}
	}
}

// CanExecute returns true if gRPC call should be attempted (CLOSED or HALF_OPEN)
// If OPEN, it may transition to HALF_OPEN after resetTimeout.
func (cb *CircuitBreaker) CanExecute() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	oldState := cb.state
	switch cb.state {
	case CLOSED:
		return true
	case OPEN:
		if time.Since(cb.lastStateChangeTime) > cb.resetTimeout {
			cb.state = HALF_OPEN
			cb.halfOpenSuccesses = 0
			cb.lastStateChangeTime = time.Now()

			if cb.metricsCollector != nil {
				cb.metricsCollector.RecordStateTransition(oldState, HALF_OPEN)
			}
			return true
		}
		return false
	case HALF_OPEN:
		return true
	default:
		return false
	}
}

// IsFallbackMode reports whether the circuit is OPEN
func (cb *CircuitBreaker) IsFallbackMode() bool {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state == OPEN
}

// GetState returns the current state
func (cb *CircuitBreaker) GetState() CircuitBreakerState {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// GetStats captures state and metrics snapshot
func (cb *CircuitBreaker) GetStats() CircuitBreakerStats {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	var since time.Duration
	if !cb.lastFailureTime.IsZero() {
		since = time.Since(cb.lastFailureTime)
	}

	return CircuitBreakerStats{
		State:                cb.state,
		FailureCount:         cb.failureCount,
		TotalRequests:        cb.totalRequests,
		SuccessfulRequests:   cb.successfulRequests,
		FailedRequests:       cb.failedRequests,
		FallbackActivations:  cb.fallbackActivations,
		LastFailureTime:      cb.lastFailureTime,
		TimeSinceLastFailure: since,
	}
}

// RecordFallback increments fallback counter (used when circuit is open)
func (cb *CircuitBreaker) RecordFallback() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.fallbackActivations++

	// Emit metrics if enabled
	if cb.metricsCollector != nil {
		cb.metricsCollector.RecordFallback()
	}
}

// Reset clears counters and closes the circuit (for tests)
func (cb *CircuitBreaker) Reset() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.state = CLOSED
	cb.failureCount = 0
	cb.halfOpenSuccesses = 0
	cb.lastFailureTime = time.Time{}
	cb.lastStateChangeTime = time.Now()
}

// SetThresholds configures breaker thresholds
func (cb *CircuitBreaker) SetThresholds(failureThreshold int, successThreshold int, latencyThreshold time.Duration, resetTimeout time.Duration) {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failureThreshold = failureThreshold
	cb.successThreshold = successThreshold
	cb.latencyThreshold = latencyThreshold
	cb.resetTimeout = resetTimeout
}

// String returns human readable state
func (s CircuitBreakerState) String() string {
	switch s {
	case CLOSED:
		return "CLOSED (healthy)"
	case OPEN:
		return "OPEN (failing)"
	case HALF_OPEN:
		return "HALF_OPEN (testing recovery)"
	default:
		return "UNKNOWN"
	}
}

// CallWithCircuitBreaker wraps a gRPC call with breaker + fallback
// grpcCall returns (result, latency, error)
// fallbackCall returns (result, error)
// Returns: result, source (grpc_success|grpc_failed|fallback|fallback_after_circuit_open), error
func (cb *CircuitBreaker) CallWithCircuitBreaker(
	ctx context.Context,
	grpcCall func(context.Context) (interface{}, time.Duration, error),
	fallbackCall func(context.Context) (interface{}, error),
) (interface{}, string, error) {

	// If circuit is open, immediately use fallback
	if !cb.CanExecute() {
		cb.RecordFallback()
		res, err := fallbackCall(ctx)
		return res, "fallback", err
	}

	// Attempt gRPC call
	result, latency, err := grpcCall(ctx)

	if err != nil || latency > cb.latencyThreshold {
		cb.RecordFailure(latency)

		// If circuit opened due to this failure, try fallback
		if cb.IsFallbackMode() {
			cb.RecordFallback()
			fbResult, fbErr := fallbackCall(ctx)
			return fbResult, "fallback_after_circuit_open", fbErr
		}

		return result, "grpc_failed", err
	}

	// Success path
	cb.RecordSuccess(latency)
	return result, "grpc_success", nil
}
