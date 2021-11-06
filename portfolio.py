from typing import List, Tuple, Union, Callable, Protocol
from cbpro import AuthenticatedClient
from uuid import uuid4

from order import Order, FilledOrder, BuyOrder, SellOrder, MarketOrder, \
    LimitOrder, StopOrder, MarketBuyOrder, MarketSellOrder, LimitBuyOrder, \
    LimitSellOrder, StopBuyOrder, StopSellOrder


class Portfolio:
    def __init__(self, security: str):
        self.security = security

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[[FilledOrder], None]) -> str:
        """places a market buy order

        Args:
            budget (float): alloted budget for buying
            fill_handler (Callable[[FilledOrder], None]): function called when
                order is filled

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            str: id associated to order
        """
        raise NotImplementedError

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              fill_handler: Callable[[FilledOrder], None]) -> str:
        """places a limit buy order

        Args:
            limit_price (float): limit price for buying
            budget (float): alloted budget for buying
            fill_handler (Callable[[FilledOrder], None]): function called when
                order is filled

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            str: id associated to order
        """
        raise NotImplementedError

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, fill_handler: Callable[[FilledOrder],
                                                                   None]) -> str:
        """places a stop buy order (stop entry)

        Args:
            stop_price (float): stop price for triggering limit buy
            limit_price (float): limit price for buying
            budget (float): alloted budget for buying
            fill_handler (Callable[[FilledOrder], None]): function called when
                order is filled

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            str: id associated to order
        """
        raise NotImplementedError

    def place_market_sell_order(self, quantity: float,
                                fill_handler: Callable[[FilledOrder], None]) -> str:
        """places a market sell order

        Args:
            quantity (float): quantity to sell
            fill_handler (Callable[[FilledOrder], None]): function called when
                order is filled

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            str: id associated to order
        """
        raise NotImplementedError

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               fill_handler: Callable[[FilledOrder], None]) -> str:
        """places a limit sell order

        Args:
            limit_price (float): limit price for selling
            quantity (float): quantity to sell
            fill_handler (Callable[[FilledOrder], None]): function called when
                order is filled

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            str: id associated to order
        """
        raise NotImplementedError

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, fill_handler: Callable[[FilledOrder],
                                                                      None]) -> str:
        """places a stop sell order (stop loss)

        Args:
            stop_price (float): stop price for triggering limit sell
            limit_price (float): limit price for selling
            quantity (float): quantity to sell
            fill_handler (Callable[[FilledOrder], None]): function called when
                order is filled

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            str: id associated to order
        """
        raise NotImplementedError

    def get_budget(self) -> float:
        """get total budget for buying and selling

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            float: total budget for buying and selling
        """
        raise NotImplementedError

    def get_quantity(self) -> float:
        """get quantity of security held

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            float: quantity of security held
        """
        raise NotImplementedError

    def get_orders(self) -> List[Order]:
        """get placed orders for this portfolio

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            List[Order]: list of placed orders for this portfolio
        """
        raise NotImplementedError

    def cancel_order(order: Order):
        """cancel a placed order for this portfolio

        Args:
            order (Order): an existing order for this portfolio

        Raises:
            NotImplementedError: must be implemented by subclass
        """
        raise NotImplementedError

    def reset(self, price: float):
        raise NotImplementedError

    def step(self, price: float):
        raise NotImplementedError


