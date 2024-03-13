import datetime
import CONSTANT
from colorama import Back, Style
from logger import printing
print = printing

def prepare_data():  # Preparing login auth data
    user_id, password, enctoken = None, None, None
    existing_data = read_from_file()

    if existing_data:
        print("User Exist: ")
        user_id = existing_data["user_id"]
        password = existing_data["password"]
        enctoken = existing_data["enctoken"]
        print("Your User ID: ", user_id)
        print("Your Password: ", password)
        print("Your Enctoken: ", enctoken)

        user_input = input_with_timeout("Overwrite this data? (y/n) (defalut n): ", 5)
        if user_input is None or user_input.lower() != "y":
            print("Proceeding without change.")
            print(" ")
            return user_id, password, enctoken

    print("Please overwrite the login creds.")
    print(" ")

    user_id, password, enctoken = get_login_creds()
    save_to_file(user_id, password, enctoken)
    print("Proceeding with changes.")
    return user_id, password, enctoken


def get_LTP(asset, kite):  # Get latest price
    return LTP(asset, kite)


def login_with_user_data(user_id, password, enctoken):  # Login return authorized obj
    return login(user_id, password, enctoken)


def get_order_history(kite, id):  # Get an order history
    return order_history(kite, id)


def cancel_order_by_id(kite, order_id, amo_or_regular):
    variety = (
        CONSTANT.VARIETY_REG if amo_or_regular == "regular" else CONSTANT.VARIETY_AMO
    )
    parent_order_id = CONSTANT.PARENT_ID_NONE

    return cancel_order(kite, variety, order_id, parent_order_id)


