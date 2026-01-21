package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"sync"

	"github.com/go-redis/redis/v8"
	"github.com/user/kiki-agent/cmd/syncshield/compliance"
)

var rdb *redis.Client
var maxBurstBudget = 500.0
var windowSeconds = 60.0
var gdprLogger *compliance.GDPRAuditLogger
var consentManager *compliance.ConsentManager
var iso27001 *compliance.ISO27001Controls
var ccpa *compliance.CCPACompliance

// In-memory fallback for budget window when Redis is unavailable
var (
	memMu        sync.Mutex
	memSpendWind []struct {
		ts  float64
		amt float64
	}
)

func checkBudget() bool {
	ctx := context.Background()
	now := float64(time.Now().Unix())

	// Remove old entries
	rdb.ZRemRangeByScore(ctx, "spend_window", "-inf", strconv.FormatFloat(now-windowSeconds, 'f', 0, 64))

	// Get current spend
	spendData, err := rdb.ZRangeWithScores(ctx, "spend_window", 0, -1).Result()
	if err != nil {
		log.Printf("Redis error: %v", err)
		// Use in-memory fallback window instead of permissive allow
		memMu.Lock()
		defer memMu.Unlock()
		// Prune old
		cutoff := now - windowSeconds
		pruned := memSpendWind[:0]
		total := 0.0
		for _, e := range memSpendWind {
			if e.ts >= cutoff {
				pruned = append(pruned, e)
				total += e.amt
			}
		}
		memSpendWind = pruned
		return total < maxBurstBudget
	}

	total := 0.0
	for _, z := range spendData {
		amount, _ := strconv.ParseFloat(z.Member.(string), 64)
		total += amount
	}

	return total < maxBurstBudget
}

// ValidateBid implements the Governor: checks LTV outliers and budget
func ValidateBid(predictedLTV float64) bool {
	// Rule 1: Safety Ceiling - Never bid if LTV is nonsensical
	if predictedLTV > 10000 {
		log.Printf("🛡️ GOVERNOR VETO: LTV %.2f exceeds safety ceiling", predictedLTV)
		logValidation("VETO", predictedLTV, "Safety ceiling exceeded")
		if gdprLogger != nil {
			gdprLogger.LogBidValidation("system", predictedLTV, "DENIED", "Safety ceiling exceeded")
		}
		return false
	}

	// Rule 2: Minimum threshold - Don't bid on very low LTV
	if predictedLTV < 10 {
		log.Printf("🛡️ GOVERNOR VETO: LTV %.2f below minimum threshold", predictedLTV)
		logValidation("VETO", predictedLTV, "Below minimum threshold")
		if gdprLogger != nil {
			gdprLogger.LogBidValidation("system", predictedLTV, "DENIED", "Below minimum threshold")
		}
		return false
	}

	// Rule 3: Budget check - Sliding window validation
	if !checkBudget() {
		log.Printf("🛡️ GOVERNOR VETO: Budget limit exceeded")
		logValidation("VETO", predictedLTV, "Budget limit exceeded")
		if gdprLogger != nil {
			gdprLogger.LogBidValidation("system", predictedLTV, "DENIED", "Budget limit exceeded")
		}
		return false
	}

	log.Printf("✅ GOVERNOR APPROVED: LTV %.2f within safe parameters", predictedLTV)
	logValidation("APPROVED", predictedLTV, "Within safe parameters")
	if gdprLogger != nil {
		gdprLogger.LogBidValidation("system", predictedLTV, "APPROVED", "Within safe parameters")
	}
	return true
}

// logValidation writes compliance decisions to audit log
func logValidation(decision string, ltv float64, reason string) {
	file, err := os.OpenFile("shield_audit.csv", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Error opening shield audit log: %v", err)
		return
	}
	defer file.Close()

	timestamp := time.Now().Format(time.RFC3339)
	record := fmt.Sprintf("%s,%s,%.2f,%s\n", timestamp, decision, ltv, reason)
	if _, err := file.WriteString(record); err != nil {
		log.Printf("Error writing to shield audit log: %v", err)
	}
}

func addSpend(amount float64) {
	ctx := context.Background()
	now := float64(time.Now().Unix())
	rdb.ZAdd(ctx, "spend_window", &redis.Z{
		Score:  now,
		Member: strconv.FormatFloat(amount, 'f', 2, 64),
	})
	// Always mirror to in-memory window for fallback
	memMu.Lock()
	memSpendWind = append(memSpendWind, struct {
		ts  float64
		amt float64
	}{ts: now, amt: amount})
	memMu.Unlock()
}

