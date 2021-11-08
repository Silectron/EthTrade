from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from math import inf

from ethtrade.order import FilledOrder, SellOrder
from ethtrade.portfolio.portfolio import Portfolio
from ethtrade.strategy import Strategy


@dataclass
class Level:
    budget: float
    quantity: int
    lower_bound: float
    upper_bound: float
    order_ids: List[str] = field(default_factory=list)
    next: Level = None
    prev: Level = None


class GridStrategy(Strategy):
    def __init__(self, portfolio: Portfolio, levels: List[float]):
        super().__init__(portfolio)
        self.order_id_to_level_map: Dict[str, Level] = {}

        self._construct_linked_list(levels)

    def _construct_linked_list(self, levels: List[float]):
        n = len(levels) - 1

        self.current_level = Level(0, 0, 0, levels[0])

        for i in range(n):
            budget = self.portfolio.budget / n

            self.current_level.next = Level(
                budget, 0, levels[i], levels[i + 1])
            self.current_level.next.prev = self.current_level
            self.current_level = self.current_level.next

            # place orders
            order_id = self.portfolio.place_stop_buy_order(
                levels[i] - 50, levels[i], budget, self._buy_callback)
            self.order_id_to_level_map[order_id] = self.current_level
            self.current_level.order_ids.append(order_id)

        self.current_level.next = Level(0, 0, levels[n], inf)
        self.current_level.next.prev = self.current_level

    def _buy_callback(self, filled_order: FilledOrder):
        level = self.order_id_to_level_map[filled_order.order.order_id]
        level.budget -= filled_order.order.budget
        level.quantity += filled_order.quantity

        del self.order_id_to_level_map[filled_order.order.order_id]
        level.order_ids.remove(filled_order.order.order_id)

    def _sell_callback(self, filled_order: FilledOrder):
        level = self.order_id_to_level_map[filled_order.order.order_id]
        level.budget += filled_order.price * filled_order.quantity
        level.quantity -= filled_order.quantity

        del self.order_id_to_level_map[filled_order.order.order_id]
        level.order_ids.remove(filled_order.order.order_id)

        order_id = self.portfolio.place_limit_buy_order(
            level.lower_bound, level.budget, self._buy_callback)
        self.order_id_to_level_map[order_id] = level
        level.order_ids.append(order_id)

    def _next_level(self):
        self.current_level = self.current_level.next

    def _prev_level(self):
        self.current_level = self.current_level.prev

    def reset(self, price: float):
        if price > self.current_level.upper_bound:
            while price > self.current_level.next.upper_bound:
                self._next_level()

        elif price < self.current_level.lower_bound:
            while price < self.current_level.prev.lower_bound:
                self._prev_level()

        self.portfolio.reset(price)

    def _handle_rising_entering_level(self, price: float):
        ...

    def _handle_falling_entering_level(self, price: float):
        ...

    def _handle_rising_leaving_level(self, price: float):
        level = self.current_level

        while level.prev is not None:
            remaining_quantity = level.quantity

            for order_id in level.order_ids:
                order = self.portfolio.get_order_by_id(order_id)
                if isinstance(order, SellOrder):
                    self.portfolio.cancel_order(order_id)

                    del self.order_id_to_level_map[order_id]
                    level.order_ids.remove(order_id)

                    order_id = self.portfolio.place_stop_sell_order(
                        level.upper_bound + 50, level.upper_bound,
                        order.quantity, order.fill_handler)
                    self.order_id_to_level_map[order_id] = level
                    level.order_ids.append(order_id)

                    remaining_quantity -= order.quantity

            if remaining_quantity > 0:
                order_id = self.portfolio.place_stop_sell_order(
                    level.upper_bound + 50, level.upper_bound,
                    remaining_quantity, self._sell_callback)
                self.order_id_to_level_map[order_id] = level
                level.order_ids.append(order_id)

            level = level.prev
        ...

    def _handle_falling_leaving_level(self, price: float):
        ...

    def step(self, price: float):
        if price > self.current_level.upper_bound:
            self._handle_rising_leaving_level(price)

            while price > self.current_level.upper_bound:
                self._next_level()

            self._handle_rising_entering_level(price)

        elif price < self.current_level.lower_bound:
            self._handle_falling_leaving_level(price)

            while price < self.current_level.lower_bound:
                self._prev_level()

            self._handle_falling_entering_level(price)

        self.portfolio.step(price)
