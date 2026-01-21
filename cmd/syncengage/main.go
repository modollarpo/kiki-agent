package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	pb "github.com/user/kiki-agent/api/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// Customer represents a CRM customer record
type Customer struct {
	ID              string    `json:"customer_id"`
	Email           string    `json:"email"`
	LastPurchase    time.Time `json:"last_purchase"`
	TotalSpend      float64   `json:"total_spend"`
	PurchaseCount   int       `json:"purchase_count"`
	EngagementScore float64   `json:"engagement_score"`
	LTV             float64   `json:"ltv"`
	ChurnRisk       string    `json:"churn_risk"` // low, medium, high
	LastEngagement  time.Time `json:"last_engagement"`
}

// RetentionTrigger represents an automated retention action
type RetentionTrigger struct {
	CustomerID   string    `json:"customer_id"`
	TriggerType  string    `json:"trigger_type"` // dormant, churn_risk, high_value_check
	Action       string    `json:"action"`       // email, offer, survey
	Message      string    `json:"message"`
	DiscountPct  float64   `json:"discount_pct"`
	ExecutedAt   time.Time `json:"executed_at"`
	PredictedLTV float64   `json:"predicted_ltv"`
}

// Global state
var (
	ltvClient   pb.LTVServiceClient
	auditLogger *csv.Writer
	auditFile   *os.File
)

// Initialize LTV service connection
func initLTVService() {
	addr := os.Getenv("LTV_GRPC_ADDR")
	if addr == "" {
		addr = "localhost:50051"
	}
	conn, err := grpc.Dial(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Printf("⚠️ Warning: Could not connect to LTV service: %v", err)
		log.Printf("🔄 SyncEngage will operate in heuristic mode")
		return
	}
	ltvClient = pb.NewLTVServiceClient(conn)
	log.Println("✅ Connected to SyncValue™ AI Brain (LTV Service)")
}

// Fetch LTV prediction for a customer
func fetchLTV(customerID string, spend, score float64) (float64, string) {
	if ltvClient == nil {
		// Fallback heuristic
		ltv := spend*1.2 + score*10
		return ltv, "Heuristic: No LTV service available"
	}

	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	resp, err := ltvClient.PredictLTV(ctx, &pb.LTVRequest{
		CustomerId:      customerID,
		RecentSpend:     spend,
		EngagementScore: score,
	})

	if err != nil {
		log.Printf("⚠️ LTV prediction failed: %v", err)
		ltv := spend*1.2 + score*10
		return ltv, "Fallback heuristic"
	}

	return resp.PredictedLtv, resp.Explanation
}

// Assess churn risk based on recency and engagement
func assessChurnRisk(customer Customer) string {
	daysSinceLastPurchase := time.Since(customer.LastPurchase).Hours() / 24
	daysSinceLastEngagement := time.Since(customer.LastEngagement).Hours() / 24

	if daysSinceLastPurchase > 90 || daysSinceLastEngagement > 60 {
		return "high"
	} else if daysSinceLastPurchase > 45 || daysSinceLastEngagement > 30 {
		return "medium"
	}
	return "low"
}

// Generate retention trigger based on customer profile
func generateRetentionTrigger(customer Customer) *RetentionTrigger {
	ltv, explanation := fetchLTV(customer.ID, customer.TotalSpend, customer.EngagementScore)
	customer.LTV = ltv
	customer.ChurnRisk = assessChurnRisk(customer)

	log.Printf("📊 Customer %s | LTV: %.2f | Churn Risk: %s", customer.ID, ltv, customer.ChurnRisk)
	log.Printf("   🧠 AI: %s", explanation)

	trigger := &RetentionTrigger{
		CustomerID:   customer.ID,
		ExecutedAt:   time.Now(),
		PredictedLTV: ltv,
	}

	// Decision logic based on churn risk and LTV
	switch customer.ChurnRisk {
	case "high":
		if ltv > 200 {
			// High-value at-risk customer
			trigger.TriggerType = "churn_risk_high_value"
			trigger.Action = "offer"
			trigger.DiscountPct = 20.0
			trigger.Message = fmt.Sprintf("We miss you! Here's 20%% off your next order (LTV: $%.0f)", ltv)
			log.Printf("🎯 RETENTION TRIGGER: High-value customer (LTV $%.0f) - 20%% discount offer", ltv)
		} else {
			// Standard at-risk customer
			trigger.TriggerType = "churn_risk_standard"
			trigger.Action = "email"
			trigger.DiscountPct = 10.0
			trigger.Message = "We haven't seen you in a while. Here's 10% off to welcome you back!"
			log.Printf("📧 RETENTION TRIGGER: At-risk customer (LTV $%.0f) - 10%% re-engagement email", ltv)
		}

	case "medium":
		if ltv > 300 {
			// Premium customer check-in
			trigger.TriggerType = "high_value_check"
			trigger.Action = "survey"
			trigger.Message = "How's everything going? We value your feedback."
			log.Printf("⭐ LOYALTY TRIGGER: Premium customer (LTV $%.0f) - feedback survey", ltv)
		} else {
			// Moderate engagement nudge
			trigger.TriggerType = "dormant"
			trigger.Action = "email"
			trigger.Message = "Check out what's new! Exclusive updates just for you."
			log.Printf("📬 ENGAGEMENT TRIGGER: Moderate customer (LTV $%.0f) - content update", ltv)
		}

	case "low":
		if ltv > 500 {
			// VIP customer appreciation
			trigger.TriggerType = "high_value_check"
			trigger.Action = "offer"
			trigger.DiscountPct = 15.0
			trigger.Message = fmt.Sprintf("Thank you for being a VIP! Exclusive 15%% off (LTV: $%.0f)", ltv)
			log.Printf("👑 VIP TRIGGER: High-value loyal customer (LTV $%.0f) - exclusive offer", ltv)
		}
		// Active low-risk customers don't need aggressive triggers
	}

	// Compliance check with SyncShield before executing trigger
	if trigger.TriggerType != "" {
		if guardWithSyncShield(trigger.PredictedLTV) {
			logAudit(trigger)
		} else {
			log.Printf("🛡️ COMPLIANCE: Trigger for %s suppressed by SyncShield", customer.ID)
			return nil
		}
	}

	return trigger
}

