from math import isfinite, ulp


class SimulationDomainError(ValueError):
    pass


def finite_number(value: float, name: str) -> float:
    try:
        valid = not isinstance(value, bool) and isfinite(value)
    except (TypeError, OverflowError):
        valid = False
    if not valid:
        raise SimulationDomainError(f"{name} must be finite and numerically representable")
    return value


def positive_price(value: float, name: str = "Price") -> float:
    finite_number(value, name)
    if value <= 0:
        raise SimulationDomainError(f"{name} must remain positive; this configuration leaves the model's price domain")
    if ulp(value) > 0.01:
        raise SimulationDomainError(f"{name} is too large to represent the model's one-cent price ticks")
    return value


def positive_quantity(value: int) -> int:
    if type(value) is not int or value <= 0:
        raise SimulationDomainError("Quantity must be a positive integer")
    finite_number(value, "Quantity")
    return value
