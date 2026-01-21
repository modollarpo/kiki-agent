package crm

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// HubSpotConnector integrates with HubSpot CRM
type HubSpotConnector struct {
	APIKey     string
	BaseURL    string
	httpClient *http.Client
}

// NewHubSpotConnector creates a new HubSpot CRM connector
func NewHubSpotConnector(apiKey string) *HubSpotConnector {
	return &HubSpotConnector{
		APIKey:  apiKey,
		BaseURL: "https://api.hubapi.com",
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (h *HubSpotConnector) Connect() error {
	// Test API key by fetching account info
	req, err := http.NewRequest("GET", h.BaseURL+"/contacts/v1/lists/all/contacts/all", nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+h.APIKey)

	resp, err := h.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("HubSpot authentication failed: %d", resp.StatusCode)
	}

	return nil
}

func (h *HubSpotConnector) FetchCustomers(filter map[string]interface{}) ([]Customer, error) {
	req, err := http.NewRequest("GET", h.BaseURL+"/contacts/v1/lists/all/contacts/all?count=100", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+h.APIKey)

	resp, err := h.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var hubspotResp struct {
		Contacts []struct {
			VID        int64 `json:"vid"`
			Properties struct {
				Email     struct{ Value string } `json:"email"`
				FirstName struct{ Value string } `json:"firstname"`
				LastName  struct{ Value string } `json:"lastname"`
				Phone     struct{ Value string } `json:"phone"`
			} `json:"properties"`
		} `json:"contacts"`
	}

	if err := json.Unmarshal(body, &hubspotResp); err != nil {
		return nil, err
	}

	customers := make([]Customer, 0, len(hubspotResp.Contacts))
	for _, contact := range hubspotResp.Contacts {
		customers = append(customers, Customer{
			ID:        fmt.Sprintf("%d", contact.VID),
			Email:     contact.Properties.Email.Value,
			FirstName: contact.Properties.FirstName.Value,
			LastName:  contact.Properties.LastName.Value,
			Phone:     contact.Properties.Phone.Value,
		})
	}

	return customers, nil
}

func (h *HubSpotConnector) GetCustomer(id string) (*Customer, error) {
	req, err := http.NewRequest("GET", h.BaseURL+"/contacts/v1/contact/vid/"+id+"/profile", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+h.APIKey)

	resp, err := h.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var contact struct {
		VID        int64 `json:"vid"`
		Properties struct {
			Email     struct{ Value string } `json:"email"`
			FirstName struct{ Value string } `json:"firstname"`
			LastName  struct{ Value string } `json:"lastname"`
		} `json:"properties"`
	}

	if err := json.Unmarshal(body, &contact); err != nil {
		return nil, err
	}

	return &Customer{
		ID:        id,
		Email:     contact.Properties.Email.Value,
		FirstName: contact.Properties.FirstName.Value,
		LastName:  contact.Properties.LastName.Value,
	}, nil
}

func (h *HubSpotConnector) UpdateCustomer(customer Customer) error {
	// Implementation for updating HubSpot contact
	return fmt.Errorf("not implemented")
}

func (h *HubSpotConnector) SendMessage(customerID, channel, message string, metadata map[string]string) error {
	// Implementation for sending messages via HubSpot
	return fmt.Errorf("not implemented")
}

func (h *HubSpotConnector) CreateTag(customerID, tag string) error {
	// Implementation for adding tags in HubSpot
	return fmt.Errorf("not implemented")
}

func (h *HubSpotConnector) GetName() string {
	return "HubSpot"
}

func (h *HubSpotConnector) Close() error {
	return nil
}
