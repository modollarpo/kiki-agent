package compliance

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

// AuditLevel defines the severity of audit events
type AuditLevel string

const (
	LevelInfo     AuditLevel = "INFO"
	LevelWarning  AuditLevel = "WARNING"
	LevelCritical AuditLevel = "CRITICAL"
	LevelSecurity AuditLevel = "SECURITY"
)

// AuditEvent represents a compliance audit log entry
type AuditEvent struct {
	Timestamp     time.Time              `json:"timestamp"`
	EventID       string                 `json:"event_id"`
	Level         AuditLevel             `json:"level"`
	EventType     string                 `json:"event_type"`
	UserID        string                 `json:"user_id"`     // Hashed for GDPR
	CustomerID    string                 `json:"customer_id"` // Hashed for GDPR
	Action        string                 `json:"action"`
	Resource      string                 `json:"resource"`
	Outcome       string                 `json:"outcome"` // APPROVED, DENIED, ERROR
	Reason        string                 `json:"reason"`
	IPAddress     string                 `json:"ip_address"` // For security audit
	UserAgent     string                 `json:"user_agent"`
	DataAccessed  []string               `json:"data_accessed"`  // PII fields accessed
	RetentionDays int                    `json:"retention_days"` // GDPR data retention
	Metadata      map[string]interface{} `json:"metadata"`
}

// GDPRAuditLogger handles GDPR/CCPA compliant audit logging
type GDPRAuditLogger struct {
	csvWriter     *csv.Writer
	jsonWriter    *os.File
	csvFile       *os.File
	mu            sync.Mutex
	retentionDays int
}

// NewGDPRAuditLogger creates a new GDPR-compliant audit logger
func NewGDPRAuditLogger(csvPath, jsonPath string, retentionDays int) (*GDPRAuditLogger, error) {
	csvFile, err := os.OpenFile(csvPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600) // Restricted permissions
	if err != nil {
		return nil, fmt.Errorf("failed to open CSV audit log: %w", err)
	}

	jsonFile, err := os.OpenFile(jsonPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
	if err != nil {
		csvFile.Close()
		return nil, fmt.Errorf("failed to open JSON audit log: %w", err)
	}

	csvWriter := csv.NewWriter(csvFile)

	// Write CSV header if file is new
	fileInfo, _ := csvFile.Stat()
	if fileInfo.Size() == 0 {
		csvWriter.Write([]string{
			"timestamp", "event_id", "level", "event_type", "user_id_hash",
			"customer_id_hash", "action", "resource", "outcome", "reason",
			"ip_address", "data_accessed", "retention_days",
		})
		csvWriter.Flush()
	}

	return &GDPRAuditLogger{
		csvWriter:     csvWriter,
		jsonWriter:    jsonFile,
		csvFile:       csvFile,
		retentionDays: retentionDays,
	}, nil
}

// LogEvent writes a GDPR-compliant audit event to both CSV and JSON logs
func (g *GDPRAuditLogger) LogEvent(event AuditEvent) error {
	g.mu.Lock()
	defer g.mu.Unlock()

	// Set defaults
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now()
	}
	if event.EventID == "" {
		event.EventID = generateEventID(event)
	}
	if event.RetentionDays == 0 {
		event.RetentionDays = g.retentionDays
	}

	// Hash PII fields for GDPR compliance
	if event.UserID != "" {
		event.UserID = hashPII(event.UserID)
	}
	if event.CustomerID != "" {
		event.CustomerID = hashPII(event.CustomerID)
	}

	// Write to CSV (structured for easy parsing)
	dataAccessedStr := ""
	if len(event.DataAccessed) > 0 {
		dataAccessedStr = fmt.Sprintf("%v", event.DataAccessed)
	}

	csvRecord := []string{
		event.Timestamp.Format(time.RFC3339),
		event.EventID,
		string(event.Level),
		event.EventType,
		event.UserID,
		event.CustomerID,
		event.Action,
		event.Resource,
		event.Outcome,
		event.Reason,
		event.IPAddress,
		dataAccessedStr,
		fmt.Sprintf("%d", event.RetentionDays),
	}

	if err := g.csvWriter.Write(csvRecord); err != nil {
		return fmt.Errorf("failed to write CSV audit log: %w", err)
	}
	g.csvWriter.Flush()

	// Write to JSON (full event with metadata)
	jsonData, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal JSON audit log: %w", err)
	}

	if _, err := g.jsonWriter.Write(append(jsonData, '\n')); err != nil {
		return fmt.Errorf("failed to write JSON audit log: %w", err)
	}

	return nil
}

