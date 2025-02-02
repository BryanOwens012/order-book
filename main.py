"""
Driver file
"""

from stock_exchange import StockExchange
from order import LimitOrder, MarketOrder, OrderDirection


def main():
    """
    Driver
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
        ticker="AAPL", direction=OrderDirection.ASK, quantity=20, limit_price=140
    )
    print(f"\nSubmitting limit order: {limit_order_2}")
    exchange.submit_limit_order(limit_order_2)

    limit_order_3 = LimitOrder(
        ticker="AAPL", direction=OrderDirection.BID, quantity=40, limit_price=160
    )
    print(f"\nSubmitting limit order: {limit_order_3}")
    exchange.submit_limit_order(limit_order_3)


if __name__ == "__main__":
    main()
