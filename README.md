# order-book

Builds a simulated stock market order book.

All operations complete in optimal amortized time complexity.

## Features

Order:
- Market order
- Limit order
- Submit and/or execute order (full or partial fill)
- Update order
- Cancel order

Order book:
- Bids
- Asks
- Order submission history
- Order execution history
- Order error history (invalid orders)
- For any particular ticket, order limit orders first by price level, then by submission time

## Data structures used

- Within a price level, orders are a dict. Since orders are ordered by timestamp, and timestamp is monotonically increasing, all insertions are done at the end. (If we partially fill an order, we can simply update the `quantity` of the existing order, instead of trying to insert a new one into the list with the same timestamp.) Thus, Python's native dict, which guarantees insertion order, suffices for O(1) CRUD of orders. (If we instead wanted to insert new orders into the middle of the orders list, we'd have to implement our own doubly-linked dictionary.)

- Price levels are required to be (at least) partially ordered, so we use a priority queue for that

- Order history is just a list. In this implementation, it will naturally be ordered by `filled_at`.