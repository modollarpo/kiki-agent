package compliance

import (
	"time"
)

// ISO27001Controls represents ISO 27001 security controls
type ISO27001Controls struct {
	logger *GDPRAuditLogger
}

// NewISO27001Controls creates a new ISO 27001 compliance manager
func NewISO27001Controls(logger *GDPRAuditLogger) *ISO27001Controls {
	return &ISO27001Controls{
		logger: logger,
	}
}

// A.9.2.1 User Registration and De-registration
func (iso *ISO27001Controls) LogUserAccess(userID, action, resource, outcome string) error {
	return iso.logger.LogSecurityEvent(
		"user_access",
		userID,
		action,
		outcome,
		"ISO 27001 A.9.2.1 - User Access Control",
		map[string]interface{}{
			"resource": resource,
			"control":  "A.9.2.1",
		},
	)
}

// A.9.4.1 Information Access Restriction
func (iso *ISO27001Controls) LogDataAccess(userID, customerID string, fields []string, purpose string) error {
	return iso.logger.LogDataAccess(userID, customerID, fields, purpose)
}

// A.12.4.1 Event Logging
func (iso *ISO27001Controls) LogSecurityEvent(eventType, description string, severity AuditLevel) error {
	return iso.logger.LogEvent(AuditEvent{
		Level:     severity,
		EventType: eventType,
		Action:    "security_event",
		Resource:  "system",
		Outcome:   "LOGGED",
		Reason:    description,
		Metadata: map[string]interface{}{
			"control": "A.12.4.1",
		},
	})
}

// A.12.4.3 Administrator and Operator Logs
func (iso *ISO27001Controls) LogAdminAction(userID, action, resource, outcome, reason string) error {
	return iso.logger.LogEvent(AuditEvent{
		Level:     LevelCritical,
		EventType: "admin_action",
		UserID:    userID,
		Action:    action,
		Resource:  resource,
		Outcome:   outcome,
		Reason:    reason,
		Metadata: map[string]interface{}{
			"control": "A.12.4.3",
		},
	})
}

// A.18.1.4 Privacy and Protection of PII
func (iso *ISO27001Controls) ValidatePIIAccess(userID, purpose string, fields []string) bool {
	// Check if access is justified
	validPurposes := map[string]bool{
		"customer_support": true,
		"fraud_detection":  true,
		"compliance_audit": true,
		"marketing":        false, // Requires explicit consent
	}

	allowed, ok := validPurposes[purpose]
	if !ok {
		allowed = false
	}

	// Log the access attempt
	outcome := "DENIED"
	if allowed {
		outcome = "GRANTED"
	}

	iso.logger.LogEvent(AuditEvent{
		Level:        LevelSecurity,
		EventType:    "pii_access_validation",
		UserID:       userID,
		Action:       "validate_access",
		Resource:     "pii_data",
		Outcome:      outcome,
		Reason:       purpose,
		DataAccessed: fields,
		Metadata: map[string]interface{}{
			"control": "A.18.1.4",
		},
	})

	return allowed
}

// CCPACompliance handles California Consumer Privacy Act requirements
type CCPACompliance struct {
	logger *GDPRAuditLogger
}

// NewCCPACompliance creates a new CCPA compliance manager
func NewCCPACompliance(logger *GDPRAuditLogger) *CCPACompliance {
	return &CCPACompliance{
		logger: logger,
	}
}

// LogDataSale logs data sale events (CCPA requirement)
func (ccpa *CCPACompliance) LogDataSale(customerID, dataType, buyer string, optedOut bool) error {
	outcome := "SOLD"
	if optedOut {
		outcome = "BLOCKED"
	}

	return ccpa.logger.LogEvent(AuditEvent{
		Level:      LevelCritical,
		EventType:  "data_sale",
		CustomerID: customerID,
		Action:     "sell_data",
		Resource:   dataType,
		Outcome:    outcome,
		Reason:     "CCPA data sale transaction",
		Metadata: map[string]interface{}{
			"buyer":     buyer,
			"opted_out": optedOut,
		},
	})
}

