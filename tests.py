"""
Test functions are here
"""

from order import LimitOrder, MarketOrder, OrderDirection
from stock_exchange import StockExchange


def test_0():
    """
    Test #0
    """

    exchange = StockExchange()

    limit_order0 = LimitOrder(
        ticker="AAPL", direction=OrderDirection.BID, quantity=100, limit_price=100
    )
    print(f"\nSubmitting limit order: {limit_order0}")
    exchange.submit_limit_order(limit_order0)

    limit_order_1 = LimitOrder(
        ticker="AAPL", direction=OrderDirection.BID, quantity=200, limit_price=110
    )
    print(f"\nSubmitting limit order: {limit_order_1}")
    exchange.submit_limit_order(limit_order_1)

    market_order_0 = MarketOrder(
        ticker="AAPL", direction=OrderDirection.ASK, quantity=50
    )
    print(f"\nSubmitting market order: {market_order_0}")
    exchange.submit_market_order(market_order_0)

    limit_order_2 = LimitOrder(
        ticker="AAPL", direction=OrderDirection.ASK, quantity=100, limit_price=140
    )
    print(f"\nSubmitting limit order: {limit_order_2}")
    exchange.submit_limit_order(limit_order_2)

    print(f"Result: {exchange.order_books['AAPL'].price_levels}")

    limit_order_3 = LimitOrder(
        ticker="AAPL", direction=OrderDirection.BID, quantity=40, limit_price=160
    )
    print(f"\nSubmitting limit order: {limit_order_3}")
    exchange.submit_limit_order(limit_order_3)

    limit_order_4 = LimitOrder(
        ticker="GOOG", direction=OrderDirection.BID, quantity=30, limit_price=150
    )
    print(f"\nSubmitting limit order: {limit_order_4}")
    exchange.submit_limit_order(limit_order_4)

    print("\n")

    for order_book in exchange.order_books.values():
        print(order_book.get_active_orders_str())
