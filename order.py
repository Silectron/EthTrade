from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


@dataclass
class Order:
    exec_handler: Callable[[Order], None]


@dataclass
class BuyOrder(Order):
    budget: float


@dataclass
class SellOrder(Order):
    quantity: float


@dataclass
class MarketOrder(Order):
    ...


@dataclass
class LimitOrder(Order):
    limit_price: float


@dataclass
class StopOrder(Order):
    stop_price: float
    limit_price: float


@dataclass
class MarketBuyOrder(MarketOrder, BuyOrder):
    ...


@dataclass
class LimitBuyOrder(LimitOrder, BuyOrder):
    ...


@dataclass
class StopBuyOrder(StopOrder, BuyOrder):
    ...


@dataclass
class MarketSellOrder(MarketOrder, SellOrder):
    ...


@dataclass
class LimitSellOrder(LimitOrder, SellOrder):
    ...


@dataclass
class StopSellOrder(StopOrder, SellOrder):
    ...
