from __future__ import annotations
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
from math import inf


@dataclass
class Level:
    budget: float
    lower_bound: float
    upper_bound: float
    next: Level = None
    prev: Level = None
    order: Order


class Portfolio:
    def __init__(self, budget: float, securities: Dict[str, int],
                 transaction_fee: float):
        self.budget = budget
        self.securities = securities
        self.transaction_fee = transaction_fee

    def buy_all(self, price: float, security: str):
        self.budget = self.budget * (1 - self.transaction_fee)
        self.securities[security] += self.budget / price
        self.budget = 0

    def sell_all(self, price: float, security: str):
        self.budget += self.securities[security] * price
        self.budget = self.budget * (1 - self.transaction_fee)
        self.securities[security] = 0


class OrderType(Enum):
    MARKET = 1
    LIMIT = 2
    STOP = 3


class Order:
    def __init__(self, security: str, price: float, quantity: int,
                 order_type: OrderType):
        self.security = security
        self.price = price
        self.quantity = quantity
        self.order_type = order_type

# entry


class BuyOrder(Order):
    def __init__(self, security: str, price: float, quantity: int,
                 order_type: OrderType):
        super().__init__(security, price, quantity, order_type)

# loss


class SellOrder(Order):
    def __init__(self, security: str, price: float, quantity: int,
                 order_type: OrderType):
        super().__init__(security, price, quantity, order_type)


class GridStrategy:
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        self.portfolio = portfolio
        self.current_level = self._construct_linked_list(levels)

    def _construct_linked_list(self, levels: List[float]) -> Level:
        n = len(levels) - 1

        current_level = Level(0, 0, levels[0])

        for i in range(n):
            current_level.next = Level(
                portfolio.budget / n, levels[i], levels[i + 1])
            current_level.next.prev = current_level
            current_level = current_level.next

        current_level.next = Level(0, levels[n], inf)
        current_level.next.prev = current_level

        return current_level

    def _next_level(self, level: Level) -> Level | None:
        return level.next

    def _prev_level(self, level: Level) -> Level | None:
        return level.prev

    def _place_order(self, order: Order):
        self.current_level.order = order

    def reset(self, price: float):
        self.current_level = self.current_level.next
        while self.current_level.prev:
            self.current_level = self.current_level.prev

    def step(self, price: float):
        ...


def main():
    strategy = GridStrategy(
        Portfolio(1000, {'AAPL': 0, 'MSFT': 0}, 0.01), [10, 20, 30])


if __name__ == '__main__':
    main()
