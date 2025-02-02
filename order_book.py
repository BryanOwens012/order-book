"""
Order book
"""

from dataclasses import dataclass
from typing import Tuple, Optional

from order import LimitOrder, MarketOrder, Order, OrderDirection
from price_level import PriceLevel
from util import Price, CustomPQ, InvalidOrderException


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

        self.active_orders: dict[OrderDirection, CustomPQ[Tuple[Price, PriceLevel]]] = {
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

        self.price_levels: dict[OrderDirection, dict[Price, PriceLevel]] = {
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

    def get_active_orders_str(self):
        """
        Get active orders as string
        """

        result = ""

        result += f"Active orders for {self.ticker}: ===========\n\n"

        for direction in OrderDirection:
            result += f"{direction.name}:\n"

            pq = self.active_orders[direction]
            copied_pq: CustomPQ[Tuple[Price, PriceLevel]] = CustomPQ()

            while not pq.empty():
                priority, price_level = pq.get()
                copied_pq.put((priority, price_level))

                for order in price_level.orders.values():
                    result += f"Price: {price_level.price}, Order: {order}\n"

            pq = copied_pq

            result += "\n"

        return result

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
                    continue

            # Process orders at this price level
            orders_to_remove = []
            for matched_order in matched_price_level.orders.values():
                if order.filled_at:
                    break

                while not matched_order.filled_at:
                    if order.filled_at:
                        break
                    self.fill_quantities(matched_order, order, matched_price)

                if matched_order.filled_at:
                    orders_to_remove.append(matched_order.order_id)

            # Remove filled orders
            for order_id in orders_to_remove:
                del matched_price_level.orders[order_id]

            # If price level still has orders, put it back
            if matched_price_level.orders:
                unmatched.append((priority, matched_price_level))
            else:
                del self.price_levels[direction * -1][matched_price]

        # Put all unmatched price levels back
        for priority, price_level in unmatched:
            active_orders.put((priority, price_level))

    def submit_market_order(self, market_order: MarketOrder):
        """
        Submit and execute (fill, if possible) a market order
        """

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
                price_level = PriceLevel(limit_price)
                price_levels[limit_price] = price_level

                active_orders.put((direction * limit_price, price_level))

            price_level.orders[limit_order.order_id] = limit_order
