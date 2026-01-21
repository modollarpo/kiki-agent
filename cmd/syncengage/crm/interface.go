package crm

import (
	"time"
)

// Customer represents a CRM customer record
type Customer struct {
	ID              string    `json:"customer_id"`
	Email           string    `json:"email"`
	Phone           string    `json:"phone"`
	FirstName       string    `json:"first_name"`
	LastName        string    `json:"last_name"`
	LastPurchase    time.Time `json:"last_purchase"`
	TotalSpend      float64   `json:"total_spend"`
	PurchaseCount   int       `json:"purchase_count"`
	EngagementScore float64   `json:"engagement_score"`
	LTV             float64   `json:"ltv"`
	ChurnRisk       string    `json:"churn_risk"`
	LastEngagement  time.Time `json:"last_engagement"`
	Tags            []string  `json:"tags"`
	Segment         string    `json:"segment"` // VIP, Regular, At-Risk, etc.
}

// CRMConnector defines the interface all CRM integrations must implement
type CRMConnector interface {
	// Connect establishes connection to the CRM
	Connect() error

	// FetchCustomers retrieves all customers or a filtered subset
	FetchCustomers(filter map[string]interface{}) ([]Customer, error)

	// GetCustomer retrieves a single customer by ID
	GetCustomer(id string) (*Customer, error)

	// UpdateCustomer updates customer data in the CRM
	UpdateCustomer(customer Customer) error

	// SendMessage sends a message to a customer (email, SMS, etc.)
	SendMessage(customerID, channel, message string, metadata map[string]string) error

	// CreateTag adds a tag to a customer
	CreateTag(customerID, tag string) error

	// GetName returns the CRM provider name
	GetName() string

	// Close closes the CRM connection
	Close() error
}
