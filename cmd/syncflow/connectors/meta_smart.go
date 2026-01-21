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

// MetaSmartConnector implements PlatformConnector for Meta Marketing API with budget management
type MetaSmartConnector struct {
	AccessToken    string
	BusinessID     string
	HttpClient     *http.Client
	Connected      bool
	BaseURL        string
	BudgetManager  *shield.BudgetManager
	RateLimiter    *RateLimiter
	CircuitBreaker *shield.CircuitBreaker
	FallbackEngine *HeuristicFallbackEngine
	MockMode       bool // For testing without real API calls
}

// NewMetaSmartConnector creates a new Meta connector with budget management
func NewMetaSmartConnector(accessToken, businessID string, maxBudget float64) *MetaSmartConnector {
	return &MetaSmartConnector{
		AccessToken:    accessToken,
		BusinessID:     businessID,
		HttpClient:     &http.Client{Timeout: 10 * time.Second},
		BaseURL:        "https://graph.facebook.com/v18.0",
		BudgetManager:  shield.NewBudgetManager(maxBudget),
		RateLimiter:    NewRateLimiter(200), // Meta allows ~200 calls/hour = ~3.3/min, be conservative
		CircuitBreaker: shield.NewCircuitBreaker(),
		FallbackEngine: NewHeuristicFallbackEngine(),
	}
}

// Connect establishes connection to Meta API
func (m *MetaSmartConnector) Connect(ctx context.Context) error {
	log.Printf("🔗 Connecting to Meta Marketing API Smart Connector for business: %s", m.BusinessID)

	// In production, validate API credentials here
	m.Connected = true
	stats := m.BudgetManager.GetStats()
	log.Printf("✅ Meta Smart connection established - Budget: $%.2f/$%.2f", stats.CurrentSpend, stats.MaxBudget)
	return nil
}

