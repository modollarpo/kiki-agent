package connectors

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/user/kiki-agent/cmd/syncshield/shield"
)

// TradeDeskSmartConnector implements PlatformConnector for The Trade Desk OpenRTB with budget management
type TradeDeskSmartConnector struct {
	APIKey         string
	PartnerID      string
	HttpClient     *http.Client
	Connected      bool
	BaseURL        string
	BudgetManager  *shield.BudgetManager
	RateLimiter    *RateLimiter
	CircuitBreaker *shield.CircuitBreaker
	FallbackEngine *HeuristicFallbackEngine
	MockMode       bool // For testing without real API calls
}

// NewTradeDeskSmartConnector creates a new Trade Desk connector with budget management
func NewTradeDeskSmartConnector(apiKey, partnerID string, maxBudget float64) *TradeDeskSmartConnector {
	return &TradeDeskSmartConnector{
		APIKey:         apiKey,
		PartnerID:      partnerID,
		HttpClient:     &http.Client{Timeout: 10 * time.Second},
		BaseURL:        "https://api.thetradedesk.com/v3",
		BudgetManager:  shield.NewBudgetManager(maxBudget),
		RateLimiter:    NewRateLimiter(300), // Trade Desk is more generous with rate limits
		CircuitBreaker: shield.NewCircuitBreaker(),
		FallbackEngine: NewHeuristicFallbackEngine(),
	}
}

