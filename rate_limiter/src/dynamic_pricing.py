"""
Dynamic Pricing and Request Admission Control

This module implements the dual-based pricing mechanism:
1. Compare request price (π) vs customer willingness-to-pay
2. Accept/reject based on price comparison
3. Track revenue and acceptance rates
4. Apply minimum pricing floor even when no congestion
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

# Minimum price per request (base rate even with slack capacity)
MIN_PRICE_PER_REQUEST = 0.01  # $0.01 base price


class RequestDecision(Enum):
    """Possible outcomes for a request"""
    ACCEPTED_FREE = "accepted_free"  # π = 0, no charge
    ACCEPTED_CHARGED = "accepted_charged"  # π > 0, customer willing to pay
    REJECTED_PRICE = "rejected_price"  # π > customer's willingness
    REJECTED_HARD_SLA = "rejected_hard_sla"  # Would violate hard constraint
    REJECTED_CAPACITY = "rejected_capacity"  # No capacity available


@dataclass
class Request:
    """Represents an incoming API request"""
    client_id: str
    timestamp: float
    tier: str
    max_price: float  # Customer's predefined willingness-to-pay


@dataclass
class RequestOutcome:
    """Outcome of processing a request"""
    request: Request
    decision: RequestDecision
    dual_price: float  # Current system price when request arrived
    charge: float  # Amount charged (0 if rejected or free)
    processing_time_ms: float  # Time to make decision


class DynamicPricingController:
    """
    Controls request admission based on dual prices.

    VRP Connection: Similar to dynamic dial-a-ride systems that accept/reject
    requests based on current vehicle availability and marginal costs.
    """

    def __init__(self, enable_charging: bool = True):
        """
        Initialize pricing controller.

        Args:
            enable_charging: Whether to actually charge clients (vs simulation)
        """
        self.enable_charging = enable_charging

        # Statistics
        self.total_requests = 0
        self.accepted_requests = 0
        self.rejected_requests = 0
        self.total_revenue = 0.0
        self.outcomes_by_tier: Dict[str, List[RequestOutcome]] = {}

        # Price history for analytics
        self.price_samples: List[Tuple[float, float]] = []  # (timestamp, price)

    def process_request(self,
                       request: Request,
                       current_dual_price: float,
                       hard_sla_headroom: float = 0.0) -> RequestOutcome:
        """
        Process an incoming request using dual-based pricing.

        Decision logic:
        1. Check hard SLA constraints (for premium clients)
        2. Apply minimum pricing floor (even with slack capacity)
        3. Compare effective price vs customer's willingness-to-pay
        4. Accept/reject and charge accordingly

        Args:
            request: The incoming request
            current_dual_price: Current π from LP solution
            hard_sla_headroom: Available capacity before violating SLAs (req/s)

        Returns:
            RequestOutcome with decision and charge
        """
        start_time = time.time()
        self.total_requests += 1

        # Apply minimum pricing floor: effective_price = max(π, min_price)
        # This ensures base revenue even when no congestion
        effective_price = max(current_dual_price, MIN_PRICE_PER_REQUEST)

        # Record price sample (use effective price)
        self.price_samples.append((request.timestamp, effective_price))

        # Check hard SLA constraints (premium tier)
        if request.tier == "premium" and hard_sla_headroom <= 0:
            decision = RequestDecision.REJECTED_HARD_SLA
            charge = 0.0
            self.rejected_requests += 1

        # Compare effective price vs willingness-to-pay
        elif request.max_price >= effective_price:
            # Customer willing to pay the effective price
            if effective_price <= MIN_PRICE_PER_REQUEST and current_dual_price == 0:
                # Slack capacity but charging minimum price
                decision = RequestDecision.ACCEPTED_CHARGED
            else:
                # Congestion pricing in effect
                decision = RequestDecision.ACCEPTED_CHARGED

            charge = effective_price if self.enable_charging else 0.0
            self.accepted_requests += 1
            self.total_revenue += charge

        else:
            # Customer not willing to pay effective price
            decision = RequestDecision.REJECTED_PRICE
            charge = 0.0
            self.rejected_requests += 1

        processing_time = (time.time() - start_time) * 1000  # ms

        outcome = RequestOutcome(
            request=request,
            decision=decision,
            dual_price=current_dual_price,
            charge=charge,
            processing_time_ms=processing_time
        )

        # Track by tier
        if request.tier not in self.outcomes_by_tier:
            self.outcomes_by_tier[request.tier] = []
        self.outcomes_by_tier[request.tier].append(outcome)

        return outcome

    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        acceptance_rate = (
            self.accepted_requests / self.total_requests
            if self.total_requests > 0 else 0.0
        )

        # Per-tier statistics
        tier_stats = {}
        for tier, outcomes in self.outcomes_by_tier.items():
            accepted = sum(1 for o in outcomes
                          if o.decision in [RequestDecision.ACCEPTED_FREE,
                                           RequestDecision.ACCEPTED_CHARGED])
            total = len(outcomes)
            revenue = sum(o.charge for o in outcomes)
            avg_price_paid = revenue / accepted if accepted > 0 else 0.0

            tier_stats[tier] = {
                'total_requests': total,
                'accepted': accepted,
                'rejected': total - accepted,
                'acceptance_rate': accepted / total if total > 0 else 0.0,
                'revenue': revenue,
                'avg_price_paid': avg_price_paid
            }

        # Price statistics
        prices = [p for _, p in self.price_samples]
        price_stats = {
            'mean': np.mean(prices) if prices else 0.0,
            'median': np.median(prices) if prices else 0.0,
            'std': np.std(prices) if prices else 0.0,
            'min': np.min(prices) if prices else 0.0,
            'max': np.max(prices) if prices else 0.0,
            'samples': len(prices)
        }

        return {
            'total_requests': self.total_requests,
            'accepted_requests': self.accepted_requests,
            'rejected_requests': self.rejected_requests,
            'acceptance_rate': acceptance_rate,
            'total_revenue': self.total_revenue,
            'revenue_per_request': self.total_revenue / self.total_requests if self.total_requests > 0 else 0.0,
            'tier_stats': tier_stats,
            'price_stats': price_stats
        }

    def print_summary(self):
        """Print human-readable statistics summary"""
        stats = self.get_statistics()

        print("\n" + "=" * 70)
        print("DYNAMIC PRICING SUMMARY")
        print("=" * 70)

        print(f"\nOverall Statistics:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Accepted: {stats['accepted_requests']} ({stats['acceptance_rate']:.1%})")
        print(f"  Rejected: {stats['rejected_requests']} ({1-stats['acceptance_rate']:.1%})")
        print(f"  Total revenue: ${stats['total_revenue']:.2f}")
        print(f"  Revenue per request: ${stats['revenue_per_request']:.4f}")

        print(f"\nPer-Tier Breakdown:")
        for tier, tier_stats in stats['tier_stats'].items():
            print(f"\n  {tier.upper()}:")
            print(f"    Requests: {tier_stats['total_requests']}")
            print(f"    Acceptance rate: {tier_stats['acceptance_rate']:.1%}")
            print(f"    Revenue: ${tier_stats['revenue']:.2f}")
            print(f"    Avg price paid: ${tier_stats['avg_price_paid']:.4f}")

        print(f"\nPrice Statistics:")
        print(f"  Mean: ${stats['price_stats']['mean']:.4f}")
        print(f"  Median: ${stats['price_stats']['median']:.4f}")
        print(f"  Std Dev: ${stats['price_stats']['std']:.4f}")
        print(f"  Range: ${stats['price_stats']['min']:.4f} - ${stats['price_stats']['max']:.4f}")


def simulate_dynamic_pricing():
    """
    Simulate dynamic pricing over time with varying load.
    """
    print("=" * 70)
    print("Dynamic Pricing Simulation")
    print("=" * 70)

    from .rate_limiter_core import Client, RateLimiterLP

    # Create pricing controller
    controller = DynamicPricingController(enable_charging=True)

    # Create rate limiter
    limiter = RateLimiterLP(capacity=100.0, use_gurobi=True)

    # Simulate 3 scenarios: low, medium, high load
    scenarios = [
        ("Low Load", 0.6),
        ("Medium Load", 1.0),
        ("High Load", 1.5)
    ]

    print("\nScenario simulation:")
    print("-" * 70)

    for scenario_name, load_factor in scenarios:
        print(f"\n{scenario_name} (load factor: {load_factor}x)")

        # Create clients with varying demand
        clients = [
            Client(
                id="alice",
                tier="premium",
                weight=10.0,
                min_rate=30.0,
                max_willingness_to_pay=0.50,
                current_demand=50.0 * load_factor
            ),
            Client(
                id="bob",
                tier="standard",
                weight=5.0,
                min_rate=0.0,
                max_willingness_to_pay=0.20,
                current_demand=40.0 * load_factor
            ),
            Client(
                id="carol",
                tier="free",
                weight=1.0,
                min_rate=0.0,
                max_willingness_to_pay=0.0,
                current_demand=30.0 * load_factor
            )
        ]

        # Solve LP to get dual price
        solution = limiter.solve(clients, verbose=False)
        dual_price = solution.dual_price

        print(f"  Dual price (π): ${dual_price:.4f}/request")

        # Simulate requests from each client
        current_time = 0.0
        for client in clients:
            # Generate several requests for this client
            num_requests = int(client.current_demand / 10)  # Sample of demand
            for _ in range(num_requests):
                request = Request(
                    client_id=client.id,
                    timestamp=current_time,
                    tier=client.tier,
                    max_price=client.max_willingness_to_pay
                )
                outcome = controller.process_request(request, dual_price)
                current_time += 0.1

        # Show decisions for this scenario
        print(f"  Decisions:")
        for client in clients:
            decision_text = "✓ Accept" if client.max_willingness_to_pay >= dual_price else "✗ Reject"
            if dual_price == 0:
                decision_text = "✓ Accept (free)"
            print(f"    {client.id:10s}: {decision_text} "
                  f"(willing to pay ${client.max_willingness_to_pay:.2f})")

    # Print final summary
    controller.print_summary()


if __name__ == "__main__":
    simulate_dynamic_pricing()
