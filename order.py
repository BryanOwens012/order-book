"""
Everything related to orders
"""

from copy import deepcopy
from dataclasses import dataclass
from enum import IntEnum
import time
import uuid

from util import Price, InvalidOrderException, Timestamp, make_human_readable


class OrderDirection(IntEnum):
    """
    Enum for order direction


    ASK = Sell
    BID = Buy
    """

    ASK = 1
    BID = -1


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

        self.canceled_at: Timestamp = None

        return self

    def __repr__(self) -> str:
        """
        Representation of the order
        """

        return (
            "{"
            + f"Order(ticker={self.ticker}, direction={self.direction.name}, quantity={self.quantity}, submitted_at={make_human_readable(self.submitted_at)})"
            + "}"
        )

    def __str__(self) -> str:
        """
        Representation of the order
        """

        return self.__repr__()

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

        print(
            f"\t--> Filled at ${filled_price} ({quantity} of {self.quantity} shares): {self}"
        )

        self.quantity -= quantity

        return copied_order

    def fill_fully(self, filled_price: Price) -> "Order":
        """
        Fill this order completely
        """

        self.filled_at = time.time()
        self.filled_price = filled_price

        print(
            f"\t--> Filled at ${filled_price} ({self.quantity} of {self.quantity} shares): {self}"
        )

        return self


@dataclass
class LimitOrder(Order):
    """
    An submitted order executed only when a certain price is reached
    """

    limit_price: Price

    def __post_init__(self) -> "LimitOrder":
        """
        Post init method
        """

        if self.limit_price <= 0:
            raise InvalidOrderException(self, "Limit price must be positive")

        super().__post_init__()

        return self

    def __repr__(self) -> str:
        """
        Representation of the order
        """

        return (
            "{"
            + f"LimitOrder(ticker={self.ticker}, direction={self.direction.name}, quantity={self.quantity}, limit_price=${self.limit_price}, submitted_at={make_human_readable(self.submitted_at)})"
            + "}"
        )

    def __str__(self) -> str:
        """
        Representation of the order
        """

        return self.__repr__()


@dataclass
class MarketOrder(Order):
    """
    An order executed at the current best market price
    """

    def __post_init__(self) -> "MarketOrder":
        """
        Post init method
        """

        super().__post_init__()

        return self

    def __repr__(self) -> str:
        """
        Representation of the order
        """

        return (
            "{"
            + f"MarketOrder(ticker={self.ticker}, direction={self.direction.name}, quantity={self.quantity}, submitted_at={make_human_readable(self.submitted_at)})"
            + "}"
        )

    def __str__(self) -> str:
        """
        Representation of the order
        """

        return self.__repr__()
