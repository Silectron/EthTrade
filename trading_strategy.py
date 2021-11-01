from typing import List
from enum import Enum
from abc import abstractmethod
from dataclasses import dataclass
import numpy as np
import pandas as pd


class OrderType(Enum):
    MARKET = 1
    LIMIT = 2
    STOP = 3


@dataclass
class Order:
    price: float
    quantity: int
    order_type: OrderType


@dataclass
class BuyOrder(Order):
    ...


@dataclass
class SellOrder(Order):
    ...


class Portfolio:
    def __init__(self, budget: float, transaction_fee: float):
        self.budget = budget
        self.quantity = 0
        self.transaction_fee = transaction_fee

    def buy(self, price: float, quantity: int):
        self.budget -= price * quantity * (1 + self.transaction_fee)
        self.quantity += quantity
        print(f"Bought {quantity} shares at {price}")

    def sell(self, price: float, quantity: int):
        self.budget += price * quantity * (1 - self.transaction_fee)
        self.quantity -= quantity
        print(f"Sold {quantity} shares at {price}")

    def networth(self, price: float):
        return self.budget + self.quantity * price


class TradingStrategy:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    @abstractmethod
    def update(self, price: float):
        raise NotImplementedError


class StaticGridStrategy(TradingStrategy):
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        super().__init__(portfolio)
        self.n = len(levels) - 1
        self.levels = levels
        self.orders = [BuyOrder(levels[i], self.portfolio.budget / self.levels[i]
                                / self.n, OrderType.STOP) for i in range(self.n)]
        self.index = 0
        self.unlocked = False

    def _place_stop_buy_order(self, price: float, quantity: int):
        self.orders[self.index] = BuyOrder(price, quantity, OrderType.STOP)

    def _place_stop_sell_order(self, price: float, quantity: int):
        self.orders[self.index] = SellOrder(price, quantity, OrderType.STOP)

    def _execute_buy(self, order: Order):
        self.portfolio.buy(order.price, order.quantity)
        self._place_stop_sell_order(
            self.levels[self.index + 1], order.quantity)

    def _execute_sell(self, order: Order):
        before_budget = self.portfolio.budget
        self.portfolio.sell(order.price, order.quantity)
        after_budget = self.portfolio.budget

        self._place_stop_buy_order(self.levels[self.index],
                                   (after_budget - before_budget) /
                                   self.levels[self.index])

    def update(self, price: float):
        if not self.unlocked and price > self.levels[self.index]:
            self.unlocked = True

        if self.unlocked and price < self.levels[self.index]:
            # leaving grid level top-down
            order = self.orders[self.index]
            if price >= order.price and isinstance(order, BuyOrder):
                self._execute_buy()

            if self.index > 0:
                self.index -= 1
                # entering grid level top-down

        elif price > self.levels[self.index + 1]:
            # leaving grid level bottom-up
            order = self.orders[self.index]
            if price >= order.price and isinstance(order, SellOrder):
                self._execute_sell(self, order)

            if self.index < self.n - 1:
                self.index += 1
                # entering grid level bottom-up
                order = self.orders[self.index]
                if price >= order.price and isinstance(order, BuyOrder):
                    self._execute_buy()


def main():
    pct = 1.05
    levels = np.cumprod(np.ones(5) * pct) * 3000 / pct
    portfolio = Portfolio(10000, 0.005)
    strategy = StaticGridStrategy(portfolio, levels)

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

    df = df[df.index > '2021-06-01']

    for i in range(len(df) - 1):
        strategy.update(df.iloc[i]['close'])
    print(
        f'{df.iloc[i]["close"]}: {portfolio.networth(df.iloc[i]["close"])}, {strategy.index}')


if __name__ == "__main__":
    main()
