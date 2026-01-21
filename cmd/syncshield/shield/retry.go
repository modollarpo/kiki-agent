package shield

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"time"
)

// RetryPolicy defines retry behavior for transient failures
// Implements exponential backoff with jitter to prevent thundering herd
type RetryPolicy struct {
	MaxAttempts       int           // Maximum retry attempts (0 = no retries)
	InitialBackoff    time.Duration // Initial backoff duration (e.g., 100ms)
	MaxBackoff        time.Duration // Maximum backoff duration (e.g., 30s)
	BackoffMultiplier float64       // Multiplier for exponential growth (e.g., 2.0)
	JitterFraction    float64       // Jitter as fraction of backoff (0.0-1.0)
}

// DefaultRetryPolicy returns sensible defaults for most use cases
func DefaultRetryPolicy() *RetryPolicy {
	return &RetryPolicy{
		MaxAttempts:       3, // Retry up to 3 times
		InitialBackoff:    100 * time.Millisecond,
		MaxBackoff:        30 * time.Second,
		BackoffMultiplier: 2.0,  // Double backoff each retry
		JitterFraction:    0.25, // Add ±25% jitter
	}
}

// RetryableFunc defines a function that can be retried
// Returns (result, error)
// If error is permanent (non-transient), retries stop immediately
type RetryableFunc func(ctx context.Context, attempt int) (interface{}, error)

// IsRetryable determines if an error should trigger a retry
// Override this to customize retry logic for specific error types
type IsRetryable func(error) bool

// DefaultIsRetryable implements common retry logic
func DefaultIsRetryable(err error) bool {
	if err == nil {
		return false
	}

	// Common transient errors (extend as needed)
	errStr := err.Error()

	// Network timeouts
	if contains(errStr, "timeout") || contains(errStr, "deadline exceeded") {
		return true
	}

	// Connection errors
	if contains(errStr, "connection refused") || contains(errStr, "connection reset") {
		return true
	}

	// HTTP 5xx errors
	if contains(errStr, "500") || contains(errStr, "502") || contains(errStr, "503") || contains(errStr, "504") {
		return true
	}

	// Temporary unavailability
	if contains(errStr, "temporarily unavailable") || contains(errStr, "service unavailable") {
		return true
	}

	// Default: don't retry
	return false
}

// ExecuteWithRetry executes fn with exponential backoff retry logic
// Returns (result, attempts, error)
// - result: final result from successful call
// - attempts: total attempts made (1 = success on first try, 2 = 1 retry, etc.)
// - error: final error (nil if succeeded within MaxAttempts)
func (rp *RetryPolicy) ExecuteWithRetry(
	ctx context.Context,
	fn RetryableFunc,
	isRetryable IsRetryable,
) (interface{}, int, error) {

	var lastErr error
	attempt := 0

	for attempt = 1; attempt <= rp.MaxAttempts; attempt++ {
		// Execute function
		result, err := fn(ctx, attempt)

		// Success - no retry needed
		if err == nil {
			return result, attempt, nil
		}

		lastErr = err

		// Check if error is retryable
		if !isRetryable(err) {
			// Permanent error - stop immediately
			return nil, attempt, fmt.Errorf("permanent error (attempt %d/%d): %w", attempt, rp.MaxAttempts, err)
		}

		// Last attempt failed - no more retries
		if attempt >= rp.MaxAttempts {
			break
		}

		// Calculate backoff duration
		backoff := rp.calculateBackoff(attempt)

		// Check context before sleeping
		select {
		case <-ctx.Done():
			return nil, attempt, fmt.Errorf("context canceled after %d attempts: %w", attempt, ctx.Err())
		case <-time.After(backoff):
			// Continue to next retry
		}
	}

	// All retries exhausted
	return nil, attempt, fmt.Errorf("max retries exceeded (%d attempts): %w", attempt, lastErr)
}

// calculateBackoff computes exponential backoff with jitter
// Formula: backoff = min(InitialBackoff * (BackoffMultiplier ^ (attempt-1)), MaxBackoff)
// Jitter: backoff ± (backoff * JitterFraction * random)
func (rp *RetryPolicy) calculateBackoff(attempt int) time.Duration {
	// Exponential backoff
	backoff := float64(rp.InitialBackoff) * math.Pow(rp.BackoffMultiplier, float64(attempt-1))

	// Cap at MaxBackoff
	if backoff > float64(rp.MaxBackoff) {
		backoff = float64(rp.MaxBackoff)
	}

	// Add jitter to prevent thundering herd
	if rp.JitterFraction > 0 {
		jitter := backoff * rp.JitterFraction * (2.0*rand.Float64() - 1.0) // ±jitter
		backoff += jitter
	}

	// Ensure non-negative
	if backoff < 0 {
		backoff = 0
	}

	return time.Duration(backoff)
}

// Helper function to check if string contains substring (case-insensitive)
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && containsRec(s, substr, 0))
}

func containsRec(s, substr string, idx int) bool {
	if idx+len(substr) > len(s) {
		return false
	}
	if s[idx:idx+len(substr)] == substr {
		return true
	}
	return containsRec(s, substr, idx+1)
}

// RetryStats tracks retry execution statistics
type RetryStats struct {
	TotalCalls        int64         // Total function calls
	SuccessFirstTry   int64         // Succeeded on first attempt
	SuccessAfterRetry int64         // Succeeded after 1+ retries
	PermanentFailures int64         // Non-retryable errors
	ExhaustedRetries  int64         // All retries failed
	AvgAttempts       float64       // Average attempts per call
	AvgBackoff        time.Duration // Average backoff duration
}
