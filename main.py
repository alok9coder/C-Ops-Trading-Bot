import random
import threading
import time
import msvcrt

import analyzer
import bot_actions
import config
import database

# The list of items to scan in each market sweep.
TARGET_SKIN_PORTFOLIO = [
    "URATIO - FINISHER",
    "GLOVES - AZURE DYNASTY",
    "GLOVES - BENGAL",
    "KUKRI - SUN STONE",
]


def emergency_panic_listener() -> None:
    # Background listener that sets the run-state to False when the user presses Q or ESC.
    while config.Config.is_running():
        if msvcrt.kbhit():
            key = msvcrt.getwch()
            if key.lower() == "q" or key == "\x1b":
                config.Config.set_running_state(False)
                print("[PANIC] Emergency stop received. Halting bot actions immediately.")
                return
        time.sleep(0.12)


def initialize_system() -> None:
    # Reset the database and apply the marketplace filter before beginning automation.
    print("Initializing Critical Ops trading bot...")
    database.reset_market_catalog()
    bot_actions.activate_by_type_filter()
    print("System initialized and BY TYPE filter activated.")


def scan_portfolio_and_build_feed() -> dict[str, tuple[int, int]]:
    # Scan the visible catalog rows and return the current price and volume values.
    market_feed: dict[str, tuple[int, int]] = {}
    rows = bot_actions.scan_catalog_rows(TARGET_SKIN_PORTFOLIO)
    for row in rows:
        market_feed[row.skin_name] = (row.price_value, row.volume_value)
    return market_feed


def main_loop() -> None:
    # Main execution loop that continuously evaluates and places bids.
    panic_thread = threading.Thread(target=emergency_panic_listener, daemon=True)
    panic_thread.start()

    while config.Config.is_running():
        try:
            print("Starting sweep for target skins...")
            database.reset_market_catalog()
            market_feed = scan_portfolio_and_build_feed()

            for skin_name in TARGET_SKIN_PORTFOLIO:
                if not config.Config.is_running():
                    break

                if skin_name not in market_feed:
                    continue

                print(f"Processing portfolio skin: {skin_name}")
                target_price, _ = market_feed[skin_name]
                bot_actions.open_skin_detail(bot_actions.scan_catalog_rows([skin_name])[0].row_center)

                lowest_sell_price, highest_buy_request = bot_actions.extract_skin_detail_prices()
                decision = analyzer.evaluate_skin_bid(
                    skin_name=skin_name,
                    current_market_highest_buy_request=highest_buy_request,
                    lowest_sell_price=lowest_sell_price,
                )

                database.save_or_update_skin_record(
                    skin_name=skin_name,
                    highest_bp=highest_buy_request,
                    lowest_sp=lowest_sell_price,
                    calculated_margin=analyzer.calculate_net_profit(lowest_sell_price, highest_buy_request + 1),
                )

                if decision is None:
                    print(f"No viable bid decision for {skin_name}. Returning to catalog.")
                    bot_actions.return_to_catalog()
                    continue

                print(
                    f"Decision for {skin_name}: {decision.action} at {decision.target_bid} with margin {decision.profit_margin:.2f}"
                )

                if not analyzer.reserve_budget_for_bid(decision):
                    print(f"Insufficient budget to reserve bid for {skin_name}.")
                    bot_actions.return_to_catalog()
                    continue

                bot_actions.place_bid(decision.target_bid)
                database.record_bid_history(
                    skin_name=decision.skin_name,
                    action=decision.action,
                    bid_value=decision.target_bid,
                    profit_margin=decision.profit_margin,
                )
                print(f"Placed bid for {skin_name} at {decision.target_bid}.")
                bot_actions.return_to_catalog()

                time.sleep(random.uniform(2.0, 4.0))

            print("Sweep complete. Sleeping before next cycle.")
            time.sleep(random.uniform(6.0, 10.0))

        except Exception as exc:
            print(f"[ERROR] {exc}")
            time.sleep(random.uniform(2.0, 4.0))

    print("Bot stopped by emergency signal or user request.")


def main() -> None:
    # Entry point for the bot that initializes state and starts the main loop.
    try:
        initialize_system()
        main_loop()
    except KeyboardInterrupt:
        config.Config.set_running_state(False)
        print("Keyboard interrupt detected; shutting down.")


if __name__ == "__main__":
    main()
