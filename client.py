import kiteapp as kt


def login(user_id, password, enctoken):  # Login return authorized obj
    return kt.KiteApp(user_id, password, enctoken)


def LTP(asset, kite):  # Get latest LTP of the asset
    asset_ltp = kite.ltp(asset)
    return round(float(asset_ltp[asset]["last_price"]), 2)


def order_history(kite, id):  # Get History on an order
    return kite.order_history(id)


def cancel_order(kite, variety, order_id, parent_order_id):
    return kite.cancel_order(variety, order_id, parent_order_id)


def place_buy_order(
    kite,
    price,
    tradingsymbol,
    quantity,
    variety,
    exchange,
    transaction_type,
    product,
    order_type,
    validity,
):  # Buy limit order
    order_id = kite.place_order(
        variety,
        exchange,
        tradingsymbol,
        transaction_type,
        quantity,
        product,
        order_type,
        price,
        validity,
    )
    return order_id


def place_sell_profit_order(
    kite,
    price,
    tradingsymbol,
    quantity,
    variety,
    exchange,
    transaction_type,
    product,
    order_type,
    validity,
):  # Sell limit order
    order_id = kite.place_order(
        variety,
        exchange,
        tradingsymbol,
        transaction_type,
        quantity,
        product,
        order_type,
        price,
        validity,
    )
    return order_id


def place_sell_loss_order(
    kite,
    price,
    tradingsymbol,
    quantity,
    variety,
    exchange,
    transaction_type,
    product,
    order_type,
    validity,
    validity_ttl,
    disclosed_quantity,
    trigger_price,
):  # Sell loss order
    order_id = kite.place_order(
        variety,
        exchange,
        tradingsymbol,
        transaction_type,
        quantity,
        product,
        order_type,
        price,
        validity,
        validity_ttl,
        disclosed_quantity,
        trigger_price,
    )
    return order_id
