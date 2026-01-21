package crm

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// ShopifyConnector integrates with Shopify ecommerce platform
type ShopifyConnector struct {
	ShopURL     string // e.g., "mystore.myshopify.com"
	AccessToken string
	APIVersion  string
	httpClient  *http.Client
}

// NewShopifyConnector creates a new Shopify connector
func NewShopifyConnector(shopURL, accessToken string) *ShopifyConnector {
	return &ShopifyConnector{
		ShopURL:     shopURL,
		AccessToken: accessToken,
		APIVersion:  "2024-01",
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (s *ShopifyConnector) Connect() error {
	url := fmt.Sprintf("https://%s/admin/api/%s/shop.json", s.ShopURL, s.APIVersion)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("X-Shopify-Access-Token", s.AccessToken)

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("Shopify authentication failed: %d", resp.StatusCode)
	}

	return nil
}

func (s *ShopifyConnector) FetchCustomers(filter map[string]interface{}) ([]Customer, error) {
	url := fmt.Sprintf("https://%s/admin/api/%s/customers.json?limit=250", s.ShopURL, s.APIVersion)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("X-Shopify-Access-Token", s.AccessToken)

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var shopifyResp struct {
		Customers []struct {
			ID            int64  `json:"id"`
			Email         string `json:"email"`
			FirstName     string `json:"first_name"`
			LastName      string `json:"last_name"`
			Phone         string `json:"phone"`
			OrdersCount   int    `json:"orders_count"`
			TotalSpent    string `json:"total_spent"`
			LastOrderName string `json:"last_order_name"`
			Tags          string `json:"tags"`
			UpdatedAt     string `json:"updated_at"`
		} `json:"customers"`
	}

	if err := json.Unmarshal(body, &shopifyResp); err != nil {
		return nil, err
	}

	customers := make([]Customer, 0, len(shopifyResp.Customers))
	for _, shopifyCustomer := range shopifyResp.Customers {
		var totalSpend float64
		fmt.Sscanf(shopifyCustomer.TotalSpent, "%f", &totalSpend)

		tags := []string{}
		if shopifyCustomer.Tags != "" {
			tags = strings.Split(shopifyCustomer.Tags, ",")
			for i := range tags {
				tags[i] = strings.TrimSpace(tags[i])
			}
		}

		customer := Customer{
			ID:            fmt.Sprintf("%d", shopifyCustomer.ID),
			Email:         shopifyCustomer.Email,
			FirstName:     shopifyCustomer.FirstName,
			LastName:      shopifyCustomer.LastName,
			Phone:         shopifyCustomer.Phone,
			PurchaseCount: shopifyCustomer.OrdersCount,
			TotalSpend:    totalSpend,
			Tags:          tags,
		}

		// Parse updated_at timestamp
		if t, err := time.Parse(time.RFC3339, shopifyCustomer.UpdatedAt); err == nil {
			customer.LastEngagement = t
		}

		customers = append(customers, customer)
	}

	return customers, nil
}

func (s *ShopifyConnector) GetCustomer(id string) (*Customer, error) {
	url := fmt.Sprintf("https://%s/admin/api/%s/customers/%s.json", s.ShopURL, s.APIVersion, id)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("X-Shopify-Access-Token", s.AccessToken)

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var shopifyResp struct {
		Customer struct {
			ID          int64  `json:"id"`
			Email       string `json:"email"`
			FirstName   string `json:"first_name"`
			LastName    string `json:"last_name"`
			OrdersCount int    `json:"orders_count"`
			TotalSpent  string `json:"total_spent"`
		} `json:"customer"`
	}

	if err := json.Unmarshal(body, &shopifyResp); err != nil {
		return nil, err
	}

	var totalSpend float64
	fmt.Sscanf(shopifyResp.Customer.TotalSpent, "%f", &totalSpend)

	return &Customer{
		ID:            id,
		Email:         shopifyResp.Customer.Email,
		FirstName:     shopifyResp.Customer.FirstName,
		LastName:      shopifyResp.Customer.LastName,
		PurchaseCount: shopifyResp.Customer.OrdersCount,
		TotalSpend:    totalSpend,
	}, nil
}

func (s *ShopifyConnector) UpdateCustomer(customer Customer) error {
	return fmt.Errorf("not implemented")
}

func (s *ShopifyConnector) SendMessage(customerID, channel, message string, metadata map[string]string) error {
	// Shopify doesn't have built-in messaging - would integrate with email provider
	return fmt.Errorf("not implemented - use email provider integration")
}

func (s *ShopifyConnector) CreateTag(customerID, tag string) error {
	// Add tag to Shopify customer
	url := fmt.Sprintf("https://%s/admin/api/%s/customers/%s.json", s.ShopURL, s.APIVersion, customerID)

	// First, get current tags
	customer, err := s.GetCustomer(customerID)
	if err != nil {
		return err
	}

	// Add new tag
	newTags := append(customer.Tags, tag)
	tagsStr := strings.Join(newTags, ", ")

	payload := map[string]interface{}{
		"customer": map[string]interface{}{
			"id":   customerID,
			"tags": tagsStr,
		},
	}

	payloadBytes, _ := json.Marshal(payload)
	req, err := http.NewRequest("PUT", url, strings.NewReader(string(payloadBytes)))
	if err != nil {
		return err
	}
	req.Header.Set("X-Shopify-Access-Token", s.AccessToken)
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("failed to update tags: %d", resp.StatusCode)
	}

	return nil
}

func (s *ShopifyConnector) GetName() string {
	return "Shopify"
}

func (s *ShopifyConnector) Close() error {
	return nil
}
