from __future__ import annotations
from typing import List, Dict, Callable
from dataclasses import dataclass
from enum import Enum
from math import inf
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from collections import defaultdict


###############################################################################
# Order Section
###############################################################################


class OrderType(Enum):
    MARKET = 1
    LIMIT = 2
    STOP = 3


@dataclass
class Order:
    price: float
    quantity: int
    total: float
    order_type: OrderType
    callback: Callable[[Order], None]


class BuyOrder(Order):
    ...


class SellOrder(Order):
    ...


class OrderList:
    def __init__(self):
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []

    def add_order(self, order: Order):
        if isinstance(order, BuyOrder):
            self.buy_orders.append(order)
        elif isinstance(order, SellOrder):
            self.sell_orders.append(order)

    def remove_order(self, order: Order):
        if isinstance(order, BuyOrder):
            self.buy_orders.remove(order)
        elif isinstance(order, SellOrder):
            self.sell_orders.remove(order)


###############################################################################
# Portfolio Section
###############################################################################


class Portfolio:
    def __init__(self, security: str, budget: float, quantity: float,
                 transaction_fee: int | float, orders: OrderList = None):
        self.security: str = security
        self.budget: float = budget
        self.quantity: int = quantity
        self.transaction_fee: int | float = transaction_fee
        self.orders: OrderList = orders if orders else OrderList()

    def apply_fee(self, budget: float) -> float:
        if isinstance(self.transaction_fee, int):
            return budget - self.transaction_fee
        elif isinstance(self.transaction_fee, float):
            return budget * (1 - self.transaction_fee)

    def unapply_fee(self, budget: float) -> float:
        if isinstance(self.transaction_fee, int):
            return budget + self.transaction_fee
        elif isinstance(self.transaction_fee, float):
            return budget / (1 - self.transaction_fee)

    def create_buy_limit_order(self, price: float, quantity: float,
                               callback: Callable[[Order], None]) -> Order | None:
        total = self.unapply_fee(price * quantity)

        if total > self.budget:
            print("Budget is not enough")
            return

        return BuyOrder(price, quantity, total, OrderType.LIMIT, callback)

    def create_sell_limit_order(self, price: float, quantity: float,
                                callback: Callable[[Order], None]) -> Order | None:
        total = self.apply_fee(price * quantity)

        if quantity > self.quantity:
            print("Quantity is not enough")
            return

        return SellOrder(price, quantity, total, OrderType.LIMIT, callback)

    def create_buy_stop_order(self, price: float, quantity: float,
                              callback: Callable[[Order], None]) -> Order | None:
        total = self.unapply_fee(price * quantity)

        if total > self.budget:
            print("Budget is not enough")
            return

        return BuyOrder(price, quantity, total, OrderType.STOP, callback)

    def create_sell_stop_order(self, price: float, quantity: float,
                               callback: Callable[[Order], None]) -> Order | None:
        total = self.apply_fee(price * quantity)

        if quantity > self.quantity:
            print("Quantity is not enough")
            return

        return SellOrder(price, quantity, total, OrderType.STOP, callback)

    def reset(self, price: float):
        raise NotImplementedError

    def step(self, price: float):
        raise NotImplementedError


