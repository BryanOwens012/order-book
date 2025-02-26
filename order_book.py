"""
Order book
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import time
from copy import deepcopy
import uuid

from order import LimitOrder, MarketOrder, Order, OrderDirection
from price_level import PriceLevel
from util import Dollars, CustomPQ, InvalidOrderException


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

        self.orders_by_id: dict[uuid.UUID, LimitOrder] = {}

        self.active_orders: dict[
            OrderDirection, CustomPQ[Tuple[Dollars, PriceLevel]]
        ] = {
            OrderDirection.BID: CustomPQ(),
            OrderDirection.ASK: CustomPQ(),
        }

        self.executed_orders: dict[OrderDirection, list[Order]] = {
            OrderDirection.BID: [],
            OrderDirection.ASK: [],
        }

        self.invalid_orders: dict[OrderDirection, list[Order]] = {
            OrderDirection.BID: [],
            OrderDirection.ASK: [],
        }

        self.price_levels: dict[OrderDirection, dict[Dollars, PriceLevel]] = {
            OrderDirection.BID: {},
            OrderDirection.ASK: {},
        }

    def __repr__(self):
        """
        Representation of the order book
        """

        return (
            "{"
            + f"OrderBook(ticker={self.ticker}, active_orders={self.active_orders}, executed_orders={self.executed_orders}, invalid_orders={self.invalid_orders}, price_levels={self.price_levels})"
            + "}"
        )

    def __str__(self):
        """
        Representation of the order book
        """

        return self.__repr__()

    def get_active_orders_str(self) -> str:
        """
        Get active orders as string
        """

        result = ""

        result += f"Active orders for {self.ticker}: ===========\n\n"

        for direction in OrderDirection:
            result += f"{direction.name}:\n"

            pq = self.active_orders[direction]
            copied_pq: CustomPQ[Tuple[Dollars, PriceLevel]] = CustomPQ()

            if pq.empty():
                result += "(No active orders)\n\n"
                continue

            while not pq.empty():
                priority, price_level = pq.get()
                copied_pq.put((priority, price_level))

                for order in price_level.orders.values():
                    if order.canceled_at:
                        continue

                    result += f"Price: {price_level.price}, Order: {order}\n"

            pq = copied_pq

            result += "\n"

        return result

    def fill(self, a: Order, b: Order, price: Dollars):
        """
        Fill orders against each other
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

        if not (filled_a and filled_b):
            self.invalid_orders[a.direction].append(a)
            self.invalid_orders[b.direction].append(b)

            raise InvalidOrderException(a, "Failed to fill orders")

        self.executed_orders[filled_a.direction].append(filled_a)
        self.executed_orders[filled_b.direction].append(filled_b)

    def execute_order(self, order: Order) -> Order:
        """
        Execute an order
        """

        ticker = order.ticker
        if ticker != self.ticker:
            raise InvalidOrderException(order, "Tickers must match")

        direction = order.direction
        active_orders = self.active_orders[direction * -1]

        # Store unmatched price levels to put back
        unmatched = []

        while not active_orders.empty():
            if order.filled_at:
                break

            priority, matched_price_level = active_orders.get()
            matched_price = matched_price_level.price

            # Price check for limit orders
            if isinstance(order, LimitOrder):
                if (
                    direction == OrderDirection.BID
                    and matched_price > order.limit_price
                ) or (
                    direction == OrderDirection.ASK
                    and matched_price < order.limit_price
                ):
                    unmatched.append((priority, matched_price_level))
                    break

            # Process orders at this price level
            orders_to_remove = []
            for matched_order in matched_price_level.orders.values():
                if order.filled_at:
                    break
                if matched_order.canceled_at:
                    orders_to_remove.append(matched_order.order_id)
                    continue

                while not matched_order.filled_at:
                    if order.filled_at:
                        break
                    self.fill(matched_order, order, matched_price)

                if matched_order.filled_at:
                    orders_to_remove.append(matched_order.order_id)

            # Remove filled orders
            for order_id in orders_to_remove:
                del matched_price_level.orders[order_id]
                del self.orders_by_id[order_id]

            # If price level still has orders, put it back
            if matched_price_level.orders:
                unmatched.append((priority, matched_price_level))
            else:
                del self.price_levels[direction * -1][matched_price]

        # Put all unmatched price levels back
        for priority, price_level in unmatched:
            active_orders.put((priority, price_level))

        return order

    def submit_market_order(self, market_order: MarketOrder) -> MarketOrder:
        """
        Submit and execute (fill, if possible) a market order
        """

        self.orders_by_id[market_order.order_id] = market_order

        direction = market_order.direction
        invalid_orders = self.invalid_orders[direction]

        self.execute_order(market_order)

        if not market_order.filled_at:
            invalid_orders.append(market_order)

            if direction == OrderDirection.BID:
                raise InvalidOrderException(
                    market_order, "Failed to fill market order: no more asks available"
                )

            raise InvalidOrderException(
                market_order,
                "Failed to fill market order: no more bids available",
            )

        return market_order

    def submit_limit_order(self, limit_order: LimitOrder) -> LimitOrder:
        """
        Submit a limit order
        """

        self.orders_by_id[limit_order.order_id] = limit_order

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
                price_level = PriceLevel(limit_price)
                price_levels[limit_price] = price_level

                active_orders.put((direction * limit_price, price_level))

            price_level.orders[limit_order.order_id] = limit_order

        return limit_order

    def cancel_limit_order(self, order_id: uuid.UUID) -> LimitOrder:
        """
        Cancel a limit order
        """

        if order_id not in self.orders_by_id:
            raise InvalidOrderException(
                None, f"Could not find an order with order ID {order_id}"
            )

        order: LimitOrder = self.orders_by_id[order_id]
        del self.orders_by_id[order_id]
        order.canceled_at = time.time()

        price_level = self.price_levels[order.direction][order.limit_price]
        del price_level.orders[order_id]

        if not price_level.orders:
            del self.price_levels[order.direction][order.limit_price]

        return order

    def update_limit_order(
        self,
        order_id: uuid.UUID,
        new_quantity: Optional[int],
        new_price: Optional[float],
    ) -> LimitOrder:
        """
        Update a limit order
        Basically equivalent to canceling and resubmitting
        """

        order = self.cancel_limit_order(order_id)

        new_order = deepcopy(order)
        new_order.quantity = new_quantity if new_quantity else order.quantity
        new_order.limit_price = new_price if new_price else order.limit_price
        new_order.canceled_at = None
        new_order.submitted_at = time.time()
        new_order.order_id = uuid.uuid4()

        return self.submit_limit_order(new_order)