// Connect establishes connection to Trade Desk OpenRTB
func (t *TradeDeskSmartConnector) Connect(ctx context.Context) error {
	log.Printf("🔗 Connecting to Trade Desk OpenRTB Smart Connector for partner: %s", t.PartnerID)

	// In production, validate API credentials here
	t.Connected = true
	stats := t.BudgetManager.GetStats()
	log.Printf("✅ Trade Desk Smart connection established - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	return nil
}

// PlaceBid sends an OpenRTB 2.5 compliant bid to Trade Desk with safety checks
func (t *TradeDeskSmartConnector) PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error) {
	if !t.Connected {
		return nil, fmt.Errorf("not connected to Trade Desk")
	}

	// Record latest LTV to improve fallback median quality
	t.FallbackEngine.RecordLTV("tradedesk", req.PredictedLTV)

	// Decide bid source via circuit breaker
	bidAmount := req.BidAmount
	decisionSource := "ai"
	if !t.CircuitBreaker.CanExecute() {
		t.CircuitBreaker.RecordFallback()
		bidAmount = t.FallbackEngine.CalculateFallbackBid("tradedesk", req.PredictedLTV)
		decisionSource = "fallback"
	}

	// Safety Check 1: Budget validation
	if !t.BudgetManager.CanSpend(bidAmount) {
		stats := t.BudgetManager.GetStats()
		log.Printf("🛡️ BUDGET VETO: Trade Desk bid $%.2f exceeds remaining budget $%.2f", bidAmount, stats.RemainingBudget)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("Budget exceeded: $%.2f spent of $%.2f limit", stats.CurrentSpend, stats.MaxBudget),
			PlatformCode: "BUDGET_EXCEEDED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("budget exceeded")
	}

	// Safety Check 2: Rate limiting
	if !t.RateLimiter.CanMakeCall() {
		log.Printf("⚠️ RATE LIMIT: Too many Trade Desk API calls, throttling")
		return &BidResponse{
			Success:      false,
			Message:      "Rate limit exceeded, throttling API calls",
			PlatformCode: "RATE_LIMITED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("rate limited")
	}

	log.Printf("📍 PlaceBid (Trade Desk OpenRTB 2.5): Customer=%s, LTV=%.2f, Bid=$%.2f (source=%s)", req.CustomerID, req.PredictedLTV, bidAmount, decisionSource)

	// OpenRTB 2.5 Bid Response format with LTV extensions
	openRTBBid := map[string]interface{}{
		"id":      fmt.Sprintf("BID_%d", time.Now().Unix()),
		"impid":   req.CustomerID,
		"price":   bidAmount,
		"nurl":    "https://kiki-agent.com/win-notice",  // Win notice URL
		"burl":    "https://kiki-agent.com/billing",     // Billing notice URL
		"lurl":    "https://kiki-agent.com/loss-notice", // Loss notice URL
		"adomain": []string{"kiki-agent.com"},
		"ext": map[string]interface{}{
			"kiki": map[string]interface{}{
				"ltv_signal":     req.PredictedLTV,
				"ltv_confidence": req.Explanation,
				"bid_strategy":   "LTV_OPTIMIZED",
				"timestamp":      req.Timestamp.Unix(),
			},
		},
	}

	payloadBytes, _ := json.Marshal(openRTBBid)
	apiURL := fmt.Sprintf("%s/bids?api_key=%s", t.BaseURL, t.APIKey)

	// Mock mode for testing
	callStart := time.Now()

	if t.MockMode {
		log.Printf("🧪 MOCK MODE: Simulating Trade Desk OpenRTB call")
		t.RateLimiter.RecordCall()
		t.BudgetManager.AddSpend(bidAmount)
		stats := t.BudgetManager.GetStats()
		log.Printf("✅ Trade Desk bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		t.CircuitBreaker.RecordSuccess(time.Since(callStart))

		return &BidResponse{
			Success:      true,
			BidID:        fmt.Sprintf("MOCK_TTD_%d", time.Now().Unix()),
			Message:      "Bid placed via OpenRTB 2.5 to Trade Desk (MOCK)",
			PlatformCode: "TRADEDESK_RTB_SMART",
			Timestamp:    time.Now(),
		}, nil
	}

	resp, err := t.HttpClient.Post(apiURL, "application/json", bytes.NewBuffer(payloadBytes))
	if err != nil {
		t.CircuitBreaker.RecordFailure(time.Since(callStart))
		log.Printf("❌ Trade Desk API error: %v", err)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("API error: %v", err),
			PlatformCode: "TRADEDESK_ERROR",
			Timestamp:    time.Now(),
		}, err
	}
	defer resp.Body.Close()

	// Record successful API call
	t.RateLimiter.RecordCall()

	// If bid was successful, record the spend
	if resp.StatusCode == 200 {
		t.BudgetManager.AddSpend(bidAmount)
		stats := t.BudgetManager.GetStats()
		log.Printf("✅ Trade Desk bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		t.CircuitBreaker.RecordSuccess(time.Since(callStart))
	} else {
		t.CircuitBreaker.RecordFailure(time.Since(callStart))
	}

	return &BidResponse{
		Success:      resp.StatusCode == 200,
		BidID:        fmt.Sprintf("TTD_%d", time.Now().Unix()),
		Message:      "Bid placed via OpenRTB 2.5 to Trade Desk",
		PlatformCode: "TRADEDESK_RTB_SMART",
		Timestamp:    time.Now(),
	}, nil
}

// UpdateCampaignBudget updates Trade Desk campaign budget with budget checks
func (t *TradeDeskSmartConnector) UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error) {
	if !t.Connected {
		return nil, fmt.Errorf("not connected to Trade Desk")
	}

	// Check if this budget update would exceed our limits
	if !t.BudgetManager.CanSpend(budgetAmount) {
		return nil, fmt.Errorf("budget update would exceed limits")
	}

	log.Printf("💰 UpdateCampaignBudget (Trade Desk): Campaign=%s, Budget=$%.2f", campaignID, budgetAmount)

	return &BidResponse{
		Success:      true,
		Message:      fmt.Sprintf("Trade Desk campaign %s budget updated to $%.2f", campaignID, budgetAmount),
		PlatformCode: "TRADEDESK_BUDGET",
		Timestamp:    time.Now(),
	}, nil
}

// UpdateTargetAudience updates audience for Trade Desk
func (t *TradeDeskSmartConnector) UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error) {
	if !t.Connected {
		return nil, fmt.Errorf("not connected to Trade Desk")
	}

	log.Printf("🎯 UpdateTargetAudience (Trade Desk): Campaign=%s, Audience=%s", campaignID, audienceID)

	return &BidResponse{
		Success:      true,
		Message:      fmt.Sprintf("Trade Desk audience updated for campaign %s", campaignID),
		PlatformCode: "TRADEDESK_AUDIENCE",
		Timestamp:    time.Now(),
	}, nil
}

// GetStatus returns the connection status with budget info
func (t *TradeDeskSmartConnector) GetStatus() string {
	if t.Connected {
		stats := t.BudgetManager.GetStats()
		return fmt.Sprintf("Connected to Trade Desk OpenRTB - Budget: $%.2f/$%.2f (%.1f%% used)",
			stats.CurrentSpend,
			stats.MaxBudget,
			(stats.CurrentSpend/stats.MaxBudget)*100)
	}
	return "Disconnected"
}

// Close cleanly disconnects from Trade Desk
func (t *TradeDeskSmartConnector) Close() error {
	stats := t.BudgetManager.GetStats()
	log.Printf("🔌 Trade Desk connection closed - Final spend: $%.2f", stats.CurrentSpend)
	t.Connected = false
	return nil
}

// GetBudgetStats returns current budget statistics
func (t *TradeDeskSmartConnector) GetBudgetStats() shield.WindowStats {
	return t.BudgetManager.GetStats()
}
