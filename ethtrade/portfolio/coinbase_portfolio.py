from decimal import Decimal, ROUND_DOWN
from cbpro import AuthenticatedClient
from typing import Callable, Generator, List, Union

from ethtrade.order import FilledOrder, Order, BuyOrder, SellOrder
from ethtrade.portfolio import Portfolio


class CoinbasePortfolio(Portfolio):
    def __init__(self, security_pair: str, cbpro_client: AuthenticatedClient):
        super().__init__(security_pair)
        self.client = cbpro_client
        self.currency_account_id = self._get_account_by_currency(security_pair.split('-')[1])
        self.crypto_account_id = self._get_account_by_currency(security_pair.split('-')[0])
        self.max_retries = 5
        
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
        """Convert budget to size helper function.

        Args:
            limit_price (float): Limit price of crypto order.
            budget (float): Budget in account currency.

        Raises:
            ValueError: Limit price or budget is invalid.

        Returns:
            float: Size of crypto order with precision of 6 decimal places.
        """        ''''''
        if limit_price <= 0 or budget <= 0:
            raise ValueError("Limit price and budget must be greater than 0")
        
        return float(Decimal(budget / limit_price).quantize(Decimal('0.000001'), rounding=ROUND_DOWN))

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        """Place a market buy order.

        Args:
            budget (float): Budget in account currency.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Budget is invalid.
            Exception: Market buy order failed.
            ConnectionError: raise exception

        Returns:
            str: order id
        """        ''''''
        try:
            if budget <= 0:
                raise ValueError("Budget must be greater than 0")
            json_res = self.client.place_market_order(
                product_id=self.security, side="buy", funds=budget)

            if 'id' not in json_res:
                raise Exception("Market buy order failed")

            return json_res['id']
        except Exception as e:
            raise ConnectionError(str(e))
            

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        """Place a limit buy order with price/unit for amount (size) of crypto.

        Args:
            limit_price (float): Limit price of crypto order.
            budget (float): Budget in account currency to be used.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Limit price or budget is invalid.
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

            if not isinstance(json_res, list) and 'id' not in json_res and json_res['message']:
                raise Exception("Limit buy order failed::" +
                                json_res["message"])
                
            return json_res['id']
        except Exception as e:
            raise ConnectionError(str(e))

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, fill_handler: Callable[
                                 [FilledOrder], None]) -> str:
        """Place a stop buy order with price/unit for amount (size) of crypto.

        Args:
            stop_price (float): Stop price of crypto order.
            limit_price (float): Limit price of crypto order.
            budget (float): Budget in account currency to be used.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Stop price or limit price or budget is invalid.
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

            if not isinstance(json_res, list) and 'id' not in json_res:
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
        """Place a market sell order.

        Args:
            quantity (float): Quantity of crypto order.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Quantity is invalid.
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
        """Place a limit sell order with price/unit for amount (size) of crypto.

        Args:
            limit_price (float): Limit price of crypto order.
            quantity (float): Quantity of crypto order.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Limit price or quantity is invalid.
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
        """Place a stop sell order with price/unit for amount (size) of crypto.

        Args:
            stop_price (float): Stop price of crypto order.
            limit_price (float): Limit price of crypto order.
            quantity (float): Quantity of crypto order.
            fill_handler (Callable[ [FilledOrder], None]): [description]

        Raises:
            ValueError: Stop price, limit price or quantity is invalid.
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
                raise Exception("Stop sell order failed::" +
                                json_res["message"])
            else:
                return json_res['id']

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_budget(self) -> float:
        """Get available budget in account currency.

        Raises:
            Exception: Get budget failed.
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
                raise Exception("Get budget failed::" + json_res["message"])

            return json_res['available']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_quantity(self) -> float:
        """Get quantity of crypto holdings in account.

        Raises:
            Exception: Get crypto quantity failed.
            ConnectionError: raise exception

        Returns:
            float: quantity of crypto holdings in account
        """        ''''''
        try:
            json_res = self.client.get_account(self.crypto_account_id)

            if 'id' not in json_res:
                raise Exception("Get quantity failed::" + json_res["message"])

            return json_res['hold']
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))

    def get_order_ids(self) -> List[str]:
        """Get list of order ids for security pair.

        Raises:
            Exception: Get order ids failed.
            Exception: Get order ids failed with message.
            ConnectionError: raise exception

        Returns:
            List[str]: list of order ids
        """        ''''''
        try:
            json_res = self.client.get_orders(product_id=self.security, status=["open", "pending", "active", "done"])

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
            Exception: Get order by id failed.
            ConnectionError: raise exception

        Returns:
            Union[Order, None]: Order object
        """        ''''''
        try:
            json_res = self.client.get_order(order_id)

            if 'id' not in json_res:
                raise Exception("Get order failed::" + json_res["message"])
            
            if json_res['side'] == 'buy':
                if json_res['type'] == 'limit':
                    price = float(json_res['price'])
                elif json_res['type'] == 'market':
                    price = round(float(json_res['executed_value']) / float(json_res['filled_size']), 6)
                order = BuyOrder(order_id=json_res['id'], budget=price, fill_handler=None)
            elif json_res['side'] == 'sell':
                order = SellOrder(order_id=json_res['id'], quantity=float(json_res['size']), fill_handler=None)
            else :
                raise Exception("Get order failed::invalid side")
            
            if json_res['status'] == 'done' and json_res['settled'] == True and json_res['done_reason'] == 'filled':
                print(FilledOrder(order=order, quantity=float(json_res['filled_size']), price=float(json_res['executed_value'])+float(json_res['fill_fees'])))
                
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
            Exception: Get accounts failed.
            ConnectionError: raise exception

        Returns:
            List[str]: list of account ids
        """        ''''''
        try:
            json_res = self.client.get_accounts()

            if json_res is None:
                raise Exception("Get accounts failed::" + json_res["message"])

            return json_res
        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))
        
    def get_filled_orders(self) -> List[FilledOrder]:
        """Get list of filled orders.

        Raises:
            Exception: Get filled orders failed.
            Exception: Get filled orders failed with message.
            Exception: Invalid side for order. Side must be buy or sell.
            ConnectionError: raise exception

        Returns:
            List[FilledOrder]: list of filled orders
        """        ''''''
        try:
            json_res = self.client.get_orders(product_id=self.security, status=["done"])

            if json_res is None:
                raise Exception("Get orders failed::empty message")
            elif not isinstance(json_res, Generator) and not isinstance(json_res, list) and json_res['message'] is not None:
                raise Exception(
                    "Get orders failed::" + json_res["message"] if "message" in json_res else "unknown")
                
            list_filled_orders = []
            try:
                while(1):
                    next_order = next(json_res)
                    
                    if next_order['side'] == 'buy':
                        if next_order['type'] == 'limit':
                            price = float(next_order['price'])
                        elif next_order['type'] == 'market':
                            price = round(float(next_order['executed_value']) / float(next_order['filled_size']), 6)
                        order = BuyOrder(order_id=next_order['id'], budget=price, fill_handler=None)
                    elif next_order['side'] == 'sell':
                        order = SellOrder(order_id=next_order['id'], quantity=float(next_order['size']), fill_handler=None)
                    else :
                        raise Exception("Get order failed::invalid side")
                    
                    list_filled_orders.append(FilledOrder(order=order, quantity=float(next_order['filled_size']), price=float(next_order['executed_value'])+float(next_order['fill_fees'])))
                    
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
            Exception: Get order fills failed.
            Exception: Get order fills failed with message.
            ConnectionError: raise exception

        Returns:
            List[str]: list of fills for a given order
        """        ''''''
        try:
            json_res = self.client.get_fills(order_id=order_id)

            if json_res is None:
                raise Exception("Get order fills failed::No content response")
            elif not isinstance(json_res, Generator) and 'message' in json_res:
               raise Exception("Get order fills failed::" + json_res["message"])

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
            Exception: Get order fills failed.
            Exception: Get order fills failed with message.
            ConnectionError: raise exception

        Returns:
            List[str]: list of fills
        """        ''''''
        try:
            json_res = self.client.get_fills(product_id=self.security)

            if json_res is None:
                raise Exception("Get order fills failed::No content response")
            elif not isinstance(json_res, Generator) and 'message' in json_res:
               raise Exception("Get order fills failed::" + json_res["message"])

            list_filled_orders = list(json_res)
            if len(list_filled_orders) > 0 and list_filled_orders[0] == 'message':
                return []

            return list_filled_orders

        except ValueError as e:
            print(str(e))
        except Exception as e:
            raise ConnectionError(str(e))
        
