import unittest

from app.strategies.inventory_market_maker import InventoryMarketMaker


class InventoryMarketMakerTests(unittest.TestCase):
    def test_inventory_shifts_reservation_price_in_correct_direction(self):
        maker = InventoryMarketMaker(spread=0.04, inventory_risk_factor=0.001)
        for inventory, expected in ((0, (99.98, 100.02)), (30, (99.95, 99.99)), (-30, (100.01, 100.05))):
            with self.subTest(inventory=inventory):
                maker.portfolio.inventory = inventory
                bid, ask = maker.generate_quotes(100)
                self.assertEqual((bid.price, ask.price), expected)
