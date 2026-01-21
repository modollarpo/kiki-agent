# KIKI Super-Admin Dashboard

This is the web-based admin UI for the KIKI platform. It provides:
- Real-time service health and metrics
- Budget and campaign management
- Audit and compliance logs
- Alerts and notifications
- User and role management

## Structure
- `index.html` — Main entry point
- `css/` — Dashboard styles
- `js/` — Application logic
- `components/` — UI components
- `pages/` — Dashboard sections


## Database Credentials

- **Database Name:** kikidb
- **Username:** dolapo
- **Password:** Aquila2615
- **Host:** localhost

## Getting Started
1. Start the Admin API backend (`cmd/admin/main.go`)
2. Open `web/admin/index.html` in your browser
3. The dashboard will auto-fetch health status from `/api/admin/health`

## Next Steps
- Implement additional API endpoints in Admin API
- Build out dashboard pages and components
- Integrate with Prometheus, PostgreSQL, and all microservices
