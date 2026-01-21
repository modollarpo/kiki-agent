package crm

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// SendGridEmailProvider sends emails via SendGrid API
type SendGridEmailProvider struct {
	APIKey     string
	httpClient *http.Client
}

// NewSendGridProvider creates a new SendGrid email provider
func NewSendGridProvider(apiKey string) *SendGridEmailProvider {
	return &SendGridEmailProvider{
		APIKey: apiKey,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// EmailContent represents email data
type EmailContent struct {
	To          string
	From        string
	Subject     string
	HTMLContent string
	TextContent string
}

// SendEmail sends an email via SendGrid
func (s *SendGridEmailProvider) SendEmail(email EmailContent) error {
	payload := map[string]interface{}{
		"personalizations": []map[string]interface{}{
			{
				"to": []map[string]string{
					{"email": email.To},
				},
			},
		},
		"from": map[string]string{
			"email": email.From,
		},
		"subject": email.Subject,
		"content": []map[string]string{
			{
				"type":  "text/html",
				"value": email.HTMLContent,
			},
			{
				"type":  "text/plain",
				"value": email.TextContent,
			},
		},
	}

	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	req, err := http.NewRequest("POST", "https://api.sendgrid.com/v3/mail/send", bytes.NewReader(payloadBytes))
	if err != nil {
		return err
	}

	req.Header.Set("Authorization", "Bearer "+s.APIKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 202 {
		return fmt.Errorf("SendGrid API error: %d", resp.StatusCode)
	}

	return nil
}

// TwilioSMSProvider sends SMS via Twilio API
type TwilioSMSProvider struct {
	AccountSID string
	AuthToken  string
	FromPhone  string
	httpClient *http.Client
}

// NewTwilioProvider creates a new Twilio SMS provider
func NewTwilioProvider(accountSID, authToken, fromPhone string) *TwilioSMSProvider {
	return &TwilioSMSProvider{
		AccountSID: accountSID,
		AuthToken:  authToken,
		FromPhone:  fromPhone,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// SendSMS sends an SMS via Twilio
func (t *TwilioSMSProvider) SendSMS(toPhone, message string) error {
	url := fmt.Sprintf("https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json", t.AccountSID)

	payload := fmt.Sprintf("To=%s&From=%s&Body=%s", toPhone, t.FromPhone, message)

	req, err := http.NewRequest("POST", url, bytes.NewBufferString(payload))
	if err != nil {
		return err
	}

	req.SetBasicAuth(t.AccountSID, t.AuthToken)
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := t.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 201 {
		return fmt.Errorf("Twilio API error: %d", resp.StatusCode)
	}

	return nil
}
