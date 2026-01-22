package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/go-redis/redis/v8"
)

var ctx = context.Background()

func main() {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "redis:6379"
	}
	client := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})
	fmt.Println("SyncFlow Go service started. Waiting for jobs...")
	for {
		job, err := client.BLPop(ctx, 0, "syncflow-queue").Result()
		if err != nil {
			log.Println("Error reading from Redis:", err)
			continue
		}
		fmt.Println("Processing job:", job[1])
		// Add SyncFlow processing logic here
	}
}