func main() {
	// Load environment configuration
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}
	if v := os.Getenv("MAX_BURST_BUDGET"); v != "" {
		if f, err := strconv.ParseFloat(v, 64); err == nil {
			maxBurstBudget = f
		}
	}
	if v := os.Getenv("WINDOW_SECONDS"); v != "" {
		if f, err := strconv.ParseFloat(v, 64); err == nil {
			windowSeconds = f
		}
	}
	retentionDays := 2555
	if v := os.Getenv("RETENTION_DAYS"); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			retentionDays = i
		}
	}

	// Initialize GDPR-compliant audit logging
	var err error
	gdprLogger, err = compliance.NewGDPRAuditLogger(
		"shield_audit_gdpr.csv",
		"shield_audit_gdpr.json",
		retentionDays,
	)
	if err != nil {
		log.Fatalf("Failed to initialize GDPR audit logger: %v", err)
	}
	defer gdprLogger.Close()

	// Initialize compliance managers
	consentManager = compliance.NewConsentManager(gdprLogger)
	iso27001 = compliance.NewISO27001Controls(gdprLogger)
	ccpa = compliance.NewCCPACompliance(gdprLogger)

	log.Println("🛡️ SyncShield™ - Regulatory Guardrail Agent")
	log.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	log.Println("✅ GDPR-compliant audit logging enabled")
	log.Println("✅ CCPA compliance framework active")
	log.Println("✅ ISO 27001 security controls operational")
	log.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

	rdb = redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})
	defer rdb.Close()

	// HTTP endpoints
	http.HandleFunc("/check", complianceHandler)
	http.HandleFunc("/spend", spendHandler)
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/consent/grant", grantConsentHandler)
	http.HandleFunc("/consent/revoke", revokeConsentHandler)
	http.HandleFunc("/consent/status", consentStatusHandler)
	http.HandleFunc("/dsr/create", createDSRHandler)
	http.HandleFunc("/compliance/report", complianceReportHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}
	log.Printf("🌐 SyncShield API starting on :%s", port)
	log.Printf("   Compliance: http://localhost:%s/check", port)
	log.Printf("   Health: http://localhost:%s/health", port)
	log.Printf("   Consent: http://localhost:%s/consent/*", port)
	log.Printf("   DSR: http://localhost:%s/dsr/*", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func spendHandler(w http.ResponseWriter, r *http.Request) {
	amountStr := r.URL.Query().Get("amount")
	amount, err := strconv.ParseFloat(amountStr, 64)
	if err != nil {
		http.Error(w, "Invalid amount", http.StatusBadRequest)
		return
	}
	addSpend(amount)
	fmt.Fprintf(w, "Spend recorded: %.2f", amount)
}

func complianceHandler(w http.ResponseWriter, r *http.Request) {
	ltvStr := r.URL.Query().Get("ltv")
	if ltvStr == "" {
		http.Error(w, "Missing LTV parameter", http.StatusBadRequest)
		return
	}

	ltv, err := strconv.ParseFloat(ltvStr, 64)
	if err != nil {
		http.Error(w, "Invalid LTV value", http.StatusBadRequest)
		return
	}

	// Log the compliance check attempt
	if iso27001 != nil {
		iso27001.LogUserAccess("system", "validate_bid", "ltv_prediction", "PROCESSING")
	}

	if ValidateBid(ltv) {
		fmt.Fprintf(w, "Compliance check passed")
	} else {
		http.Error(w, "Bid validation failed", http.StatusForbidden)
	}
}

// Health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	status := map[string]interface{}{
		"status":          "healthy",
		"service":         "SyncShield™ Regulatory Guardrail",
		"gdpr_compliant":  gdprLogger != nil,
		"iso27001_active": iso27001 != nil,
		"ccpa_compliant":  ccpa != nil,
		"redis_connected": rdb.Ping(context.Background()).Err() == nil,
		"timestamp":       time.Now().Format(time.RFC3339),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

// Grant consent endpoint
func grantConsentHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	// Accept either JSON body or query params
	var payload struct {
		CustomerID  string `json:"customer_id"`
		ConsentType string `json:"consent_type"`
		Type        string `json:"type"`
		IPAddress   string `json:"ip_address"`
		UserAgent   string `json:"user_agent"`
		LegalBasis  string `json:"legal_basis"`
	}

	contentType := r.Header.Get("Content-Type")
	if contentType == "application/json" {
		_ = json.NewDecoder(r.Body).Decode(&payload)
	}

	customerID := payload.CustomerID
	if customerID == "" {
		customerID = r.URL.Query().Get("customer_id")
	}
	consentType := payload.ConsentType
	if consentType == "" {
		consentType = payload.Type
	}
	if consentType == "" {
		consentType = r.URL.Query().Get("type")
	}
	ipAddress := payload.IPAddress
	if ipAddress == "" {
		ipAddress = r.RemoteAddr
	}
	userAgent := payload.UserAgent
	if userAgent == "" {
		userAgent = r.UserAgent()
	}
	legalBasis := payload.LegalBasis
	if legalBasis == "" {
		legalBasis = "Consent"
	}

	if customerID == "" || consentType == "" {
		http.Error(w, "Missing required parameters", http.StatusBadRequest)
		return
	}

	err := consentManager.GrantConsent(
		customerID,
		compliance.ConsentType(consentType),
		ipAddress,
		userAgent,
		legalBasis,
	)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "granted",
		"message": "Consent successfully recorded",
	})
}

