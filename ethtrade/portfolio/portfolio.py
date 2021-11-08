from typing import List, Union, Callable

from ethtrade.order import Order, FilledOrder


class Portfolio:
    """Base class for Portfolio"""

    def __init__(self, security: str):
        """construct portfolio for a security

        Args:
            security (str): name of the security
        """
        self.security = security

    def place_market_buy_order(self, budget: float,
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
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
                              fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
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
                             budget: float, fill_handler: Callable[
                                 [FilledOrder], None]) -> str:
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
                                fill_handler: Callable[
                                    [FilledOrder], None]) -> str:
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
                               fill_handler: Callable[
                                   [FilledOrder], None]) -> str:
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
                              quantity: float, fill_handler: Callable[
                                  [FilledOrder], None]) -> str:
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

    def get_order_ids(self) -> List[str]:
        """get all place order ids for this portfolio

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            List[str]: list of placed order ids for this portfolio
        """
        raise NotImplementedError

    def get_order_by_id(self, order_id: str) -> Union[Order, None]:
        """get order by id

        Args:
            order_id (str): an existing order id for this portfolio

        Raises:
            NotImplementedError: must be implemented by subclass

        Returns:
            Union[Order, None]: order associated to order_id
        """
        raise NotImplementedError

    def cancel_order(order_id: str):
        """cancel a placed order for this portfolio

        Args:
            order (str): an existing order id for this portfolio

        Raises:
            NotImplementedError: must be implemented by subclass
        """
        raise NotImplementedError

    def reset(self, price: float):
        raise NotImplementedError

    def step(self, price: float):
        raise NotImplementedError
