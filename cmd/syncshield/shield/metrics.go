package shield

import (
	"sync"
	"time"
)

// MetricsCollector provides observability for circuit breaker and resilience patterns
// Exports Prometheus-compatible metrics for production monitoring
type MetricsCollector struct {
	mu sync.RWMutex

	// Circuit Breaker State Counters
	breakerStateClosed   int64 // Total time in CLOSED state (healthy)
	breakerStateOpen     int64 // Total time in OPEN state (failing)
	breakerStateHalfOpen int64 // Total time in HALF_OPEN state (probing recovery)

	// Request Counters
	totalRequests      int64 // All requests attempted
	successfulRequests int64 // Requests that succeeded via gRPC
	failedRequests     int64 // Requests that failed (error or latency)
	fallbackRequests   int64 // Requests served by fallback heuristic

	// Latency Histograms (in milliseconds)
	latencyBuckets map[string]int64 // Buckets: p50, p75, p90, p95, p99
	latencySamples []float64        // Recent latency samples (for percentile calculation)

	// Error Tracking
	errorsByType map[string]int64 // Count errors by type (timeout, 5xx, etc.)

	// State Transition Tracking
	stateTransitions     int64 // Total state transitions
	lastStateChange      time.Time
	lastStateChangedFrom CircuitBreakerState
	lastStateChangedTo   CircuitBreakerState

	// Configuration
	maxLatencySamples int // Max samples to keep for percentile calculation
}

// NewMetricsCollector creates a metrics collector with default configuration
func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{
		latencyBuckets:    make(map[string]int64),
		errorsByType:      make(map[string]int64),
		latencySamples:    make([]float64, 0, 1000),
		maxLatencySamples: 1000,
		lastStateChange:   time.Now(),
	}
}

// RecordRequest increments total request counter
func (mc *MetricsCollector) RecordRequest() {
	mc.mu.Lock()
	defer mc.mu.Unlock()
	mc.totalRequests++
}

// RecordSuccess increments successful request counter and tracks latency
func (mc *MetricsCollector) RecordSuccess(latency time.Duration) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.successfulRequests++
	mc.recordLatency(latency)
}

// RecordFailure increments failed request counter, tracks latency, and categorizes error
func (mc *MetricsCollector) RecordFailure(latency time.Duration, errorType string) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.failedRequests++
	mc.recordLatency(latency)

	// Track error type (timeout, 5xx, etc.)
	if errorType != "" {
		mc.errorsByType[errorType]++
	}
}

// RecordFallback increments fallback request counter
func (mc *MetricsCollector) RecordFallback() {
	mc.mu.Lock()
	defer mc.mu.Unlock()
	mc.fallbackRequests++
}

// RecordStateTransition tracks circuit breaker state changes
func (mc *MetricsCollector) RecordStateTransition(from, to CircuitBreakerState) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.stateTransitions++
	mc.lastStateChange = time.Now()
	mc.lastStateChangedFrom = from
	mc.lastStateChangedTo = to

	// Update time-in-state counters
	// Note: This is a simplified version; for production, use time-weighted averages
	switch to {
	case CLOSED:
		mc.breakerStateClosed++
	case OPEN:
		mc.breakerStateOpen++
	case HALF_OPEN:
		mc.breakerStateHalfOpen++
	}
}

// recordLatency adds a latency sample and updates histogram buckets
func (mc *MetricsCollector) recordLatency(latency time.Duration) {
	latencyMs := float64(latency.Milliseconds())

	// Add to samples
	mc.latencySamples = append(mc.latencySamples, latencyMs)

	// Keep only recent samples
	if len(mc.latencySamples) > mc.maxLatencySamples {
		mc.latencySamples = mc.latencySamples[len(mc.latencySamples)-mc.maxLatencySamples:]
	}

	// Update histogram buckets
	mc.updateHistogram(latencyMs)
}

