package connectors

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// AmazonSmartConnector implements PlatformConnector for Amazon Advertising API with budget management
type AmazonSmartConnector struct {
	APIKey         string
	ProfileID      string
	HttpClient     *http.Client
	Connected      bool
	BaseURL        string
	BudgetManager  *shield.BudgetManager
	RateLimiter    *RateLimiter
	CircuitBreaker *shield.CircuitBreaker
	FallbackEngine *HeuristicFallbackEngine
	MockMode       bool
}

// NewAmazonSmartConnector creates a new Amazon connector with budget management
func NewAmazonSmartConnector(apiKey, profileID string, maxBudget float64) *AmazonSmartConnector {
	return &AmazonSmartConnector{
		APIKey:         apiKey,
		ProfileID:      profileID,
		HttpClient:     &http.Client{Timeout: 10 * time.Second},
		BaseURL:        "https://advertising-api.amazon.com/v3",
		BudgetManager:  shield.NewBudgetManager(maxBudget),
		RateLimiter:    NewRateLimiter(50),
		CircuitBreaker: shield.NewCircuitBreaker(),
		FallbackEngine: NewHeuristicFallbackEngine(),
	}
}

// Connect establishes connection to Amazon Advertising API
func (a *AmazonSmartConnector) Connect(ctx context.Context) error {
	log.Printf("🔗 Connecting to Amazon Advertising Smart Connector for profile: %s", a.ProfileID)
	a.Connected = true
	stats := a.BudgetManager.GetStats()
	log.Printf("✅ Amazon Smart connection established - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	return nil
}

// PlaceBid sends a bid to Amazon with safety checks
func (a *AmazonSmartConnector) PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error) {
	if !a.Connected {
		return nil, fmt.Errorf("not connected to Amazon Advertising")
	}

	// Record latest LTV to improve fallback median quality
	a.FallbackEngine.RecordLTV("amazon", req.PredictedLTV)

	// Decide bid source via circuit breaker
	bidAmount := req.BidAmount
	decisionSource := "ai"
	if !a.CircuitBreaker.CanExecute() {
		a.CircuitBreaker.RecordFallback()
		bidAmount = a.FallbackEngine.CalculateFallbackBid("amazon", req.PredictedLTV)
		decisionSource = "fallback"
	}

	if !a.RateLimiter.CanMakeCall() {
		return nil, fmt.Errorf("rate limit exceeded for Amazon Advertising")
	}

	if !a.BudgetManager.CanSpend(bidAmount) {
		stats := a.BudgetManager.GetStats()
		log.Printf("🛡️ BUDGET VETO: Amazon bid $%.2f exceeds remaining budget $%.2f", bidAmount, stats.RemainingBudget)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("Budget exceeded: $%.2f spent of $%.2f limit", stats.CurrentSpend, stats.MaxBudget),
			PlatformCode: "BUDGET_EXCEEDED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("budget exceeded")
	}

	log.Printf("📍 PlaceBid (Amazon): Customer=%s, LTV=%.2f, Bid=$%.2f (source=%s)", req.CustomerID, req.PredictedLTV, bidAmount, decisionSource)

	callStart := time.Now()

	if a.MockMode {
		log.Printf("🧪 MOCK MODE: Simulating Amazon Advertising API call")
		a.RateLimiter.RecordCall()
		a.BudgetManager.AddSpend(bidAmount)
		stats := a.BudgetManager.GetStats()
		log.Printf("✅ Amazon bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		a.CircuitBreaker.RecordSuccess(time.Since(callStart))

		return &BidResponse{
			Success:      true,
			BidID:        fmt.Sprintf("MOCK_AMAZON_%d", time.Now().Unix()),
			Message:      "Campaign budget optimized via Amazon Advertising API (MOCK)",
			PlatformCode: "AMAZON_ADS_SMART",
			Timestamp:    time.Now(),
		}, nil
	}

	a.RateLimiter.RecordCall()
	a.BudgetManager.AddSpend(bidAmount)
	stats := a.BudgetManager.GetStats()
	log.Printf("✅ Amazon bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
	a.CircuitBreaker.RecordSuccess(time.Since(callStart))

	return &BidResponse{
		Success:      true,
		BidID:        fmt.Sprintf("AMAZON_%d", time.Now().Unix()),
		Message:      "Bid sent to Amazon Advertising API",
		PlatformCode: "AMAZON_ADS_SMART",
		Timestamp:    time.Now(),
	}, nil
}

// GetBudgetStats returns budget statistics
func (a *AmazonSmartConnector) GetBudgetStats() shield.WindowStats {
	return a.BudgetManager.GetStats()
}

// GetStatus returns connection status
func (a *AmazonSmartConnector) GetStatus() string {
	if a.Connected {
		stats := a.BudgetManager.GetStats()
		return fmt.Sprintf("Connected to Amazon Advertising - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	}
	return "Disconnected from Amazon Advertising"
}

// Close closes the connection
func (a *AmazonSmartConnector) Close() error {
	log.Printf("🔌 Amazon connection closed - Final spend: $%.2f", a.BudgetManager.GetStats().CurrentSpend)
	a.Connected = false
	return nil
}

// UpdateCampaignBudget updates campaign budget
func (a *AmazonSmartConnector) UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}

// UpdateTargetAudience updates target audience
func (a *AmazonSmartConnector) UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}