// Revoke consent endpoint
func revokeConsentHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	// Accept either JSON body or query params
	var payload struct {
		CustomerID  string `json:"customer_id"`
		ConsentType string `json:"consent_type"`
		Type        string `json:"type"`
		IPAddress   string `json:"ip_address"`
	}

	contentType := r.Header.Get("Content-Type")
	if contentType == "application/json" {
		_ = json.NewDecoder(r.Body).Decode(&payload)
	}

	customerID := payload.CustomerID
	if customerID == "" {
		customerID = r.URL.Query().Get("customer_id")
	}
	consentType := payload.ConsentType
	if consentType == "" {
		consentType = payload.Type
	}
	if consentType == "" {
		consentType = r.URL.Query().Get("type")
	}
	ipAddress := payload.IPAddress
	if ipAddress == "" {
		ipAddress = r.RemoteAddr
	}

	if customerID == "" || consentType == "" {
		http.Error(w, "Missing required parameters", http.StatusBadRequest)
		return
	}

	err := consentManager.RevokeConsent(
		customerID,
		compliance.ConsentType(consentType),
		ipAddress,
	)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "revoked",
		"message": "Consent successfully revoked",
	})
}

// Check consent status endpoint
func consentStatusHandler(w http.ResponseWriter, r *http.Request) {
	// Accept either JSON body or query params
	var payload struct {
		CustomerID string `json:"customer_id"`
	}
	if r.Header.Get("Content-Type") == "application/json" {
		_ = json.NewDecoder(r.Body).Decode(&payload)
	}

	customerID := payload.CustomerID
	if customerID == "" {
		customerID = r.URL.Query().Get("customer_id")
	}
	if customerID == "" {
		http.Error(w, "Missing customer_id parameter", http.StatusBadRequest)
		return
	}

	consents := consentManager.GetConsents(customerID)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(consents)
}

// Create Data Subject Request endpoint
func createDSRHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	// Accept either JSON body or query params
	var payload struct {
		CustomerID  string `json:"customer_id"`
		RequestType string `json:"request_type"`
		Type        string `json:"type"`
		RequestedBy string `json:"requested_by"`
		Details     string `json:"details"`
	}
	if r.Header.Get("Content-Type") == "application/json" {
		_ = json.NewDecoder(r.Body).Decode(&payload)
	}

	customerID := payload.CustomerID
	if customerID == "" {
		customerID = r.URL.Query().Get("customer_id")
	}
	requestType := payload.RequestType
	if requestType == "" {
		requestType = payload.Type
	}
	if requestType == "" {
		requestType = r.URL.Query().Get("type")
	}
	requestedBy := payload.RequestedBy
	if requestedBy == "" {
		requestedBy = r.URL.Query().Get("requested_by")
	}

	if customerID == "" || requestType == "" {
		http.Error(w, "Missing required parameters", http.StatusBadRequest)
		return
	}

	dsrManager := compliance.NewDataSubjectRequestManager(gdprLogger)
	request, err := dsrManager.CreateRequest(customerID, requestType, requestedBy)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(request)
}

// Compliance report endpoint
func complianceReportHandler(w http.ResponseWriter, r *http.Request) {
	period := r.URL.Query().Get("period")
	if period == "" {
		period = "monthly"
	}

	report := compliance.GenerateComplianceReport(period)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(report)
}
