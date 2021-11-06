from __future__ import annotations
from typing import List
from dataclasses import dataclass
from math import inf
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from portfolio import Portfolio, SimulationPortfolio
from orders import Order, BuyOrder, SellOrder

###############################################################################
# Strategy Section
###############################################################################


class Strategy:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def reset(self, price: float):
        raise NotImplementedError

    def step(self, price: float):
        raise NotImplementedError


@ dataclass
class Level:
    budget: float
    lower_bound: float
    upper_bound: float
    next: Level = None
    prev: Level = None


class GridStrategy(Strategy):
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        super().__init__(portfolio)
        self._construct_linked_list(levels)

    def _construct_linked_list(self, levels: List[float]):
        n = len(levels) - 1

        self.current_level = Level(0, 0, levels[0])

        for i in range(n):
            budget = self.portfolio.budget / n

            self.portfolio.place_stop_buy_order(
                0.95 * levels[i], levels[i], budget, self._buy_callback)

            self.current_level.next = Level(budget, levels[i], levels[i + 1])
            self.current_level.next.prev = self.current_level
            self.current_level = self.current_level.next

        self.current_level.next = Level(0, levels[n], inf)
        self.current_level.next.prev = self.current_level

    def _buy_callback(self, order: Order):
        level = self.current_level

        # TODO: refactor this
        while order.price != level.lower_bound:
            if order.price < level.lower_bound:
                level = level.prev
            elif order.price > level.lower_bound:
                level = level.next

        level.budget -= order.total

        self.portfolio.place_limit_sell_order(
            level.upper_bound, order.quantity, self._sell_callback)

    def _sell_callback(self, order: Order):
        level = self.current_level

        # TODO: refactor this
        while order.price != level.upper_bound:
            if order.price < level.upper_bound:
                level = level.prev
            elif order.price > level.upper_bound:
                level = level.next

        level.budget += order.total

        self.portfolio.create_buy_limit_order(
            level.lower_bound, level.budget, self._buy_callback)

    def _next_level(self):
        self.current_level = self.current_level.next

    def _prev_level(self):
        self.current_level = self.current_level.prev

    def reset(self, price: float):
        if price > self.current_level.upper_bound:
            while price > self.current_level.next.upper_bound:
                self._next_level()

        elif price < self.current_level.lower_bound:
            while price < self.current_level.prev.lower_bound:
                self._prev_level()

        self.portfolio.reset(price)

    def _handle_rising_entering_level(self, price: float):
        ...

    def _handle_falling_entering_level(self, price: float):
        ...

    def _handle_rising_leaving_level(self, price: float):
        ...

    def _handle_falling_leaving_level(self, price: float):
        ...

    def step(self, price: float):
        if price > self.current_level.upper_bound:
            self._handle_rising_leaving_level(price)

            while price > self.current_level.upper_bound:
                self._next_level()

            self._handle_rising_entering_level(price)

        elif price < self.current_level.lower_bound:
            self._handle_falling_leaving_level(price)

            while price < self.current_level.lower_bound:
                self._prev_level()

            self._handle_falling_entering_level(price)

        self.portfolio.step(price)


def main():
    portfolio = SimulationPortfolio('ETC-USD', 1000, 0, 0.005)

    pct = 1.05
    levels = np.cumprod(np.ones(5) * pct) * 3000 / pct
    strategy = GridStrategy(portfolio, levels)

    df = pd.read_csv('Bitstamp_ETHUSD_1h.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()

    df = df[df.index > '2021-06-20']

    strategy.reset(df.iloc[0].close)

    for i in range(len(df)):
        strategy.step(df.iloc[i]['close'])
    print("Networth:", portfolio.budget +
          portfolio.quantity * df.iloc[i]['close'])

    domain = range(len(df))

    plt.plot(domain, df['close'])

    buy_orders = []
    sell_orders = []

    for i, (price, orders) in enumerate(portfolio.order_history):
        for order in orders:
            if isinstance(order, BuyOrder):
                buy_orders.append([i, price])
            elif isinstance(order, SellOrder):
                sell_orders.append([i, price])

    plt.scatter(*zip(*buy_orders), c='r', s=100, marker='v')
    plt.scatter(*zip(*sell_orders), c='g', s=100, marker='^')

    for level in levels:
        plt.axhline(level, color='k', alpha=0.1, linestyle='--')

    plt.show()


if __name__ == '__main__':
    main()
