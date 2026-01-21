package budget

import (
	"fmt"
	"sync"
	"time"
)

// SlidingWindowBudget enforces spend limits over a rolling time window
// [S] Sliding Window Budgeter - A-Z Roadmap
// Prevents capital leaks from burst spending (e.g., 1000 bids in 30 seconds)
type SlidingWindowBudget struct {
	mu sync.RWMutex

	// Configuration
	WindowDuration time.Duration // Default: 10 minutes
	MaxBurstLimit  float64       // Maximum spend allowed in the window

	// Spend tracking
	spendHistory []SpendEvent
}

// SpendEvent tracks a single spend occurrence
type SpendEvent struct {
	Timestamp time.Time
	Amount    float64
	Platform  string
	RequestID string
}

// NewSlidingWindowBudget creates a new budgeter with configurable window and limit
func NewSlidingWindowBudget(windowDuration time.Duration, maxBurstLimit float64) *SlidingWindowBudget {
	return &SlidingWindowBudget{
		WindowDuration: windowDuration,
		MaxBurstLimit:  maxBurstLimit,
		spendHistory:   []SpendEvent{},
	}
}

// RecordSpend adds a spend event to the sliding window
// Returns error if the spend would exceed the burst limit
func (b *SlidingWindowBudget) RecordSpend(amount float64, platform, requestID string) error {
	b.mu.Lock()
	defer b.mu.Unlock()

	now := time.Now()

	// Evict old events outside the window
	b.evictOldEvents(now)

	// Check if adding this spend would exceed the burst limit
	currentSpend := b.getCurrentSpendLocked()
	if currentSpend+amount > b.MaxBurstLimit {
		return &BudgetExceededError{
			CurrentSpend:   currentSpend,
			RequestedSpend: amount,
			BurstLimit:     b.MaxBurstLimit,
			WindowStart:    now.Add(-b.WindowDuration),
			WindowEnd:      now,
		}
	}

	// Record the spend
	b.spendHistory = append(b.spendHistory, SpendEvent{
		Timestamp: now,
		Amount:    amount,
		Platform:  platform,
		RequestID: requestID,
	})

	return nil
}

// CanSpend checks if a spend amount is allowed without recording it
func (b *SlidingWindowBudget) CanSpend(amount float64) bool {
	b.mu.RLock()
	defer b.mu.RUnlock()

	now := time.Now()

	// Calculate current spend in the window
	currentSpend := 0.0
	cutoff := now.Add(-b.WindowDuration)

	for _, event := range b.spendHistory {
		if event.Timestamp.After(cutoff) {
			currentSpend += event.Amount
		}
	}

	return currentSpend+amount <= b.MaxBurstLimit
}

// GetCurrentSpend returns the total spend in the current window
func (b *SlidingWindowBudget) GetCurrentSpend() float64 {
	b.mu.RLock()
	defer b.mu.RUnlock()

	return b.getCurrentSpendLocked()
}

// getCurrentSpendLocked calculates current spend (caller must hold lock)
func (b *SlidingWindowBudget) getCurrentSpendLocked() float64 {
	now := time.Now()
	cutoff := now.Add(-b.WindowDuration)

	total := 0.0
	for _, event := range b.spendHistory {
		if event.Timestamp.After(cutoff) {
			total += event.Amount
		}
	}

	return total
}

// evictOldEvents removes spend events outside the sliding window
func (b *SlidingWindowBudget) evictOldEvents(now time.Time) {
	cutoff := now.Add(-b.WindowDuration)

	// Find the first event within the window
	firstValid := 0
	for i, event := range b.spendHistory {
		if event.Timestamp.After(cutoff) {
			firstValid = i
			break
		}
	}

	// Slice away old events
	if firstValid > 0 {
		b.spendHistory = b.spendHistory[firstValid:]
	}
}

// GetBudgetStatus returns current budget utilization
func (b *SlidingWindowBudget) GetBudgetStatus() BudgetStatus {
	b.mu.RLock()
	defer b.mu.RUnlock()

	now := time.Now()
	currentSpend := b.getCurrentSpendLocked()
	remainingBudget := b.MaxBurstLimit - currentSpend

	// Calculate spend rate ($ per minute)
	windowMinutes := b.WindowDuration.Minutes()
	spendRate := currentSpend / windowMinutes

	return BudgetStatus{
		TotalBudget:     b.MaxBurstLimit,
		CurrentSpend:    currentSpend,
		RemainingBudget: remainingBudget,
		SpendRatePerMin: spendRate,
		WindowStart:     now.Add(-b.WindowDuration),
		WindowEnd:       now,
		BudgetExceeded:  currentSpend >= b.MaxBurstLimit,
		UtilizationPct:  (currentSpend / b.MaxBurstLimit) * 100,
		EventCount:      len(b.spendHistory),
	}
}

// BudgetStatus represents current budget utilization
type BudgetStatus struct {
	TotalBudget     float64
	CurrentSpend    float64
	RemainingBudget float64
	SpendRatePerMin float64
	WindowStart     time.Time
	WindowEnd       time.Time
	BudgetExceeded  bool
	UtilizationPct  float64
	EventCount      int
}

// BudgetExceededError is returned when a spend would exceed the burst limit
type BudgetExceededError struct {
	CurrentSpend   float64
	RequestedSpend float64
	BurstLimit     float64
	WindowStart    time.Time
	WindowEnd      time.Time
}

func (e *BudgetExceededError) Error() string {
	return fmt.Sprintf(
		"budget exceeded: current spend $%.2f + requested $%.2f = $%.2f exceeds burst limit $%.2f (window: %s to %s)",
		e.CurrentSpend,
		e.RequestedSpend,
		e.CurrentSpend+e.RequestedSpend,
		e.BurstLimit,
		e.WindowStart.Format(time.RFC3339),
		e.WindowEnd.Format(time.RFC3339),
	)
}

// Reset clears the spend history (use with caution!)
func (b *SlidingWindowBudget) Reset() {
	b.mu.Lock()
	defer b.mu.Unlock()

	b.spendHistory = []SpendEvent{}
}

// GetSpendByPlatform returns spend breakdown by platform
func (b *SlidingWindowBudget) GetSpendByPlatform() map[string]float64 {
	b.mu.RLock()
	defer b.mu.RUnlock()

	now := time.Now()
	cutoff := now.Add(-b.WindowDuration)

	spendByPlatform := make(map[string]float64)
	for _, event := range b.spendHistory {
		if event.Timestamp.After(cutoff) {
			spendByPlatform[event.Platform] += event.Amount
		}
	}

	return spendByPlatform
}