class SimulationPortfolio(Portfolio):
    def __init__(self, security: str, budget: float, quantity: float,
                 transaction_fee: int | float, orders: OrderList = OrderList()):
        super().__init__(security, budget, quantity, transaction_fee, orders)
        self.orders_history: List[Order] = []

    def _execute_order(self, order: Order):
        if isinstance(order, BuyOrder):
            self.quantity += order.quantity
            self.budget -= order.total
            self.orders.remove_order(order)
            print(
                f"Bought {order.quantity:.2f} {self.security} at {order.price:.2f}")

        elif isinstance(order, SellOrder):
            self.quantity -= order.quantity
            self.budget += order.total
            self.orders.remove_order(order)
            print(
                f"Sold {order.quantity:.2f} {self.security} at {order.price:.2f}")

        order.callback(order)
        self.orders_history[-1].append(order)

    def reset(self, price: float):
        ...

    def step(self, price: float):
        self.orders_history.append([])

        for order in self.orders.buy_orders:
            if order.order_type == OrderType.MARKET:
                self._execute_order(order)
            elif order.order_type == OrderType.LIMIT:
                if order.price >= price:
                    self._execute_order(order)
            elif order.order_type == OrderType.STOP:
                if order.price <= price:
                    self._execute_order(order)

        for order in self.orders.sell_orders:
            if order.order_type == OrderType.MARKET:
                self._execute_order(order)
            elif order.order_type == OrderType.LIMIT:
                if order.price <= price:
                    self._execute_order(order)
            elif order.order_type == OrderType.STOP:
                if order.price >= price:
                    self._execute_order(order)


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
        self.current_level = self._construct_linked_list(levels)

    def _construct_linked_list(self, levels: List[float]) -> Level:
        n = len(levels) - 1

        current_level = Level(0, 0, levels[0])

        for i in range(n):
            budget = self.portfolio.budget / n

            price = levels[i]
            quantity = self.portfolio.apply_fee(budget) / price
            order = self.portfolio.create_buy_stop_order(
                price, quantity, self._buy_callback)
            self._place_order(order)

            current_level.next = Level(budget, levels[i], levels[i + 1])
            current_level.next.prev = current_level
            current_level = current_level.next

        current_level.next = Level(0, levels[n], inf)
        current_level.next.prev = current_level

        return current_level

    def _buy_callback(self, order: Order):
        level = self.current_level

        # TODO: refactor this
        while order.price != level.lower_bound:
            if order.price < level.lower_bound:
                level = level.prev
            elif order.price > level.lower_bound:
                level = level.next

        level.budget -= order.total

        order = self.portfolio.create_sell_limit_order(
            level.upper_bound, order.quantity, self._sell_callback)
        self._place_order(order)

    def _sell_callback(self, order: Order):
        level = self.current_level

        # TODO: refactor this
        while order.price != level.upper_bound:
            if order.price < level.upper_bound:
                level = level.prev
            elif order.price > level.upper_bound:
                level = level.next

        level.budget += order.total

        order = self.portfolio.create_buy_limit_order(
            level.lower_bound, self.portfolio.apply_fee(level.budget) / level.lower_bound, self._buy_callback)
        self._place_order(order)

    def _next_level(self):
        self.current_level = self.current_level.next

    def _prev_level(self):
        self.current_level = self.current_level.prev

    def _place_order(self, order: Order):
        if order is None:
            return
        self.portfolio.orders.add_order(order)

    def reset(self, price: float):
        if price > self.current_level.upper_bound:
            while price > self.current_level.next.upper_bound:
                self._next_level()

        elif price < self.current_level.lower_bound:
            while price < self.current_level.prev.lower_bound:
                self._prev_level()

        self.portfolio.reset(price)

    def _handle_rising_entering_level(self, price: float):
        # def callback(order: Order):
        #     n = 0
        #     level = self.current_level if self.current_level.next is not None else self.current_level.prev
        #     while level.prev is not None:
        #         if level.budget == 0:
        #             n += 1
        #         level = level.prev

        #     while level.next is not None:
        #         if level.prev is None:
        #             level = level.next
        #             continue

        #         if level.budget == 0:
        #             level.budget = order.total / n

        #         level = level.next

        # sell_orders = self.portfolio.orders.sell_orders
        # total_quantity = 0
        # for i in range(len(sell_orders) - 1):
        #     if sell_orders[i].price <= self.current_level.lower_bound:
        #         total_quantity += sell_orders[i].quantity
        #         self.portfolio.orders.remove_order(sell_orders[i])
        #     else:
        #         break

        # if total_quantity > 0:
        #     self._place_order(self.portfolio.create_sell_stop_order(
        #         self.current_level.lower_bound, total_quantity, callback))
        ...

    def _handle_falling_entering_level(self, price: float):
        ...

    def _handle_rising_leaving_level(self, price: float):
        # if self.current_level.budget != 0:
        #     order = self.portfolio.create_buy_stop_order(self.current_level.upper_bound,
        #                                                  self.portfolio.apply_fee(self.current_level.budget) /
        #                                                  self.current_level.upper_bound, self._buy_callback)
        #     self._place_order(order)
        ...

    def _handle_falling_leaving_level(self, price: float):
        ...

    def step(self, price: float):
        if price > self.current_level.upper_bound:
            self._handle_rising_leaving_level(price)

            while price > self.current_level.next.upper_bound:
                self._next_level()

            self._handle_rising_entering_level(price)

        elif price < self.current_level.lower_bound:
            self._handle_falling_leaving_level(price)

            while price < self.current_level.prev.lower_bound:
                self._prev_level()

            self._handle_falling_entering_level(price)

        self.portfolio.step(price)


def calc_actual_profit(budget: float, pct: float, num_sells_per_level: List[int]):
    n = len(num_sells_per_level)
    budget_per_level = budget / n
    profit = 0
    for i in range(n):
        profit += budget_per_level * pct ** num_sells_per_level[i]
    return profit


def main():
    portfolio = SimulationPortfolio('ETC-USD', 1000, 0, 0.0)

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
        # print networth of portfolio
        print("Networth:", portfolio.budget +
              portfolio.quantity * df.iloc[i]['close'])

    domain = range(len(df))

    plt.plot(domain, df['close'])

    buy_orders = []
    sell_orders = []

    for i, orders in enumerate(portfolio.orders_history):
        for order in orders:
            if isinstance(order, BuyOrder):
                buy_orders.append([i, order.price])
            elif isinstance(order, SellOrder):
                sell_orders.append([i, order.price])

    num_sells_per_level = defaultdict(int)
    for sell_order in buy_orders:
        num_sells_per_level[sell_order[1] * pct] += 1

    print(list(num_sells_per_level.values()))
    print(calc_actual_profit(portfolio.budget,
          pct, list(num_sells_per_level.values())))

    plt.scatter(*zip(*buy_orders), c='r', marker='v')
    plt.scatter(*zip(*sell_orders), c='g', marker='^')

    for level in levels:
        plt.axhline(level, color='k', alpha=0.1, linestyle='--')

    plt.show()


if __name__ == '__main__':
    main()
