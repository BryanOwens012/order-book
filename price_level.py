"""
Price level
"""

import uuid
from dataclasses import dataclass

from util import Dollars
from order import LimitOrder


@dataclass
class PriceLevel:
    """
    A price level in the order book
    """

    price: Dollars

    def __post_init__(self):
        """
        Post init method
        """

        self.orders: dict[uuid.UUID, LimitOrder] = {}

    def __repr__(self):
        """
        Representation of the price level
        """

        return "{" + f"PriceLevel(price=${self.price}, orders={self.orders})" + "}"

    def __str__(self):
        """
        Representation of the price level
        """

        return self.__repr__()
