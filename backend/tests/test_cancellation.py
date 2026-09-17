import unittest

from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook


class CancellationTests(unittest.TestCase):
    def test_cancelled_order_cannot_execute(self):
        for side in (OrderSide.BUY, OrderSide.SELL):
            with self.subTest(side=side):
                book = OrderBook()
                book.add_order(Order(1, side, 100, 10))
                self.assertTrue(book.cancel_order(1))
                self.assertFalse(book.cancel_order(1))
                opposite = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
                book.add_order(Order(2, opposite, 100, 10))
                self.assertEqual(book.match_orders(), [])
                self.assertEqual(len(book.bids) + len(book.asks), 1)