def place_sell_limit_order(
    kite,
    limit_price,
    asset,
    n_qnty_big,
    lot_qnty,
    n_qnty_small,
    lot_size,
    amo_or_regular,
):  # SELL LIMIT ORDER
    price = limit_price
    tradingsymbol = asset.split(":")[1]

    variety = (
        CONSTANT.VARIETY_REG if amo_or_regular == "regular" else CONSTANT.VARIETY_AMO
    )

    quantity = CONSTANT.QUANTITY_ZERO
    exchange = CONSTANT.EXCHANGE_NFO
    transaction_type = CONSTANT.TRANSACTION_TYPE_SELL
    product = CONSTANT.PRODUCT_NRML
    order_type = CONSTANT.ORDER_TYPE_LIMIT
    validity = CONSTANT.VALIDITY_DAY

    order_id_arr = []
    order_placed = 0
    n_qnty_big_copy = n_qnty_big

    # Loop over and SELL all
    while n_qnty_big > 0:
        quantity = lot_qnty
        order_id = place_sell_profit_order(
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
        )
        order_id_arr.append(order_id)

        order_placed = order_placed + 1
        if n_qnty_small > 0:
            print(
                Back.GREEN
                + f"SELL LIMIT ORDER PLACED: {order_placed}/{n_qnty_big_copy + 1} [{order_id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )
        else:
            print(
                Back.GREEN
                + f"SELL LIMIT ORDER PLACED: {order_placed}/{n_qnty_big_copy} [{order_id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )

        n_qnty_big = n_qnty_big - 1

    quantity = n_qnty_small * lot_size
    order_id = place_sell_profit_order(
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
    )
    order_id_arr.append(order_id)

    order_placed = order_placed + 1
    print(
        Back.GREEN
        + f"SELL LIMIT ORDER PLACED: {order_placed}/{n_qnty_big_copy + 1} [{order_id}] @{datetime.datetime.now()}"
        + Style.RESET_ALL
    )
    return order_id_arr

def place_sell_stoploss_direct_order(
    kite,
    loss_price,
    asset,
    n_qnty_big,
    lot_qnty,
    n_qnty_small,
    lot_size,
    amo_or_regular,
):  # SELL SL DIRECT ORDER
    
    trigger_price = loss_price - CONSTANT.TRIGGER_PRICE_OFFSET
    lower_band_price = loss_price - CONSTANT.LOWER_BAND_PRICE_OFFSET
    order_id_arr = place_sl_order(
                    kite,
                    trigger_price,
                    lower_band_price,
                    asset,
                    n_qnty_big,
                    lot_qnty,
                    n_qnty_small,
                    lot_size,
                    amo_or_regular,
                )
    return order_id_arr
    
    
    
def place_sell_stoploss_order(
    kite,
    loss_price,
    asset,
    n_qnty_big,
    lot_qnty,
    n_qnty_small,
    lot_size,
    amo_or_regular,
):  # SELL SL ORDER
    order_id_arr = []

    # Loop over and set trigger price and lower band price on basis of LTP
    while True:
        last_price = get_LTP(asset, kite)
        if last_price <= loss_price:
            trigger_price = loss_price - CONSTANT.TRIGGER_PRICE_OFFSET
            lower_band_price = loss_price - CONSTANT.LOWER_BAND_PRICE_OFFSET
            last_price = get_LTP(asset, kite)
            if last_price <= trigger_price:
                loss_price = last_price
                continue
            else:
                # If best trigger and lower band price is set then call method to SELL all by passing n_qnty
                order_id_arr = place_sl_order(
                    kite,
                    trigger_price,
                    lower_band_price,
                    asset,
                    n_qnty_big,
                    lot_qnty,
                    n_qnty_small,
                    lot_size,
                    amo_or_regular,
                )
                # Controll passed to SELL method so break this loop and return
                break
        else:
            break

    return order_id_arr


def place_sl_order(
    kite,
    trigger_price,
    lower_band_price,
    asset,
    n_qnty_big,
    lot_qnty,
    n_qnty_small,
    lot_size,
    amo_or_regular,
):
    price = lower_band_price
    tradingsymbol = asset.split(":")[1]

    variety = (
        CONSTANT.VARIETY_REG if amo_or_regular == "regular" else CONSTANT.VARIETY_AMO
    )

    exchange = CONSTANT.EXCHANGE_NFO
    transaction_type = CONSTANT.TRANSACTION_TYPE_SELL
    quantity = CONSTANT.QUANTITY_ZERO
    product = CONSTANT.PRODUCT_NRML
    order_type = CONSTANT.ORDER_TYPE_SL
    validity = CONSTANT.VALIDITY_DAY
    validity_ttl = CONSTANT.VALIDITY_TTL_NONE
    disclosed_quantity = CONSTANT.DISCLOSED_QUANTITY_NONE

    order_id_arr = []
    order_placed = 0
    n_qnty_big_copy = n_qnty_big

    # Loop over and SELL all
    while n_qnty_big > 0:
        quantity = lot_qnty
        order_id = place_sell_loss_order(
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
        )
        order_id_arr.append(order_id)

        order_placed = order_placed + 1
        if n_qnty_small > 0:
            print(
                Back.GREEN
                + f"SELL SL ORDER PLACED: {order_placed}/{n_qnty_big_copy + 1} [{order_id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )
        else:
            print(
                Back.GREEN
                + f"SELL SL ORDER PLACED: {order_placed}/{n_qnty_big_copy} [{order_id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )

        n_qnty_big = n_qnty_big - 1

    quantity = n_qnty_small * lot_size
    order_id = place_sell_loss_order(
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
    )
    order_id_arr.append(order_id)

    order_placed = order_placed + 1
    print(
        Back.GREEN
        + f"SELL SL ORDER PLACED: {order_placed}/{n_qnty_big_copy + 1} [{order_id}] @{datetime.datetime.now()}"
        + Style.RESET_ALL
    )
    return order_id_arr


def is_buy_order_placed(
    asset, kite, buy_price, n_qnty_big, lot_qnty, n_qnty_small, lot_size, amo_or_regular
):  # BUY LIMIT ORDER
    price = buy_price
    tradingsymbol = asset.split(":")[1]

    variety = (
        CONSTANT.VARIETY_REG if amo_or_regular == "regular" else CONSTANT.VARIETY_AMO
    )

    quantity = CONSTANT.QUANTITY_ZERO
    exchange = CONSTANT.EXCHANGE_NFO
    transaction_type = CONSTANT.TRANSACTION_TYPE_BUY
    product = CONSTANT.PRODUCT_NRML
    order_type = CONSTANT.ORDER_TYPE_LIMIT
    validity = CONSTANT.VALIDITY_DAY

    order_id_arr = []
    order_placed = 0
    n_qnty_big_copy = n_qnty_big

    while n_qnty_big > 0:
        quantity = lot_qnty
        order_id = place_buy_order(
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
        )
        order_id_arr.append(order_id)

        order_placed = order_placed + 1
        if n_qnty_small > 0:
            print(
                Back.GREEN
                + f"BUY LIMIT ORDER PLACED: {order_placed}/{n_qnty_big_copy + 1} [{order_id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )
        else:
            print(
                Back.GREEN
                + f"BUY LIMIT ORDER PLACED: {order_placed}/{n_qnty_big_copy} [{order_id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )

        n_qnty_big = n_qnty_big - 1

    quantity = n_qnty_small * lot_size
    order_id = place_buy_order(
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
    )
    order_id_arr.append(order_id)

    order_placed = order_placed + 1
    print(
        Back.GREEN
        + f"BUY LIMIT ORDER PLACED: {order_placed}/{n_qnty_big_copy + 1} [{order_id}] @{datetime.datetime.now()}"
        + Style.RESET_ALL
    )

    return (True if len(order_id_arr) > 0 else False), order_id_arr


from utilities import read_from_file, input_with_timeout, get_login_creds, save_to_file
from client import (
    LTP,
    place_sell_profit_order,
    place_sell_loss_order,
    place_buy_order,
    login,
    order_history,
    cancel_order,
)
