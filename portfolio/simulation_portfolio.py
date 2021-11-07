
from order import Order, FilledOrder, BuyOrder, SellOrder, MarketOrder, \
    LimitOrder, StopOrder, MarketBuyOrder, MarketSellOrder, LimitBuyOrder, \
    LimitSellOrder, StopBuyOrder, StopSellOrder
from portfolio import Portfolio

from uuid import uuid4
from typing import Union, List, Dict, Tuple, Callable


class SimulationPortfolio(Portfolio):
    def __init__(self, security: str, budget: float, quantity: float,
                 transaction_fee: Union[int, float]):
        super().__init__(security)
        self.budget: float = budget
        self.quantity: float = quantity
        self.transaction_fee: Union[int, float] = transaction_fee

        self.order_book: Dict[str, Order] = {}
        self.order_fill: List[Tuple[int, FilledOrder]] = []

        self.index = 0

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
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = MarketBuyOrder(order_id, fill_handler, budget)
        self.order_book[order_id] = order

        return order_id

    def place_limit_buy_order(self, limit_price: float, budget: float,
                              fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = LimitBuyOrder(order_id, fill_handler, budget, limit_price)
        self.order_book[order_id] = order

        return order_id

    def place_stop_buy_order(self, stop_price: float, limit_price: float,
                             budget: float, fill_handler: Callable[
                                 [FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = StopBuyOrder(order_id, fill_handler,
                             budget, stop_price, limit_price)
        self.order_book[order_id] = order

        return order_id

    def place_market_sell_order(self, quantity: float,
                                fill_handler: Callable[
                                    [FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = MarketSellOrder(order_id, fill_handler, quantity)
        self.order_book[order_id] = order

        return order_id

    def place_limit_sell_order(self, limit_price: float, quantity: float,
                               fill_handler: Callable[[
                                   FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = LimitSellOrder(order_id, fill_handler, quantity, limit_price)
        self.order_book[order_id] = order

        return order_id

    def place_stop_sell_order(self, stop_price: float, limit_price: float,
                              quantity: float, fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
        order_id = str(uuid4())
        order = StopSellOrder(order_id, fill_handler,
                              quantity, stop_price, limit_price)
        self.order_book[order_id] = order

        return order_id

    def get_budget(self) -> float:
        return self.budget

    def get_quantity(self) -> float:
        return self.quantity

    def get_order_ids(self) -> List[str]:
        return list(self.order_book)

    def get_order_by_id(self, order_id: str) -> Union[Order, None]:
        return self.order_book[order_id]

    def cancel_order(self, order_id: str):
        if order_id in self.order_book:
            del self.order_book[order_id]

    def reset(self, price: float):
        # self.order_book.clear()
        self.order_fill.clear()
        self.index = 0

    def step(self, price: float):
        for order_id in self.get_order_ids():
            order = self.get_order_by_id(order_id)

            if isinstance(order, MarketOrder):
                filled_order = self._fill_order(price, order)
                del self.order_book[order_id]
                self.order_fill.append((self.index, filled_order))

            elif isinstance(order, LimitOrder):
                if (isinstance(order, BuyOrder) and price <= order.limit_price) or \
                        (isinstance(order, SellOrder) and price >= order.limit_price):
                    filled_order = self._fill_order(price, order)
                    del self.order_book[order_id]
                    self.order_fill.append((self.index, filled_order))

            elif isinstance(order, StopOrder):
                if isinstance(order, BuyOrder):
                    if price >= order.stop_price:
                        new_order = LimitBuyOrder(
                            order.order_id,
                            order.fill_handler,
                            order.budget,
                            order.limit_price)
                        self.order_book[new_order.order_id] = new_order

                elif isinstance(order, SellOrder):
                    if price <= order.stop_price:
                        new_order = LimitSellOrder(
                            order.order_id,
                            order.fill_handler,
                            order.quantity,
                            order.limit_price)
                        self.order_book[new_order.order_id] = new_order

        self.index += 1
