# Stage 1: Build
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .
RUN go build -o syncflow ./main.go

# Stage 2: Run
FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/syncflow .
HEALTHCHECK --interval=30s --timeout=3s \
  CMD ./syncflow --check-health || exit 1
CMD ["./syncflow"]