package main

import (
	"bytes"
	"context"
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"

	pb "github.com/user/kiki-agent/api/pb"
	"github.com/user/kiki-agent/cmd/syncflow/connectors"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// Data Structures
type SpendRecord struct {
	Timestamp time.Time
	Amount    float64
}

// Global Safety State
var (
	spendHistory   []SpendRecord
	mu             sync.Mutex
	maxBurstBudget = 500.0
	cache          map[string]PredictionResult
	cacheMu        sync.Mutex
)

type PredictionResult struct {
	LTV         float64
	Explanation string
	Timestamp   time.Time
}

func fetchLTV(client pb.LTVServiceClient, customerID string, spend, score float64) (float64, string) {
	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// Check semantic cache first
	key := "ltv:" + customerID
	cacheMu.Lock()
	if result, ok := cache[key]; ok && time.Since(result.Timestamp) < 5*time.Minute {
		cacheMu.Unlock()
		log.Printf(" CACHE HIT: Using cached LTV %.2f for %s", result.LTV, customerID)
		return result.LTV, result.Explanation
	}
	cacheMu.Unlock()

	// 1. Attempt High-Performance gRPC Call
	resp, err := client.PredictLTV(ctx, &pb.LTVRequest{
		CustomerId:      customerID,
		RecentSpend:     spend,
		EngagementScore: score,
	})

	if err != nil {
		// 2. DEGRADED MODE: Fallback to Heuristic
		log.Printf(" BRAIN OFFLINE: Using Safety Heuristic for %s", customerID)
		ltv := spend * 1.1
		explanation := fmt.Sprintf("Degraded mode: %.2f * 1.1 = %.2f", spend, ltv)
		// Cache even degraded results
		cacheMu.Lock()
		cache[key] = PredictionResult{LTV: ltv, Explanation: explanation, Timestamp: time.Now()}
		cacheMu.Unlock()
		return ltv, explanation
	}

	ltv := resp.PredictedLtv
	explanation := resp.Explanation
	// Cache the result
	cacheMu.Lock()
	cache[key] = PredictionResult{LTV: ltv, Explanation: explanation, Timestamp: time.Now()}
	cacheMu.Unlock()
	log.Printf(" CACHE MISS: Computed LTV %.2f for %s", ltv, customerID)

	return ltv, explanation
}

func checkBudget(ltv float64) bool {
	url := fmt.Sprintf("http://localhost:8081/check?ltv=%.2f", ltv)
	resp, err := http.Get(url)
	if err != nil {
		log.Printf("Budget check failed: %v", err)
		return false // Fail safe: deny if can't check
	}
	defer resp.Body.Close()
	return resp.StatusCode == 200
}

func recordSpend(amount float64) {
	url := fmt.Sprintf("http://localhost:8081/spend?amount=%.2f", amount)
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(nil))
	if err != nil {
		log.Printf("Spend recording failed: %v", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		log.Printf("Spend recording error: %s", string(body))
	}
	log.Printf(" Spend recorded: $%.2f", amount)
}

func CheckBudget() bool {
	mu.Lock()
	defer mu.Unlock()
	total := 0.0
	for _, r := range spendHistory {
		if time.Since(r.Timestamp) < 10*time.Minute {
			total += r.Amount
		}
	}
	return total < maxBurstBudget
}

// LogDecision writes a bidding decision to audit_log.csv
func LogDecision(customerID string, predictedLTV, bidAmount float64, decision, mode string) {
	file, err := os.OpenFile("../../audit_log.csv", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Error opening audit log: %v", err)
		return
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	timestamp := time.Now().Format(time.RFC3339)
	record := []string{timestamp, customerID, strconv.FormatFloat(predictedLTV, 'f', 2, 64), strconv.FormatFloat(bidAmount, 'f', 2, 64), decision, mode}
	if err := writer.Write(record); err != nil {
		log.Printf("Error writing to audit log: %v", err)
	}
}

func main() {
	// Set up gRPC connection
	conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()
	client := pb.NewLTVServiceClient(conn)

	log.Println(" KIKI SyncFlow gRPC Agent Online...")

	// Initialize in-memory semantic cache (for demo; use Redis in production)
	cache = make(map[string]PredictionResult)

	// Start health check server in background
	go func() {
		http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("OK"))
		})
		log.Println("Health server starting on :8082")
		if err := http.ListenAndServe(":8082", nil); err != nil {
			log.Printf("Health server error: %v", err)
		}
	}()

	// Initialize connector based on configuration
	connectorConfig := connectors.ConnectorConfig{
		Type:       connectors.GoogleAds, // Or Meta, TradeDesk
		APIKey:     os.Getenv("GOOGLE_ADS_API_KEY"),
		CustomerID: os.Getenv("GOOGLE_ADS_CUSTOMER_ID"),
	}

	connector, err := connectors.NewConnector(connectorConfig)
	if err != nil {
		log.Fatalf("Failed to create connector: %v", err)
	}

	// Connect to the ad platform
	ctx := context.Background()
	if err := connector.Connect(ctx); err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer connector.Close()

	log.Printf("Platform Status: %s", connector.GetStatus())

	ticker := time.NewTicker(2 * time.Second)

	for range ticker.C {
		// Simulate customer data
		customerID := "user_1"
		spend := 50.0
		score := 0.8

		ltv, explanation := fetchLTV(client, customerID, spend, score)

		if !checkBudget(ltv) {
			log.Println("  SAFETY ALERT: Bid validation failed. Bidding paused.")
			continue
		}

		// Log AI explanation for transparency
		log.Printf(" AI Explanation: %s", explanation)

		// Anomaly detection: flag unusually high LTV predictions
		mode := "normal"
		if ltv > 500 {
			log.Printf(" ANOMALY ALERT: Unusual LTV prediction of %.2f detected", ltv)
			mode = "anomaly"
		}

		var decision string
		var bidAmount float64
		if ltv > 100 && checkBudget(ltv) {
			decision = "Placed"
			bidAmount = 10.0

			// Place bid via connector
			bidReq := &connectors.BidRequest{
				CustomerID:   customerID,
				PredictedLTV: ltv,
				BidAmount:    bidAmount,
				Explanation:  explanation,
				Timestamp:    time.Now(),
				CampaignID:   "campaign_123",
				AudienceID:   "audience_456",
			}

			bidResp, err := connector.PlaceBid(ctx, bidReq)
			if err != nil {
				log.Printf("❌ Bid placement failed: %v", err)
			} else {
				log.Printf("✅ Bid placed: %s (ID: %s)", bidResp.Message, bidResp.BidID)
			}

			recordSpend(bidAmount)
		} else {
			decision = "Skipped"
			bidAmount = 0.0
			log.Println("Low Value - Skipping")
		}

		// Audit Logic: Log Decision
		LogDecision(customerID, ltv, bidAmount, decision, mode)
	}
}
