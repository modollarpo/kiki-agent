package shield

import (
	"fmt"
	"net/http"
	"strings"
	"time"
)

// PrometheusExporter exposes circuit breaker metrics in Prometheus format
// Serves metrics at /metrics endpoint for scraping by Prometheus server
type PrometheusExporter struct {
	collector *MetricsCollector
	port      int
}

// NewPrometheusExporter creates a new exporter for the given metrics collector
func NewPrometheusExporter(collector *MetricsCollector, port int) *PrometheusExporter {
	return &PrometheusExporter{
		collector: collector,
		port:      port,
	}
}

// Start begins serving metrics on the configured port
func (pe *PrometheusExporter) Start() error {
	http.HandleFunc("/metrics", pe.metricsHandler)
	http.HandleFunc("/health", pe.healthHandler)

	addr := fmt.Sprintf(":%d", pe.port)
	return http.ListenAndServe(addr, nil)
}

// metricsHandler serves Prometheus-formatted metrics
func (pe *PrometheusExporter) metricsHandler(w http.ResponseWriter, r *http.Request) {
	summary := pe.collector.GetMetricsSummary()

	var builder strings.Builder

	// Header comment
	builder.WriteString("# HELP syncflow_circuit_breaker Circuit breaker resilience metrics\n")
	builder.WriteString("# TYPE syncflow_circuit_breaker_requests_total counter\n")

	// Request counters
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_requests_total{status=\"success\"} %d\n", summary.SuccessfulRequests))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_requests_total{status=\"failure\"} %d\n", summary.FailedRequests))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_requests_total{status=\"fallback\"} %d\n", summary.FallbackRequests))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_requests_total{status=\"total\"} %d\n", summary.TotalRequests))

	// State counters
	builder.WriteString("\n# HELP syncflow_circuit_breaker_state_count State transition counts\n")
	builder.WriteString("# TYPE syncflow_circuit_breaker_state_count counter\n")
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_state_count{state=\"closed\"} %d\n", summary.BreakerStateClosed))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_state_count{state=\"open\"} %d\n", summary.BreakerStateOpen))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_state_count{state=\"half_open\"} %d\n", summary.BreakerStateHalfOpen))

	// State transitions
	builder.WriteString("\n# HELP syncflow_circuit_breaker_transitions_total Total state transitions\n")
	builder.WriteString("# TYPE syncflow_circuit_breaker_transitions_total counter\n")
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_transitions_total %d\n", summary.StateTransitions))

	// Latency percentiles (as gauges)
	builder.WriteString("\n# HELP syncflow_circuit_breaker_latency_ms Latency percentiles in milliseconds\n")
	builder.WriteString("# TYPE syncflow_circuit_breaker_latency_ms gauge\n")
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_latency_ms{quantile=\"0.5\"} %.2f\n", summary.LatencyP50))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_latency_ms{quantile=\"0.75\"} %.2f\n", summary.LatencyP75))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_latency_ms{quantile=\"0.90\"} %.2f\n", summary.LatencyP90))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_latency_ms{quantile=\"0.95\"} %.2f\n", summary.LatencyP95))
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_latency_ms{quantile=\"0.99\"} %.2f\n", summary.LatencyP99))

	// Latency histogram buckets
	builder.WriteString("\n# HELP syncflow_circuit_breaker_latency_bucket Latency distribution buckets\n")
	builder.WriteString("# TYPE syncflow_circuit_breaker_latency_bucket histogram\n")
	for bucket, count := range summary.LatencyBuckets {
		builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_latency_bucket{le=\"%s\"} %d\n", bucket, count))
	}

	// Error counters by type
	if len(summary.ErrorsByType) > 0 {
		builder.WriteString("\n# HELP syncflow_circuit_breaker_errors_total Errors by type\n")
		builder.WriteString("# TYPE syncflow_circuit_breaker_errors_total counter\n")
		for errorType, count := range summary.ErrorsByType {
			builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_errors_total{type=\"%s\"} %d\n", errorType, count))
		}
	}

	// Last state change timestamp
	builder.WriteString("\n# HELP syncflow_circuit_breaker_last_state_change_timestamp_seconds Last state change timestamp\n")
	builder.WriteString("# TYPE syncflow_circuit_breaker_last_state_change_timestamp_seconds gauge\n")
	builder.WriteString(fmt.Sprintf("syncflow_circuit_breaker_last_state_change_timestamp_seconds %d\n", summary.LastStateChange.Unix()))

	// Write response
	w.Header().Set("Content-Type", "text/plain; version=0.0.4")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(builder.String()))
}

// healthHandler provides a simple health check endpoint
func (pe *PrometheusExporter) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(fmt.Sprintf(
		`{"status":"healthy","timestamp":"%s"}`,
		time.Now().Format(time.RFC3339),
	)))
}
