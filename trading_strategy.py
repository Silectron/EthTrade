from typing import Protocol, List
from enum import Enum
from abc import abstractmethod
from dataclasses import dataclass
import numpy as np
import pandas as pd


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
    def __init__(self, portfolio: Portfolio, grid: List[float]):
        super().__init__(portfolio)
        self.n = len(grid) - 1
        self.grid = grid
        self.orders = [None] * self.n
        self.index = 0

    def update(self, price: float):
        if price < self.grid[self.index]:
            # leaving grid level top-down

            if self.index > 0:
                self.index -= 1
                # entered grid level top-down

        elif price > self.grid[self.index]:
            # leaving grid level bottom-up

            if self.index < self.n - 1:
                self.index += 1
                # entered grid level bottom-up


def main():
    grid = np.cumprod(np.ones(10) * 1.03) * 3000 / 1.03
    portfolio = Portfolio(1000, 0.005)
    strategy = StaticGridStrategy(portfolio, grid)

    df = pd.read_csv('HistoricalData_1635060599752.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()

    for i in range(len(df) - 1):
        strategy.update(df.iloc[i]['Close/Last'])
        print(
            f'{df.iloc[i]["Close/Last"]}: {portfolio.networth(df.iloc[i]["Close/Last"])}')


if __name__ == "__main__":
    main()
