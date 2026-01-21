package crm

import (
	"database/sql"
	"time"

	_ "github.com/lib/pq" // PostgreSQL driver
)

// PostgreSQLConnector integrates with custom PostgreSQL CRM database
type PostgreSQLConnector struct {
	db         *sql.DB
	connString string
}

// NewPostgreSQLConnector creates a new PostgreSQL CRM connector
func NewPostgreSQLConnector(connString string) *PostgreSQLConnector {
	return &PostgreSQLConnector{
		connString: connString,
	}
}

func (p *PostgreSQLConnector) Connect() error {
	var err error
	p.db, err = sql.Open("postgres", p.connString)
	if err != nil {
		return err
	}

	// Test connection
	if err := p.db.Ping(); err != nil {
		return err
	}

	return nil
}

func (p *PostgreSQLConnector) FetchCustomers(filter map[string]interface{}) ([]Customer, error) {
	query := `
		SELECT 
			id, email, phone, first_name, last_name,
			last_purchase_date, total_spend, purchase_count,
			engagement_score, last_engagement_date
		FROM customers
		WHERE last_purchase_date > NOW() - INTERVAL '180 days'
		LIMIT 1000
	`

	rows, err := p.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	customers := make([]Customer, 0)
	for rows.Next() {
		var c Customer
		var lastPurchase, lastEngagement sql.NullTime

		err := rows.Scan(
			&c.ID, &c.Email, &c.Phone, &c.FirstName, &c.LastName,
			&lastPurchase, &c.TotalSpend, &c.PurchaseCount,
			&c.EngagementScore, &lastEngagement,
		)
		if err != nil {
			continue
		}

		if lastPurchase.Valid {
			c.LastPurchase = lastPurchase.Time
		}
		if lastEngagement.Valid {
			c.LastEngagement = lastEngagement.Time
		}

		customers = append(customers, c)
	}

	return customers, nil
}

func (p *PostgreSQLConnector) GetCustomer(id string) (*Customer, error) {
	query := `
		SELECT 
			id, email, phone, first_name, last_name,
			last_purchase_date, total_spend, purchase_count,
			engagement_score, last_engagement_date
		FROM customers
		WHERE id = $1
	`

	var c Customer
	var lastPurchase, lastEngagement sql.NullTime

	err := p.db.QueryRow(query, id).Scan(
		&c.ID, &c.Email, &c.Phone, &c.FirstName, &c.LastName,
		&lastPurchase, &c.TotalSpend, &c.PurchaseCount,
		&c.EngagementScore, &lastEngagement,
	)
	if err != nil {
		return nil, err
	}

	if lastPurchase.Valid {
		c.LastPurchase = lastPurchase.Time
	}
	if lastEngagement.Valid {
		c.LastEngagement = lastEngagement.Time
	}

	return &c, nil
}

func (p *PostgreSQLConnector) UpdateCustomer(customer Customer) error {
	query := `
		UPDATE customers
		SET engagement_score = $2, last_engagement_date = $3
		WHERE id = $1
	`

	_, err := p.db.Exec(query, customer.ID, customer.EngagementScore, time.Now())
	return err
}

func (p *PostgreSQLConnector) SendMessage(customerID, channel, message string, metadata map[string]string) error {
	// Log message to outbound_messages table
	query := `
		INSERT INTO outbound_messages (customer_id, channel, message, metadata, created_at)
		VALUES ($1, $2, $3, $4, $5)
	`

	metadataJSON := "{}"
	_, err := p.db.Exec(query, customerID, channel, message, metadataJSON, time.Now())
	return err
}

func (p *PostgreSQLConnector) CreateTag(customerID, tag string) error {
	query := `
		INSERT INTO customer_tags (customer_id, tag, created_at)
		VALUES ($1, $2, $3)
		ON CONFLICT DO NOTHING
	`

	_, err := p.db.Exec(query, customerID, tag, time.Now())
	return err
}

func (p *PostgreSQLConnector) GetName() string {
	return "PostgreSQL"
}

func (p *PostgreSQLConnector) Close() error {
	if p.db != nil {
		return p.db.Close()
	}
	return nil
}
