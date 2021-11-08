from cbpro import AuthenticatedClient
from typing import Callable

from ethtrade.order import FilledOrder
from ethtrade.portfolio import Portfolio


class CoinbasePortfolio(Portfolio):
    def __init__(self, security: str, cbpro_client: AuthenticatedClient):
        super().__init__(security)
        self.client = cbpro_client

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_market_order(
                product_id=self.security, side="buy", funds=budget)

            if json_res['id'] is None:
                raise Exception("Market buy order failed")

        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_limit_order(
                product_id=self.security, side="buy",
                price=limit_price, funds=budget)

            if json_res['id'] is None:
                raise Exception("Limit buy order failed")

        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, fill_handler: Callable[
                                 [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_stop_order(
                product_id=self.security, side="entry",
                price=limit_price, funds=budget,
                stop=stop_price)

            if json_res['id'] is None:
                raise Exception("Stop buy order failed")
            else:
                return json_res['id']

        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))

    def place_market_sell_order(self, quantity: float,
                                fill_handler: Callable[
                                    [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_market_order(
                product_id=self.security, side="sell", size=quantity)

            if json_res['id'] is None:
                raise Exception("Market sell order failed")
            else:
                return json_res['id']

        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_limit_order(
                product_id=self.security, side="sell",
                price=limit_price, size=quantity)

            if json_res['id'] is None:
                raise Exception("Limit sell order failed")
            else:
                return json_res['id']

        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_stop_order(
                roduct_id=self.security, side="loss",
                price=limit_price, size=quantity, stop=stop_price)

            if json_res['id'] is None:
                raise Exception("Stop sell order failed")
            else:
                return json_res['id']

        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))
