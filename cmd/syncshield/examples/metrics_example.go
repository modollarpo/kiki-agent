package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// Example: Real-Time LTV Momentum Tracking with Circuit Breaker Metrics
//
// This example demonstrates the "Heartbeat Dashboard" concept for KIKI Agent™:
// 1. Real-time LTV prediction tracking with accuracy monitoring
// 2. Circuit breaker resilience metrics
// 3. Prometheus metrics export on :9090
// 4. Visual console output showing LTV momentum trends
//
// This simulates the SyncValue™ (AI Brain) → SyncFlow™ (Execution Layer) pipeline
// with realistic LTV predictions, bid placements, and fallback scenarios.
//
// Run this example:
//   go run metrics_example.go
//
// Then monitor:
//   curl http://localhost:9090/metrics
//   curl http://localhost:9090/health
//
// Watch the console for real-time LTV momentum tracking

// LTVMomentumTracker tracks LTV predictions over time to prove AI accuracy
type LTVMomentumTracker struct {
	mu sync.RWMutex

	// Prediction tracking
	predictions        []LTVPrediction
	totalPredictions   int64
	correctPredictions int64 // Predicted LTV within 10% of actual

	// Accuracy metrics
	avgAccuracy    float64 // Running average accuracy
	targetAccuracy float64 // Target: 94.7% (from pitch)

	// Momentum metrics
	ltvTrend        string // "RISING", "STABLE", "FALLING"
	avgPredictedLTV float64
	avgActualLTV    float64
}

// LTVPrediction represents a single LTV prediction event
type LTVPrediction struct {
	Timestamp    time.Time
	CustomerID   string
	PredictedLTV float64
	ActualLTV    float64 // Simulated for demo; in production, from SyncEngage™
	BidAmount    float64
	Platform     string
	Source       string // "ai" or "fallback"
	Latency      time.Duration
}

// NewLTVMomentumTracker creates a tracker with target accuracy
func NewLTVMomentumTracker(targetAccuracy float64) *LTVMomentumTracker {
	return &LTVMomentumTracker{
		predictions:    make([]LTVPrediction, 0, 1000),
		targetAccuracy: targetAccuracy,
		ltvTrend:       "STABLE",
	}
}

// RecordPrediction adds a new LTV prediction and updates accuracy metrics
func (tracker *LTVMomentumTracker) RecordPrediction(pred LTVPrediction) {
	tracker.mu.Lock()
	defer tracker.mu.Unlock()

	tracker.predictions = append(tracker.predictions, pred)
	tracker.totalPredictions++

	// Calculate accuracy (within 10% tolerance)
	accuracy := 1.0 - (abs(pred.PredictedLTV-pred.ActualLTV) / pred.ActualLTV)
	if accuracy >= 0.90 {
		tracker.correctPredictions++
	}

	// Update running averages
	tracker.avgAccuracy = float64(tracker.correctPredictions) / float64(tracker.totalPredictions) * 100
	tracker.updateTrends()

	// Keep only recent predictions (last 1000)
	if len(tracker.predictions) > 1000 {
		tracker.predictions = tracker.predictions[len(tracker.predictions)-1000:]
	}
}

// updateTrends calculates LTV momentum based on recent predictions
func (tracker *LTVMomentumTracker) updateTrends() {
	if len(tracker.predictions) < 10 {
		return
	}

	// Calculate averages for last 10 predictions
	recentPredicted := 0.0
	recentActual := 0.0
	count := min(10, len(tracker.predictions))

	for i := len(tracker.predictions) - count; i < len(tracker.predictions); i++ {
		recentPredicted += tracker.predictions[i].PredictedLTV
		recentActual += tracker.predictions[i].ActualLTV
	}

	tracker.avgPredictedLTV = recentPredicted / float64(count)
	tracker.avgActualLTV = recentActual / float64(count)

	// Determine trend
	diff := tracker.avgActualLTV - tracker.avgPredictedLTV
	if diff > 10 {
		tracker.ltvTrend = "RISING ↗"
	} else if diff < -10 {
		tracker.ltvTrend = "FALLING ↘"
	} else {
		tracker.ltvTrend = "STABLE →"
	}
}

