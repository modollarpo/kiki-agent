package main

import (
	"fmt"
	"os"
)

func main() {
	if len(os.Args) < 2 {
		printUsage()
		return
	}

	demo := os.Args[1]

	switch demo {
	case "budget":
		fmt.Println()
		DemoBudgeter()
	case "metrics":
		fmt.Println()
		DemoLTVMomentum()
	case "all":
		fmt.Println()
		DemoBudgeter()
		fmt.Println()
		DemoLTVMomentum()
	default:
		fmt.Printf("Unknown demo: %s\n", demo)
		printUsage()
	}
}

func printUsage() {
	fmt.Println("📊 KIKI Agent™ Examples")
	fmt.Println()
	fmt.Println("Usage: go run . [demo]")
	fmt.Println()
	fmt.Println("Demos:")
	fmt.Println("  budget   - Sliding Window Budgeter (burst protection)")
	fmt.Println("  metrics  - LTV Momentum Tracking (real-time dashboard)")
	fmt.Println("  all      - Run all demos")
	fmt.Println()
	fmt.Println("Examples:")
	fmt.Println("  go run . budget")
	fmt.Println("  go run . metrics")
	fmt.Println("  go run . all")
	fmt.Println()
}
