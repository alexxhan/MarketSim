import unittest
from unittest.mock import patch

from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook
from app.market.trade import Trade
from app.market.validation import SimulationDomainError
from app.simulation.engine import SimulationEngine


class OrderIdentityTests(unittest.TestCase):
    def test_collision_boundary_cannot_attribute_external_buy_to_maker(self):
        for strategy, boundary in (("basic", 1_000_000), ("inventory", 2_000_000)):
            with self.subTest(strategy=strategy):
                engine = SimulationEngine(strategy=strategy, seed=42)
                engine.market_maker.next_order_id = boundary
                engine.order_book.add_order(Order(900, OrderSide.BUY, 99, 100))
                engine.order_book.add_order(Order(901, OrderSide.SELL, 101, 100))
                order = Order(boundary, OrderSide.BUY, 101, 4)
                with patch.object(engine.order_flow, "generate_order", return_value=order):
                    state = engine.step()
                self.assertAlmostEqual(state["cash"], 100400.08)
                self.assertEqual(state["inventory"], -4)
                self.assertEqual(state["metrics"]["market_maker_buy_fills"], 0)
                self.assertEqual(state["metrics"]["market_maker_sell_fills"], 1)
                self.assertEqual(state["metrics"]["market_maker_executed_volume"], 4)

    def test_colliding_external_bid_cannot_cancel_maker_ask(self):
        for strategy, boundary in (("basic", 1_000_000), ("inventory", 2_000_000)):
            with self.subTest(strategy=strategy):
                engine = SimulationEngine(strategy=strategy, seed=42)
                engine.market_maker.next_order_id = boundary
                external = Order(boundary + 1, OrderSide.BUY, 99, 100)
                engine.order_book.add_order(external)
                engine.order_book.add_order(Order(901, OrderSide.SELL, 101, 100))
                orders = [Order(1, OrderSide.BUY, 98, 1), Order(2, OrderSide.BUY, 100.05, 20)]
                with patch.object(engine.order_flow, "generate_order", side_effect=orders):
                    engine.step()
                    state = engine.step()
                self.assertIn(external, engine.order_book.bids)
                self.assertNotIn((engine.market_maker.owner, boundary + 1), [o.identity for o in engine.order_book.asks])
                self.assertEqual(state["inventory"], -10)
                self.assertAlmostEqual(state["cash"], 101000.2)
                self.assertEqual(state["metrics"]["market_maker_executed_volume"], 10)

    def test_duplicate_live_identity_rejected_but_owner_namespaces_are_distinct(self):
        book = OrderBook()
        book.add_order(Order(1, OrderSide.BUY, 99, 1))
        book.add_order(Order(1, OrderSide.BUY, 98, 1, owner="market_maker"))
        with self.assertRaises(ValueError):
            book.add_order(Order(1, OrderSide.SELL, 101, 1))
        self.assertTrue(book.cancel_order(1, "market_maker"))
        self.assertEqual([order.identity for order in book.bids], [(None, 1)])

    def test_self_trade_prevention_cancels_newer_order_on_either_side(self):
        for side in (OrderSide.BUY, OrderSide.SELL):
            with self.subTest(side=side):
                book = OrderBook()
                opposite = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
                resting = Order(1, side, 100, 5, owner="market_maker")
                book.add_order(resting)
                book.add_order(Order(2, opposite, 100, 3, owner="market_maker"))
                self.assertEqual(book.match_orders(), [])
                self.assertEqual(resting.quantity, 5)
                self.assertEqual(len(book.bids) + len(book.asks), 1)
                book.add_order(Order(2, opposite, 100, 3))
                trade, = book.match_orders()
                self.assertEqual(trade.quantity, 3)
                self.assertNotEqual(trade.buyer_owner, trade.seller_owner)

    def test_fill_ownership_survives_quote_replacement(self):
        maker = SimulationEngine().market_maker
        maker.generate_quotes(100)
        maker.generate_quotes(100)
        maker.process_trade(Trade(1, 99, 99.98, 4, buyer_owner=maker.owner))
        self.assertEqual(maker.portfolio.inventory, 4)
        self.assertAlmostEqual(maker.portfolio.cash, 99600.08)
        with self.assertRaises(SimulationDomainError):
            maker.process_trade(Trade(3, 4, 100, 1, buyer_owner=maker.owner, seller_owner=maker.owner))