// GetMomentumReport returns a formatted report for console display
func (tracker *LTVMomentumTracker) GetMomentumReport() string {
	tracker.mu.RLock()
	defer tracker.mu.RUnlock()

	status := "🟢 ON-TARGET"
	if tracker.avgAccuracy < tracker.targetAccuracy {
		status = "🟡 BELOW TARGET"
	}

	return fmt.Sprintf(`
┌─────────────────────────────────────────────────────────────┐
│ 📈 LTV MOMENTUM TRACKER - KIKI Agent™ Heartbeat            │
├─────────────────────────────────────────────────────────────┤
│ Total Predictions:      %6d                               │
│ Correct Predictions:    %6d (±10%% tolerance)              │
│ Current Accuracy:       %6.2f%% %s                  │
│ Target Accuracy:        %6.2f%% (dRNN promise)            │
├─────────────────────────────────────────────────────────────┤
│ Avg Predicted LTV:      $%.2f                              │
│ Avg Actual LTV:         $%.2f                              │
│ LTV Trend:              %s                                 │
├─────────────────────────────────────────────────────────────┤
│ Metrics: http://localhost:9090/metrics                      │
│ Health:  http://localhost:9090/health                       │
└─────────────────────────────────────────────────────────────┘`,
		tracker.totalPredictions,
		tracker.correctPredictions,
		tracker.avgAccuracy,
		status,
		tracker.targetAccuracy,
		tracker.avgPredictedLTV,
		tracker.avgActualLTV,
		tracker.ltvTrend,
	)
}

func DemoLTVMomentum() {
	log.Println("═══════════════════════════════════════════════════════════")
	log.Println("  KIKI Agent™ - Real-Time LTV Momentum Tracking Demo")
	log.Println("  Simulating SyncValue™ (AI) → SyncFlow™ (Execution)")
	log.Println("═══════════════════════════════════════════════════════════")

	// Initialize components
	breaker := shield.NewCircuitBreaker()
	collector := breaker.EnableMetrics()
	tracker := NewLTVMomentumTracker(94.7) // Target: 94.7% accuracy

	// Start Prometheus exporter
	exporter := shield.NewPrometheusExporter(collector, 9090)
	go func() {
		log.Println("\n📊 Starting Prometheus metrics server on :9090")
		if err := exporter.Start(); err != nil {
			log.Fatalf("Failed to start metrics exporter: %v", err)
		}
	}()

	// Wait for server to start
	time.Sleep(500 * time.Millisecond)

	// Run simulation phases
	ctx := context.Background()
	platforms := []string{"google_ads", "meta", "tiktok", "linkedin", "amazon", "tradedesk", "x"}

	log.Println("\n🚀 Starting real-time simulation...")
	log.Println("   (Updates every 2 seconds - Press Ctrl+C to stop)")

	// Phase 1: Healthy AI predictions (10 cycles)
	log.Println("\n━━━ PHASE 1: Healthy AI Operation ━━━")
	for cycle := 1; cycle <= 10; cycle++ {
		simulateLTVPredictionCycle(ctx, breaker, tracker, platforms, "healthy", cycle)
		time.Sleep(2 * time.Second)
	}

	// Phase 2: Introduce latency spikes (5 cycles)
	log.Println("\n━━━ PHASE 2: Latency Degradation ━━━")
	for cycle := 1; cycle <= 5; cycle++ {
		simulateLTVPredictionCycle(ctx, breaker, tracker, platforms, "degraded", cycle)
		time.Sleep(2 * time.Second)
	}

	// Phase 3: Circuit breaker opens, fallback mode (5 cycles)
	log.Println("\n━━━ PHASE 3: Circuit OPEN - Fallback Mode ━━━")
	for cycle := 1; cycle <= 5; cycle++ {
		simulateLTVPredictionCycle(ctx, breaker, tracker, platforms, "fallback", cycle)
		time.Sleep(2 * time.Second)
	}

	// Phase 4: Recovery (5 cycles)
	log.Println("\n━━━ PHASE 4: Recovery - AI Restored ━━━")
	for cycle := 1; cycle <= 5; cycle++ {
		simulateLTVPredictionCycle(ctx, breaker, tracker, platforms, "recovery", cycle)
		time.Sleep(2 * time.Second)
	}

	// Final report
	log.Println("\n" + tracker.GetMomentumReport())

	// Print detailed circuit breaker stats
	stats := breaker.GetStats()
	summary := collector.GetMetricsSummary()

	log.Println("\n┌─────────────────────────────────────────────────────────────┐")
	log.Println("│ 🛡️  CIRCUIT BREAKER RESILIENCE STATS                       │")
	log.Println("├─────────────────────────────────────────────────────────────┤")
	log.Printf("│ Current State:          %-35s │\n", stats.State)
	log.Printf("│ Total Requests:         %-35d │\n", stats.TotalRequests)
	log.Printf("│ Successful:             %-35d │\n", stats.SuccessfulRequests)
	log.Printf("│ Failed:                 %-35d │\n", stats.FailedRequests)
	log.Printf("│ Fallback Activations:   %-35d │\n", stats.FallbackActivations)
	log.Printf("│ State Transitions:      %-35d │\n", summary.StateTransitions)
	log.Println("├─────────────────────────────────────────────────────────────┤")
	log.Printf("│ Latency p50:            %-30.2fms │\n", summary.LatencyP50)
	log.Printf("│ Latency p95:            %-30.2fms │\n", summary.LatencyP95)
	log.Printf("│ Latency p99:            %-30.2fms │\n", summary.LatencyP99)
	log.Println("└─────────────────────────────────────────────────────────────┘")

	log.Println("\n✅ Simulation complete. Metrics server still running.")
	log.Println("   Visit http://localhost:9090/metrics for Prometheus export")
	log.Println("   Press Ctrl+C to stop")

	// Keep server running
	select {}
}

