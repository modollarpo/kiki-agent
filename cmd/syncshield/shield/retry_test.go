package shield

import (
	"context"
	"errors"
	"testing"
	"time"
)

func TestRetryPolicySuccessFirstAttempt(t *testing.T) {
	policy := DefaultRetryPolicy()

	callCount := 0
	fn := func(ctx context.Context, attempt int) (interface{}, error) {
		callCount++
		return "success", nil
	}

	result, attempts, err := policy.ExecuteWithRetry(context.Background(), fn, DefaultIsRetryable)

	if err != nil {
		t.Fatalf("Expected no error, got: %v", err)
	}

	if attempts != 1 {
		t.Errorf("Expected 1 attempt, got %d", attempts)
	}

	if callCount != 1 {
		t.Errorf("Expected 1 call, got %d", callCount)
	}

	if result != "success" {
		t.Errorf("Expected 'success', got %v", result)
	}
}

func TestRetryPolicySuccessAfterRetries(t *testing.T) {
	policy := DefaultRetryPolicy()

	callCount := 0
	fn := func(ctx context.Context, attempt int) (interface{}, error) {
		callCount++
		if callCount < 3 {
			return nil, errors.New("timeout") // Transient error
		}
		return "success after 2 retries", nil
	}

	start := time.Now()
	_, attempts, err := policy.ExecuteWithRetry(context.Background(), fn, DefaultIsRetryable)
	elapsed := time.Since(start)

	if err != nil {
		t.Fatalf("Expected no error, got: %v", err)
	}

	if attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", attempts)
	}

	if callCount != 3 {
		t.Errorf("Expected 3 calls, got %d", callCount)
	}

	// Should have backoff delays
	minExpected := 100*time.Millisecond + 200*time.Millisecond // First retry + second retry backoffs
	if elapsed < minExpected {
		t.Errorf("Expected at least %v of backoff, got %v", minExpected, elapsed)
	}

	t.Logf("✅ Succeeded after %d attempts in %v", attempts, elapsed)
}

func TestRetryPolicyPermanentError(t *testing.T) {
	policy := DefaultRetryPolicy()

	callCount := 0
	fn := func(ctx context.Context, attempt int) (interface{}, error) {
		callCount++
		return nil, errors.New("permanent error: invalid input") // Non-retryable
	}

	_, attempts, err := policy.ExecuteWithRetry(context.Background(), fn, DefaultIsRetryable)

	if err == nil {
		t.Fatal("Expected error for permanent failure")
	}

	if attempts != 1 {
		t.Errorf("Expected 1 attempt (no retries for permanent error), got %d", attempts)
	}

	if callCount != 1 {
		t.Errorf("Expected 1 call, got %d", callCount)
	}

	t.Logf("✅ Permanent error stopped after %d attempt", attempts)
}

func TestRetryPolicyMaxRetriesExceeded(t *testing.T) {
	policy := DefaultRetryPolicy()

	callCount := 0
	fn := func(ctx context.Context, attempt int) (interface{}, error) {
		callCount++
		return nil, errors.New("timeout") // Always fails with retryable error
	}

	_, attempts, err := policy.ExecuteWithRetry(context.Background(), fn, DefaultIsRetryable)

	if err == nil {
		t.Fatal("Expected error after max retries")
	}

	if attempts != policy.MaxAttempts {
		t.Errorf("Expected %d attempts, got %d", policy.MaxAttempts, attempts)
	}

	if callCount != policy.MaxAttempts {
		t.Errorf("Expected %d calls, got %d", policy.MaxAttempts, callCount)
	}

	t.Logf("✅ Max retries exceeded after %d attempts", attempts)
}

