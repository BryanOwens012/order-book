"""
Utilities
"""

from queue import PriorityQueue
from typing import Any
from datetime import datetime

Dollars = float
Timestamp = float


class CustomPQ(PriorityQueue):
    """
    Wrapper around PriorityQueue, to allow for custom __repr__ and __str__ methods
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        queue_values = [elt[1].__repr__() for elt in self.queue]
        return "{" + f"CustomPQ({', '.join(queue_values)})" + "}"

    def __str__(self):
        return self.__repr__()


class InvalidOrderException(Exception):
    """
    Exception for invalid order
    """

    def __init__(self, order: Any, message: str):
        self.order = order
        self.message = message
        super().__init__(message)


def make_human_readable(timestamp: Timestamp):
    """
    Convert timestamp to human readable format
    """

    return datetime.fromtimestamp(timestamp).strftime("%f")[2:]
