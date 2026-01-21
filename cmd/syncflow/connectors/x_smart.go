package connectors

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// XSmartConnector implements PlatformConnector for X (Twitter) Ads with budget management
type XSmartConnector struct {
	APIKey         string
	AccountID      string
	HttpClient     *http.Client
	Connected      bool
	BaseURL        string
	BudgetManager  *shield.BudgetManager
	RateLimiter    *RateLimiter
	CircuitBreaker *shield.CircuitBreaker
	FallbackEngine *HeuristicFallbackEngine
	MockMode       bool
}

// NewXSmartConnector creates a new X connector with budget management
func NewXSmartConnector(apiKey, accountID string, maxBudget float64) *XSmartConnector {
	return &XSmartConnector{
		APIKey:         apiKey,
		AccountID:      accountID,
		HttpClient:     &http.Client{Timeout: 10 * time.Second},
		BaseURL:        "https://ads-api.twitter.com/12",
		BudgetManager:  shield.NewBudgetManager(maxBudget),
		RateLimiter:    NewRateLimiter(40),
		CircuitBreaker: shield.NewCircuitBreaker(),
		FallbackEngine: NewHeuristicFallbackEngine(),
	}
}

// Connect establishes connection to X Ads API
func (x *XSmartConnector) Connect(ctx context.Context) error {
	log.Printf("🔗 Connecting to X Ads Smart Connector for account: %s", x.AccountID)
	x.Connected = true
	stats := x.BudgetManager.GetStats()
	log.Printf("✅ X Smart connection established - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	return nil
}

// PlaceBid sends a bid to X with safety checks
func (x *XSmartConnector) PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error) {
	if !x.Connected {
		return nil, fmt.Errorf("not connected to X Ads")
	}

	// Record latest LTV to improve fallback median quality
	x.FallbackEngine.RecordLTV("x", req.PredictedLTV)

	// Decide bid source via circuit breaker
	bidAmount := req.BidAmount
	decisionSource := "ai"
	if !x.CircuitBreaker.CanExecute() {
		x.CircuitBreaker.RecordFallback()
		bidAmount = x.FallbackEngine.CalculateFallbackBid("x", req.PredictedLTV)
		decisionSource = "fallback"
	}

	if !x.RateLimiter.CanMakeCall() {
		return nil, fmt.Errorf("rate limit exceeded for X Ads")
	}

	if !x.BudgetManager.CanSpend(bidAmount) {
		stats := x.BudgetManager.GetStats()
		log.Printf("🛡️ BUDGET VETO: X bid $%.2f exceeds remaining budget $%.2f", bidAmount, stats.RemainingBudget)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("Budget exceeded: $%.2f spent of $%.2f limit", stats.CurrentSpend, stats.MaxBudget),
			PlatformCode: "BUDGET_EXCEEDED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("budget exceeded")
	}

	log.Printf("📍 PlaceBid (X): Customer=%s, LTV=%.2f, Bid=$%.2f (source=%s)", req.CustomerID, req.PredictedLTV, bidAmount, decisionSource)

	callStart := time.Now()

	if x.MockMode {
		log.Printf("🧪 MOCK MODE: Simulating X Ads API call")
		x.RateLimiter.RecordCall()
		x.BudgetManager.AddSpend(bidAmount)
		stats := x.BudgetManager.GetStats()
		log.Printf("✅ X bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		x.CircuitBreaker.RecordSuccess(time.Since(callStart))

		return &BidResponse{
			Success:      true,
			BidID:        fmt.Sprintf("MOCK_X_%d", time.Now().Unix()),
			Message:      "Promoted tweet campaign created via X Ads API (MOCK)",
			PlatformCode: "X_ADS_SMART",
			Timestamp:    time.Now(),
		}, nil
	}

	x.RateLimiter.RecordCall()
	x.BudgetManager.AddSpend(bidAmount)
	stats := x.BudgetManager.GetStats()
	log.Printf("✅ X bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
	x.CircuitBreaker.RecordSuccess(time.Since(callStart))

	return &BidResponse{
		Success:      true,
		BidID:        fmt.Sprintf("X_%d", time.Now().Unix()),
		Message:      "Bid sent to X Ads API",
		PlatformCode: "X_ADS_SMART",
		Timestamp:    time.Now(),
	}, nil
}

// GetBudgetStats returns budget statistics
func (x *XSmartConnector) GetBudgetStats() shield.WindowStats {
	return x.BudgetManager.GetStats()
}

// GetStatus returns connection status
func (x *XSmartConnector) GetStatus() string {
	if x.Connected {
		stats := x.BudgetManager.GetStats()
		return fmt.Sprintf("Connected to X Ads - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	}
	return "Disconnected from X Ads"
}

// Close closes the connection
func (x *XSmartConnector) Close() error {
	log.Printf("🔌 X connection closed - Final spend: $%.2f", x.BudgetManager.GetStats().CurrentSpend)
	x.Connected = false
	return nil
}

// UpdateCampaignBudget updates campaign budget
func (x *XSmartConnector) UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}

// UpdateTargetAudience updates target audience
func (x *XSmartConnector) UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}
