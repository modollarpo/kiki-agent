package connectors

import (
	"fmt"
)

// ConnectorType defines supported ad platforms
type ConnectorType string

const (
	GoogleAds      ConnectorType = "google_ads"
	GoogleAdsSmart ConnectorType = "google_ads_smart" // With BudgetManager
	Meta           ConnectorType = "meta"
	MetaSmart      ConnectorType = "meta_smart" // With BudgetManager
	TradeDesk      ConnectorType = "tradedesk"
	TradeDeskSmart ConnectorType = "tradedesk_smart" // With BudgetManager
	Amazon         ConnectorType = "amazon"
	AmazonSmart    ConnectorType = "amazon_smart" // With BudgetManager
	X              ConnectorType = "x"
	XSmart         ConnectorType = "x_smart" // With BudgetManager
	LinkedIn       ConnectorType = "linkedin"
	LinkedInSmart  ConnectorType = "linkedin_smart" // With BudgetManager
	TikTok         ConnectorType = "tiktok"
	TikTokSmart    ConnectorType = "tiktok_smart" // With BudgetManager
)

// ConnectorConfig holds configuration for connector initialization
type ConnectorConfig struct {
	Type         ConnectorType
	APIKey       string  // Primary authentication key
	AccessToken  string  // For OAuth2 platforms
	CustomerID   string  // For Google Ads
	BusinessID   string  // For Meta
	PartnerID    string  // For Trade Desk
	ProfileID    string  // For Amazon
	AccountID    string  // For X, LinkedIn
	AdvertiserID string  // For TikTok
	MaxBudget    float64 // For smart connectors with budget management
}

// NewConnector creates and returns the appropriate connector based on type
func NewConnector(config ConnectorConfig) (PlatformConnector, error) {
	switch config.Type {
	case GoogleAds:
		return NewGoogleAdsConnector(config.APIKey, config.CustomerID), nil
	case GoogleAdsSmart:
		if config.MaxBudget <= 0 {
			return nil, fmt.Errorf("google_ads_smart requires MaxBudget > 0")
		}
		return NewGoogleAdsSmartConnector(config.APIKey, config.CustomerID, config.MaxBudget), nil
	case Meta:
		return NewMetaConnector(config.APIKey, config.BusinessID), nil
	case MetaSmart:
		if config.MaxBudget <= 0 {
			return nil, fmt.Errorf("meta_smart requires MaxBudget > 0")
		}
		return NewMetaSmartConnector(config.APIKey, config.BusinessID, config.MaxBudget), nil
	case TradeDesk:
		return NewTradesDeskConnector(config.APIKey, config.PartnerID), nil
	case TradeDeskSmart:
		if config.MaxBudget <= 0 {
			return nil, fmt.Errorf("tradedesk_smart requires MaxBudget > 0")
		}
		return NewTradeDeskSmartConnector(config.APIKey, config.PartnerID, config.MaxBudget), nil
	case Amazon:
		return NewAmazonConnector(config.APIKey, config.ProfileID), nil
	case AmazonSmart:
		if config.MaxBudget <= 0 {
			return nil, fmt.Errorf("amazon_smart requires MaxBudget > 0")
		}
		return NewAmazonSmartConnector(config.APIKey, config.ProfileID, config.MaxBudget), nil
	case X:
		return NewXConnector(config.APIKey, config.AccountID), nil
	case XSmart:
		if config.MaxBudget <= 0 {
			return nil, fmt.Errorf("x_smart requires MaxBudget > 0")
		}
		return NewXSmartConnector(config.APIKey, config.AccountID, config.MaxBudget), nil
	case LinkedIn:
		return NewLinkedInConnector(config.AccessToken, config.AccountID), nil
	case LinkedInSmart:
		if config.MaxBudget <= 0 {
			return nil, fmt.Errorf("linkedin_smart requires MaxBudget > 0")
		}
		return NewLinkedInSmartConnector(config.AccessToken, config.AccountID, config.MaxBudget), nil
	case TikTok:
		return NewTikTokConnector(config.AccessToken, config.AdvertiserID), nil
	case TikTokSmart:
		if config.MaxBudget <= 0 {
			return nil, fmt.Errorf("tiktok_smart requires MaxBudget > 0")
		}
		return NewTikTokSmartConnector(config.AccessToken, config.AdvertiserID, config.MaxBudget), nil
	default:
		return nil, fmt.Errorf("unsupported connector type: %s", config.Type)
	}
}