// Log retention trigger to audit trail
func logAudit(trigger *RetentionTrigger) {
	if auditLogger == nil {
		return
	}
	auditLogger.Write([]string{
		trigger.ExecutedAt.Format(time.RFC3339),
		trigger.CustomerID,
		trigger.TriggerType,
		trigger.Action,
		trigger.Message,
		fmt.Sprintf("%.2f", trigger.DiscountPct),
		fmt.Sprintf("%.2f", trigger.PredictedLTV),
	})
	auditLogger.Flush()
}

// Initialize audit log
func initAuditLog() {
	var err error
	auditFile, err = os.OpenFile("syncengage_audit.csv", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Printf("⚠️ Could not open audit log: %v", err)
		return
	}

	auditLogger = csv.NewWriter(auditFile)
	// Write header if new file
	fileInfo, _ := auditFile.Stat()
	if fileInfo.Size() == 0 {
		auditLogger.Write([]string{"timestamp", "customer_id", "trigger_type", "action", "message", "discount_pct", "predicted_ltv"})
		auditLogger.Flush()
	}

	log.Println("✅ Audit log initialized: syncengage_audit.csv")
}

// guardWithSyncShield queries SyncShield to validate budget/governor
func guardWithSyncShield(ltv float64) bool {
	// call SHIELD_URL (env) or default http://localhost:8081/check
	client := &http.Client{Timeout: 400 * time.Millisecond}
	shieldURL := os.Getenv("SHIELD_URL")
	if shieldURL == "" {
		shieldURL = "http://localhost:8081/check"
	}
	url := fmt.Sprintf("%s?ltv=%.2f", shieldURL, ltv)
	resp, err := client.Get(url)
	if err != nil {
		// Be permissive if SyncShield is unreachable
		log.Printf("⚠️ SyncShield unreachable (%v). Proceeding permissively.", err)
		return true
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusOK {
		return true
	}
	if resp.StatusCode == http.StatusForbidden {
		return false
	}
	// Default permissive for any other status
	return true
}

// HTTP health endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	status := map[string]interface{}{
		"status":     "healthy",
		"service":    "SyncEngage™ Retention Agent",
		"ltv_client": ltvClient != nil,
		"timestamp":  time.Now().Format(time.RFC3339),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

// HTTP API endpoint to trigger retention check for a customer
func triggerRetentionHandler(w http.ResponseWriter, r *http.Request) {
	var customer Customer
	if err := json.NewDecoder(r.Body).Decode(&customer); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	trigger := generateRetentionTrigger(customer)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(trigger)
}

// Simulate CRM data polling (in production, this would integrate with Salesforce, HubSpot, etc.)
func simulateCRMPolling() {
	log.Println("🔄 Starting CRM polling simulation...")

	// Sample customer data
	customers := []Customer{
		{
			ID:              "cust_001",
			Email:           "alice@example.com",
			LastPurchase:    time.Now().AddDate(0, 0, -95), // 95 days ago
			TotalSpend:      450.0,
			PurchaseCount:   12,
			EngagementScore: 8.5,
			LastEngagement:  time.Now().AddDate(0, 0, -70),
		},
		{
			ID:              "cust_002",
			Email:           "bob@example.com",
			LastPurchase:    time.Now().AddDate(0, 0, -15), // 15 days ago
			TotalSpend:      850.0,
			PurchaseCount:   28,
			EngagementScore: 9.2,
			LastEngagement:  time.Now().AddDate(0, 0, -3),
		},
		{
			ID:              "cust_003",
			Email:           "charlie@example.com",
			LastPurchase:    time.Now().AddDate(0, 0, -50), // 50 days ago
			TotalSpend:      120.0,
			PurchaseCount:   4,
			EngagementScore: 6.0,
			LastEngagement:  time.Now().AddDate(0, 0, -35),
		},
		{
			ID:              "cust_004",
			Email:           "diana@example.com",
			LastPurchase:    time.Now().AddDate(0, 0, -5), // 5 days ago
			TotalSpend:      1200.0,
			PurchaseCount:   45,
			EngagementScore: 9.8,
			LastEngagement:  time.Now().AddDate(0, 0, -1),
		},
	}

	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		log.Println("\n═══════════════════════════════════════════════════")
		log.Println("🔍 CRM Sync Cycle: Analyzing customer retention...")
		log.Println("═══════════════════════════════════════════════════")

		for _, customer := range customers {
			generateRetentionTrigger(customer)
		}

		log.Println("═══════════════════════════════════════════════════")
	}
}

func main() {
	log.Println("🚀 KIKI SyncEngage™ - Post-Acquisition Loyalty Agent")
	log.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

	initAuditLog()
	defer func() {
		if auditFile != nil {
			auditFile.Close()
		}
	}()

	initLTVService()

	// Start HTTP server
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/trigger", triggerRetentionHandler)

	go func() {
		log.Println("🌐 HTTP API starting on :8083")
		log.Println("   Health: http://localhost:8083/health")
		log.Println("   Trigger: POST http://localhost:8083/trigger")
		if err := http.ListenAndServe(":8083", nil); err != nil {
			log.Fatal(err)
		}
	}()

	// Start CRM polling simulation
	simulateCRMPolling()
}
