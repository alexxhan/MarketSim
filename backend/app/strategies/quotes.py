from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, localcontext

from app.market.validation import SimulationDomainError, positive_price


def quote_prices(reservation_price: float, spread: float) -> tuple[float, float]:
    positive_price(reservation_price, "Reservation price")
    positive_price(spread, "Spread")
    try:
        with localcontext() as context:
            context.prec = 340
            center = Decimal(str(reservation_price))
            half_spread = Decimal(str(spread)) / 2
            tick = Decimal("0.01")
            bid = float((center - half_spread).quantize(tick, rounding=ROUND_FLOOR))
            ask = float((center + half_spread).quantize(tick, rounding=ROUND_CEILING))
    except (InvalidOperation, OverflowError) as error:
        raise SimulationDomainError("Quotes exceed the model's numerical price domain") from error
    positive_price(bid, "Bid price")
    positive_price(ask, "Ask price")
    if bid >= ask:
        raise SimulationDomainError("Distinct tick-aligned quotes cannot be represented at this price")
    return bid, ask
