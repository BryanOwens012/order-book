# order-book

Builds a simulated stock market order book

## Features

Order:
- Market order
- Limit order
- Submit and/or execute order (full or partial fill)
- Update order

Order book:
- Bids
- Asks
- Order submission history
- Order execution history
- For any particular ticket, order limit orders first by price level, then by submission time

## Data structures used

- Within a price level, since orders are ordered by timestamp, and timestamp is monotonically increasing, all insertions are done at the end. (If we partially fill an order, we can simply update the `quantity` of the existing order, instead of trying to insert a new one into the list with the same timestamp.) Thus, Python's native dict, which guarantees insertion order, suffices for O(1) CRUD of orders. (If we wanted to insert new orders into the middle of the orders list, we'd have to implement our own doubly-linked dictionary.)