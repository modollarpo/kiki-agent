package connectors

import (
	"context"
	"time"
)

// BidRequest represents a standardized bid request to an ad platform
type BidRequest struct {
	CustomerID   string
	PredictedLTV float64
	BidAmount    float64
	Explanation  string
	Timestamp    time.Time
	CampaignID   string
	AudienceID   string
}

// BidResponse represents the result of a bid placement
type BidResponse struct {
	Success      bool
	BidID        string
	Message      string
	PlatformCode string
	Timestamp    time.Time
}

// PlatformConnector defines the interface all ad platform adapters must implement
type PlatformConnector interface {
	// Connect establishes connection to the ad platform
	Connect(ctx context.Context) error

	// PlaceBid sends a bid to the ad platform with LTV-based decision
	PlaceBid(ctx context.Context, req *BidRequest) (*BidResponse, error)

	// UpdateCampaignBudget adjusts campaign budget based on LTV insights
	UpdateCampaignBudget(ctx context.Context, campaignID string, budgetAmount float64) (*BidResponse, error)

	// UpdateTargetAudience modifies audience targeting based on predicted LTV
	UpdateTargetAudience(ctx context.Context, campaignID string, audienceID string) (*BidResponse, error)

	// GetStatus returns the connection status
	GetStatus() string

	// Close cleanly disconnects from the platform
	Close() error
}