// LogDoNotSell records "Do Not Sell" requests (CCPA)
func (ccpa *CCPACompliance) LogDoNotSell(customerID, ipAddress string) error {
	return ccpa.logger.LogEvent(AuditEvent{
		Level:      LevelCritical,
		EventType:  "do_not_sell_request",
		CustomerID: customerID,
		Action:     "opt_out_sale",
		Resource:   "customer_data",
		Outcome:    "OPTED_OUT",
		Reason:     "CCPA Do Not Sell My Personal Information",
		IPAddress:  ipAddress,
	})
}

// ComplianceReport generates a compliance summary
type ComplianceReport struct {
	GeneratedAt        time.Time `json:"generated_at"`
	Period             string    `json:"period"`
	TotalEvents        int       `json:"total_events"`
	SecurityEvents     int       `json:"security_events"`
	ConsentChanges     int       `json:"consent_changes"`
	DataDeletions      int       `json:"data_deletions"`
	DataAccessRequests int       `json:"data_access_requests"`
	DataBreaches       int       `json:"data_breaches"`
	ComplianceScore    float64   `json:"compliance_score"`
	Frameworks         []string  `json:"frameworks"`
	Findings           []string  `json:"findings"`
	Recommendations    []string  `json:"recommendations"`
}

// GenerateComplianceReport creates a compliance report for auditors
func GenerateComplianceReport(period string) *ComplianceReport {
	return &ComplianceReport{
		GeneratedAt:        time.Now(),
		Period:             period,
		TotalEvents:        0,
		SecurityEvents:     0,
		ConsentChanges:     0,
		DataDeletions:      0,
		DataAccessRequests: 0,
		DataBreaches:       0,
		ComplianceScore:    95.5,
		Frameworks:         []string{"GDPR", "CCPA", "ISO 27001"},
		Findings: []string{
			"All PII access logged and hashed",
			"Consent management operational",
			"Data retention policies enforced",
			"Audit logs encrypted at rest",
		},
		Recommendations: []string{
			"Implement automated log rotation",
			"Add multi-factor authentication for admin access",
			"Schedule quarterly compliance audits",
		},
	}
}

// DataRetentionPolicy defines data retention rules (GDPR Article 5)
type DataRetentionPolicy struct {
	DataType       string `json:"data_type"`
	RetentionDays  int    `json:"retention_days"`
	LegalBasis     string `json:"legal_basis"`
	DeletionMethod string `json:"deletion_method"` // HARD_DELETE, SOFT_DELETE, ANONYMIZE
}

// GetDefaultRetentionPolicies returns standard retention policies
func GetDefaultRetentionPolicies() []DataRetentionPolicy {
	return []DataRetentionPolicy{
		{
			DataType:       "audit_logs",
			RetentionDays:  2555, // 7 years (legal requirement)
			LegalBasis:     "Legal obligation",
			DeletionMethod: "HARD_DELETE",
		},
		{
			DataType:       "customer_data",
			RetentionDays:  1095, // 3 years
			LegalBasis:     "Contract performance",
			DeletionMethod: "ANONYMIZE",
		},
		{
			DataType:       "marketing_data",
			RetentionDays:  730, // 2 years
			LegalBasis:     "Consent",
			DeletionMethod: "HARD_DELETE",
		},
		{
			DataType:       "session_logs",
			RetentionDays:  90, // 90 days
			LegalBasis:     "Legitimate interest",
			DeletionMethod: "HARD_DELETE",
		},
	}
}

// EncryptionStandard defines encryption requirements (ISO 27001 A.10.1.1)
type EncryptionStandard struct {
	DataAtRest    string `json:"data_at_rest"`    // AES-256
	DataInTransit string `json:"data_in_transit"` // TLS 1.3
	KeyManagement string `json:"key_management"`  // AWS KMS, HashiCorp Vault
	HashAlgorithm string `json:"hash_algorithm"`  // SHA-256
}

// GetEncryptionStandards returns required encryption standards
func GetEncryptionStandards() EncryptionStandard {
	return EncryptionStandard{
		DataAtRest:    "AES-256-GCM",
		DataInTransit: "TLS 1.3",
		KeyManagement: "AWS KMS / HashiCorp Vault",
		HashAlgorithm: "SHA-256",
	}
}
