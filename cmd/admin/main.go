package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/websocket"
	_ "github.com/lib/pq"
	"github.com/prometheus/client_golang/api"
	v1 "github.com/prometheus/client_golang/api/prometheus/v1"
)

// Database connection helper
func getDB() (*sql.DB, error) {
	host := os.Getenv("DB_HOST")
	name := os.Getenv("DB_NAME")
	user := os.Getenv("DB_USER")
	pass := os.Getenv("DB_PASSWORD")
	dsn := fmt.Sprintf("host=%s dbname=%s user=%s password=%s sslmode=disable", host, name, user, pass)
	return sql.Open("postgres", dsn)
}

// Admin API - Port 8085
// Aggregates metrics from all services and provides real-time monitoring

const PORT = 8085

// ServiceStatus represents the health of a microservice
type ServiceStatus struct {
	Name           string             `json:"name"`
	Status         string             `json:"status"` // "up", "down", "degraded"
	Uptime         float64            `json:"uptime"` // percentage
	RequestsPerSec float64            `json:"requests_per_sec"`
	ErrorRate      float64            `json:"error_rate"` // percentage
	Latency        map[string]float64 `json:"latency"`    // p50, p95, p99
	LastCheck      time.Time          `json:"last_check"`
}

// DashboardMetrics represents aggregated platform metrics
type DashboardMetrics struct {
	Timestamp       time.Time                `json:"timestamp"`
	Services        map[string]ServiceStatus `json:"services"`
	Uptime          float64                  `json:"uptime"`
	ActiveCampaigns int                      `json:"active_campaigns"`
	DailyRevenue    float64                  `json:"daily_revenue"`
	TotalBudget     float64                  `json:"total_budget"`
	SpentToday      float64                  `json:"spent_today"`
}

// AdminAlert represents an alert event
type AdminAlert struct {
	ID        string    `json:"id"`
	Severity  string    `json:"severity"` // "info", "warning", "critical"
	Message   string    `json:"message"`
	Service   string    `json:"service"`
	Timestamp time.Time `json:"timestamp"`
	Resolved  bool      `json:"resolved"`
}

// AdminAction represents an action taken by an admin
type AdminAction struct {
	ID        string    `json:"id"`
	AdminID   string    `json:"admin_id"`
	Action    string    `json:"action"`
	Resource  string    `json:"resource"`
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
}

// Admin represents an authenticated admin user
type Admin struct {
	ID       string   `json:"id"`
	Username string   `json:"username"`
	Role     string   `json:"role"` // super_admin, manager, analyst, operator
	Perms    []string `json:"perms"`
}

type AdminServer struct {
	mu               sync.RWMutex
	metrics          DashboardMetrics
	alerts           []AdminAlert
	actions          []AdminAction
	clients          map[*websocket.Conn]bool
	broadcast        chan interface{}
	prometheus       v1.API
	serviceEndpoints map[string]string
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // In production, validate origin
	},
}

func NewAdminServer() *AdminServer {
	// Initialize Prometheus client
	client, err := api.NewClient(api.Config{
		Address: "http://localhost:9090", // Prometheus on port 9090
	})
	if err != nil {
		log.Printf("Warning: Could not connect to Prometheus: %v", err)
	}

	server := &AdminServer{
		clients:    make(map[*websocket.Conn]bool),
		broadcast:  make(chan interface{}, 100),
		prometheus: v1.NewAPI(client),
		serviceEndpoints: map[string]string{
			"syncshield": "http://localhost:8081/health",
			"syncengage": "http://localhost:8083/health",
			"syncflow":   "http://localhost:8082/health",
			"synccreate": "http://localhost:8084/health",
			"syncvalue":  "http://localhost:50051/health", // gRPC
		},
		metrics: DashboardMetrics{
			Timestamp: time.Now(),
			Services:  make(map[string]ServiceStatus),
		},
	}

	return server
}

