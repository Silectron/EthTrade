from __future__ import annotations
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from math import inf
from dataclasses import dataclass, field
from typing import List, Dict

from ethtrade.portfolio import Portfolio, SimulationPortfolio
from ethtrade.order import FilledOrder, BuyOrder, SellOrder


class Strategy:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def reset(self, price: float):
        raise NotImplementedError

    def step(self, price: float):
        raise NotImplementedError


@dataclass
class Level:
    budget: float
    quantity: int
    lower_bound: float
    upper_bound: float
    order_ids: List[str] = field(default_factory=list)
    next: Level = None
    prev: Level = None


class GridStrategy(Strategy):
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        super().__init__(portfolio)
        self.order_id_to_level_map: Dict[str, Level] = {}

        self._construct_linked_list(levels)

    def _construct_linked_list(self, levels: List[float]):
        n = len(levels) - 1

        self.current_level = Level(0, 0, 0, levels[0])

        for i in range(n):
            budget = self.portfolio.budget / n

            self.current_level.next = Level(
                budget, 0, levels[i], levels[i + 1])
            self.current_level.next.prev = self.current_level
            self.current_level = self.current_level.next

            # place orders
            order_id = self.portfolio.place_stop_buy_order(
                levels[i] - 50, levels[i], budget, self._buy_callback)
            self.order_id_to_level_map[order_id] = self.current_level
            self.current_level.order_ids.append(order_id)

        self.current_level.next = Level(0, 0, levels[n], inf)
        self.current_level.next.prev = self.current_level

    def _buy_callback(self, filled_order: FilledOrder):
        level = self.order_id_to_level_map[filled_order.order.order_id]
        level.budget -= filled_order.order.budget
        level.quantity += filled_order.quantity

        del self.order_id_to_level_map[filled_order.order.order_id]
        level.order_ids.remove(filled_order.order.order_id)

    def _sell_callback(self, filled_order: FilledOrder):
        level = self.order_id_to_level_map[filled_order.order.order_id]
        level.budget += filled_order.price * filled_order.quantity
        level.quantity -= filled_order.quantity

        del self.order_id_to_level_map[filled_order.order.order_id]
        level.order_ids.remove(filled_order.order.order_id)

        order_id = self.portfolio.place_limit_buy_order(
            level.lower_bound, level.budget, self._buy_callback)
        self.order_id_to_level_map[order_id] = level
        level.order_ids.append(order_id)

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
        level = self.current_level

        while level.prev is not None:
            remaining_quantity = level.quantity

            for order_id in level.order_ids:
                order = self.portfolio.get_order_by_id(order_id)
                if isinstance(order, SellOrder):
                    self.portfolio.cancel_order(order_id)

                    del self.order_id_to_level_map[order_id]
                    level.order_ids.remove(order_id)

                    order_id = self.portfolio.place_stop_sell_order(
                        level.upper_bound + 50, level.upper_bound,
                        order.quantity, order.fill_handler)
                    self.order_id_to_level_map[order_id] = level
                    level.order_ids.append(order_id)

                    remaining_quantity -= order.quantity

            if remaining_quantity > 0:
                order_id = self.portfolio.place_stop_sell_order(
                    level.upper_bound + 50, level.upper_bound,
                    remaining_quantity, self._sell_callback)
                self.order_id_to_level_map[order_id] = level
                level.order_ids.append(order_id)

            level = level.prev
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
    portfolio = SimulationPortfolio('ETC-USD', 10000, 0, 0.005)

    pct = 1.05
    levels = np.cumprod(np.ones(5) * pct) * 3000 / pct
    strategy = GridStrategy(portfolio, levels)

    df = pd.read_csv('data/Bitstamp_ETHUSD_1h.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()

    df = df[df.index > '2021-06-20']
    # df = df[df.index > '2021-08-19']
    # df = df[df.index < '2021-08-25']

    strategy.reset(df.iloc[0].close)

    for i in range(len(df)):
        strategy.step(df.iloc[i]['close'])
    print("Networth:", portfolio.budget +
          portfolio.quantity * df.iloc[i]['close'])

    domain = range(len(df))

    plt.plot(domain, df['close'])

    buy_orders = []
    sell_orders = []

    for step, filled_order in portfolio.order_fill:
        if isinstance(filled_order.order, BuyOrder):
            buy_orders.append([step, filled_order.price])
        elif isinstance(filled_order.order, SellOrder):
            sell_orders.append([step, filled_order.price])

    plt.scatter(*zip(*buy_orders), c='r', s=100, marker='v')
    plt.scatter(*zip(*sell_orders), c='g', s=100, marker='^')

    for level in levels:
        plt.axhline(level, color='k', alpha=0.1, linestyle='--')

    plt.show()


if __name__ == '__main__':
    main()