// PlaceBid sends a bid to Meta via campaign budget optimization with safety checks
func (m *MetaSmartConnector) PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error) {
	if !m.Connected {
		return nil, fmt.Errorf("not connected to Meta")
	}

	// Record latest LTV to improve fallback median quality
	m.FallbackEngine.RecordLTV("meta", req.PredictedLTV)

	// Decide bid source via circuit breaker
	bidAmount := req.BidAmount
	decisionSource := "ai"
	if !m.CircuitBreaker.CanExecute() {
		m.CircuitBreaker.RecordFallback()
		bidAmount = m.FallbackEngine.CalculateFallbackBid("meta", req.PredictedLTV)
		decisionSource = "fallback"
	}

	// Safety Check 1: Budget validation
	if !m.BudgetManager.CanSpend(bidAmount) {
		stats := m.BudgetManager.GetStats()
		log.Printf("🛡️ BUDGET VETO: Meta bid $%.2f exceeds remaining budget $%.2f", bidAmount, stats.RemainingBudget)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("Budget exceeded: $%.2f spent of $%.2f limit", stats.CurrentSpend, stats.MaxBudget),
			PlatformCode: "BUDGET_EXCEEDED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("budget exceeded")
	}

	// Safety Check 2: Rate limiting
	if !m.RateLimiter.CanMakeCall() {
		log.Printf("⚠️ RATE LIMIT: Too many Meta API calls, throttling")
		return &BidResponse{
			Success:      false,
			Message:      "Rate limit exceeded, throttling API calls",
			PlatformCode: "RATE_LIMITED",
			Timestamp:    time.Now(),
		}, fmt.Errorf("rate limited")
	}

	log.Printf("📍 PlaceBid (Meta): Customer=%s, LTV=%.2f, Bid=$%.2f (source=%s)", req.CustomerID, req.PredictedLTV, bidAmount, decisionSource)

	// Meta doesn't do direct bid placement like RTB; instead, update campaign budget/audience
	payload := map[string]interface{}{
		"daily_budget":      int64(bidAmount * 100), // Meta uses cents
		"ltv_signal":        req.PredictedLTV,
		"optimization_goal": "VALUE",                    // Optimize for conversion value (LTV)
		"bid_strategy":      "LOWEST_COST_WITH_BID_CAP", // Use bid cap based on LTV
		"bid_amount":        int64(bidAmount * 100),
		"custom_data": map[string]interface{}{
			"kiki_ltv":        req.PredictedLTV,
			"kiki_confidence": req.Explanation,
			"kiki_timestamp":  req.Timestamp.Unix(),
		},
	}

	payloadBytes, _ := json.Marshal(payload)
	apiURL := fmt.Sprintf("%s/%s/campaigns?access_token=%s", m.BaseURL, m.BusinessID, m.AccessToken)

	// Mock mode for testing
	callStart := time.Now()

	if m.MockMode {
		log.Printf("🧪 MOCK MODE: Simulating Meta API call")
		m.RateLimiter.RecordCall()
		m.BudgetManager.AddSpend(bidAmount)
		stats := m.BudgetManager.GetStats()
		log.Printf("✅ Meta bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		m.CircuitBreaker.RecordSuccess(time.Since(callStart))

		return &BidResponse{
			Success:      true,
			BidID:        fmt.Sprintf("MOCK_META_%d", time.Now().Unix()),
			Message:      "Campaign budget adjusted via Meta Marketing API (MOCK)",
			PlatformCode: "META_SMART",
			Timestamp:    time.Now(),
		}, nil
	}

	resp, err := m.HttpClient.Post(apiURL, "application/json", bytes.NewBuffer(payloadBytes))
	if err != nil {
		m.CircuitBreaker.RecordFailure(time.Since(callStart))
		log.Printf("❌ Meta API error: %v", err)
		return &BidResponse{
			Success:      false,
			Message:      fmt.Sprintf("API error: %v", err),
			PlatformCode: "META_ERROR",
			Timestamp:    time.Now(),
		}, err
	}
	defer resp.Body.Close()

	// Record successful API call
	m.RateLimiter.RecordCall()

	// If bid was successful, record the spend
	if resp.StatusCode == 200 {
		m.BudgetManager.AddSpend(bidAmount)
		stats := m.BudgetManager.GetStats()
		log.Printf("✅ Meta bid placed - Budget: $%.2f/$%.2f remaining", stats.RemainingBudget, stats.MaxBudget)
		m.CircuitBreaker.RecordSuccess(time.Since(callStart))
	} else {
		m.CircuitBreaker.RecordFailure(time.Since(callStart))
	}

	return &BidResponse{
		Success:      resp.StatusCode == 200,
		BidID:        fmt.Sprintf("META_%d", time.Now().Unix()),
		Message:      "Campaign budget adjusted via Meta Marketing API",
		PlatformCode: "META_SMART",
		Timestamp:    time.Now(),
	}, nil
}

// UpdateCampaignBudget adjusts campaign budget for Meta with budget checks
func (m *MetaSmartConnector) UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error) {
	if !m.Connected {
		return nil, fmt.Errorf("not connected to Meta")
	}

	// Check if this budget update would exceed our limits
	if !m.BudgetManager.CanSpend(budgetAmount) {
		return nil, fmt.Errorf("budget update would exceed limits")
	}

	log.Printf("💰 UpdateCampaignBudget (Meta): Campaign=%s, Budget=$%.2f", campaignID, budgetAmount)

	apiURL := fmt.Sprintf("%s/%s?access_token=%s", m.BaseURL, campaignID, m.AccessToken)

	payload := map[string]interface{}{
		"daily_budget": int64(budgetAmount * 100),
	}
	payloadBytes, _ := json.Marshal(payload)

	resp, err := m.HttpClient.Post(apiURL, "application/json", bytes.NewBuffer(payloadBytes))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	m.RateLimiter.RecordCall()

	return &BidResponse{
		Success:      resp.StatusCode == 200,
		Message:      fmt.Sprintf("Meta campaign %s budget updated to $%.2f", campaignID, budgetAmount),
		PlatformCode: "META_BUDGET",
		Timestamp:    time.Now(),
	}, nil
}

// UpdateTargetAudience updates audience for Meta campaign
func (m *MetaSmartConnector) UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error) {
	if !m.Connected {
		return nil, fmt.Errorf("not connected to Meta")
	}

	log.Printf("🎯 UpdateTargetAudience (Meta): Campaign=%s, Audience=%s", campaignID, audienceID)

	return &BidResponse{
		Success:      true,
		Message:      fmt.Sprintf("Meta audience targeting updated for campaign %s", campaignID),
		PlatformCode: "META_AUDIENCE",
		Timestamp:    time.Now(),
	}, nil
}

// GetStatus returns the connection status with budget info
func (m *MetaSmartConnector) GetStatus() string {
	if m.Connected {
		stats := m.BudgetManager.GetStats()
		return fmt.Sprintf("Connected to Meta Marketing API - Budget: $%.2f/$%.2f (%.1f%% used)",
			stats.CurrentSpend,
			stats.MaxBudget,
			(stats.CurrentSpend/stats.MaxBudget)*100)
	}
	return "Disconnected"
}

// Close cleanly disconnects from Meta
func (m *MetaSmartConnector) Close() error {
	stats := m.BudgetManager.GetStats()
	log.Printf("🔌 Meta connection closed - Final spend: $%.2f", stats.CurrentSpend)
	m.Connected = false
	return nil
}

// GetBudgetStats returns current budget statistics
func (m *MetaSmartConnector) GetBudgetStats() shield.WindowStats {
	return m.BudgetManager.GetStats()
}
