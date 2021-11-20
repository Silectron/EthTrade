from decimal import Decimal, ROUND_DOWN
from cbpro import AuthenticatedClient
from typing import Callable, Generator, List, Union

from ethtrade.order import FilledOrder, Order, BuyOrder, SellOrder, LimitOrder, MarketOrder, StopOrder, LimitSellOrder, LimitBuyOrder, MarketBuyOrder, MarketSellOrder, StopBuyOrder, StopSellOrder
from ethtrade.portfolio import Portfolio


class CoinbasePortfolio(Portfolio):
    def __init__(self, security_pair: str, cbpro_client: AuthenticatedClient):
        super().__init__(security_pair)
        self.client = cbpro_client
        self.currency_account_id = self._get_account_by_currency(
            security_pair.split('-')[1])
        self.crypto_account_id = self._get_account_by_currency(
            security_pair.split('-')[0])
        self.rate = 0.005
        self.max_retries = 5
        self.checked_orders = set()

    def _get_account_by_currency(self, currency: str) -> str:
        """Get account id by currency.

        Args:
            currency (str): Currency name (e.g. 'USD', 'USDT', 'ETH').

        Raises:
            Exception: Incorrect currency name.
            Exception: Get accounts failed.
            Exception: Account not found.
            ConnectionError: raise exception

        Returns:
            str: Account id.
        """        ''''''
        try:
            json_res = self.client.get_accounts()

            if json_res is None:
                raise Exception(
                    "Get accounts failed:: likely incorrect account currency. Currency name for ETH is ETH")
            elif not isinstance(json_res, list) and json_res["message"] is not None:
                raise Exception("Get accounts failed::" + json_res["message"])

            for account in json_res:
                if 'currency' in account and account['currency'] == currency:
                    return account['id']
            raise ValueError("Account not found for " +
                             currency + ". Recheck currency name")
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def _validate_price_quantity(price: float, quantity: float) -> None:
        """Validate price and quantity helper function.

        Args:
            price (float): Price or limit price.
            quantity (float): Quantity of crypto order.

        Raises:
            ValueError: Price or quantity is invalid.
        """        ''''''
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and Quantity must be greater than 0")

    def _convert_budget_to_size(self, limit_price: float, budget: float) -> float:
        """Convert budget to size with fee deduction helper function.

        Args:
            limit_price (float): Limit price of crypto order.
            budget (float): Budget in account currency.

        Raises:
            ValueError: Limit price or budget is invalid.
            ValueError: Budget is not enough. Size must be greater than 0.00029 per order for ETH

        Returns:
            float: Size of crypto order with precision of 6 decimal places.
        """        ''''''
        if limit_price <= 0 or budget <= 0:
            raise ValueError("Limit price and budget must be greater than 0")
        size = float(Decimal(budget / limit_price * (1-self.rate)
                             ).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN))
        if (size < 0.00029):
            raise ValueError("Size must be greater than 0.00029 per order")
        return size

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        """Place a market buy order.

        Args:
            budget (float): Budget in account currency.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Budget is invalid. Needs to be greater than 1.
            Exception: Market buy order failed with message.
            Exception: Market buy order failed.
            ConnectionError: raise exception

        Returns:
            str: order id
        """        ''''''
        try:
            if budget < 1:
                # For ETH-USDT
                raise ValueError("Budget must be greater than 1")
            json_res = self.client.place_market_order(
                product_id=self.security, side="buy", funds=budget)

            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception(json_res['message'])
                else:
                    raise Exception("Market buy order failed")

            return json_res['id']
        except Exception as e:
            raise ConnectionError(str(e))

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        """Place a limit buy order with price/unit and budget for amount (size) of crypto.

        Args:
            limit_price (float): Limit price of crypto order.
            budget (float): Budget in account currency to be used.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Limit price or budget is invalid.
            Exception: Limit buy order failed with message.
            Exception: Limit buy order failed.
            ConnectionError: raise exception

        Returns:
            str: order id
        """        ''''''
        try:
            size = self._convert_budget_to_size(limit_price, budget)

            json_res = self.client.place_limit_order(
                product_id=self.security, side="buy",
                price=limit_price, size=size)

            if 'id' not in json_res:
                if json_res['message']:
                    raise Exception("Limit buy order failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Limit buy order failed")

            return json_res['id']
        except Exception as e:
            raise ConnectionError(str(e))

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, fill_handler: Callable[
                                 [FilledOrder], None]) -> str:
        """Place a stop buy order with price/unit and budget for amount (size) of crypto.

        Args:
            stop_price (float): Stop price of crypto order.
            limit_price (float): Limit price of crypto order.
            budget (float): Budget in account currency to be used.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Stop price or limit price or budget is invalid.
            Exception: Stop buy order failed with message.
            Exception: Stop buy order failed.
            ConnectionError: raise exception

        Returns:
            str: order id
        """        ''''''
        try:
            if stop_price <= 0:
                raise ValueError("Stop price must be greater than 0")
            size = self._convert_budget_to_size(limit_price, budget)

            json_res = self.client.place_stop_order(
                product_id=self.security, side='buy',
                price=stop_price, size=size)

            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception("Stop buy order failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Stop buy order failed")

            return json_res['id']

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def place_market_sell_order(self, quantity: float,
                                fill_handler: Callable[
                                    [FilledOrder], None]) -> str:
        """Place a market sell order.

        Args:
            quantity (float): Quantity of crypto order.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Quantity is invalid.
            Exception: Market sell order failed with message.
            Exception: Market sell order failed.
            ConnectionError: raise exception

        Returns:
            str: order id
        """        ''''''
        try:
            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0")

            json_res = self.client.place_market_order(
                product_id=self.security, side="sell", size=quantity)

            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception("Market sell order failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Market sell order failed")

            return json_res['id']

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        """Place a limit sell order with price/unit for amount (size) of crypto.

        Args:
            limit_price (float): Limit price of crypto order.
            quantity (float): Quantity of crypto order.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Limit price or quantity is invalid.
            Exception: Limit sell order failed with message.
            Exception: Limit sell order failed.
            ConnectionError: raise exception

        Returns:
            str: order id
        """        ''''''
        try:
            self._validate_price_quantity(limit_price, quantity)

            json_res = self.client.place_limit_order(
                product_id=self.security, side="sell",
                price=limit_price, size=quantity)

            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception("Limit sell order failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Limit sell order failed")

            return json_res['id']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        """Place a stop sell order with price/unit for amount (size) of crypto.

        Args:
            stop_price (float): Stop price of crypto order.
            limit_price (float): Limit price of crypto order.
            quantity (float): Quantity of crypto order.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Stop price, limit price or quantity is invalid.
            Exception: Place stop sell order failed with message.
            Exception: Place stop sell order failed.
            ConnectionError: raise exception

        Returns:
            str: order id
        """        ''''''
        try:
            if stop_price <= 0:
                raise ValueError("Stop price must be greater than 0")
            self._validate_price_quantity(limit_price, quantity)

            json_res = self.client.place_stop_order(
                roduct_id=self.security, stop_type="loss",
                price=limit_price, size=quantity, stop=stop_price)

            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception("Stop sell order failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Stop sell order failed")

            return json_res['id']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_budget(self) -> float:
        """Get available budget in account currency.

        Raises:
            Exception: Get budget failed with message.
            Exception: Get budget failed.
            Exception: Get available budget failed.
            ConnectionError: raise exception

        Returns:
            float: available budget in account currency
        """        ''''''
        try:
            json_res = self.client.get_account(self.currency_account_id)
            '''
                {
                    "id": "a1b2c3d4",
                    "balance": "1.100",
                    "holds": "0.100",
                    "available": "1.00",
                    "currency": "USD"
                }
            '''
            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception("Get available budget failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Get available budget failed")
            elif 'available' not in json_res:
                raise Exception(
                    "Get budget failed::field available not present")

            return json_res['available']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_quantity(self) -> float:
        """Get quantity of crypto holdings in account.

        Raises:
            Exception: Get crypto quantity failed with message.
            Exception: Get crypto quantity failed.
            Exception: Get crypto hold quantity failed.
            ConnectionError: raise exception

        Returns:
            float: quantity of crypto holdings in account
        """        ''''''
        try:
            json_res = self.client.get_account(self.crypto_account_id)

            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception("Get quantity failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Get quantity failed")
            elif 'hold' not in json_res:
                raise Exception("Get quantity failed::field hold not present")

            return json_res['hold']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_order_ids(self) -> List[str]:
        """Get list of order ids (open, pending or active) for security pair.

        Raises:
            Exception: Get order ids failed.
            Exception: Get order ids failed with message.
            ConnectionError: raise exception

        Returns:
            List[str]: list of order ids
        """        ''''''
        try:
            json_res = self.client.get_orders(product_id=self.security, status=[
                                              "open", "pending", "active"])  # TODO: remove pending?

            if json_res is None:
                raise Exception("Get orders failed::empty message")
            elif not isinstance(json_res, Generator) and not isinstance(json_res, list) and json_res['message'] is not None:
                raise Exception(
                    "Get orders failed::" + json_res["message"] if "message" in json_res else "unknown")

            list_of_orders = list(json_res)

            if len(list_of_orders) > 0 and list_of_orders[0] == 'message':
                return []

            return list_of_orders

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_order_by_id(self, order_id: str) -> Union[Order, None]:
        """Get order by order id.

        Args:
            order_id (str): order id

        Raises:
            Exception: Get order by id failed with message.
            Exception: Get order by id failed.
            Exception: Get order by id side failed.
            ConnectionError: raise exception

        Returns:
            Union[Order, None]: Order object
        """        ''''''
        try:
            json_res = self.client.get_order(order_id)

            if 'id' not in json_res:
                if 'message' in json_res:
                    raise Exception("Get order failed::" + json_res["message"])
                else:
                    raise Exception("Get order failed")
            elif 'side' not in json_res:
                raise Exception("Get order failed::field side not present")

            if json_res['side'] == 'buy':
                if json_res['type'] == 'limit':
                    price = float(json_res['price'])
                    budget = float(json_res['size']) * price / (1 - self.rate)
                    if 'stop' in json_res and json_res['stop'] == 'entry':
                        order = StopBuyOrder(order_id=order_id, fill_handler=None, budget=budget, stop_price=float(
                            json_res['stop_price']), limit_price=price)
                    else:
                        order = LimitBuyOrder(
                            order_id=order_id, fill_handler=None, budget=budget, limit_price=price)
                elif json_res['type'] == 'market':
                    price = round(
                        float(json_res['executed_value']) / float(json_res['filled_size']), 6)
                    order = MarketBuyOrder(order_id=json_res['id'], fill_handler=None, budget=float(
                        json_res['executed_value']) / (1 - self.rate))

                if json_res['status'] == 'done' and json_res['settled'] == True and json_res['done_reason'] == 'filled':
                    return FilledOrder(order=order, price=float(json_res['executed_value'])+float(json_res['fill_fees']), quantity=float(json_res['filled_size']))
            elif json_res['side'] == 'sell':
                if json_res['type'] == 'limit':
                    price = float(json_res['price'])
                    quantity = float(json_res['size'])
                    if 'stop' in json_res and json_res['stop'] == 'loss':
                        order = StopSellOrder(order_id=order_id, fill_handler=None, quantity=quantity, stop_price=float(
                            json_res['stop_price']), limit_price=price)
                    else:
                        order = LimitSellOrder(
                            order_id=order_id, fill_handler=None, quantity=quantity, limit_price=price)
                elif json_res['type'] == 'market':
                    order = MarketSellOrder(
                        order_id=json_res['id'], fill_handler=None, quantity=float(json_res['size']))

                if json_res['status'] == 'done' and json_res['settled'] == True and json_res['done_reason'] == 'filled':
                    return FilledOrder(order=order, price=float(json_res['executed_value'])-float(json_res['fill_fees']), quantity=float(json_res['filled_size']))
            else:
                raise Exception("Get order failed::invalid side")

            return order
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def cancel_order(self, order_id: str):
        """Cancel order by order id.

        Args:
            order_id (str): order id to cancel

        Raises:
            Exception: Cancel order failed.
            ConnectionError: raise exception
        """        ''''''
        try:
            for _ in range(self.max_retries):
                json_res = self.client.cancel_order(order_id)
                if json_res is None or not json_res:
                    continue
                else:
                    return
            raise Exception("Cancel order failed " +
                            str(self.max_retries) + " times")

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_accounts(self) -> List[str]:
        """Get list of account ids for api account.

        Raises:
            Exception: Get accounts failed no content.
            Exception: Get accounts failed with message.
            Exception: Get accounts failed.
            ConnectionError: raise exception

        Returns:
            List[str]: list of account ids
        """        ''''''
        try:
            json_res = self.client.get_accounts()

            if json_res is None:
                raise Exception("Get accounts failed")
            elif not isinstance(json_res, list):
                if 'message' in json_res:
                    raise Exception("Get accounts failed::" +
                                    json_res["message"])
                else:
                    raise Exception("Get accounts failed::empty message")

            return json_res
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_filled_orders(self) -> List[FilledOrder]:
        """Get list of unchecked filled orders.

        Raises:
            Exception: Get filled orders failed no content.
            Exception: Get filled orders failed with message.
            Exception: Get filled orders failed.
            Exception: Invalid side for order. Side must be buy or sell.
            ConnectionError: raise exception

        Returns:
            List[FilledOrder]: list of unchecked filled orders
        """        ''''''
        try:
            json_res = self.client.get_orders(
                product_id=self.security, status=["done"])

            if json_res is None:
                raise Exception("Get orders failed")
            elif not isinstance(json_res, Generator) and not isinstance(json_res, list):
                if json_res['message'] is not None:
                    raise Exception(
                        "Get orders failed::" + json_res["message"] if "message" in json_res else "unknown")
                else:
                    raise Exception("Get orders failed::empty message")

            list_filled_orders = []
            try:
                while(1):
                    next_order = next(json_res)
                    if not 'done_reason' in next_order and next_order['done_reason'] != 'filled':
                        continue
                    
                    if next_order['id'] in self.checked_orders:
                        continue
                    
                    self.checked_orders.append(next_order['id'])
                    
                    if next_order['side'] == 'buy':
                        if next_order['type'] == 'limit':
                            price = float(next_order['price'])
                            budget = float(
                                next_order['size']) * price / (1 - self.rate)
                            if 'stop' in next_order and next_order['stop'] == 'entry':
                                order = StopBuyOrder(order_id=next_order['id'], fill_handler=None, budget=budget, stop_price=float(
                                    next_order['stop_price']), limit_price=price)
                            else:
                                order = LimitBuyOrder(
                                    order_id=next_order['id'], fill_handler=None, budget=budget, limit_price=price)
                        elif next_order['type'] == 'market':
                            price = round(
                                float(next_order['executed_value']) / float(next_order['filled_size']), 6)
                            order = MarketBuyOrder(order_id=next_order['id'], fill_handler=None, budget=float(
                                next_order['executed_value']) / (1 - self.rate))

                        list_filled_orders.append(FilledOrder(order=order, price=float(
                            next_order['executed_value'])+float(next_order['fill_fees']), quantity=float(next_order['filled_size'])))
                    elif next_order['side'] == 'sell':
                        if next_order['type'] == 'limit':
                            price = float(next_order['price'])
                            quantity = float(next_order['size'])
                            if 'stop' in next_order and next_order['stop'] == 'loss':
                                order = StopSellOrder(order_id=next_order['id'], fill_handler=None, quantity=quantity, stop_price=float(
                                    next_order['stop_price']), limit_price=price)
                            else:
                                order = LimitSellOrder(
                                    order_id=next_order['id'], fill_handler=None, quantity=quantity, limit_price=price)
                        elif next_order['type'] == 'market':
                            order = MarketSellOrder(
                                order_id=next_order['id'], fill_handler=None, quantity=float(next_order['size']))

                        list_filled_orders.append(FilledOrder(order=order, price=float(
                            next_order['executed_value'])-float(next_order['fill_fees']), quantity=float(next_order['filled_size'])))
                    else:
                        raise Exception("Get order failed::invalid side")

            except StopIteration:
                pass

            return list_filled_orders

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_order_fills_by_order(self, order_id: str) -> List[str]:
        """Get fills for order by order id.

        Args:
            order_id (str): order id

        Raises:
            Exception: Get order fills failed no content.
            Exception: Get order fills failed with message.
            Exception: Get order fills failed.
            ConnectionError: raise exception

        Returns:
            List[str]: list of fills for a given order
        """        ''''''
        try:
            json_res = self.client.get_fills(order_id=order_id)

            if json_res is None:
                raise Exception("Get order fills failed")
            elif not isinstance(json_res, Generator) or not isinstance(json_res, list):
                if 'message' in json_res:
                    raise Exception(
                        "Get order fills failed::" + json_res["message"])
                else:
                    raise Exception("Get order fills failed::Empty message")

            list_filled_orders = list(json_res)
            if len(list_filled_orders) > 0 and list_filled_orders[0] == 'message':
                return []

            return list_filled_orders

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_order_fills(self) -> List[str]:
        """Get fills for all orders by security pair (product id).

        Raises:
            Exception: Get order fills failed no content.
            Exception: Get order fills failed with message.
            Exception: Get order fills failed.
            ConnectionError: raise exception

        Returns:
            List[str]: list of fills
        """        ''''''
        try:
            json_res = self.client.get_fills(product_id=self.security)

            if json_res is None:
                raise Exception("Get order fills failed")
            elif not isinstance(json_res, Generator) or not isinstance(json_res, list):
                if 'message' in json_res:
                    raise Exception(
                        "Get order fills failed::" + json_res["message"])
                else:
                    raise Exception("Get order fills failed::Empty message")

            list_filled_orders = list(json_res)
            if len(list_filled_orders) > 0 and list_filled_orders[0] == 'message':
                return []

            return list_filled_orders

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def step(self, price: float):
        for order_id in self.get_filled_orders():
            # Handle place stop orders?
            ...