// updateHistogram categorizes latency into buckets for quick querying
func (mc *MetricsCollector) updateHistogram(latencyMs float64) {
	// Prometheus-style buckets
	buckets := []float64{10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000}

	for _, bucket := range buckets {
		if latencyMs <= bucket {
			mc.latencyBuckets[formatBucket(bucket)]++
			return
		}
	}

	// Greater than all buckets
	mc.latencyBuckets["+Inf"]++
}

// GetLatencyPercentiles calculates p50, p75, p90, p95, p99 from recent samples
func (mc *MetricsCollector) GetLatencyPercentiles() map[string]float64 {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	if len(mc.latencySamples) == 0 {
		return map[string]float64{
			"p50": 0,
			"p75": 0,
			"p90": 0,
			"p95": 0,
			"p99": 0,
		}
	}

	// Sort samples (simple bubble sort for small datasets)
	samples := make([]float64, len(mc.latencySamples))
	copy(samples, mc.latencySamples)
	sortFloat64(samples)

	return map[string]float64{
		"p50": percentile(samples, 0.50),
		"p75": percentile(samples, 0.75),
		"p90": percentile(samples, 0.90),
		"p95": percentile(samples, 0.95),
		"p99": percentile(samples, 0.99),
	}
}

// GetMetricsSummary returns a snapshot of all metrics for export
func (mc *MetricsCollector) GetMetricsSummary() MetricsSummary {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	percentiles := mc.GetLatencyPercentiles()

	return MetricsSummary{
		TotalRequests:        mc.totalRequests,
		SuccessfulRequests:   mc.successfulRequests,
		FailedRequests:       mc.failedRequests,
		FallbackRequests:     mc.fallbackRequests,
		BreakerStateClosed:   mc.breakerStateClosed,
		BreakerStateOpen:     mc.breakerStateOpen,
		BreakerStateHalfOpen: mc.breakerStateHalfOpen,
		StateTransitions:     mc.stateTransitions,
		LastStateChange:      mc.lastStateChange,
		LatencyP50:           percentiles["p50"],
		LatencyP75:           percentiles["p75"],
		LatencyP90:           percentiles["p90"],
		LatencyP95:           percentiles["p95"],
		LatencyP99:           percentiles["p99"],
		ErrorsByType:         copyMap(mc.errorsByType),
		LatencyBuckets:       copyMap(mc.latencyBuckets),
	}
}

// MetricsSummary provides a point-in-time snapshot of all metrics
type MetricsSummary struct {
	TotalRequests      int64
	SuccessfulRequests int64
	FailedRequests     int64
	FallbackRequests   int64

	BreakerStateClosed   int64
	BreakerStateOpen     int64
	BreakerStateHalfOpen int64

	StateTransitions int64
	LastStateChange  time.Time

	LatencyP50 float64
	LatencyP75 float64
	LatencyP90 float64
	LatencyP95 float64
	LatencyP99 float64

	ErrorsByType   map[string]int64
	LatencyBuckets map[string]int64
}

// Helper functions

func formatBucket(value float64) string {
	if value < 1000 {
		return string(rune(value)) + "ms"
	}
	return string(rune(value/1000)) + "s"
}

func percentile(sorted []float64, p float64) float64 {
	if len(sorted) == 0 {
		return 0
	}

	index := int(float64(len(sorted)) * p)
	if index >= len(sorted) {
		index = len(sorted) - 1
	}

	return sorted[index]
}

func sortFloat64(arr []float64) {
	// Simple insertion sort for small datasets
	for i := 1; i < len(arr); i++ {
		key := arr[i]
		j := i - 1
		for j >= 0 && arr[j] > key {
			arr[j+1] = arr[j]
			j--
		}
		arr[j+1] = key
	}
}

func copyMap(src map[string]int64) map[string]int64 {
	dst := make(map[string]int64, len(src))
	for k, v := range src {
		dst[k] = v
	}
	return dst
}
