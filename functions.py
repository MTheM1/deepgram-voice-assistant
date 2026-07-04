# Simple in-memory storage
ORDERS_DB = {"orders": {}, "next_id": 1}
MENU_DB = {
    "espresso": {"name": "Espresso", "price": 9,
                 "description": "A concentrated coffee shot with a rich, bold flavor",
                 "quantity": 40},
    "latte": {"name": "Latte", "price": 15,
              "description": "Espresso with steamed milk and a smooth, creamy finish", "quantity": 35},
    "cappuccino": {"name": "Cappuccino", "price": 18,
                    "description": "Espresso with steamed milk foam and a balanced coffee taste", "quantity": 30},
    "americano": {"name": "Americano", "price": 10,
                   "description": "Espresso diluted with hot water for a lighter coffee profile", "quantity": 28},
    "cold brew": {"name": "Cold Brew", "price": 10,
                   "description": "Slow-steeped iced coffee with a smooth, mellow flavor", "quantity": 25},
    "mocha": {"name": "Mocha", "price": 19,
              "description": "Espresso blended with chocolate and steamed milk", "quantity": 20},
    "muffin": {"name": "Muffin", "price": 8,
                         "description": "Fresh baked muffin with and a soft crumb", "quantity": 18},
    "croissant": {"name": "Croissant", "price": 6,
                   "description": "Buttery, flaky pastry baked fresh each morning", "quantity": 22},
    "banana bread": {"name": "Banana Bread", "price": 5,
                     "description": "Moist sliced quick bread with ripe banana flavor", "quantity": 16},
    "spanish latte": {"name": "spanish Latte", "price": 4.65,
                    "description": "coffee with steamed milk for a warm, aromatic drink", "quantity": 24}
}


def get_menu_item_info(item_name):
    """Get menu item information."""
    item = MENU_DB.get(item_name.lower())
    if item:
        return {
            "name": item["name"],
            "description": item["description"],
            "price": item["price"],
            "quantity": item["quantity"]
        }
    return {"error": f"Menu item '{item_name}' not found"}


def place_order(customer_name, item_name, quantity):
    """Place a coffee shop order."""
    item = MENU_DB.get(item_name.lower())
    if not item:
        return {"error": f"Menu item '{item_name}' not found"}

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"error": "Quantity must be a whole number"}

    if quantity <= 0:
        return {"error": "Quantity must be greater than zero"}

    if quantity > item["quantity"]:
        return {"error": f"Only {item['quantity']} {item['name']} available"}

    item["quantity"] -= quantity

    order_id = ORDERS_DB["next_id"]
    ORDERS_DB["next_id"] += 1

    order = {
        "id": order_id,
        "customer": customer_name,
        "item": item["name"],
        "quantity": quantity,
        "total": item["price"] * quantity,
        "status": "pending"
    }
    ORDERS_DB["orders"][order_id] = order

    return {
        "order_id": order_id,
        "message": f"Order {order_id} placed: {quantity} {item['name']} for ${order['total']:.2f}",
        "total": order['total'],
        "quantity": quantity
    }


def lookup_order(order_id):
    """Look up an order."""
    order = ORDERS_DB["orders"].get(int(order_id))
    if order:
        return {
            "order_id": order_id,
            "customer": order["customer"],
            "item": order["item"],
            "quantity": order["quantity"],
            "total": order["total"],
            "status": order["status"]
        }
    return {"error": f"Order {order_id} not found"}


# Function mapping dictionary
FUNCTION_MAP = {
    'get_menu_item_info': get_menu_item_info,
    'place_order': place_order,
    'lookup_order': lookup_order
}