class CoinbasePortfolio(Portfolio):
    def __init__(self, security: str, cbpro_client: AuthenticatedClient):
        super().__init__(security)
        self.client = cbpro_client

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[[FilledOrder], None]) -> str:
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

    def place_limit_buy_order(self, limit_price: float, budget: float, fill_handler: Callable[[FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_limit_order(
                product_id=self.security, side="buy", price=limit_price, funds=budget)
            if json_res['id'] is None:
                raise Exception("Limit buy order failed")
        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))

    def place_stop_buy_order(self, stop_price: float, limit_price: float, budget: float, fill_handler: Callable[[FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_stop_order(
                product_id=self.security, side="entry", price=limit_price, funds=budget,
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

    def place_market_sell_order(self, quantity: float, fill_handler: Callable[[FilledOrder], None]) -> str:
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

    def place_limit_sell_order(self, limit_price: float, quantity: float, fill_handler: Callable[[FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_limit_order(
                product_id=self.security, side="sell", price=limit_price, size=quantity)
            if json_res['id'] is None:
                raise Exception("Limit sell order failed")
            else:
                return json_res['id']
        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))

    def place_stop_sell_order(self, stop_price: float, limit_price: float, quantity: float, fill_handler: Callable[[FilledOrder], None]) -> str:
        try:
            json_res = self.client.place_stop_order(
                product_id=self.security, side="loss", price=limit_price, size=quantity,
                stop=stop_price)
            if json_res['id'] is None:
                raise Exception("Stop sell order failed")
            else:
                return json_res['id']
        except Exception as e:
            if isinstance(e, ValueError):
                print(str(e))
            else:
                raise ConnectionError(str(e))


class SimulationPortfolio(Portfolio):
    def __init__(self, security: str, budget: float, quantity: float,
                 transaction_fee: Union[int, float]):
        super().__init__(security)
        self.budget: float = budget
        self.quantity: float = quantity
        self.transaction_fee: Union[int, float] = transaction_fee

        self.order_book: List[Order] = []
        self.order_history: Tuple[float, List[Order]] = []

    def _apply_fee(self, budget: float) -> float:
        if isinstance(self.transaction_fee, int):
            return budget - self.transaction_fee
        elif isinstance(self.transaction_fee, float):
            return budget * (1 - self.transaction_fee)

    def _unapply_fee(self, budget: float) -> float:
        if isinstance(self.transaction_fee, int):
            return budget + self.transaction_fee
        elif isinstance(self.transaction_fee, float):
            return budget / (1 - self.transaction_fee)

    def _fill_order(self, price, order: Order) -> FilledOrder:
        if isinstance(order, BuyOrder):
            budget = self._apply_fee(order.budget)
            quantity = budget / price

            print(
                f"Bought {quantity:.4f} {self.security} at {price:.2f}")

            self.budget -= order.budget
            self.quantity += quantity

        elif isinstance(order, SellOrder):
            quantity = order.quantity
            budget = self._apply_fee(quantity * price)

            print(
                f"Sold {quantity:.4f} {self.security} at {price:.2f}")

            self.quantity -= quantity
            self.budget += budget

        filled_order = FilledOrder(order, price, quantity)
        order.fill_handler(filled_order)

        return filled_order

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[[FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = MarketBuyOrder(order_id, fill_handler, budget)
        self.order_book.append(order)

        return order_id

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              fill_handler: Callable[[FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = LimitBuyOrder(order_id, fill_handler, budget, limit_price)
        self.order_book.append(order)

        return order_id

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, fill_handler: Callable[[FilledOrder],
                                                                   None]) -> str:
        order_id = str(uuid4())
        order = StopBuyOrder(order_id, fill_handler,
                             budget, stop_price, limit_price)
        self.order_book.append(order)

        return order_id

    def place_market_sell_order(self, quantity: float,
                                fill_handler: Callable[[FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = MarketSellOrder(order_id, fill_handler, quantity)
        self.order_book.append(order)

        return order_id

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               fill_handler: Callable[[FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = LimitSellOrder(order_id, fill_handler, quantity, limit_price)
        self.order_book.append(order)

        return order_id

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, fill_handler: Callable[[FilledOrder],
                                                                      None]) -> str:
        order_id = str(uuid4())
        order = StopSellOrder(order_id, fill_handler,
                              quantity, stop_price, limit_price)
        self.order_book.append(order)

        return order_id

    def get_budget(self) -> float:
        return self.budget

    def get_quantity(self) -> float:
        return self.quantity

    def get_orders(self) -> List[Order]:
        return self.order_book

    def cancel_order(self, order: Order):
        self.order_book.remove(order)

    def reset(self, price: float):
        # self.order_book.clear()
        # self.order_history.clear()
        ...

    def step(self, price: float):
        orders_to_remove = []
        orders_to_record = []

        for order in self.order_book:
            if isinstance(order, MarketOrder):
                filled_order = self._fill_order(price, order)
                orders_to_remove.append(order)
                orders_to_record.append(filled_order)

            elif isinstance(order, LimitOrder):
                if (isinstance(order, BuyOrder) and price <= order.limit_price) or \
                        (isinstance(order, SellOrder) and price >= order.limit_price):
                    filled_order = self._fill_order(price, order)
                    orders_to_remove.append(order)
                    orders_to_record.append(filled_order)

            elif isinstance(order, StopOrder):
                if isinstance(order, BuyOrder):
                    if price >= order.stop_price:
                        new_order = LimitBuyOrder(
                            order.order_id,
                            order.fill_handler,
                            order.budget,
                            order.limit_price)
                        self.order_book.append(new_order)
                        orders_to_remove.append(order)

                elif isinstance(order, SellOrder):
                    if price <= order.stop_price:
                        new_order = LimitSellOrder(
                            order.order_id,
                            order.fill_handler,
                            order.quantity,
                            order.limit_price)
                        self.order_book.append(new_order)
                        orders_to_remove.append(order)

        for order in orders_to_remove:
            self.order_book.remove(order)

        self.order_history.append((price, orders_to_record))
