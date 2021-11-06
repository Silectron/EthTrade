from __future__ import annotations
from typing import List
from dataclasses import dataclass
from math import inf
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from orders import OrderType, Order, BuyOrder, SellOrder, OrderList
from portfolio import Portfolio, SimulationPortfolio


###############################################################################
# Order Section
###############################################################################


###############################################################################
# Portfolio Section
###############################################################################


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
    quantity: int
    lower_bound: float
    upper_bound: float
    next: Level = None
    prev: Level = None


class GridStrategy(Strategy):
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        super().__init__(portfolio)
        self._construct_linked_list(levels)
        # self._distribute_budget()

    def _construct_linked_list(self, levels: List[float]):
        n = len(levels) - 1

        self.current_level = Level(0, 0, 0, levels[0])

        for i in range(n):
            budget = self.portfolio.budget / n

            price = levels[i]
            quantity = self.portfolio.apply_fee(budget) / price
            order = self.portfolio.create_buy_stop_order(
                price, quantity, self._buy_callback)
            self._place_order(order)

            self.current_level.next = Level(
                budget, 0, levels[i], levels[i + 1])
            self.current_level.next.prev = self.current_level
            self.current_level = self.current_level.next

        self.current_level.next = Level(0, 0, levels[n], inf)
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
        level.quantity += order.quantity

        print(
            f"bought {order.quantity} for {order.total} at level {level.lower_bound}")

    def _sell_callback(self, order: Order):
        level = self.current_level
        # TODO: refactor this
        while order.price != level.upper_bound:
            if order.price < level.upper_bound:
                level = level.prev
            elif order.price > level.upper_bound:
                level = level.next

        level.budget += order.total
        level.quantity -= order.quantity

        buy_order = self.portfolio.create_buy_limit_order(self.current_level.lower_bound,
                                                          self.portfolio.apply_fee(self.current_level.budget) /
                                                          self.current_level.lower_bound, self._buy_callback)
        self._place_order(buy_order)

        print(
            f"sold {order.quantity} for {order.total} at level {level.upper_bound}")

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
        def distribute_callback(order: Order):
            n = 0
            # get any level that is not the head
            level = self.current_level if self.current_level.next is not None else self.current_level.prev
            # go to level immediately below level where sell was executed
            while order.price != level.upper_bound:
                if order.price < level.upper_bound:
                    level = level.prev
                elif order.price > level.upper_bound:
                    level = level.next

            # Go through levels below level where sell was executed and stop before tail level
            # count the number of levels that sold in the aggregated sell order
            while level.prev is not None:
                if level.budget == 0:
                    n += 1

                # omit the tail level
                if level.prev.prev is None:
                    break
                level = level.prev

            if n == 0:
                return

            # from level immediately above tail level, redistribute the sell amount to each level with budget 0
            # until before the level where sell was executed (order.price > level.lower_bound)
            while level.next is not None and order.price > level.lower_bound:
                if level.budget == 0:
                    level.budget = order.total / n
                    level.quantity = 0

                    print(
                        f"Level {level.lower_bound} now has {level.budget} from sell at {order.price}")

                    # this shouldn't be necessary
                    # buy_order = self.portfolio.create_buy_limit_order(level.lower_bound,
                    #                                                   self.portfolio.apply_fee(level.budget) /
                    #                                                   level.lower_bound, self._buy_callback)
                    # self._place_order(buy_order)

                level = level.next
            print(
                f"sold {order.quantity} at {order.price} for total of {order.total} to {n} levels")

        total_quantity = 0
        # Find all sell orders below or at the lower bound of the current level
        sell_orders = [
            order for order in self.portfolio.orders.sell_orders if order.price <= self.current_level.lower_bound]

        # return if there are no sell orders below or at the lower bound of the current level
        if len(sell_orders) < 1:
            return
        # return if there is only one sell order and its price is at the lower bound of the current level (no need to update order)
        elif len(sell_orders) == 1 and sell_orders[0].price == self.current_level.lower_bound:
            return

        # Aggregate the total quantity of sell orders below or at the lower bound of the current level
        for order in sell_orders:
            total_quantity += order.quantity
            self.portfolio.orders.remove_order(order)

        # Create a new sell stop order at the lower bound of the current level
        if total_quantity > 0:
            # print(
            #     f"Aggregated {total_quantity} to sell at lower bound of the current level")
            self._place_order(self.portfolio.create_sell_stop_order(
                self.current_level.lower_bound, total_quantity, distribute_callback))

    def _handle_falling_entering_level(self, price: float):
        ...

    def _handle_rising_leaving_level(self, price: float):
        # Check if we have an existing buy order in the next level
        buy_order = None
        for order in self.portfolio.orders.buy_orders:
            if order.price == self.current_level.upper_bound:
                buy_order = order
                break

        # Check if we have an existing sell order in the current level we are leaving
        sell_order = None
        for order in self.portfolio.orders.sell_orders:
            if order.price == self.current_level.next.lower_bound:
                sell_order = order
                break

        # if not and the next budget is above 0, create a buy limit order at the lower bound of the next level
        if buy_order is None and self.current_level.next.budget > 0:
            buy_order = self.portfolio.create_buy_limit_order(self.current_level.upper_bound,
                                                              self.portfolio.apply_fee(self.current_level.next.budget) /
                                                              self.current_level.upper_bound, self._buy_callback)
            self._place_order(buy_order)
            # print(
            #     f"Placed buy limit order at {self.current_level.upper_bound}")

        # if we dont and the current level has holdings, place a sell limit order at the lower bound of the next level
        if sell_order is None and self.current_level.quantity > 0:
            sell_order = self.portfolio.create_sell_stop_order(
                self.current_level.next.lower_bound, self.current_level.quantity, self._sell_callback)
            self._place_order(sell_order)
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

    df = pd.read_csv('Bitstamp_ETHUSD_2021_minute.csv')
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

    for i, (price, orders) in enumerate(portfolio.order_history):
        for order in orders:
            if isinstance(order, BuyOrder):
                buy_orders.append([i, price])
            elif isinstance(order, SellOrder):
                sell_orders.append([i, order.price])

    plt.scatter(*zip(*buy_orders), c='r', s=100, marker='v')
    plt.scatter(*zip(*sell_orders), c='g', s=100, marker='^')

    for level in levels:
        plt.axhline(level, color='k', alpha=0.1, linestyle='--')

    plt.show()


if __name__ == '__main__':
    main()