// LogBidValidation logs a bid validation event (GDPR compliant)
func (g *GDPRAuditLogger) LogBidValidation(customerID string, ltv float64, outcome, reason string) error {
	return g.LogEvent(AuditEvent{
		Level:        LevelInfo,
		EventType:    "bid_validation",
		CustomerID:   customerID,
		Action:       "validate_bid",
		Resource:     "ltv_prediction",
		Outcome:      outcome,
		Reason:       reason,
		DataAccessed: []string{"customer_id", "predicted_ltv"},
		Metadata: map[string]interface{}{
			"ltv": ltv,
		},
	})
}

// LogDataAccess logs when PII data is accessed (GDPR Article 30)
func (g *GDPRAuditLogger) LogDataAccess(userID, customerID string, fields []string, purpose string) error {
	return g.LogEvent(AuditEvent{
		Level:        LevelSecurity,
		EventType:    "data_access",
		UserID:       userID,
		CustomerID:   customerID,
		Action:       "read",
		Resource:     "customer_pii",
		Outcome:      "SUCCESS",
		Reason:       purpose,
		DataAccessed: fields,
	})
}

// LogConsentChange logs when user consent is updated (GDPR Article 7)
func (g *GDPRAuditLogger) LogConsentChange(customerID, consentType, status, ipAddress string) error {
	return g.LogEvent(AuditEvent{
		Level:      LevelCritical,
		EventType:  "consent_change",
		CustomerID: customerID,
		Action:     "update_consent",
		Resource:   consentType,
		Outcome:    status,
		Reason:     "User consent update",
		IPAddress:  ipAddress,
		Metadata: map[string]interface{}{
			"consent_type": consentType,
			"status":       status,
		},
	})
}

// LogDataDeletion logs when customer data is deleted (GDPR Right to Erasure)
func (g *GDPRAuditLogger) LogDataDeletion(customerID, requestedBy, reason string) error {
	return g.LogEvent(AuditEvent{
		Level:      LevelCritical,
		EventType:  "data_deletion",
		CustomerID: customerID,
		UserID:     requestedBy,
		Action:     "delete",
		Resource:   "customer_data",
		Outcome:    "SUCCESS",
		Reason:     reason,
		Metadata: map[string]interface{}{
			"deletion_reason": reason,
		},
	})
}

// LogSecurityEvent logs security-related events (ISO 27001)
func (g *GDPRAuditLogger) LogSecurityEvent(eventType, userID, action, outcome, reason string, metadata map[string]interface{}) error {
	return g.LogEvent(AuditEvent{
		Level:     LevelSecurity,
		EventType: eventType,
		UserID:    userID,
		Action:    action,
		Outcome:   outcome,
		Reason:    reason,
		Metadata:  metadata,
	})
}

// Close closes all audit log files
func (g *GDPRAuditLogger) Close() error {
	g.mu.Lock()
	defer g.mu.Unlock()

	g.csvWriter.Flush()

	if err := g.csvFile.Close(); err != nil {
		return err
	}
	if err := g.jsonWriter.Close(); err != nil {
		return err
	}

	return nil
}

// hashPII creates a SHA-256 hash of PII for GDPR compliance
func hashPII(data string) string {
	hash := sha256.Sum256([]byte(data))
	return fmt.Sprintf("%x", hash[:16]) // Use first 16 bytes for readability
}

// generateEventID creates a unique event ID
func generateEventID(event AuditEvent) string {
	data := fmt.Sprintf("%s-%s-%s-%d",
		event.EventType,
		event.CustomerID,
		event.Action,
		event.Timestamp.UnixNano(),
	)
	hash := sha256.Sum256([]byte(data))
	return fmt.Sprintf("%x", hash[:8])
}

// PurgeExpiredLogs removes logs older than retention period (GDPR Article 5)
func (g *GDPRAuditLogger) PurgeExpiredLogs() error {
	// This would typically query a database and delete old records
	// For file-based logs, implement log rotation
	return nil
}
