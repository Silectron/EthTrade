from __future__ import annotations
from portfolio import Portfolio, SimulationPortfolio
from order import Order, FilledOrder, BuyOrder, SellOrder, LimitBuyOrder, LimitSellOrder, StopSellOrder, StopBuyOrder
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from math import inf
from dataclasses import dataclass
from typing import List, Dict


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
    quantity: int
    lower_bound: float
    upper_bound: float
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

            # order_id = self.portfolio.place_stop_buy_order(
            #     0.995 * levels[i], levels[i], budget, self._buy_callback)
            # self.order_id_to_level_map[order_id] = self.current_level

        self.current_level.next = Level(0, 0, levels[n], inf)
        self.current_level.next.prev = self.current_level

    def _buy_callback(self, filled_order: FilledOrder):
        level: Level = self.order_id_to_level_map[filled_order.order.order_id]

        level.budget -= filled_order.order.budget
        level.quantity += filled_order.quantity

        del self.order_id_to_level_map[filled_order.order.order_id]

        # order_id = self.portfolio.place_stop_sell_order(
        #     level.upper_bound,
        #     level.upper_bound,
        #     filled_order.quantity,
        #     self._sell_callback)

        # self.order_id_to_level_map[order_id] = level

    def _sell_callback(self, filled_order: FilledOrder):
        level = self.order_id_to_level_map.get(filled_order.order.order_id)

        level.budget += filled_order.price * filled_order.quantity
        level.quantity -= filled_order.quantity

        print(level.budget)
        print(level.quantity)

        # buy_order = self.portfolio.create_buy_limit_order(self.current_level.lower_bound,
        #                                                   self.portfolio.apply_fee(self.current_level.budget) /
        #                                                   self.current_level.lower_bound, self._buy_callback)
        # self._place_order(buy_order)
        if level.budget > 0:
            order_id = self.portfolio.place_limit_buy_order(
                level.lower_bound,
                level.budget,
                self._buy_callback
            )
            self.order_id_to_level_map[order_id] = self.current_level.prev

        # print(
        #     f"sold {order.quantity} for {order.total} at level {level.upper_bound}")

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
        # After executing an aggregated sell order
        # redistribute the sell amount to each level where budget is 0
        def distribute_callback(filled_order: FilledOrder):
            n = 0

            # go to level immediately below level where sell was executed
            level = self.order_id_to_level_map.get(
                filled_order.order.order_id).prev

            # Go through levels below level where sell was executed and stop before tail level
            # count the number of levels that sold in the aggregated sell order
            while level.prev is not None:
                if level.budget == 0:
                    n += 1

                # omit the tail level
                if level.prev.prev is None:
                    break
                level = level.prev

            # from level immediately above tail level, redistribute the sell amount to each level with budget 0
            # until before the level where sell was executed (order.price > level.lower_bound)
            while level.next is not None and filled_order.price > level.lower_bound:
                if level.budget == 0:
                    level.budget = filled_order.quantity * filled_order.price / n
                    level.quantity = 0

                    # this shouldn't be necessary
                    # buy_order = self.portfolio.create_buy_limit_order(level.lower_bound,
                    #                                                   self.portfolio.apply_fee(level.budget) /
                    #                                                   level.lower_bound, self._buy_callback)
                    # self._place_order(buy_order)

                level = level.next

        total_quantity = 0
        # Find all sell orders below or at the lower bound of the current level
        sell_orders = [
            order for order in self.portfolio.get_orders() if isinstance(order, StopSellOrder) and order.limit_price <= self.current_level.lower_bound]

        # return if there are no sell orders below or at the lower bound of the current level
        if len(sell_orders) < 1:
            return
        # return if there is only one sell order and its price is at the lower bound of the current level (no need to update order)
        elif len(sell_orders) == 1 and self.order_id_to_level_map.get(sell_orders[0].order_id) == self.current_level.prev:
            return

        # Aggregate the total quantity of sell orders below or at the lower bound of the current level
        for order in sell_orders:
            total_quantity += order.quantity
            self.portfolio.cancel_order(order)

        # Create a new sell stop order at the lower bound of the current level
        if total_quantity > 0:
            # print(
            #     f"Aggregated {total_quantity} to sell at lower bound of the current level")
            # self._place_order(self.portfolio.create_sell_stop_order(
            #     self.current_level.lower_bound, total_quantity, distribute_callback))

            order_id = self.portfolio.place_stop_sell_order(
                self.current_level.lower_bound,
                self.current_level.lower_bound,
                total_quantity,
                distribute_callback)
            self.order_id_to_level_map[order_id] = self.current_level

    def _handle_falling_entering_level(self, price: float):
        ...

    def _handle_rising_leaving_level(self, price: float):

        # buy_order = None
        sell_order = None

        for order in self.portfolio.get_orders():
            # Check if we have an existing sell order in the current level we are leaving
            if isinstance(order, StopSellOrder):
                if self.order_id_to_level_map.get(order.order_id) == self.current_level:
                    sell_order = order
                    break

        # if next budget is above 0, create a buy market order at the next level
        if self.current_level.next.budget > 0:
            order_id = self.portfolio.place_market_buy_order(
                self.current_level.next.budget,
                self._buy_callback)

            self.order_id_to_level_map[order_id] = self.current_level.next

        # if we dont have a stop sell order and the current level has holdings, place a sell limit order at the lower bound of the next level
        if sell_order is None and self.current_level.quantity > 0:
            # sell_order = self.portfolio.create_sell_stop_order(
            #     self.current_level.next.lower_bound, self.current_level.quantity, self._sell_callback)
            # self._place_order(sell_order)

            order_id = self.portfolio.place_stop_sell_order(
                self.current_level.upper_bound,
                self.current_level.upper_bound,
                self.current_level.quantity,
                self._sell_callback)

            self.order_id_to_level_map[order_id] = self.current_level.next

            # print(
            #     f"placed sell order at {self.current_level.next.lower_bound}")
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

    # df = df[df.index > '2021-06-20']
    # df = df[df.index > '2021-08-19']
    df = df[df.index > '2021-08-25']

    strategy.reset(df.iloc[0].close)

    for i in range(len(df)):
        strategy.step(df.iloc[i]['close'])
    print("Networth:", portfolio.budget +
          portfolio.quantity * df.iloc[i]['close'])

    domain = range(len(df))

    plt.plot(domain, df['close'])

    buy_orders = []
    sell_orders = []

    for i, (price, filled_orders) in enumerate(portfolio.order_history):
        for filled_order in filled_orders:
            if isinstance(filled_order.order, BuyOrder):
                buy_orders.append([i, filled_order.price])
            elif isinstance(filled_order.order, SellOrder):
                sell_orders.append([i, filled_order.price])

    plt.scatter(*zip(*buy_orders), c='r', s=100, marker='v')
    plt.scatter(*zip(*sell_orders), c='g', s=100, marker='^')

    for level in levels:
        plt.axhline(level, color='k', alpha=0.1, linestyle='--')

    plt.show()


if __name__ == '__main__':
    main()
