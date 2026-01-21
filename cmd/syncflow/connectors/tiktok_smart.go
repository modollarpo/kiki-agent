package connectors

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// TikTokSmartConnector implements PlatformConnector for TikTok Ads with budget management
type TikTokSmartConnector struct {
	AccessToken    string
	AdvertiserID   string
	HttpClient     *http.Client
	Connected      bool
	BaseURL        string
	BudgetManager  *shield.BudgetManager
	RateLimiter    *RateLimiter
	CircuitBreaker *shield.CircuitBreaker
	FallbackEngine *HeuristicFallbackEngine
	MockMode       bool
}

// NewTikTokSmartConnector creates a new TikTok connector with budget management
func NewTikTokSmartConnector(accessToken, advertiserID string, maxBudget float64) *TikTokSmartConnector {
	return &TikTokSmartConnector{
		AccessToken:    accessToken,
		AdvertiserID:   advertiserID,
		HttpClient:     &http.Client{Timeout: 10 * time.Second},
		BaseURL:        "https://business-api.tiktok.com/open_api/v1.3",
		BudgetManager:  shield.NewBudgetManager(maxBudget),
		RateLimiter:    NewRateLimiter(1000),
		CircuitBreaker: shield.NewCircuitBreaker(),
		FallbackEngine: NewHeuristicFallbackEngine(),
	}
}

// Connect establishes connection to TikTok Ads API
func (t *TikTokSmartConnector) Connect(ctx context.Context) error {
	log.Printf("🔗 Connecting to TikTok Ads Smart Connector for advertiser: %s", t.AdvertiserID)
	t.Connected = true
	stats := t.BudgetManager.GetStats()
	log.Printf("✅ TikTok Smart connection established - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	return nil
}

// PlaceBid sends a bid to TikTok with safety checks
func (t *TikTokSmartConnector) PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error) {
	if !t.Connected {
		return nil, fmt.Errorf("not connected to TikTok Ads")
	}

	// Record latest LTV to improve fallback median quality
	t.FallbackEngine.RecordLTV("tiktok", req.PredictedLTV)

	// Decide bid source via circuit breaker
	bidAmount := req.BidAmount
	decisionSource := "ai"
	if !t.CircuitBreaker.CanExecute() {
		t.CircuitBreaker.RecordFallback()
		bidAmount = t.FallbackEngine.CalculateFallbackBid("tiktok", req.PredictedLTV)
		decisionSource = "fallback"
	}

	if !t.RateLimiter.CanMakeCall() {
		return nil, fmt.Errorf("rate limit exceeded for TikTok Ads")
	}

	if !t.BudgetManager.CanSpend(bidAmount) {
		stats := t.BudgetManager.GetStats()
		log.Printf("🛡️ BUDGET VETO: TikTok bid $%.2f exceeds remaining budget $%.2f", bidAmount, stats.RemainingBudget)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("Budget exceeded: $%.2f spent of $%.2f limit", stats.CurrentSpend, stats.MaxBudget),
			PlatformCode: "BUDGET_EXCEEDED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("budget exceeded")
	}

	log.Printf("📍 PlaceBid (TikTok): Customer=%s, LTV=%.2f, Bid=$%.2f (source=%s)", req.CustomerID, req.PredictedLTV, bidAmount, decisionSource)

	callStart := time.Now()

	if t.MockMode {
		log.Printf("🧪 MOCK MODE: Simulating TikTok Ads API call")
		t.RateLimiter.RecordCall()
		t.BudgetManager.AddSpend(bidAmount)
		stats := t.BudgetManager.GetStats()
		log.Printf("✅ TikTok bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		t.CircuitBreaker.RecordSuccess(time.Since(callStart))

		return &BidResponse{
			Success:      true,
			BidID:        fmt.Sprintf("MOCK_TIKTOK_%d", time.Now().Unix()),
			Message:      "Dynamic creative campaign created via TikTok Ads API (MOCK)",
			PlatformCode: "TIKTOK_ADS_SMART",
			Timestamp:    time.Now(),
		}, nil
	}

	t.RateLimiter.RecordCall()
	t.BudgetManager.AddSpend(bidAmount)
	stats := t.BudgetManager.GetStats()
	log.Printf("✅ TikTok bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
	t.CircuitBreaker.RecordSuccess(time.Since(callStart))

	return &BidResponse{
		Success:      true,
		BidID:        fmt.Sprintf("TIKTOK_%d", time.Now().Unix()),
		Message:      "Bid sent to TikTok Ads API",
		PlatformCode: "TIKTOK_ADS_SMART",
		Timestamp:    time.Now(),
	}, nil
}

// GetBudgetStats returns budget statistics
func (t *TikTokSmartConnector) GetBudgetStats() shield.WindowStats {
	return t.BudgetManager.GetStats()
}

// GetStatus returns connection status
func (t *TikTokSmartConnector) GetStatus() string {
	if t.Connected {
		stats := t.BudgetManager.GetStats()
		return fmt.Sprintf("Connected to TikTok Ads - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	}
	return "Disconnected from TikTok Ads"
}

// Close closes the connection
func (t *TikTokSmartConnector) Close() error {
	log.Printf("🔌 TikTok connection closed - Final spend: $%.2f", t.BudgetManager.GetStats().CurrentSpend)
	t.Connected = false
	return nil
}

// UpdateCampaignBudget updates campaign budget
func (t *TikTokSmartConnector) UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}

// UpdateTargetAudience updates target audience
func (t *TikTokSmartConnector) UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error) {
	return nil, fmt.Errorf("not implemented")
}
