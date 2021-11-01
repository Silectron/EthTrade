from typing import List
from enum import Enum
from abc import abstractmethod
from dataclasses import dataclass
import numpy as np
import pandas as pd
# import os


# log_file = "trading_strategy3.log"


# # open and write to file
# def write_to_file(data, filename=log_file):
#     with open(filename, 'a') as f:
#         f.write(data)


class OrderType(Enum):
    BUY = 1
    SELL = 2


@dataclass
class Order:
    price: float
    quantity: int
    order_type: OrderType


class Portfolio:
    def __init__(self, budget: float, transaction_fee: float):
        self.budget = budget
        self.quantity = 0
        self.transaction_fee = transaction_fee

    def buy(self, price: float, quantity: int):
        self.budget -= price * quantity * (1 + self.transaction_fee)
        self.quantity += quantity
        print(f"Bought {quantity} shares at {price}")
        # write_to_file(f"Bought {quantity} shares at {price}\n")

    def sell(self, price: float, quantity: int):
        self.budget += price * quantity * (1 - self.transaction_fee)
        self.quantity -= quantity
        print(f"Sold {quantity} shares at {price}")
        # write_to_file(f"Sold {quantity} shares at {price}\n")

    def networth(self, price: float):
        return self.budget + self.quantity * price


class TradingStrategy:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    @abstractmethod
    def update(self, price: float):
        raise NotImplementedError


class StaticGridStrategyV2(TradingStrategy):
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        super().__init__(portfolio)
        self.n = len(levels) - 1
        self.levels = levels
        budget = self.portfolio.budget
        self.budgets = [budget / self.n] * self.n
        self.orders = [Order(levels[i], self.budgets[i] / self.levels[i],
                             OrderType.BUY) for i in range(self.n)]
        self.index = 0
        self.unlocked = False

    def _place_stop_buy_order(self, price: float, quantity: int):
        self.orders[self.index] = Order(price, quantity, OrderType.BUY)

    def _place_stop_sell_order(self, price: float, quantity: int):
        self.orders[self.index] = Order(price, quantity, OrderType.SELL)

    def update(self, price: float):
        if not self.unlocked and price > self.levels[self.index]:
            self.unlocked = True

        if price < self.levels[self.index] and self.unlocked:
            # leaving grid level top-down
            order = self.orders[self.index]
            if order.order_type == OrderType.BUY:
                self.portfolio.buy(order.price, order.quantity)
                self.orders[self.index] = Order(self.levels[self.index + 1],
                                                order.quantity, OrderType.SELL)

            if self.index > 0:
                self.index -= 1
                # entered grid level top-down

        elif price > self.levels[self.index + 1]:
            # leaving grid level bottom-up
            if self.index < self.n - 1:
                order = self.orders[self.index]
                if order.order_type == OrderType.SELL:
                    before_budget = self.portfolio.budget
                    self.portfolio.sell(order.price, order.quantity)
                    after_budget = self.portfolio.budget
                    self.budgets[self.index] = after_budget - before_budget
                    self.orders[self.index] = Order(self.levels[self.index],
                                                    self.budgets[self.index] /
                                                    self.levels[self.index],
                                                    OrderType.BUY)
                self.index += 1

                order = self.orders[self.index]
                if order.order_type == OrderType.BUY:
                    self.portfolio.buy(order.price, order.quantity)
                    self.orders[self.index] = Order(self.levels[self.index + 1],
                                                    order.quantity, OrderType.SELL)
                # entered grid level bottom-up


class StaticGridStrategy(TradingStrategy):
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        super().__init__(portfolio)
        self.n = len(levels) - 1
        self.levels = levels
        budget = portfolio.budget
        self.budgets = [budget / self.n] * self.n
        self.orders = [None] * self.n
        self.index = 0

    def _execute_buy(self):
        order = self.orders[self.index]
        self.portfolio.buy(order.price, order.quantity)
        self.budgets[self.index] = 0
        self._place_sell_limit(self.levels[self.index + 1], order.quantity)

    def _execute_sell(self):
        order = self.orders[self.index]
        before_budget = self.portfolio.budget
        self.portfolio.sell(order.price, order.quantity)
        after_budget = self.portfolio.budget
        self.budgets[self.index] = after_budget - before_budget
        self.orders[self.index] = None

    def _place_buy_limit(self, price: float, quantity: float):
        self.orders[self.index] = Order(price, quantity, OrderType.BUY)

    def _place_sell_limit(self, price: float, quantity: int):
        self.orders[self.index] = Order(price, quantity, OrderType.SELL)

    def update(self, price: float):
        if price < self.levels[self.index]:
            # leaving grid level top-down
            order = self.orders[self.index]
            if order and order.order_type == OrderType.BUY:
                self._execute_buy()

            if self.index > 0:
                self.index -= 1
                # entered grid level top-down
                order = self.orders[self.index]
                if not order:
                    # place buy limit if no order is present
                    level = self.levels[self.index]
                    budget = self.budgets[self.index]
                    self._place_buy_limit(level, budget / level)

        elif price > self.levels[self.index + 1]:
            # leaving grid level bottom-up
            order = self.orders[self.index]
            if order and order.order_type == OrderType.BUY:
                self.orders[self.index] = None

            if self.index < self.n - 1:
                self.index += 1
                # entered grid level bottom-up
                order = self.orders[self.index]
                if order and order.order_type == OrderType.SELL:
                    # execute sell order if sell limit was placd
                    self._execute_sell()
                elif not order:
                    # OPTIONAL: place a buy limit if no order is present
                    level = self.levels[self.index]
                    budget = self.budgets[self.index]
                    self._place_buy_limit(level, budget / level)


def main():
    pct = 1.05
    levels = np.cumprod(np.ones(5) * pct) * 3000 / pct
    portfolio = Portfolio(10000, 0.005)
    strategy = StaticGridStrategyV2(portfolio, levels)

    # df = pd.read_csv('HistoricalData_1635060599752.csv')
    # df['Date'] = pd.to_datetime(df['Date'])
    # df = df.set_index('Date').sort_index()

    # for i in range(len(df) - 1):
    #     strategy.update(df.iloc[i]['Close/Last'])
    #     print(
    #         f'{df.iloc[i]["Close/Last"]}: {portfolio.networth(df.iloc[i]["Close/Last"])}')

    df = pd.read_csv('Bitstamp_ETHUSD_1h.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()

    # df = df[df.index > '2021-06-01']

    # if os.path.exists(log_file):
    #     os.remove(log_file)

    for i in range(len(df) - 1):
        strategy.update(df.iloc[i]['close'])
        print(
            f'{df.iloc[i]["close"]}: {portfolio.networth(df.iloc[i]["close"])}, {strategy.index}')
        # write_to_file(f'{df.iloc[i]["close"]}: {portfolio.networth(df.iloc[i]["close"])}, {strategy.index}\n')


if __name__ == "__main__":
    main()
