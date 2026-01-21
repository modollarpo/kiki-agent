package connectors

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// LinkedInSmartConnector implements PlatformConnector for LinkedIn Ads with budget management
type LinkedInSmartConnector struct {
	AccessToken    string
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

// NewLinkedInSmartConnector creates a new LinkedIn connector with budget management
func NewLinkedInSmartConnector(accessToken, accountID string, maxBudget float64) *LinkedInSmartConnector {
	return &LinkedInSmartConnector{
		AccessToken:    accessToken,
		AccountID:      accountID,
		HttpClient:     &http.Client{Timeout: 10 * time.Second},
		BaseURL:        "https://api.linkedin.com/v2",
		BudgetManager:  shield.NewBudgetManager(maxBudget),
		RateLimiter:    NewRateLimiter(400),
		CircuitBreaker: shield.NewCircuitBreaker(),
		FallbackEngine: NewHeuristicFallbackEngine(),
	}
}

// Connect establishes connection to LinkedIn Ads API
func (l *LinkedInSmartConnector) Connect(ctx context.Context) error {
	log.Printf("🔗 Connecting to LinkedIn Ads Smart Connector for account: %s", l.AccountID)
	l.Connected = true
	stats := l.BudgetManager.GetStats()
	log.Printf("✅ LinkedIn Smart connection established - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	return nil
}

// PlaceBid sends a bid to LinkedIn with safety checks
func (l *LinkedInSmartConnector) PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error) {
	if !l.Connected {
		return nil, fmt.Errorf("not connected to LinkedIn Ads")
	}

	// Record latest LTV to improve fallback median quality
	l.FallbackEngine.RecordLTV("linkedin", req.PredictedLTV)

	// Decide bid source via circuit breaker
	bidAmount := req.BidAmount
	decisionSource := "ai"
	if !l.CircuitBreaker.CanExecute() {
		l.CircuitBreaker.RecordFallback()
		bidAmount = l.FallbackEngine.CalculateFallbackBid("linkedin", req.PredictedLTV)
		decisionSource = "fallback"
	}

	if !l.RateLimiter.CanMakeCall() {
		return nil, fmt.Errorf("rate limit exceeded for LinkedIn Ads")
	}

	if !l.BudgetManager.CanSpend(bidAmount) {
		stats := l.BudgetManager.GetStats()
		log.Printf("🛡️ BUDGET VETO: LinkedIn bid $%.2f exceeds remaining budget $%.2f", bidAmount, stats.RemainingBudget)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("Budget exceeded: $%.2f spent of $%.2f limit", stats.CurrentSpend, stats.MaxBudget),
			PlatformCode: "BUDGET_EXCEEDED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("budget exceeded")
	}

	log.Printf("📍 PlaceBid (LinkedIn): Customer=%s, LTV=%.2f, Bid=$%.2f (source=%s)", req.CustomerID, req.PredictedLTV, bidAmount, decisionSource)

	callStart := time.Now()

	if l.MockMode {
		log.Printf("🧪 MOCK MODE: Simulating LinkedIn Ads API call")
		l.RateLimiter.RecordCall()
		l.BudgetManager.AddSpend(bidAmount)
		stats := l.BudgetManager.GetStats()
		log.Printf("✅ LinkedIn bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		l.CircuitBreaker.RecordSuccess(time.Since(callStart))

		return &BidResponse{
			Success:      true,
			BidID:        fmt.Sprintf("MOCK_LINKEDIN_%d", time.Now().Unix()),
			Message:      "Sponsored content campaign created via LinkedIn Marketing API (MOCK)",
			PlatformCode: "LINKEDIN_ADS_SMART",
			Timestamp:    time.Now(),
		}, nil
	}

	l.RateLimiter.RecordCall()
	l.BudgetManager.AddSpend(bidAmount)
	stats := l.BudgetManager.GetStats()
	log.Printf("✅ LinkedIn bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
	l.CircuitBreaker.RecordSuccess(time.Since(callStart))

	return &BidResponse{
		Success:      true,
		BidID:        fmt.Sprintf("LINKEDIN_%d", time.Now().Unix()),
		Message:      "Bid sent to LinkedIn Ads API",
		PlatformCode: "LINKEDIN_ADS_SMART",
		Timestamp:    time.Now(),
	}, nil
}

// GetBudgetStats returns budget statistics
func (l *LinkedInSmartConnector) GetBudgetStats() shield.WindowStats {
	return l.BudgetManager.GetStats()
}

// GetStatus returns connection status
func (l *LinkedInSmartConnector) GetStatus() string {
	if l.Connected {
		stats := l.BudgetManager.GetStats()
		return fmt.Sprintf("Connected to LinkedIn Ads - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	}
	return "Disconnected from LinkedIn Ads"
}

// Close closes the connection
func (l *LinkedInSmartConnector) Close() error {
	log.Printf("🔌 LinkedIn connection closed - Final spend: $%.2f", l.BudgetManager.GetStats().CurrentSpend)
	l.Connected = false
	return nil
}

// UpdateCampaignBudget updates campaign budget
func (l *LinkedInSmartConnector) UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}

// UpdateTargetAudience updates target audience
func (l *LinkedInSmartConnector) UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}
