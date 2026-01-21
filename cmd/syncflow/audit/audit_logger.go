package audit

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	_ "github.com/lib/pq"
)

// AuditLogger writes immutable audit trail entries to PostgreSQL/TimescaleDB
// [I] Immutable Audit Trail - A-Z Roadmap
type AuditLogger struct {
	db          *sql.DB
	batchBuffer []*AuditEntry
	batchSize   int
	flushTicker *time.Ticker
}

// AuditEntry represents a single audit log entry
type AuditEntry struct {
	// Request metadata
	RequestID  string    `json:"request_id"`
	Timestamp  time.Time `json:"timestamp"`
	CustomerID string    `json:"customer_id"`
	CampaignID string    `json:"campaign_id,omitempty"`

	// LTV prediction (from SyncValue™)
	PredictedLTV  float64 `json:"predicted_ltv"`
	Confidence    float64 `json:"confidence"`
	LTVLowerBound float64 `json:"ltv_lower_bound"`
	LTVUpperBound float64 `json:"ltv_upper_bound"`
	ModelVersion  string  `json:"model_version"`

	// Bid execution (from SyncFlow™)
	BidAmount     float64 `json:"bid_amount"`
	BidSource     string  `json:"bid_source"` // AI_PREDICTION | HEURISTIC_FALLBACK | MANUAL_OVERRIDE
	Platform      string  `json:"platform"`
	PlatformBidID string  `json:"platform_bid_id,omitempty"`

	// Outcome tracking
	BidStatus    string `json:"bid_status"` // ACCEPTED | REJECTED | FAILED | BUDGET_EXCEEDED
	CircuitState string `json:"circuit_state,omitempty"`
	UsedFallback bool   `json:"used_fallback"`

	// Actual LTV (populated later via ingestion)
	ActualLTV          *float64   `json:"actual_ltv,omitempty"`
	ActualLTVTimestamp *time.Time `json:"actual_ltv_timestamp,omitempty"`
	LTVErrorPct        *float64   `json:"ltv_error_pct,omitempty"`

	// Performance metrics
	ExecutionTimeMs int `json:"execution_time_ms"`
	InferenceTimeUs int `json:"inference_time_us"`

	// Budget tracking
	CampaignBudget  float64 `json:"campaign_budget"`
	CurrentSpend    float64 `json:"current_spend"`
	RemainingBudget float64 `json:"remaining_budget"`

	// Metadata (flexible JSON field)
	Metadata map[string]interface{} `json:"metadata,omitempty"`

	// Explanation (AI transparency)
	Explanation string `json:"explanation,omitempty"`
}

// NewAuditLogger creates a new audit logger with batch flushing
func NewAuditLogger(connStr string, batchSize int, flushInterval time.Duration) (*AuditLogger, error) {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Test connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	logger := &AuditLogger{
		db:          db,
		batchBuffer: make([]*AuditEntry, 0, batchSize),
		batchSize:   batchSize,
		flushTicker: time.NewTicker(flushInterval),
	}

	// Start background flush goroutine
	go logger.backgroundFlush()

	return logger, nil
}

// Write appends an audit entry to the batch buffer
func (a *AuditLogger) Write(ctx context.Context, entry *AuditEntry) error {
	// Set timestamp if not provided
	if entry.Timestamp.IsZero() {
		entry.Timestamp = time.Now()
	}

	a.batchBuffer = append(a.batchBuffer, entry)

	// Flush if batch is full
	if len(a.batchBuffer) >= a.batchSize {
		return a.Flush(ctx)
	}

	return nil
}

