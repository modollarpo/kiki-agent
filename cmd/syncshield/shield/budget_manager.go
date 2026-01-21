package shield

import (
	"sync"
	"time"
)

// BidRecord stores a single bid transaction with timestamp and amount
type BidRecord struct {
	Timestamp time.Time
	Amount    float64
}

// BudgetManager provides thread-safe sliding window budget tracking
// Critical for preventing overspend and API rate limit compliance
type BudgetManager struct {
	mu             sync.Mutex
	records        []BidRecord
	windowSize     time.Duration
	maxBurstBudget float64
}

// NewBudgetManager creates a new budget manager with specified max budget
func NewBudgetManager(maxBudget float64) *BudgetManager {
	return &BudgetManager{
		windowSize:     10 * time.Minute,
		maxBurstBudget: maxBudget,
		records:        make([]BidRecord, 0, 1000), // Pre-allocate capacity
	}
}

// AddSpend records a successful bid and prunes expired records
// This is called after a bid is successfully placed on an ad platform
func (bm *BudgetManager) AddSpend(amount float64) {
	bm.mu.Lock()
	defer bm.mu.Unlock()

	bm.records = append(bm.records, BidRecord{
		Timestamp: time.Now(),
		Amount:    amount,
	})
	bm.prune()
}

// CanSpend checks if adding the next bid would exceed the burst limit
// Returns true if the bid can be placed without exceeding budget constraints
func (bm *BudgetManager) CanSpend(nextAmount float64) bool {
	bm.mu.Lock()
	defer bm.mu.Unlock()

	bm.prune()
	var currentTotal float64
	for _, r := range bm.records {
		currentTotal += r.Amount
	}

	return (currentTotal + nextAmount) <= bm.maxBurstBudget
}

// GetCurrentSpend returns the total spend within the current window
func (bm *BudgetManager) GetCurrentSpend() float64 {
	bm.mu.Lock()
	defer bm.mu.Unlock()

	bm.prune()
	var total float64
	for _, r := range bm.records {
		total += r.Amount
	}
	return total
}

// GetRemainingBudget returns how much budget is left in the current window
func (bm *BudgetManager) GetRemainingBudget() float64 {
	bm.mu.Lock()
	defer bm.mu.Unlock()

	bm.prune()
	var total float64
	for _, r := range bm.records {
		total += r.Amount
	}
	return bm.maxBurstBudget - total
}

// prune removes expired records outside the sliding window
// Must be called with lock held
func (bm *BudgetManager) prune() {
	cutoff := time.Now().Add(-bm.windowSize)
	i := 0
	for i < len(bm.records) && bm.records[i].Timestamp.Before(cutoff) {
		i++
	}
	bm.records = bm.records[i:]
}

// GetWindowStats returns statistics about the current budget window
type WindowStats struct {
	CurrentSpend    float64
	MaxBudget       float64
	RemainingBudget float64
	RecordCount     int
	OldestRecord    time.Time
	WindowDuration  time.Duration
}

// GetStats returns current window statistics for monitoring
func (bm *BudgetManager) GetStats() WindowStats {
	bm.mu.Lock()
	defer bm.mu.Unlock()

	bm.prune()

	var total float64
	var oldest time.Time
	if len(bm.records) > 0 {
		oldest = bm.records[0].Timestamp
	}

	for _, r := range bm.records {
		total += r.Amount
	}

	return WindowStats{
		CurrentSpend:    total,
		MaxBudget:       bm.maxBurstBudget,
		RemainingBudget: bm.maxBurstBudget - total,
		RecordCount:     len(bm.records),
		OldestRecord:    oldest,
		WindowDuration:  bm.windowSize,
	}
}
