from __future__ import annotations
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

from ethtrade.portfolio import SimulationPortfolio
from ethtrade.order import BuyOrder, SellOrder
from ethtrade.strategy import GridStrategy


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