// Flush writes all buffered entries to the database
func (a *AuditLogger) Flush(ctx context.Context) error {
	if len(a.batchBuffer) == 0 {
		return nil
	}

	tx, err := a.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.PrepareContext(ctx, `
		INSERT INTO audit_log (
			timestamp, request_id, customer_id, campaign_id,
			predicted_ltv, confidence, ltv_lower_bound, ltv_upper_bound, model_version,
			bid_amount, bid_source, platform, platform_bid_id,
			bid_status, circuit_state, used_fallback,
			actual_ltv, actual_ltv_timestamp, ltv_error_pct,
			execution_time_ms, inference_time_us,
			campaign_budget, current_spend, remaining_budget,
			metadata, explanation
		) VALUES (
			$1, $2, $3, $4,
			$5, $6, $7, $8, $9,
			$10, $11, $12, $13,
			$14, $15, $16,
			$17, $18, $19,
			$20, $21,
			$22, $23, $24,
			$25, $26
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, entry := range a.batchBuffer {
		metadataJSON, err := json.Marshal(entry.Metadata)
		if err != nil {
			return fmt.Errorf("failed to marshal metadata: %w", err)
		}

		_, err = stmt.ExecContext(ctx,
			entry.Timestamp, entry.RequestID, entry.CustomerID, entry.CampaignID,
			entry.PredictedLTV, entry.Confidence, entry.LTVLowerBound, entry.LTVUpperBound, entry.ModelVersion,
			entry.BidAmount, entry.BidSource, entry.Platform, entry.PlatformBidID,
			entry.BidStatus, entry.CircuitState, entry.UsedFallback,
			entry.ActualLTV, entry.ActualLTVTimestamp, entry.LTVErrorPct,
			entry.ExecutionTimeMs, entry.InferenceTimeUs,
			entry.CampaignBudget, entry.CurrentSpend, entry.RemainingBudget,
			metadataJSON, entry.Explanation,
		)
		if err != nil {
			return fmt.Errorf("failed to insert audit entry: %w", err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	// Clear buffer after successful flush
	a.batchBuffer = a.batchBuffer[:0]

	return nil
}

// backgroundFlush periodically flushes the buffer
func (a *AuditLogger) backgroundFlush() {
	for range a.flushTicker.C {
		ctx := context.Background()
		if err := a.Flush(ctx); err != nil {
			// Log error but don't crash (audit is non-blocking)
			fmt.Printf("⚠️  Audit flush error: %v\n", err)
		}
	}
}

// Close flushes remaining entries and closes the database connection
func (a *AuditLogger) Close() error {
	a.flushTicker.Stop()

	// Final flush
	ctx := context.Background()
	if err := a.Flush(ctx); err != nil {
		return err
	}

	return a.db.Close()
}

// GetAuditTrail retrieves audit entries with filters
func (a *AuditLogger) GetAuditTrail(ctx context.Context, filters AuditFilters) ([]*AuditEntry, error) {
	query := `
		SELECT 
			timestamp, request_id, customer_id, campaign_id,
			predicted_ltv, confidence, ltv_lower_bound, ltv_upper_bound, model_version,
			bid_amount, bid_source, platform, platform_bid_id,
			bid_status, circuit_state, used_fallback,
			actual_ltv, actual_ltv_timestamp, ltv_error_pct,
			execution_time_ms, inference_time_us,
			campaign_budget, current_spend, remaining_budget,
			metadata, explanation
		FROM audit_log
		WHERE 1=1
	`

	args := []interface{}{}
	argIdx := 1

	if filters.CustomerID != "" {
		query += fmt.Sprintf(" AND customer_id = $%d", argIdx)
		args = append(args, filters.CustomerID)
		argIdx++
	}

	if filters.Platform != "" {
		query += fmt.Sprintf(" AND platform = $%d", argIdx)
		args = append(args, filters.Platform)
		argIdx++
	}

	if !filters.StartTime.IsZero() {
		query += fmt.Sprintf(" AND timestamp >= $%d", argIdx)
		args = append(args, filters.StartTime)
		argIdx++
	}

	if !filters.EndTime.IsZero() {
		query += fmt.Sprintf(" AND timestamp <= $%d", argIdx)
		args = append(args, filters.EndTime)
		argIdx++
	}

	query += " ORDER BY timestamp DESC LIMIT 1000"

	rows, err := a.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query audit trail: %w", err)
	}
	defer rows.Close()

	entries := []*AuditEntry{}
	for rows.Next() {
		entry := &AuditEntry{}
		var metadataJSON []byte

		err := rows.Scan(
			&entry.Timestamp, &entry.RequestID, &entry.CustomerID, &entry.CampaignID,
			&entry.PredictedLTV, &entry.Confidence, &entry.LTVLowerBound, &entry.LTVUpperBound, &entry.ModelVersion,
			&entry.BidAmount, &entry.BidSource, &entry.Platform, &entry.PlatformBidID,
			&entry.BidStatus, &entry.CircuitState, &entry.UsedFallback,
			&entry.ActualLTV, &entry.ActualLTVTimestamp, &entry.LTVErrorPct,
			&entry.ExecutionTimeMs, &entry.InferenceTimeUs,
			&entry.CampaignBudget, &entry.CurrentSpend, &entry.RemainingBudget,
			&metadataJSON, &entry.Explanation,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan audit entry: %w", err)
		}

		if err := json.Unmarshal(metadataJSON, &entry.Metadata); err != nil {
			return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
		}

		entries = append(entries, entry)
	}

	return entries, nil
}

// AuditFilters for querying audit trail
type AuditFilters struct {
	CustomerID string
	CampaignID string
	Platform   string
	StartTime  time.Time
	EndTime    time.Time
}

// GetAccuracyMetrics retrieves real-time accuracy metrics
func (a *AuditLogger) GetAccuracyMetrics(ctx context.Context, platform string) (*AccuracyMetrics, error) {
	query := `
		SELECT
			platform,
			COUNT(*) AS total_predictions,
			COUNT(*) FILTER (WHERE actual_ltv IS NOT NULL) AS verified_predictions,
			AVG(ltv_error_pct) AS avg_error_pct,
			COUNT(*) FILTER (WHERE ABS(ltv_error_pct) <= 10) AS within_tolerance,
			ROUND(
				COUNT(*) FILTER (WHERE ABS(ltv_error_pct) <= 10)::NUMERIC / 
				NULLIF(COUNT(*) FILTER (WHERE actual_ltv IS NOT NULL), 0) * 100, 
				2
			) AS accuracy_pct
		FROM audit_log
		WHERE timestamp >= NOW() - INTERVAL '24 hours'
	`

	if platform != "" {
		query += " AND platform = $1"
	}

	query += " GROUP BY platform"

	var row *sql.Row
	if platform != "" {
		row = a.db.QueryRowContext(ctx, query, platform)
	} else {
		row = a.db.QueryRowContext(ctx, query)
	}

	metrics := &AccuracyMetrics{}
	err := row.Scan(
		&metrics.Platform,
		&metrics.TotalPredictions,
		&metrics.VerifiedPredictions,
		&metrics.AvgErrorPct,
		&metrics.WithinTolerance,
		&metrics.AccuracyPct,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to get accuracy metrics: %w", err)
	}

	return metrics, nil
}

// AccuracyMetrics for LTV momentum tracking
type AccuracyMetrics struct {
	Platform            string
	TotalPredictions    int
	VerifiedPredictions int
	AvgErrorPct         float64
	WithinTolerance     int
	AccuracyPct         float64
}
