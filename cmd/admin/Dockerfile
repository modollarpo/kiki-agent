FROM golang:1.21-alpine AS builder

WORKDIR /build

# Install dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY cmd/admin ./

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o admin-api .

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates curl tzdata

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/admin-api .

# Copy web admin UI
COPY web/admin ./web/admin

# Expose port
EXPOSE 8085

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8085/health || exit 1

# Run the application
CMD ["./admin-api"]
