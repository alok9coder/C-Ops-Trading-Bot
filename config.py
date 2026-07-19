import threading


class Config:
    """Thread-safe singleton configuration and live state tracker."""

    _lock = threading.RLock()

    MARKET_TAX_FACTOR: float = 0.80
    MIN_PROFIT_THRESHOLD: float = 100.0

    # These live values are updated during runtime.
    AVAILABLE_BUDGET: float = 5000.0
    CURRENT_RUNNING_STATE: bool = True
    MY_ACTIVE_BUY_ORDERS: dict[str, int] = {}

    @classmethod
    def get_available_budget(cls) -> float:
        with cls._lock:
            return float(cls.AVAILABLE_BUDGET)

    @classmethod
    def set_available_budget(cls, amount: float) -> None:
        with cls._lock:
            cls.AVAILABLE_BUDGET = float(amount)

    @classmethod
    def adjust_available_budget(cls, delta: float) -> None:
        with cls._lock:
            cls.AVAILABLE_BUDGET = float(cls.AVAILABLE_BUDGET) + float(delta)

    @classmethod
    def is_running(cls) -> bool:
        with cls._lock:
            return bool(cls.CURRENT_RUNNING_STATE)

    @classmethod
    def set_running_state(cls, state: bool) -> None:
        with cls._lock:
            cls.CURRENT_RUNNING_STATE = bool(state)

    @classmethod
    def get_active_order(cls, skin_name: str) -> int | None:
        with cls._lock:
            return cls.MY_ACTIVE_BUY_ORDERS.get(skin_name)

    @classmethod
    def set_active_order(cls, skin_name: str, bid_value: int) -> None:
        with cls._lock:
            cls.MY_ACTIVE_BUY_ORDERS[skin_name] = int(bid_value)

    @classmethod
    def remove_active_order(cls, skin_name: str) -> None:
        with cls._lock:
            if skin_name in cls.MY_ACTIVE_BUY_ORDERS:
                cls.MY_ACTIVE_BUY_ORDERS.pop(skin_name, None)

    @classmethod
    def get_active_orders(cls) -> dict[str, int]:
        with cls._lock:
            return dict(cls.MY_ACTIVE_BUY_ORDERS)
