from app.simulation.order_flow import OrderFlowGenerator


generator_one = OrderFlowGenerator(
    starting_price=100.0,
    seed=42
)

generator_two = OrderFlowGenerator(
    starting_price=100.0,
    seed=42
)


print("\nGENERATOR 1\n")

orders_one = []

for _ in range(10):
    order = generator_one.generate_order()
    orders_one.append(order)

    print(
        order.side.value,
        order.quantity,
        "@",
        order.price
    )


print("\nGENERATOR 2\n")

orders_two = []

for _ in range(10):
    order = generator_two.generate_order()
    orders_two.append(order)

    print(
        order.side.value,
        order.quantity,
        "@",
        order.price
    )


for order_one, order_two in zip(
    orders_one,
    orders_two
):
    assert order_one.side == order_two.side
    assert order_one.price == order_two.price
    assert order_one.quantity == order_two.quantity


print("\nSame seed produced identical order flow")