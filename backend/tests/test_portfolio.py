import unittest

from app.market.portfolio import Portfolio


class PortfolioTests(unittest.TestCase):
    def test_buy_accounting_and_positive_inventory_mark(self):
        portfolio = Portfolio(100000)
        portfolio.buy(99.98, 10)
        self.assertAlmostEqual(portfolio.cash, 99000.20)
        self.assertEqual(portfolio.inventory, 10)
        self.assertAlmostEqual(portfolio.get_value(101), 100010.20)
        self.assertAlmostEqual(portfolio.get_pnl(101), 10.20)

    def test_sell_accounting_and_negative_inventory_mark(self):
        portfolio = Portfolio(100000)
        portfolio.sell(100.02, 10)
        self.assertAlmostEqual(portfolio.cash, 101000.20)
        self.assertEqual(portfolio.inventory, -10)
        self.assertAlmostEqual(portfolio.get_value(99), 100010.20)
        self.assertAlmostEqual(portfolio.get_pnl(99), 10.20)

    def test_round_trip_spread_capture(self):
        portfolio = Portfolio(100000)
        portfolio.buy(99.98, 10)
        portfolio.sell(100.02, 10)
        self.assertEqual(portfolio.inventory, 0)
        self.assertAlmostEqual(portfolio.cash, 100000.40)
        self.assertAlmostEqual(portfolio.get_pnl(500), 0.40)
