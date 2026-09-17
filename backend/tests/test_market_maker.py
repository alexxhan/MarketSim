import unittest

from app.market.order import OrderSide
from app.strategies.basic_market_maker import BasicMarketMaker
from app.strategies.inventory_market_maker import InventoryMarketMaker


class MarketMakerTests(unittest.TestCase):
    def test_tick_aligned_quotes_for_both_strategies(self):
        for strategy in (BasicMarketMaker, InventoryMarketMaker):
            for midprice, spread, expected in (
                (100, 0.04, (99.98, 100.02)),
                (100, 0.01, (99.99, 100.01)),
                (100.005, 0.01, (100.00, 100.01)),
                (100.005, 0.04, (99.98, 100.03)),
                (100, 0.001, (99.99, 100.01)),
            ):
                with self.subTest(strategy=strategy.__name__, midprice=midprice, spread=spread):
                    maker = strategy(spread=spread, order_size=10)
                    bid, ask = maker.generate_quotes(midprice)
                    self.assertEqual((bid.price, ask.price), expected)
                    self.assertLess(bid.price, ask.price)
                    self.assertEqual((bid.side, ask.side), (OrderSide.BUY, OrderSide.SELL))
                    self.assertEqual((bid.quantity, ask.quantity), (10, 10))
                    self.assertEqual((bid.owner, ask.owner), (maker.owner, maker.owner))
                    self.assertNotEqual(bid.identity, ask.identity)
