FROM golang:1.21-alpine

WORKDIR /app

# Copy go.mod and go.sum from project root
COPY ../../go.mod ../../go.sum ./

# Download dependencies
RUN go mod download

# Copy the source code
COPY . .

# Build the binary
RUN go build -o syncengage .

# Expose the health/API port
EXPOSE 8083

# Run the agent
CMD ["./syncengage"]
