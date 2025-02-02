"""
Stock exchange
"""

from dataclasses import dataclass

from order import LimitOrder, MarketOrder
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

    def submit_market_order(self, market_order: MarketOrder):
        """
        Submit and execute (fill, if possible) a market order
        """

        ticker = market_order.ticker

        self.get_or_create_order_book(ticker).submit_market_order(market_order)

    def submit_limit_order(self, limit_order: LimitOrder):
        """
        Submit a limit order
        """

        ticker = limit_order.ticker

        self.get_or_create_order_book(ticker).submit_limit_order(limit_order)