// simulateLTVPredictionCycle simulates one cycle of LTV predictions across platforms
func simulateLTVPredictionCycle(
	_ context.Context,
	breaker *shield.CircuitBreaker,
	tracker *LTVMomentumTracker,
	platforms []string,
	phase string,
	cycle int,
) {
	for _, platform := range platforms {
		// Generate realistic LTV prediction
		baseLTV := 100.0 + rand.Float64()*200.0 // $100-$300 range
		predictedLTV := baseLTV

		// Add noise to simulate prediction variance (±5%)
		noise := (rand.Float64() - 0.5) * 10.0
		predictedLTV += noise

		// Simulate actual LTV (ground truth from SyncEngage™)
		// In production, this comes from CRM post-acquisition tracking
		actualLTV := baseLTV + (rand.Float64()-0.5)*20.0 // ±10% variance

		var latency time.Duration
		var source string
		var success bool

		switch phase {
		case "healthy":
			// Fast, accurate AI predictions
			latency = time.Duration(20+rand.Intn(30)) * time.Millisecond
			source = "ai"
			success = true

		case "degraded":
			// Latency spikes, but still functional
			latency = time.Duration(400+rand.Intn(200)) * time.Millisecond
			source = "ai"
			success = rand.Float64() > 0.3 // 70% success rate

		case "fallback":
			// Circuit OPEN - using fallback
			latency = time.Duration(10+rand.Intn(20)) * time.Millisecond
			source = "fallback"
			success = true
			// Fallback has slightly lower accuracy (80% vs 95%)
			predictedLTV = baseLTV * getPlatformMultiplier(platform)

		case "recovery":
			// Recovering - fast again
			latency = time.Duration(25+rand.Intn(35)) * time.Millisecond
			source = "ai"
			success = true
		}

		// Execute through circuit breaker
		if success {
			breaker.RecordSuccess(latency)
		} else {
			breaker.RecordFailure(latency)
			continue
		}

		// Check if fallback is active
		if !breaker.CanExecute() {
			source = "fallback"
			breaker.RecordFallback()
			predictedLTV = baseLTV * getPlatformMultiplier(platform)
		}

		// Record prediction
		pred := LTVPrediction{
			Timestamp:    time.Now(),
			CustomerID:   fmt.Sprintf("CUST_%04d", rand.Intn(9999)),
			PredictedLTV: predictedLTV,
			ActualLTV:    actualLTV,
			BidAmount:    predictedLTV, // In real system: optimized bid calculation
			Platform:     platform,
			Source:       source,
			Latency:      latency,
		}
		tracker.RecordPrediction(pred)

		// Log prediction
		accuracy := (1.0 - abs(predictedLTV-actualLTV)/actualLTV) * 100
		log.Printf("  [Cycle %2d] %10s | LTV: $%6.2f → $%6.2f | Acc: %5.1f%% | %4s | %4dms",
			cycle, platform, predictedLTV, actualLTV, accuracy, source, latency.Milliseconds())
	}

	// Print momentum update after each cycle
	stats := breaker.GetStats()
	log.Printf("\n  💓 Heartbeat: %d predictions | Accuracy: %.1f%% | Circuit: %v\n",
		tracker.totalPredictions, tracker.avgAccuracy, stats.State)
}

// getPlatformMultiplier returns the fallback multiplier for each platform
func getPlatformMultiplier(platform string) float64 {
	multipliers := map[string]float64{
		"google_ads": 1.0,
		"meta":       1.0,
		"tradedesk":  1.0,
		"amazon":     1.0,
		"x":          0.75,
		"linkedin":   1.2,
		"tiktok":     1.5,
	}

	if mult, ok := multipliers[platform]; ok {
		return mult
	}
	return 1.0
}

// Helper functions
func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