// HealthCheckService polls a service's health endpoint
func (s *AdminServer) HealthCheckService(name, endpoint string) ServiceStatus {
	status := ServiceStatus{
		Name:      name,
		Status:    "down",
		Latency:   make(map[string]float64),
		LastCheck: time.Now(),
	}

	client := &http.Client{Timeout: 5 * time.Second}
	start := time.Now()
	resp, err := client.Get(endpoint)
	duration := time.Since(start).Seconds() * 1000 // ms

	if err != nil || resp.StatusCode != http.StatusOK {
		return status
	}
	defer resp.Body.Close()

	status.Status = "up"
	status.Latency["current"] = duration
	status.Uptime = 99.95 + (5 - duration/100) // Rough estimate

	return status
}

// CollectMetrics aggregates metrics from all sources
func (s *AdminServer) CollectMetrics(ctx context.Context) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		s.mu.Lock()

		// Check all services
		for name, endpoint := range s.serviceEndpoints {
			status := s.HealthCheckService(name, endpoint)
			s.metrics.Services[name] = status
		}

		// Update timestamp
		s.metrics.Timestamp = time.Now()

		// Broadcast update to WebSocket clients
		s.mu.Unlock()
		select {
		case s.broadcast <- s.metrics:
		default:
		}
	}
}

// HandleWebSocket handles real-time metric subscriptions
func (s *AdminServer) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}
	defer conn.Close()

	s.mu.Lock()
	s.clients[conn] = true
	s.mu.Unlock()

	log.Printf("WebSocket client connected. Total clients: %d", len(s.clients))

	// Send current metrics immediately
	s.mu.RLock()
	conn.WriteJSON(map[string]interface{}{
		"type":    "metrics",
		"data":    s.metrics,
		"message": "Connected to KIKI Super-Admin",
	})
	s.mu.RUnlock()

	// Listen for client messages
	for {
		var msg map[string]interface{}
		err := conn.ReadJSON(&msg)
		if err != nil {
			s.mu.Lock()
			delete(s.clients, conn)
			s.mu.Unlock()
			log.Printf("WebSocket client disconnected. Remaining: %d", len(s.clients))
			break
		}

		// Handle commands from client
		if command, ok := msg["command"].(string); ok {
			s.handleAdminCommand(command, msg)
		}
	}
}

// BroadcastMetrics sends metrics to all connected WebSocket clients
func (s *AdminServer) BroadcastMetrics() {
	for {
		update := <-s.broadcast
		s.mu.RLock()
		for client := range s.clients {
			err := client.WriteJSON(map[string]interface{}{
				"type": "metrics",
				"data": update,
			})
			if err != nil {
				client.Close()
				delete(s.clients, client)
			}
		}
		s.mu.RUnlock()
	}
}

func (s *AdminServer) handleAdminCommand(command string, msg map[string]interface{}) {
	switch command {
	case "restart_service":
		if service, ok := msg["service"].(string); ok {
			action := AdminAction{
				ID:        fmt.Sprintf("action_%d", time.Now().Unix()),
				Action:    "restart",
				Resource:  service,
				Status:    "pending",
				Timestamp: time.Now(),
			}
			s.mu.Lock()
			s.actions = append(s.actions, action)
			s.mu.Unlock()
			log.Printf("Action: Restart %s", service)
		}
	case "pause_campaign":
		if campaign, ok := msg["campaign"].(string); ok {
			log.Printf("Action: Pause campaign %s", campaign)
		}
	}
}

// HTTP Handlers

// GET /api/admin/health - Overall platform health
func (s *AdminServer) handleHealth(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	upCount := 0
	for _, svc := range s.metrics.Services {
		if svc.Status == "up" {
			upCount++
		}
	}

	response := map[string]interface{}{
		"status":         "ok",
		"timestamp":      s.metrics.Timestamp,
		"services_up":    upCount,
		"services_total": len(s.metrics.Services),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// GET /api/admin/metrics - Aggregated metrics
func (s *AdminServer) handleMetrics(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.metrics)
}

// GET /api/admin/services - Service status
func (s *AdminServer) handleServices(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.metrics.Services)
}

