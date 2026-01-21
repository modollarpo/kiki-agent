package crm

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// SalesforceConnector integrates with Salesforce CRM
type SalesforceConnector struct {
	InstanceURL string
	AccessToken string
	httpClient  *http.Client
}

// NewSalesforceConnector creates a new Salesforce CRM connector
func NewSalesforceConnector(instanceURL, accessToken string) *SalesforceConnector {
	return &SalesforceConnector{
		InstanceURL: instanceURL,
		AccessToken: accessToken,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (s *SalesforceConnector) Connect() error {
	// Test connection by querying user info
	req, err := http.NewRequest("GET", s.InstanceURL+"/services/oauth2/userinfo", nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+s.AccessToken)

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("Salesforce authentication failed: %d", resp.StatusCode)
	}

	return nil
}

func (s *SalesforceConnector) FetchCustomers(filter map[string]interface{}) ([]Customer, error) {
	query := "SELECT Id, Email, FirstName, LastName, Phone FROM Contact LIMIT 100"
	url := fmt.Sprintf("%s/services/data/v58.0/query/?q=%s", s.InstanceURL, query)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+s.AccessToken)

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var sfResp struct {
		Records []struct {
			ID        string `json:"Id"`
			Email     string `json:"Email"`
			FirstName string `json:"FirstName"`
			LastName  string `json:"LastName"`
			Phone     string `json:"Phone"`
		} `json:"records"`
	}

	if err := json.Unmarshal(body, &sfResp); err != nil {
		return nil, err
	}

	customers := make([]Customer, 0, len(sfResp.Records))
	for _, record := range sfResp.Records {
		customers = append(customers, Customer{
			ID:        record.ID,
			Email:     record.Email,
			FirstName: record.FirstName,
			LastName:  record.LastName,
			Phone:     record.Phone,
		})
	}

	return customers, nil
}

func (s *SalesforceConnector) GetCustomer(id string) (*Customer, error) {
	url := fmt.Sprintf("%s/services/data/v58.0/sobjects/Contact/%s", s.InstanceURL, id)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+s.AccessToken)

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var record struct {
		ID        string `json:"Id"`
		Email     string `json:"Email"`
		FirstName string `json:"FirstName"`
		LastName  string `json:"LastName"`
	}

	if err := json.Unmarshal(body, &record); err != nil {
		return nil, err
	}

	return &Customer{
		ID:        record.ID,
		Email:     record.Email,
		FirstName: record.FirstName,
		LastName:  record.LastName,
	}, nil
}

func (s *SalesforceConnector) UpdateCustomer(customer Customer) error {
	return fmt.Errorf("not implemented")
}

func (s *SalesforceConnector) SendMessage(customerID, channel, message string, metadata map[string]string) error {
	return fmt.Errorf("not implemented")
}

func (s *SalesforceConnector) CreateTag(customerID, tag string) error {
	return fmt.Errorf("not implemented")
}

func (s *SalesforceConnector) GetName() string {
	return "Salesforce"
}

func (s *SalesforceConnector) Close() error {
	return nil
}
