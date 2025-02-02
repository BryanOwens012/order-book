"""
Driver file
"""

from dataclasses import dataclass
from enum import StrEnum
import time
import uuid
from queue import PriorityQueue
from typing import Tuple, Optional, Union
from copy import deepcopy

Timestamp = float
Price = float


class InvalidOrderException(Exception):
    """
    Exception for invalid order
    """

    def __init__(self, order: "Order", message: str):
        self.order = order
        self.message = message
        super().__init__(message)


class OrderDirection(StrEnum):
    """
    Enum for order direction

    BID = Buy
    ASK = Sell
    """

    BID = "bid"
    ASK = "ask"


@dataclass
class Order:
    """
    One order being submitted and/or executed

    If an order is partially filled,
    it will be split into multiple orders (with the same `submitted_at`).

    Once an order is filled, it cannot be updated or cancelled.
    """

    ticker: str
    direction: OrderDirection
    quantity: int

    def __post_init__(self) -> "Order":
        """
        Post init method
        """

        if self.quantity <= 0:
            raise InvalidOrderException(self, "Quantity must be positive")
        if not self.ticker:
            raise InvalidOrderException(self, "Ticker must be non-empty")
        if self.direction not in OrderDirection:
            raise InvalidOrderException(self, "Invalid direction")

        self.order_id: uuid.UUID = uuid.uuid4()
        self.submitted_at: Timestamp = time.time()
        self.filled_at: Timestamp = None
        self.filled_price: Price = None

        return self

    def fill_partially(self, quantity: int, filled_price: Price) -> "Order":
        """
        Split this order into two orders
        """

        if quantity <= 0:
            raise InvalidOrderException(self, "Quantity must be positive")

        if quantity >= self.quantity:
            raise InvalidOrderException(
                self, "Quantity must be less than the original order"
            )

        copied_order = deepcopy(self)
        copied_order.quantity = quantity
        copied_order.order_id = uuid.uuid4()
        copied_order.filled_at = time.time()
        copied_order.filled_price = filled_price

        self.quantity -= quantity

        return copied_order

    def fill_fully(self, filled_price: Price) -> "Order":
        """
        Fill this order completely
        """

        self.filled_at = time.time()
        self.filled_price = filled_price

        return self


@dataclass
class LimitOrder(Order):
    """
    An submitted order executed only when a certain price is reached
    """

    limit_price: Price

    def __post_init__(self):
        """
        Post init method
        """

        if self.limit_price <= 0:
            raise InvalidOrderException(self, "Limit price must be positive")


@dataclass
class MarketOrder(Order):
    """
    An order executed at the current best market price
    """


@dataclass
class PriceLevel:
    """
    A price level in the order book
    """

    price: Price

    def __post_init__(self):
        """
        Post init method
        """

        self.orders: dict[uuid.UUID, LimitOrder] = {}


@dataclass
class OrderBook:
    """
    Order book
    """

    ticker: str

    def __post_init__(self):
        """
        Post init method
        """

        if not self.ticker:
            raise ValueError("Ticker must be non-empty")

        self.active_orders: dict[
            OrderDirection, PriorityQueue[Tuple[Price, PriceLevel]]
        ] = {
            OrderDirection.BID: PriorityQueue(),
            OrderDirection.ASK: PriorityQueue(),
        }

        self.executed_orders: dict[OrderDirection, list[Order]] = {
            OrderDirection.BID: [],
            OrderDirection.ASK: [],
        }

        self.invalid_orders: dict[OrderDirection, list[Order]] = {
            OrderDirection.BID: [],
            OrderDirection.ASK: [],
        }

        self.price_levels: dict[OrderDirection, dict[Price, PriceLevel]] = {
            OrderDirection.BID: {},
            OrderDirection.ASK: {},
        }

    def fill_quantities(self, a: Order, b: Order, price: Price):
        """
        Fill quantities
        """

        if not (a.ticker == self.ticker and b.ticker == self.ticker):
            raise InvalidOrderException(a, "Tickers must match")

        filled_a: Optional[Order] = None
        filled_b: Optional[Order] = None

        if a.quantity == b.quantity:
            filled_a = a.fill_fully(price)
            filled_b = b.fill_fully(price)

        if a.quantity > b.quantity:
            filled_a = a.fill_partially(b.quantity, price)
            filled_b = b.fill_fully(price)

        if a.quantity < b.quantity:
            filled_a = a.fill_fully(price)
            filled_b = b.fill_partially(a.quantity, price)

        if filled_a is None or filled_b is None:
            self.invalid_orders[a.direction].append(a)
            self.invalid_orders[b.direction].append(b)

            raise InvalidOrderException(a, "Failed to fill orders")

        self.executed_orders[filled_a.direction].append(filled_a)
        self.executed_orders[filled_b.direction].append(filled_b)

    def execute_order(self, order: Order):
        """
        Execute an order
        """

        ticker = order.ticker

        if ticker != self.ticker:
            raise InvalidOrderException(order, "Tickers must match")

        direction = order.direction

        active_orders = self.active_orders[direction]
        invalid_orders = self.invalid_orders[direction]

        if not active_orders:
            invalid_orders.append(order)
            raise InvalidOrderException(
                order, "Failed to submit market order: no more asks available"
            )

        while not active_orders.empty():
            if order.filled_at:
                break

            # We ignore the pq priority value; it's positive or negative, as appropriate, to represent the top of the order book
            _, matched_price_level = active_orders.get()
            matched_price = matched_price_level.price

            for matched_order in list(matched_price_level.orders.values()):
                if order.filled_at:
                    break

                while not matched_order.filled_at:
                    if order.filled_at:
                        break

                    self.fill_quantities(matched_order, order, matched_price)

                del matched_price_level.orders[matched_order.order_id]
            else:
                del self.price_levels[direction][matched_price]

    def submit_market_order(self, market_order: MarketOrder):
        """
        Submit and execute (fill, if possible) a market order
        """

        direction = market_order.direction
        invalid_orders = self.invalid_orders[direction]

        self.execute_order(market_order)

        if not market_order.filled_at:
            invalid_orders.append(market_order)
            raise InvalidOrderException(
                market_order, "Failed to fill market order: no more asks available"
            )

    def submit_limit_order(self, limit_order: LimitOrder):
        """
        Submit a limit order
        """

        direction = limit_order.direction
        limit_price = limit_order.limit_price

        price_levels = self.price_levels[direction]
        active_orders = self.active_orders[direction]

        self.execute_order(limit_order)

        if not limit_order.filled_at:
            price_level: Optional[PriceLevel] = None

            if limit_price in price_levels:
                price_level = price_levels[limit_price]
            else:
                new_price_level = PriceLevel(limit_price)
                price_levels[limit_price] = new_price_level

                if direction == OrderDirection.BID:
                    active_orders.put((-limit_price, new_price_level))
                else:
                    active_orders.put((limit_price, new_price_level))

            price_level.orders[limit_order.order_id] = limit_order


@dataclass
class Exchange:
    """
    Stock market exchange
    """

    def __post_init__(self):
        """
        Post init method
        """

        self.order_books: dict[str, OrderBook] = {}

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


def main():
    """
    Driver
    """

    exchange = Exchange()
    exchange.submit_market_order(MarketOrder("AAPL", OrderDirection.BID, 100))


if __name__ == "__main__":
    main()
