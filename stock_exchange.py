"""
Stock exchange
"""

from dataclasses import dataclass
from typing import Optional

from order import LimitOrder, MarketOrder, OrderDirection
from order_book import OrderBook


@dataclass
class StockExchange:
    """
    Stock market exchange
    """

    def __post_init__(self):
        """
        Post init method
        """

        self.order_books: dict[str, OrderBook] = {}

    def __repr__(self):
        """
        Representation of the exchange
        """

        return "{" + f"Exchange(order_books={self.order_books})" + "}"

    def __str__(self):
        """
        Representation of the exchange
        """

        return self.__repr__()

    def get_or_create_order_book(self, ticker: str) -> OrderBook:
        """
        Ensure an order book exists for a ticker
        """

        if ticker not in self.order_books:
            self.order_books[ticker] = OrderBook(ticker)

        return self.order_books[ticker]

    def submit_market_order(self, market_order: MarketOrder) -> MarketOrder:
        """
        Submit and execute (fill, if possible) a market order
        """

        ticker = market_order.ticker

        return self.get_or_create_order_book(ticker).submit_market_order(market_order)

    def submit_limit_order(self, limit_order: LimitOrder) -> LimitOrder:
        """
        Submit a limit order
        """

        ticker = limit_order.ticker

        return self.get_or_create_order_book(ticker).submit_limit_order(limit_order)

    def cancel_limit_order(
        self, ticker: str, direction: OrderDirection, price: float, order_id: str
    ) -> LimitOrder:
        """
        Cancel a limit order
        """

        return self.get_or_create_order_book(ticker).cancel_limit_order(
            direction, price, order_id
        )

    def update_limit_order(
        self,
        ticker: str,
        direction: OrderDirection,
        price: float,
        order_id: str,
        new_quantity: Optional[int],
        new_price: Optional[float],
    ) -> LimitOrder:
        """
        Update a limit order
        """

        return self.get_or_create_order_book(ticker).update_limit_order(
            direction, price, order_id, new_quantity, new_price
        )

    def get_active_orders_str(self, ticker: str) -> str:
        """
        Get a string representation of the active orders for a ticker
        """

        return self.get_or_create_order_book(ticker).get_active_orders_str()
