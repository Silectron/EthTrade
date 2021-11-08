import unittest
from unittest import TestCase

from ethtrade.portfolio import SimulationPortfolio


class TestSimulationPortfolio(TestCase):
    prices = [3026.98, 3008.71, 2966.4, 2983.0, 3005.27, 2996.12, 2995.0,
              3002.88, 3003.79, 2982.02, 2973.44, 2996.49, 3022.45, 3044.56,
              3068.03, 3048.29, 3050.34, 3133.43, 3149.0, 3157.43, 3165.31,
              3170.97, 3185.18, 3228.86, 3238.03, 3230.33, 3216.68, 3226.21,
              3226.92, 3227.21, 3216.59, 3199.98, 3207.5, 3217.95, 3206.0,
              3236.78, 3262.07, 3282.81, 3284.59, 3266.8, 3250.73, 3236.12,
              3254.77, 3259.87, 3292.83, 3259.99, 3285.64, 3250.91, 3267.03,
              3266.02, 3279.58, 3272.26, 3291.58, 3278.07, 3295.57, 3289.21,
              3284.24, 3299.17, 3254.96, 3293.17, 3285.09, 3263.58, 3276.43,
              3290.44, 3279.48, 3264.51, 3215.8, 3230.55, 3252.68, 3253.82,
              3226.15, 3247.02, 3252.82, 3229.83, 3228.07, 3245.76, 3229.6,
              3259.04, 3265.77, 3251.89, 3267.15, 3253.49, 3258.03, 3238.15,
              3234.82, 3166.78, 3182.0, 3179.54, 3179.27, 3156.19, 3177.23,
              3156.31, 3170.0, 3216.16, 3241.55, 3250.41, 3263.91, 3300.26,
              3343.41, 3348.62, 3329.33, 3330.63, 3326.13, 3334.83, 3353.0,
              3333.21, 3345.0, 3343.64, 3345.53, 3313.68, 3325.63, 3352.6,
              3333.55, 3327.92, 3310.82, 3341.59, 3339.71, 3336.24, 3317.25,
              3312.51, 3295.0, 3305.96, 3323.66, 3338.23, 3335.87, 3350.85,
              3350.96, 3336.72, 3326.65, 3310.33, 3323.87, 3318.56, 3250.12,
              3237.5, 3210.54, 3167.7, 3178.8, 3188.91, 3217.12, 3218.73,
              3195.44, 3214.02, 3175.68]

    def test_place_market_buy_order(self):
        portfolio = SimulationPortfolio('ETH-USDC', 1000, 0, 0.005)
        portfolio.reset(self.prices[0])

        for price in self.prices:
            if price == 3284.59:
                portfolio.place_market_buy_order(
                    portfolio.get_budget(), lambda x: None)
            portfolio.step(price)

        self.assertEqual(portfolio.get_budget(), 0)
        self.assertEqual(portfolio.get_quantity(), 1000 * 0.995 / 3284.59)

    def test_place_limit_buy_order(self):
        portfolio = SimulationPortfolio('ETH-USDC', 1000, 0, 0.005)
        portfolio.reset(self.prices[0])

        portfolio.place_limit_buy_order(
            3000, portfolio.get_budget(), lambda x: None)

        for price in self.prices:
            portfolio.step(price)

        self.assertEqual(portfolio.get_budget(), 0)
        self.assertEqual(portfolio.get_quantity(), 1000 * 0.995 / 2966.4)

    def test_place_stop_buy_order(self):
        portfolio = SimulationPortfolio('ETH-USDC', 1000, 0, 0.005)
        portfolio.reset(self.prices[0])

        portfolio.place_stop_buy_order(
            3250, 3200, portfolio.get_budget(), lambda x: None)

        for price in self.prices:
            portfolio.step(price)

        self.assertEqual(portfolio.get_budget(), 0)
        self.assertEqual(portfolio.get_quantity(), 1000 * 0.995 / 3166.78)
