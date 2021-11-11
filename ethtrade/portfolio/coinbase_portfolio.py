from cbpro import AuthenticatedClient
from typing import Callable, Generator, List, Union

from ethtrade.order import FilledOrder, Order
from ethtrade.portfolio import Portfolio


class CoinbasePortfolio(Portfolio):
    def __init__(self, security: str, account_currency: str,
                 cbpro_client: AuthenticatedClient):
        super().__init__(security)
        self.client = cbpro_client
        self.account_id = self.get_account_by_currency(account_currency)
        self.max_retries = 5

    def set_account_id(self, account_id: str):
        self.account_id = account_id

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_market_order(
                product_id=self.security, side="buy", funds=budget)

            if json_res['id'] is None:
                raise Exception("Market buy order failed")

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_limit_order(
                product_id=self.security, side="buy",
                price=limit_price, funds=budget)

            if json_res['id'] is None:
                raise Exception("Limit buy order failed::" +
                                json_res["message"])

        except ValueError as e:
            print(str(e))
        except Exception as e:
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
                raise Exception("Stop buy order failed::" +
                                json_res["message"])
            else:
                return json_res['id']

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def place_market_sell_order(self, quantity: float,
                                fill_handler: Callable[
                                    [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_market_order(
                product_id=self.security, side="sell", size=quantity)

            if json_res['id'] is None:
                raise Exception("Market sell order failed::" +
                                json_res["message"])
            else:
                return json_res['id']

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_limit_order(
                product_id=self.security, side="sell",
                price=limit_price, size=quantity)

            if json_res['id'] is None:
                raise Exception("Limit sell order failed::" +
                                json_res["message"])
            else:
                return json_res['id']

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_stop_order(
                roduct_id=self.security, stop_type="loss",
                price=limit_price, size=quantity, stop=stop_price)

            if json_res['id'] is None:
                raise Exception("Stop sell order failed::" +
                                json_res["message"])
            else:
                return json_res['id']

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_budget(self) -> float:
        try:
            json_res = self.client.get_account(self.account_id)
            '''
                {
                    "id": "a1b2c3d4",
                    "balance": "1.100",
                    "holds": "0.100",
                    "available": "1.00",
                    "currency": "USD"
                }
            '''
            if json_res['id'] is None:
                raise Exception("Get budget failed::" + json_res["message"])

            return json_res['available']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_quantity(self) -> float:
        try:
            json_res = self.client.get_account(self.account_id)

            if json_res['id'] is None:
                raise Exception("Get quantity failed::" + json_res["message"])

            return json_res['hold']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_order_ids(self) -> List[str]:
        try:
            json_res = self.client.get_orders(product_id=self.security)

            if json_res is None:
                raise Exception("Get orders failed::empty message")
            elif not isinstance(json_res, Generator):
                raise Exception(
                    "Get orders failed::" + json_res["message"] if "message" in json_res else "unknown")

            list_of_orders = []
            try:
                order = next(json_res)
                while(order is not None):
                    list_of_orders.append(str(order))
                    order = next(json_res)
            except StopIteration:
                if len(list_of_orders) > 0 and list_of_orders[0] == "message":
                    raise Exception(
                        "Get orders failed::likely provided incorrect security name. Security name for ETH is ETH-USD")

                return list_of_orders

            return list_of_orders
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_order_by_id(self, order_id: str) -> Union[Order, None]:
        try:
            json_res = self.client.get_order(order_id)

            if json_res['id'] is None:
                raise Exception("Get order failed::" + json_res["message"])

            return Order(json_res)
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def cancel_order(self, order_id: str):
        try:
            for _ in range(self.max_retries):
                json_res = self.client.cancel_order(order_id)
                if json_res is None or not json_res:
                    continue
                else:
                    return True
            raise Exception("Cancel order failed " +
                            str(self.max_retries) + " times")
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_accounts(self) -> List[str]:
        try:
            json_res = self.client.get_accounts()

            if json_res is None:
                raise Exception("Get accounts failed::" + json_res["message"])

            return json_res
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_account_by_currency(self, currency: str) -> str:
        try:
            json_res = self.client.get_accounts()

            if json_res is None:
                raise Exception(
                    "Get accounts failed::" + json_res["message"] + ". likely incorrect account currency. Currency name for ETH is ETH")

            for account in json_res:
                if account['currency'] == currency:
                    return account['id']
            raise Exception("Account not found for " +
                            currency + ". Recheck currency name")
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))