func TestRetryPolicyContextCancellation(t *testing.T) {
	policy := DefaultRetryPolicy()
	policy.InitialBackoff = 1 * time.Second // Long backoff to ensure cancellation

	callCount := 0
	fn := func(ctx context.Context, attempt int) (interface{}, error) {
		callCount++
		return nil, errors.New("timeout")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	start := time.Now()
	_, attempts, err := policy.ExecuteWithRetry(ctx, fn, DefaultIsRetryable)
	elapsed := time.Since(start)

	if err == nil {
		t.Fatal("Expected error from context cancellation")
	}

	// Should cancel before completing all retries
	if attempts >= policy.MaxAttempts {
		t.Errorf("Expected fewer than %d attempts due to cancellation, got %d", policy.MaxAttempts, attempts)
	}

	// Should cancel quickly (within 300ms, not wait for 1s backoff)
	if elapsed > 300*time.Millisecond {
		t.Errorf("Expected quick cancellation, took %v", elapsed)
	}

	t.Logf("✅ Context cancelled after %d attempts in %v", attempts, elapsed)
}

func TestRetryPolicyExponentialBackoff(t *testing.T) {
	policy := &RetryPolicy{
		MaxAttempts:       4,
		InitialBackoff:    100 * time.Millisecond,
		MaxBackoff:        1 * time.Second,
		BackoffMultiplier: 2.0,
		JitterFraction:    0.0, // No jitter for predictable testing
	}

	// Calculate expected backoffs: 100ms, 200ms, 400ms
	expectedBackoffs := []time.Duration{
		100 * time.Millisecond, // Attempt 1 backoff
		200 * time.Millisecond, // Attempt 2 backoff
		400 * time.Millisecond, // Attempt 3 backoff
	}

	for i, expected := range expectedBackoffs {
		actual := policy.calculateBackoff(i + 1)
		if actual != expected {
			t.Errorf("Attempt %d: expected backoff %v, got %v", i+1, expected, actual)
		}
	}

	t.Logf("✅ Exponential backoff verified: 100ms → 200ms → 400ms")
}

func TestRetryPolicyJitter(t *testing.T) {
	policy := &RetryPolicy{
		MaxAttempts:       3,
		InitialBackoff:    100 * time.Millisecond,
		MaxBackoff:        1 * time.Second,
		BackoffMultiplier: 2.0,
		JitterFraction:    0.25, // ±25% jitter
	}

	// Run multiple times to check jitter variation
	backoffs := make([]time.Duration, 10)
	for i := 0; i < 10; i++ {
		backoffs[i] = policy.calculateBackoff(1)
	}

	// Check that not all backoffs are identical (jitter applied)
	allSame := true
	for i := 1; i < len(backoffs); i++ {
		if backoffs[i] != backoffs[0] {
			allSame = false
			break
		}
	}

	if allSame {
		t.Error("Expected jitter to produce different backoffs, but all were identical")
	}

	// Check that backoffs are within expected range (100ms ± 25%)
	minExpected := 75 * time.Millisecond
	maxExpected := 125 * time.Millisecond

	for i, backoff := range backoffs {
		if backoff < minExpected || backoff > maxExpected {
			t.Errorf("Backoff %d: %v is outside expected range [%v, %v]", i, backoff, minExpected, maxExpected)
		}
	}

	t.Logf("✅ Jitter verified: backoffs range from %v to %v", minBackoff(backoffs), maxBackoff(backoffs))
}

func TestDefaultIsRetryableDetectsTransientErrors(t *testing.T) {
	tests := []struct {
		name      string
		err       error
		retryable bool
	}{
		{"nil error", nil, false},
		{"timeout", errors.New("connection timeout"), true},
		{"deadline exceeded", errors.New("context deadline exceeded"), true},
		{"503 service unavailable", errors.New("HTTP 503 service unavailable"), true},
		{"502 bad gateway", errors.New("HTTP 502 bad gateway"), true},
		{"connection refused", errors.New("connection refused"), true},
		{"400 bad request", errors.New("HTTP 400 bad request"), false},
		{"invalid input", errors.New("invalid input format"), false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := DefaultIsRetryable(tt.err)
			if result != tt.retryable {
				t.Errorf("Expected %v for %q, got %v", tt.retryable, tt.err, result)
			}
		})
	}
}

func TestRetryPolicyIntegrationWithCircuitBreaker(t *testing.T) {
	// This test demonstrates how retry logic complements circuit breaker
	breaker := NewCircuitBreaker()
	policy := DefaultRetryPolicy()

	callCount := 0
	fn := func(ctx context.Context, attempt int) (interface{}, error) {
		callCount++

		// Simulate transient failure on first 2 calls
		if callCount <= 2 {
			breaker.RecordFailure(100 * time.Millisecond)
			return nil, errors.New("timeout")
		}

		// Success on 3rd call
		breaker.RecordSuccess(50 * time.Millisecond)
		return "success", nil
	}

	_, attempts, err := policy.ExecuteWithRetry(context.Background(), fn, DefaultIsRetryable)

	if err != nil {
		t.Fatalf("Expected success after retries, got error: %v", err)
	}

	if attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", attempts)
	}

	// Circuit breaker should still be CLOSED (succeeded before hitting threshold)
	stats := breaker.GetStats()
	if stats.State != CLOSED {
		t.Errorf("Expected circuit breaker to remain CLOSED, got %v", stats.State)
	}

	t.Logf("✅ Retry prevented circuit breaker from opening: %d failures, then success", attempts-1)
}

// Helper functions

func minBackoff(backoffs []time.Duration) time.Duration {
	min := backoffs[0]
	for _, b := range backoffs {
		if b < min {
			min = b
		}
	}
	return min
}

func maxBackoff(backoffs []time.Duration) time.Duration {
	max := backoffs[0]
	for _, b := range backoffs {
		if b > max {
			max = b
		}
	}
	return max
}
