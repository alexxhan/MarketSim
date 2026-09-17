import unittest

from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook


class MatchingTests(unittest.TestCase):
    def test_incoming_buy_sweeps_resting_asks_at_each_resting_price(self):
        book = OrderBook()
        book.add_order(Order(1, OrderSide.SELL, 100.05, 10))
        book.add_order(Order(2, OrderSide.SELL, 100.10, 15))
        book.add_order(Order(3, OrderSide.BUY, 100.10, 20))
        trades = book.match_orders()
        self.assertEqual([(t.price, t.quantity) for t in trades], [(100.05, 10), (100.10, 10)])
        self.assertEqual(book.bids, [])
        self.assertEqual([(o.order_id, o.quantity) for o in book.asks], [(2, 5)])
        self.assertEqual(book.match_orders(), [])
