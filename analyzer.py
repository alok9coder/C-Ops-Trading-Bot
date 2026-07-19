from dataclasses import dataclass
from typing import Optional

import config


@dataclass
class BidDecision:
    """Holds a recommended action and target bid for a skin."""
    skin_name: str
    action: str
    target_bid: int
    profit_margin: float
    old_bid: int | None = None


def calculate_net_profit(lowest_sell_price: int, highest_buy_request: int) -> float:
    """Use strict marketplace tax formula per specification."""
    return float(lowest_sell_price) * config.Config.MARKET_TAX_FACTOR - float(highest_buy_request) / config.Config.MARKET_TAX_FACTOR


def is_currently_highest_bidder(skin_name: str, current_market_highest_buy_request: int) -> bool:
    # Determine whether the bot already maintains the highest bid for the skin.
    active_bid = config.Config.get_active_order(skin_name)
    if active_bid is None:
        return False
    return active_bid >= current_market_highest_buy_request


def evaluate_skin_bid(
    skin_name: str,
    current_market_highest_buy_request: int,
    lowest_sell_price: int,
) -> Optional[BidDecision]:
    """Decide whether to place a new bid or raise an existing bid."""
    if current_market_highest_buy_request <= 0 or lowest_sell_price <= 0:
        return None

    active_bid = config.Config.get_active_order(skin_name)
    target_bid = current_market_highest_buy_request + 1

    if active_bid is not None:
        if active_bid >= current_market_highest_buy_request:
            return None

        # Evaluate the budget if the existing bid is released.
        budget_if_modified = config.Config.get_available_budget() + active_bid
        if budget_if_modified < target_bid:
            return None

        profit_margin = calculate_net_profit(lowest_sell_price, target_bid)
        if profit_margin < config.Config.MIN_PROFIT_THRESHOLD:
            return None

        return BidDecision(
            skin_name=skin_name,
            action="increase",
            target_bid=target_bid,
            profit_margin=profit_margin,
            old_bid=active_bid,
        )

    budget_if_new = config.Config.get_available_budget()
    if budget_if_new < target_bid:
        return None

    profit_margin = calculate_net_profit(lowest_sell_price, target_bid)
    if profit_margin < config.Config.MIN_PROFIT_THRESHOLD:
        return None

    return BidDecision(
        skin_name=skin_name,
        action="place",
        target_bid=target_bid,
        profit_margin=profit_margin,
        old_bid=None,
    )


def reserve_budget_for_bid(decision: BidDecision) -> bool:
    """Reserve the budget and record the proposed active bid."""
    current_budget = config.Config.get_available_budget()
    if decision.action == "increase" and decision.old_bid is not None:
        effective_budget = current_budget + decision.old_bid
    else:
        effective_budget = current_budget

    if effective_budget < decision.target_bid:
        return False

    if decision.action == "increase" and decision.old_bid is not None:
        config.Config.adjust_available_budget(decision.old_bid)
    config.Config.adjust_available_budget(-decision.target_bid)
    config.Config.set_active_order(decision.skin_name, decision.target_bid)
    return True


def process_bid_outcome(skin_name: str, outcome: str, bid_value: int) -> None:
    """Update active order state after a bid confirmation or cancellation."""
    if outcome == "confirmed":
        config.Config.set_active_order(skin_name, bid_value)
    elif outcome == "cancelled":
        active_bid = config.Config.get_active_order(skin_name)
        if active_bid is not None:
            config.Config.adjust_available_budget(active_bid)
            config.Config.remove_active_order(skin_name)
