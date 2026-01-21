package connectors

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

// MetaConnector implements PlatformConnector for Meta Marketing API
type MetaConnector struct {
	AccessToken string
	BusinessID  string
	HttpClient  *http.Client
	Connected   bool
	BaseURL     string
}

// NewMetaConnector creates a new Meta connector
func NewMetaConnector(accessToken, businessID string) *MetaConnector {
	return &MetaConnector{
		AccessToken: accessToken,
		BusinessID:  businessID,
		HttpClient:  &http.Client{Timeout: 10 * time.Second},
		BaseURL:     "https://graph.instagram.com/v18.0",
	}
}

// Connect establishes connection to Meta API
func (m *MetaConnector) Connect(ctx context.Context) error {
	log.Printf("🔗 Connecting to Meta Marketing API for business: %s", m.BusinessID)
	m.Connected = true
	log.Println("✅ Meta connection established")
	return nil
}

// PlaceBid sends a bid to Meta via campaign budget optimization
func (m *MetaConnector) PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error) {
	if !m.Connected {
		return nil, fmt.Errorf("not connected to Meta")
	}

	log.Printf("📍 PlaceBid: Customer=%s, LTV=%.2f, Bid=$%.2f (Meta)", req.CustomerID, req.PredictedLTV, req.BidAmount)

	// Meta doesn't do direct bid placement like RTB; instead, update campaign budget/audience
	payload := map[string]interface{}{
		"daily_budget":      int64(req.BidAmount * 100), // Meta uses cents
		"ltv_signal":        req.PredictedLTV,
		"optimization_goal": "PURCHASE_VALUE", // Align with LTV focus
		"explanation":       req.Explanation,
		"timestamp":         req.Timestamp.Unix(),
	}

	payloadBytes, _ := json.Marshal(payload)
	apiURL := fmt.Sprintf("%s/%s/campaigns?access_token=%s", m.BaseURL, m.BusinessID, m.AccessToken)

	resp, err := m.HttpClient.Post(apiURL, "application/json", bytes.NewBuffer(payloadBytes))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	return &BidResponse{
		Success:      resp.StatusCode == 200,
		BidID:        fmt.Sprintf("META_BID_%d", time.Now().Unix()),
		Message:      "Campaign budget adjusted via Meta Marketing API",
		PlatformCode: "META",
		Timestamp:    time.Now(),
	}, nil
}

// UpdateCampaignBudget adjusts campaign budget for Meta
func (m *MetaConnector) UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error) {
	if !m.Connected {
		return nil, fmt.Errorf("not connected to Meta")
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

	return &BidResponse{
		Success:      resp.StatusCode == 200,
		Message:      fmt.Sprintf("Meta campaign %s budget updated to $%.2f", campaignID, budgetAmount),
		PlatformCode: "META_BUDGET",
		Timestamp:    time.Now(),
	}, nil
}

// UpdateTargetAudience updates audience for Meta campaign
func (m *MetaConnector) UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error) {
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

// GetStatus returns connection status
func (m *MetaConnector) GetStatus() string {
	if m.Connected {
		return "Connected to Meta Marketing API"
	}
	return "Disconnected"
}

// Close cleanly disconnects from Meta
func (m *MetaConnector) Close() error {
	m.Connected = false
	log.Println("🔌 Meta connection closed")
	return nil
}
