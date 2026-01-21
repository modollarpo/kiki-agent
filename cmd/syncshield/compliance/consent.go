package compliance

import (
	"fmt"
	"time"
)

// ConsentType represents different types of user consent
type ConsentType string

const (
	ConsentMarketing   ConsentType = "marketing"
	ConsentAnalytics   ConsentType = "analytics"
	ConsentTargeting   ConsentType = "targeting"
	ConsentProfiling   ConsentType = "profiling"
	ConsentDataSharing ConsentType = "data_sharing"
)

// ConsentStatus represents the user's consent choice
type ConsentStatus string

const (
	ConsentGranted ConsentStatus = "GRANTED"
	ConsentDenied  ConsentStatus = "DENIED"
	ConsentRevoked ConsentStatus = "REVOKED"
	ConsentPending ConsentStatus = "PENDING"
)

// UserConsent tracks user consent for GDPR/CCPA compliance
type UserConsent struct {
	CustomerID  string        `json:"customer_id"`
	ConsentType ConsentType   `json:"consent_type"`
	Status      ConsentStatus `json:"status"`
	GrantedAt   time.Time     `json:"granted_at"`
	RevokedAt   *time.Time    `json:"revoked_at,omitempty"`
	ExpiresAt   *time.Time    `json:"expires_at,omitempty"`
	IPAddress   string        `json:"ip_address"`
	UserAgent   string        `json:"user_agent"`
	Version     string        `json:"version"`     // Consent policy version
	LegalBasis  string        `json:"legal_basis"` // GDPR Article 6 basis
}

// ConsentManager manages user consent (GDPR Article 7)
type ConsentManager struct {
	consents map[string]map[ConsentType]*UserConsent
	logger   *GDPRAuditLogger
}

// NewConsentManager creates a new consent manager
func NewConsentManager(logger *GDPRAuditLogger) *ConsentManager {
	return &ConsentManager{
		consents: make(map[string]map[ConsentType]*UserConsent),
		logger:   logger,
	}
}

// GrantConsent records user consent
func (cm *ConsentManager) GrantConsent(customerID string, consentType ConsentType, ipAddress, userAgent, legalBasis string) error {
	if _, exists := cm.consents[customerID]; !exists {
		cm.consents[customerID] = make(map[ConsentType]*UserConsent)
	}

	consent := &UserConsent{
		CustomerID:  customerID,
		ConsentType: consentType,
		Status:      ConsentGranted,
		GrantedAt:   time.Now(),
		IPAddress:   ipAddress,
		UserAgent:   userAgent,
		Version:     "1.0",
		LegalBasis:  legalBasis,
	}

	cm.consents[customerID][consentType] = consent

	// Audit log
	if cm.logger != nil {
		cm.logger.LogConsentChange(customerID, string(consentType), string(ConsentGranted), ipAddress)
	}

	return nil
}

// RevokeConsent revokes user consent (GDPR Right to Withdraw)
func (cm *ConsentManager) RevokeConsent(customerID string, consentType ConsentType, ipAddress string) error {
	if consents, exists := cm.consents[customerID]; exists {
		if consent, ok := consents[consentType]; ok {
			now := time.Now()
			consent.Status = ConsentRevoked
			consent.RevokedAt = &now

			// Audit log
			if cm.logger != nil {
				cm.logger.LogConsentChange(customerID, string(consentType), string(ConsentRevoked), ipAddress)
			}

			return nil
		}
	}

	return fmt.Errorf("consent not found for customer %s and type %s", customerID, consentType)
}

// HasConsent checks if user has granted specific consent
func (cm *ConsentManager) HasConsent(customerID string, consentType ConsentType) bool {
	if consents, exists := cm.consents[customerID]; exists {
		if consent, ok := consents[consentType]; ok {
			return consent.Status == ConsentGranted && (consent.ExpiresAt == nil || consent.ExpiresAt.After(time.Now()))
		}
	}
	return false
}

// GetConsents returns all consents for a customer
func (cm *ConsentManager) GetConsents(customerID string) map[ConsentType]*UserConsent {
	if consents, exists := cm.consents[customerID]; exists {
		return consents
	}
	return make(map[ConsentType]*UserConsent)
}

// DataSubjectRequest represents a GDPR data subject request
type DataSubjectRequest struct {
	RequestID   string     `json:"request_id"`
	CustomerID  string     `json:"customer_id"`
	RequestType string     `json:"request_type"` // ACCESS, DELETION, PORTABILITY, RECTIFICATION
	Status      string     `json:"status"`       // PENDING, COMPLETED, REJECTED
	RequestedAt time.Time  `json:"requested_at"`
	CompletedAt *time.Time `json:"completed_at,omitempty"`
	RequestedBy string     `json:"requested_by"`
	ProcessedBy string     `json:"processed_by"`
	Notes       string     `json:"notes"`
}

// DataSubjectRequestManager handles GDPR data subject requests
type DataSubjectRequestManager struct {
	requests map[string]*DataSubjectRequest
	logger   *GDPRAuditLogger
}

// NewDataSubjectRequestManager creates a new DSR manager
func NewDataSubjectRequestManager(logger *GDPRAuditLogger) *DataSubjectRequestManager {
	return &DataSubjectRequestManager{
		requests: make(map[string]*DataSubjectRequest),
		logger:   logger,
	}
}

// CreateRequest creates a new data subject request
func (dsm *DataSubjectRequestManager) CreateRequest(customerID, requestType, requestedBy string) (*DataSubjectRequest, error) {
	requestID := fmt.Sprintf("DSR-%d-%s", time.Now().Unix(), customerID[:8])

	request := &DataSubjectRequest{
		RequestID:   requestID,
		CustomerID:  customerID,
		RequestType: requestType,
		Status:      "PENDING",
		RequestedAt: time.Now(),
		RequestedBy: requestedBy,
	}

	dsm.requests[requestID] = request

	// Audit log
	if dsm.logger != nil {
		dsm.logger.LogEvent(AuditEvent{
			Level:      LevelCritical,
			EventType:  "data_subject_request",
			CustomerID: customerID,
			Action:     "create_request",
			Resource:   requestType,
			Outcome:    "PENDING",
			Reason:     "GDPR/CCPA data subject request initiated",
			Metadata: map[string]interface{}{
				"request_id":   requestID,
				"request_type": requestType,
			},
		})
	}

	return request, nil
}

// CompleteRequest marks a data subject request as completed
func (dsm *DataSubjectRequestManager) CompleteRequest(requestID, processedBy, notes string) error {
	request, exists := dsm.requests[requestID]
	if !exists {
		return fmt.Errorf("request not found: %s", requestID)
	}

	now := time.Now()
	request.Status = "COMPLETED"
	request.CompletedAt = &now
	request.ProcessedBy = processedBy
	request.Notes = notes

	// Audit log
	if dsm.logger != nil {
		dsm.logger.LogEvent(AuditEvent{
			Level:      LevelCritical,
			EventType:  "data_subject_request_completed",
			CustomerID: request.CustomerID,
			UserID:     processedBy,
			Action:     "complete_request",
			Resource:   request.RequestType,
			Outcome:    "COMPLETED",
			Reason:     notes,
			Metadata: map[string]interface{}{
				"request_id": requestID,
			},
		})
	}

	return nil
}

// GetRequest retrieves a data subject request
func (dsm *DataSubjectRequestManager) GetRequest(requestID string) (*DataSubjectRequest, error) {
	request, exists := dsm.requests[requestID]
	if !exists {
		return nil, fmt.Errorf("request not found: %s", requestID)
	}
	return request, nil
}
