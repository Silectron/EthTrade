from typing import List, Tuple, Union, Callable

from orders import Order, BuyOrder, SellOrder, MarketOrder, LimitOrder, \
    StopOrder, MarketBuyOrder, MarketSellOrder, LimitBuyOrder, \
    LimitSellOrder, StopBuyOrder, StopSellOrder


class Portfolio:
    def __init__(self, security: str):
        self.security: str = security

    def place_market_buy_order(self, budget: float,
                               exec_handler: Callable[[Order], None]):
        """places a market buy order

        Args:
            budget (float): alloted budget for buying
            exec_handler (Callable[[Order], None]): function called when
                order is executed

        Raises:
            NotImplementedError: must be implemented by subclass
        """
        raise NotImplementedError

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              exec_handler: Callable[[Order], None]):
        """places a limit buy order

        Args:
            limit_price (float): limit price for buying
            budget (float): alloted budget for buying
            exec_handler (Callable[[Order], None]): function called when
                order is executed

        Raises:
            NotImplementedError: must be implemented by subclass
        """
        raise NotImplementedError

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, exec_handler: Callable[[Order],
                                                                   None]):
        """places a stop buy order (stop entry)

        Args:
            stop_price (float): stop price for triggering limit buy
            limit_price (float): limit price for buying
            budget (float): alloted budget for buying
            exec_handler (Callable[[Order], None]): function called when
                order is executed

        Raises:
            NotImplementedError: must be implemented by subclass
        """
        raise NotImplementedError

    def place_market_sell_order(self, quantity: float,
                                exec_handler: Callable[[Order], None]):
        """places a market sell order

        Args:
            quantity (float): quantity to sell
            exec_handler (Callable[[Order], None]): function called when
                order is executed

        Raises:
            NotImplementedError: must be implemented by subclass
        """
        raise NotImplementedError

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               exec_handler: Callable[[Order], None]):
        """places a limit sell order

        Args:
            limit_price (float): limit price for selling
            quantity (float): quantity to sell
            exec_handler (Callable[[Order], None]): function called when
                order is executed

        Raises:
            NotImplementedError: must be implemented by subclass
        """
        raise NotImplementedError

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, exec_handler: Callable[[Order],
                                                                      None]):
        """places a stop sell order (stop loss)

        Args:
            stop_price (float): stop price for triggering limit sell
            limit_price (float): limit price for selling
            quantity (float): quantity to sell
            exec_handler (Callable[[Order], None]): function called when
                order is executed

        Raises:
            NotImplementedError: must be implemented by subclass
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

    def reset(self, price: float):
        raise NotImplementedError

    def step(self, price: float):
        raise NotImplementedError


class CoinbasePortfolio(Portfolio):
    def __init__(self, security: str):
        super().__init__(security)
        self.client = ...


class SimulationPortfolio(Portfolio):
    def __init__(self, security: str, budget: float, quantity: float,
                 transaction_fee: Union[int, float]):
        super().__init__(security)
        self.budget: float = budget
        self.quantity: float = quantity
        self.transaction_fee: Union[int, float] = transaction_fee

        self.order_queue: List[Order] = []
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

    def _execute_order(self, price: float, order: Order):
        if isinstance(order, BuyOrder):
            if isinstance(order, MarketOrder):
                budget = self._apply_fee(order.budget)
                quantity = budget / price

                print(f"Bought {quantity:.2f} {self.security} at {price:.2f}")

                self.budget -= order.budget
                self.quantity += quantity
            elif isinstance(order, LimitOrder):
                budget = self._apply_fee(order.budget)
                quantity = budget / order.limit_price

                print(
                    f"Bought {quantity:.2f} {self.security} at \
                        {order.limit_price:.2f}")

                self.budget -= order.budget
                self.quantity += quantity

        elif isinstance(order, SellOrder):
            if isinstance(order, MarketOrder):
                quantity = order.quantity
                budget = self._apply_fee(quantity * price)

                print(f"Sold {quantity:.2f} {self.security} at {price:.2f}")

                self.quantity -= quantity
                self.budget += budget
            elif isinstance(order, LimitOrder):
                quantity = order.quantity
                budget = self._apply_fee(quantity * order.limit_price)

                print(
                    f"Sold {quantity:.2f} {self.security} at \
                        {order.limit_price:.2f}")

                self.quantity -= quantity
                self.budget += budget

        order.exec_handler(order)

    def place_market_buy_order(self, budget: float,
                               exec_handler: Callable[[Order], None]):
        self.order_queue.append(MarketBuyOrder(exec_handler, budget))

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              exec_handler: Callable[[Order], None]):
        self.order_queue.append(LimitBuyOrder(exec_handler, budget,
                                              limit_price))

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, exec_handler: Callable[[Order],
                                                                   None]):
        self.order_queue.append(StopBuyOrder(exec_handler, budget, stop_price,
                                             limit_price))

    def place_market_sell_order(self, quantity: float,
                                exec_handler: Callable[[Order], None]):
        self.order_queue.append(MarketSellOrder(exec_handler, quantity))

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               exec_handler: Callable[[Order], None]):
        self.order_queue.append(LimitSellOrder(exec_handler, quantity,
                                               limit_price))

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, exec_handler: Callable[[Order],
                                                                      None]):
        self.order_queue.append(StopSellOrder(exec_handler, quantity,
                                              stop_price, limit_price))

    def get_budget(self) -> float:
        return self.budget

    def get_quantity(self) -> float:
        return self.quantity

    def reset(self, price: float):
        # self.order_queue.clear()
        # self.order_history.clear()
        ...

    def step(self, price: float):
        orders_to_remove = []

        for order in self.order_queue:
            if isinstance(order, MarketOrder):
                self._execute_order(price, order)
                orders_to_remove.append(order)
            elif isinstance(order, LimitOrder):
                if isinstance(order, BuyOrder):
                    if price <= order.limit_price:
                        self._execute_order(price, order)
                        orders_to_remove.append(order)
                elif isinstance(order, SellOrder):
                    if price >= order.limit_price:
                        self._execute_order(price, order)
                        orders_to_remove.append(order)
            elif isinstance(order, StopOrder):
                if isinstance(order, BuyOrder):
                    if price >= order.stop_price:
                        # self.place_limit_buy_order(order.limit_price,
                        #                            order.budget,
                        #                            order.exec_handler)
                        self._execute_order(price, order)
                        orders_to_remove.append(order)
                elif isinstance(order, SellOrder):
                    if price <= order.stop_price:
                        # self.place_limit_sell_order(order.limit_price,
                        #                             order.budget,
                        #                             order.exec_handler)
                        self._execute_order(price, order)
                        orders_to_remove.append(order)

        for order in orders_to_remove:
            self.order_queue.remove(order)

        self.order_history.append((price, orders_to_remove.copy()))
