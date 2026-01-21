package main

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/user/kiki-agent/cmd/syncflow/budget"
)

// DemoBudgeter shows Sliding Window Budgeter protecting against burst spending
// Demonstrates how the budgeter prevents capital leaks during high-frequency bidding

func DemoBudgeter() {
	fmt.Println("🛡️  KIKI Agent™ Sliding Window Budgeter Demo")
	fmt.Println("   Preventing capital leaks with 10-minute burst limits")
	fmt.Println()

	// Create budgeter: 10-minute window, $5,000 burst limit
	budgeter := budget.NewSlidingWindowBudget(10*time.Minute, 5000.0)

	fmt.Println("Configuration:")
	fmt.Println("  Window Duration: 10 minutes")
	fmt.Println("  Max Burst Limit: $5,000.00")
	fmt.Println()

	// Simulate 4 phases of bid activity
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	simulateHealthyTraffic(budgeter)
	time.Sleep(2 * time.Second)

	fmt.Println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	simulateBurstTraffic(budgeter)
	time.Sleep(2 * time.Second)

	fmt.Println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	simulateBudgetExceeded(budgeter)
	time.Sleep(2 * time.Second)

	fmt.Println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	showPlatformBreakdown(budgeter)

	fmt.Println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("✅ Demo Complete")
	fmt.Println("   Sliding Window Budgeter successfully prevented capital leak")
	fmt.Println("   Integrate with circuit breaker for complete resilience stack")
}

func simulateHealthyTraffic(budgeter *budget.SlidingWindowBudget) {
	fmt.Println("Phase 1: Healthy Traffic (5 bids)")
	platforms := []string{"google_ads", "meta", "tiktok", "linkedin", "amazon"}

	for i := 0; i < 5; i++ {
		platform := platforms[rand.Intn(len(platforms))]
		bidAmount := float64(rand.Intn(200) + 50) // $50-$250

		err := budgeter.RecordSpend(bidAmount, platform, fmt.Sprintf("req-%d", i))
		if err != nil {
			fmt.Printf("  ❌ Bid rejected: %v\n", err)
		} else {
			status := budgeter.GetBudgetStatus()
			fmt.Printf("  ✅ Bid accepted: $%.2f on %s (Total: $%.2f / $%.2f)\n",
				bidAmount, platform, status.CurrentSpend, status.TotalBudget)
		}

		time.Sleep(500 * time.Millisecond)
	}

	printBudgetStatus(budgeter)
}

func simulateBurstTraffic(budgeter *budget.SlidingWindowBudget) {
	fmt.Println("Phase 2: Burst Traffic (20 rapid bids)")

	for i := 0; i < 20; i++ {
		bidAmount := float64(rand.Intn(300) + 100) // $100-$400

		err := budgeter.RecordSpend(bidAmount, "google_ads", fmt.Sprintf("burst-%d", i))
		if err != nil {
			// Budget exceeded - trigger circuit breaker
			fmt.Printf("  🔴 BURST LIMIT EXCEEDED: %v\n", err)
			fmt.Println("     → Triggering circuit breaker OPEN state")
			fmt.Println("     → Activating heuristic fallback mode")
			break
		}

		status := budgeter.GetBudgetStatus()
		utilizationIcon := "🟢"
		if status.UtilizationPct > 80 {
			utilizationIcon = "🟠"
		}
		if status.UtilizationPct > 95 {
			utilizationIcon = "🔴"
		}

		fmt.Printf("  %s Bid %d: $%.2f (Utilization: %.1f%%)\n",
			utilizationIcon, i+1, bidAmount, status.UtilizationPct)

		time.Sleep(100 * time.Millisecond)
	}

	printBudgetStatus(budgeter)
}

func simulateBudgetExceeded(budgeter *budget.SlidingWindowBudget) {
	fmt.Println("Phase 3: Budget Protection Test")

	// Try to place a large bid
	largeAmount := 1500.0

	fmt.Printf("  Attempting $%.2f bid...\n", largeAmount)

	if !budgeter.CanSpend(largeAmount) {
		fmt.Printf("  🛡️  Budget protection activated!\n")
		fmt.Printf("     Cannot spend $%.2f without exceeding burst limit\n", largeAmount)

		status := budgeter.GetBudgetStatus()
		fmt.Printf("     Current: $%.2f | Limit: $%.2f | Available: $%.2f\n",
			status.CurrentSpend, status.TotalBudget, status.RemainingBudget)
	} else {
		err := budgeter.RecordSpend(largeAmount, "tradedesk", "large-bid")
		if err != nil {
			fmt.Printf("  ❌ Bid rejected: %v\n", err)
		} else {
			fmt.Printf("  ✅ Bid accepted: $%.2f\n", largeAmount)
		}
	}

	printBudgetStatus(budgeter)
}

func showPlatformBreakdown(budgeter *budget.SlidingWindowBudget) {
	fmt.Println("Phase 4: Platform Spend Breakdown")

	spendByPlatform := budgeter.GetSpendByPlatform()

	fmt.Println("  Platform Distribution:")
	for platform, spend := range spendByPlatform {
		fmt.Printf("    %12s: $%8.2f\n", platform, spend)
	}

	status := budgeter.GetBudgetStatus()
	fmt.Println()
	fmt.Printf("  Total Spend:      $%.2f\n", status.CurrentSpend)
	fmt.Printf("  Remaining Budget: $%.2f\n", status.RemainingBudget)
	fmt.Printf("  Spend Rate:       $%.2f/min\n", status.SpendRatePerMin)
}

func printBudgetStatus(budgeter *budget.SlidingWindowBudget) {
	status := budgeter.GetBudgetStatus()

	fmt.Println()
	fmt.Println("  Budget Status:")
	fmt.Printf("    Current Spend:    $%.2f\n", status.CurrentSpend)
	fmt.Printf("    Remaining Budget: $%.2f\n", status.RemainingBudget)
	fmt.Printf("    Utilization:      %.1f%%\n", status.UtilizationPct)
	fmt.Printf("    Spend Rate:       $%.2f/min\n", status.SpendRatePerMin)
	fmt.Printf("    Events in Window: %d\n", status.EventCount)

	if status.BudgetExceeded {
		fmt.Println("    ⚠️  BUDGET EXCEEDED - CIRCUIT BREAKER ACTIVE")
	}

	fmt.Println()
}
