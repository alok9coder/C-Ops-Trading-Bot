import threading


class Config:
    """Thread-safe singleton configuration and live state tracker."""

    # Lock used to avoid concurrent mutation of global state.
    _lock = threading.RLock()

    # Fixed constants used throughout the bot.
    MARKET_TAX_FACTOR: float = 0.80
    MIN_PROFIT_THRESHOLD: float = 100.0

    # Runtime values that are updated as bids are placed and released.
    AVAILABLE_BUDGET: float = 5000.0
    CURRENT_RUNNING_STATE: bool = True
    MY_ACTIVE_BUY_ORDERS: dict[str, int] = {}

    @classmethod
    def get_available_budget(cls) -> float:
        # Return the current liquid budget available for new bids.
        with cls._lock:
            return float(cls.AVAILABLE_BUDGET)

    @classmethod
    def set_available_budget(cls, amount: float) -> None:
        # Replace the current budget with a new value.
        with cls._lock:
            cls.AVAILABLE_BUDGET = float(amount)

    @classmethod
    def adjust_available_budget(cls, delta: float) -> None:
        # Increase or decrease budget by a delta amount.
        with cls._lock:
            cls.AVAILABLE_BUDGET = float(cls.AVAILABLE_BUDGET) + float(delta)

    @classmethod
    def is_running(cls) -> bool:
        # Return whether the bot should continue running.
        with cls._lock:
            return bool(cls.CURRENT_RUNNING_STATE)

    @classmethod
    def set_running_state(cls, state: bool) -> None:
        # Set the global running flag for emergency stop or graceful shutdown.
        with cls._lock:
            cls.CURRENT_RUNNING_STATE = bool(state)

    @classmethod
    def get_active_order(cls, skin_name: str) -> int | None:
        # Return the current bid amount for a skin if one exists.
        with cls._lock:
            return cls.MY_ACTIVE_BUY_ORDERS.get(skin_name)

    @classmethod
    def set_active_order(cls, skin_name: str, bid_value: int) -> None:
        # Record a new or updated active bid for a given skin.
        with cls._lock:
            cls.MY_ACTIVE_BUY_ORDERS[skin_name] = int(bid_value)

    @classmethod
    def remove_active_order(cls, skin_name: str) -> None:
        # Remove an active bid when it has been cancelled or replaced.
        with cls._lock:
            if skin_name in cls.MY_ACTIVE_BUY_ORDERS:
                cls.MY_ACTIVE_BUY_ORDERS.pop(skin_name, None)

    @classmethod
    def get_active_orders(cls) -> dict[str, int]:
        # Return a copy of the current active buy orders dictionary.
        with cls._lock:
            return dict(cls.MY_ACTIVE_BUY_ORDERS)