// GET /api/admin/alerts - Active alerts
func (s *AdminServer) handleAlerts(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.alerts)
}

// GET /api/admin/audit-log - Audit trail
func (s *AdminServer) handleAuditLog(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.actions)
}

// POST /api/admin/alerts/config - Update alert thresholds
func (s *AdminServer) handleAlertConfig(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var config map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&config); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// In production, save to database
	log.Printf("Alert config updated: %v", config)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "updated"})
}

// POST /api/admin/services/restart?service=SERVICE_NAME - Restart a service (Go 1.21 compatible)
func (s *AdminServer) handleRestartService(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	service := r.URL.Query().Get("service")
	if service == "" {
		http.Error(w, "Missing service parameter", http.StatusBadRequest)
		return
	}
	log.Printf("Restart requested for service: %s", service)

	// In production, call docker/k8s to restart
	action := AdminAction{
		ID:        fmt.Sprintf("action_%d", time.Now().Unix()),
		Action:    "restart",
		Resource:  service,
		Status:    "pending",
		Timestamp: time.Now(),
	}

	s.mu.Lock()
	s.actions = append(s.actions, action)
	s.mu.Unlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "restart_initiated",
		"service": service,
	})
}

// Serve admin UI (static files)
func (s *AdminServer) handleStatic(w http.ResponseWriter, r *http.Request) {
	path := "./web/admin" + r.URL.Path
	http.ServeFile(w, r, path)
}

func handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var creds struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&creds); err != nil {
		http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
		return
	}
	// DEMO: Hardcoded credentials (replace with DB lookup + bcrypt in production)
	if creds.Username == "superadmin" && creds.Password == "supersecret" {
		http.SetCookie(w, &http.Cookie{
			Name:     "admin_session",
			Value:    "valid",
			Path:     "/",
			HttpOnly: true,
			Secure:   false,
			MaxAge:   3600,
		})
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok"}`))
	} else {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte(`{"error":"Invalid username or password"}`))
	}
}

func main() {
	// Test DB connection at startup
	db, err := getDB()
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	if err := db.Ping(); err != nil {
		log.Fatalf("Database not reachable: %v", err)
	}
	log.Println("Connected to Postgres DB successfully.")
	db.Close()

	server := NewAdminServer()

	// Start metrics collection in background
	go server.CollectMetrics(context.Background())

	// Start broadcasting metrics to WebSocket clients
	go server.BroadcastMetrics()

	// HTTP routes
	http.HandleFunc("/health", server.handleHealth)
	http.HandleFunc("/api/admin/health", server.handleHealth)
	http.HandleFunc("/api/admin/metrics", server.handleMetrics)
	http.HandleFunc("/api/admin/services", server.handleServices)
	http.HandleFunc("/api/admin/alerts", server.handleAlerts)
	http.HandleFunc("/api/admin/audit-log", server.handleAuditLog)
	http.HandleFunc("/api/admin/alerts/config", server.handleAlertConfig)
	http.HandleFunc("/api/admin/services/restart", server.handleRestartService)
	http.HandleFunc("/api/admin/login", handleLogin)

	// WebSocket
	http.HandleFunc("/live/metrics", server.HandleWebSocket)

	// Static files
	http.Handle("/", http.FileServer(http.Dir("./web/admin")))

	addr := fmt.Sprintf(":%d", PORT)
	log.Printf("KIKI Super-Admin listening on %s", addr)
	log.Printf("Dashboard: http://localhost:%d", PORT)

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		if err := http.ListenAndServe(addr, nil); err != nil && err != http.ErrServerClosed {
			log.Printf("Server error: %v", err)
		}
	}()

	<-sigChan
	log.Println("Admin API shutting down...")
}
