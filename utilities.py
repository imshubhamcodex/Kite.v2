import os
import msvcrt
import time
import CONSTANT
from logger import printing
print = printing

def clear_screen():
    if os.name == "nt":
        _ = os.system("cls")
    else:
        _ = os.system("clear")


def read_from_file():  # Read data from auth.txt
    if os.path.exists("auth.txt"):
        with open("auth.txt", "r") as f:
            lines = f.readlines()
            data = {}
            for line in lines:
                key, value = line.strip().split(": ")
                data[key] = value
        return data
    else:
        return None


def input_with_timeout(prompt, timeout):  # Taking input with expiration time
    print(prompt, end="", flush=True)
    start_time = time.time()
    input_chars = []

    while True:
        if msvcrt.kbhit():
            char = msvcrt.getch().decode("utf-8")
            input_chars.append(char)
            print(char, end="", flush=True)
            break

        if time.time() - start_time > timeout:
            print()
            return None

    print()
    return "".join(input_chars)


def get_login_creds():  # Input login creds
    user_id = input("Enter your user ID: ")
    password = input("Enter your password: ")
    enctoken = input("Enter your encryption token: ")
    return user_id, password, enctoken


def save_to_file(user_id, password, enctoken):  # Save login creds to auth.txt
    with open("auth.txt", "w") as f:
        f.write(f"user_id: {user_id}\n")
        f.write(f"password: {password}\n")
        f.write(f"enctoken: {enctoken}\n")


def get_asset_id():  # Input for asset ID
    asset = input("Enter Option ID: ")
    return "NFO:" + asset


def get_lot_size_n_qnty(asset):  # Calculation for lot size and qnty
    lot_qnty = 0
    lot_size = 0

    if "BANKNIFTY" in asset:
        lot_qnty = 900
        lot_size = 15
    elif "NIFTY" in asset:
        lot_qnty = 1800
        lot_size = 50

    return lot_qnty, lot_size


def seprate_id(sell_order_id_arr, kite):  # Seperate IDs of SELL orders
    sl_order_id = []
    limit_order_id = []
    for id in sell_order_id_arr:
        order = get_order_history(kite, id)
        if order[-1]["order_type"] == "SL":
            sl_order_id.append(id)
        elif order[-1]["order_type"] == "LIMIT":
            limit_order_id.append(id)

    return sl_order_id, limit_order_id


def round_to_tick_size(num):  # Rounding of numbers to tick size
    num_str = str(num)
    integer_part, decimal_part = num_str.split(".")

    if len(decimal_part) <= 1:
        return num
    else:
        rounded = (int(int(decimal_part) / 5)) * 5
        return float(integer_part + "." + str(rounded))


def set_limit_loss_price(buy_price):  # Setting up limit and loss price
    limit_price = round(buy_price + CONSTANT.LIMIT_PRICE_OFFSET, 2)
    loss_price = round(buy_price - CONSTANT.LOSS_PRICE_OFFSET, 2)

    limit_price = round_to_tick_size(limit_price)
    loss_price = round_to_tick_size(loss_price)

    return limit_price, loss_price


def is_sell_order_placed(
    asset,
    kite,
    limit_price,
    loss_price,
    n_qnty_big,
    lot_qnty,
    n_qnty_small,
    lot_size,
    amo_or_regular,
):
    last_price = get_LTP(asset, kite)
    order_id_arr = []

    # LIMIT SELL
    if last_price > limit_price:
        order_id_arr = place_sell_limit_order(
            kite,
            limit_price,
            asset,
            n_qnty_big,
            lot_qnty,
            n_qnty_small,
            lot_size,
            amo_or_regular,
        )

    # SL SELL
    elif last_price <= loss_price:
        order_id_arr = place_sell_stoploss_order(
            kite,
            loss_price,
            asset,
            n_qnty_big,
            lot_qnty,
            n_qnty_small,
            lot_size,
            amo_or_regular,
        )

    return (True if len(order_id_arr) > 0 else False), order_id_arr


from invoker import (
    place_sell_limit_order,
    place_sell_stoploss_order,
    get_LTP,
    get_order_history,
)

