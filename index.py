import os
import time
import datetime
import CONSTANT
from colorama import init, Fore, Back, Style
from invoker import (
    prepare_data,
    is_buy_order_placed,
    get_LTP,
    login_with_user_data,
    get_order_history,
    cancel_order_by_id,
)
from utilities import (
    input_with_timeout,
    get_asset_id,
    get_lot_size_n_qnty,
    clear_screen,
    set_limit_loss_price,
    is_sell_order_placed,
    seprate_id,
)
from logger import printing
print = printing

# track ltp for every two seconds
# then check if price move in rally
# if yes then place order and see if order executed within 2 seconds
# if yes then go ahead and setup sl else cancle the order then get updated ltp
# then again place order and see if order executed within 2 seconds
# if yes then go ahead and setup sl else cancle the order and repeat whole process from top

def main():
    # Initializing Value
    buy_order_id_arr = []
    sell_order_id_arr = []

    asset, loss_price, limit_price, buy_price = None, None, None, None
    n_qnty_big, lot_qnty, n_qnty_small, lot_size = 0, 0, 0, 0

    buy_qnty = 0

    # Login data fetch
    user_id, password, enctoken = prepare_data()

    # Trying login
    kite = login_with_user_data(user_id, password, enctoken)

    print(" ")
    print(
        Back.GREEN + "Hi",
        kite.profile()["user_shortname"],
        ", successfully logged in." + Style.RESET_ALL,
    )
    print(" ")

    # Trade in market type
    amo_or_regular = input_with_timeout(
        "Order on AMO or REGULAR? (a/r) (defalut REGULAR): ", 3
    )
    print(" ")
    if len(str(amo_or_regular).strip()) == 0 or str(amo_or_regular).lower() == "r":
        print(Back.BLUE + "Proceeding with REGULAR." + Style.RESET_ALL)
        amo_or_regular = "regular"
    elif str(amo_or_regular).lower() == "a":
        print(Back.BLUE + "Proceeding with AMO." + Style.RESET_ALL)
        amo_or_regular = "amo"
    else:
        print(Back.BLUE + "Proceeding with REGULAR." + Style.RESET_ALL)
        amo_or_regular = "regular"
    print(" ")

    time.sleep(0.3)
    clear_screen()

    # Taking asset ID Price and Qnty for buy order execution
    asset = get_asset_id()
    lot_qnty, lot_size = get_lot_size_n_qnty(asset)
    prev_ltp = -1
    complete_buy_id = []
    
    def track_n_place():
        nonlocal buy_order_id_arr, asset, loss_price, limit_price, buy_price, complete_buy_id 
        nonlocal n_qnty_big, lot_qnty, n_qnty_small, lot_size, buy_qnty, prev_ltp 
        
        while True:
            time.sleep(1.8) #After every two seconds
            current_ltp = get_LTP(asset, kite)
            print(Style.BRIGHT + Fore.CYAN +
                f"LTP({asset}) is Rs. {current_ltp}. Difference: {current_ltp - prev_ltp}" + Style.RESET_ALL)
            print(" ")

            if prev_ltp == -1 or current_ltp - prev_ltp < CONSTANT.THRESHOLD_POINTS:
                prev_ltp = current_ltp
                continue
            else:
                prev_ltp = current_ltp

                buy_qnty = int(CONSTANT.FUNDS / current_ltp)
                buy_price = current_ltp
                margin_req = buy_qnty * buy_price
                print(" ")
                print(Back.BLUE +
                    f"Margin needed: Rs. {margin_req} aprox." + Style.RESET_ALL)

                # Calculating qnty breakdown
                qnty = buy_qnty
                n_qnty_big = 0
                n_qnty_small = 0
                while qnty >= lot_size:
                    if qnty >= lot_qnty:
                        n_qnty_big = int(qnty / lot_qnty)
                        qnty = qnty - n_qnty_big * lot_qnty
                    else:
                        n_qnty_small = int(qnty / lot_size)
                        qnty = qnty - n_qnty_small * lot_size

                print(" ")
                print(
                    Fore.YELLOW
                    + f"Qnty breakdown: {n_qnty_big} x {lot_qnty} || {n_qnty_small} x {lot_size} >>>>> Net: {n_qnty_big * lot_qnty + n_qnty_small * lot_size} @ Left: {qnty}"
                    + Style.RESET_ALL
                )
                print(" ")

                # Place BUY order
                is_order_placed, buy_order_id_arr = is_buy_order_placed(
                    asset,
                    kite,
                    buy_price,
                    n_qnty_big,
                    lot_qnty,
                    n_qnty_small,
                    lot_size,
                    amo_or_regular,
                )

                if is_order_placed:
                    break

        # Checking if placed BUY order has been executed or not
        buy_complete_price = []
        start_time = time.time()
        while True:
            buy_qnty = 0  # Reset buy qnty
            for buy_id in buy_order_id_arr:
                order = get_order_history(kite, buy_id)  # Get order history

                if (
                    order[-1]["status"] == CONSTANT.ORDER_STATUS_COMPLETE
                ):  # If order completed
                    complete_buy_id.append(buy_id)
                    buy_complete_price.append(float(order[-1]["average_price"]))
                    buy_qnty = buy_qnty + int(
                        order[-1]["filled_quantity"]
                    )  # Update buy qnty

            if (
                len(complete_buy_id) > 0
            ):  # If any placed BUY order is completed then break the loop
                buy_price = sorted(buy_complete_price, reverse=True)[0]
                # Set limit and loss price to define SL and LIMIT orders
                limit_price, loss_price = set_limit_loss_price(buy_price)
                break

            current_time = time.time()
            if current_time - start_time >= 3:
                break

    if (len(complete_buy_id) == 0):
        print("No buy order executed, if orders are placed, it will be cancled")
        for id in buy_order_id_arr:
            order = get_order_history(kite, id)
            if (
                order[-1]["status"] == CONSTANT.ORDER_STATUS_OPEN
                or order[-1]["status"] == CONSTANT.ORDER_STATUS_OPEN_PENDING
                or order[-1]["status"] == CONSTANT.ORDER_STATUS_AMO_REQ
            ):
                order_id = cancel_order_by_id(kite, id, amo_or_regular)
                
                
        prev_ltp = get_LTP(asset, kite)     
        time.sleep(2)
        track_n_place()
        
    else:   # Buy orders are executed
        # Remove completed order ID from buy_order_id_arr [only open order id are here if any]
        for id in complete_buy_id:
            buy_order_id_arr.remove(id)

        count_buy_complete_order = 0
        for order_id in complete_buy_id:
            count_buy_complete_order = count_buy_complete_order + 1
            print(
                Back.GREEN
                + f"BUY LIMIT ORDER EXECUTED: {count_buy_complete_order}/{len(complete_buy_id)} [{order_id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )

    while True:
        # Caculating lot size and quantity for SELL
        lot_qnty, lot_size = get_lot_size_n_qnty(asset)
        qnty = buy_qnty

        n_qnty_big = 0
        n_qnty_small = 0
        qnty_copy = qnty

        while qnty_copy >= lot_size:
            if qnty_copy >= lot_qnty:
                n_qnty_big = int(qnty_copy / lot_qnty)
                qnty_copy = qnty_copy - n_qnty_big * lot_qnty
            else:
                n_qnty_small = int(qnty_copy / lot_size)
                qnty_copy = qnty_copy - n_qnty_small * lot_size

        print(" ")
        print(
            Fore.YELLOW
            + f"Qnty breakdown: {n_qnty_big} x {lot_qnty} || {n_qnty_small} x {lot_size} >>>>> Net: {n_qnty_big * lot_qnty + n_qnty_small * lot_size} @ Left: {qnty_copy}"
            + Style.RESET_ALL
        )
        print(" ")

        # Place SELL order
        is_order_placed, sell_order_id_arr = is_sell_order_placed(
            asset,
            kite,
            limit_price,
            loss_price,
            n_qnty_big,
            lot_qnty,
            n_qnty_small,
            lot_size,
            amo_or_regular,
        )

        if is_order_placed:
            # If any LIMIT or SL order placed then break loop to check for order status update
            break
        else:
            print(Style.RESET_ALL)
            print("Limit price: ", limit_price)
            print("Loss price: ", loss_price)



    print("Checking for SELL or BUY status update.")
    sl_order_id, limit_order_id = seprate_id(sell_order_id_arr, kite)
    qnty_pending = n_qnty_big * lot_qnty + n_qnty_small * lot_size

    order_placed_flag = True
    booked_profit = False
    while qnty_pending >= 0 and len(sl_order_id) * len(limit_order_id) == 0:
        print("Wating for status update...")
        time.sleep(0.1)

        # Reset qnty pending
        if order_placed_flag:
            qnty_pending = 0

        if amo_or_regular == "regular":
            order_status = CONSTANT.ORDER_STATUS_OPEN
        else:
            order_status = CONSTANT.ORDER_STATUS_AMO_REQ

        qnty_to_add = 0
        buy_pending_order_complete = []
        for buy_id in buy_order_id_arr:
            order = get_order_history(kite, buy_id)
            # If pending BUY order has been executed then update qnty
            if order[-1]["status"] == CONSTANT.ORDER_STATUS_COMPLETE:
                qnty_to_add = qnty_to_add + int(order[-1]["filled_quantity"])
                buy_pending_order_complete.append(buy_id)

        # Print the recent completed BUY order
        count_buy_complete_order = 0
        for id in buy_pending_order_complete:
            count_buy_complete_order = count_buy_complete_order + 1
            buy_order_id_arr.remove(id)
            print(
                Back.GREEN
                + f"BUY LIMIT ORDER EXECUTED: {count_buy_complete_order}/{len(buy_pending_order_complete)} [{id}] @{datetime.datetime.now()}"
                + Style.RESET_ALL
            )

        # Update qnty pending
        if qnty_to_add > 0:
            qnty_pending = int(qnty_pending) + int(qnty_to_add)

        # Checking for SL update status
        changed_ids = []
        freed_qnty = []
        count_complete_order = 0
        for sl_id in sl_order_id:
            order = get_order_history(kite, sl_id)

            loss_price_gain_trigger = buy_price + CONSTANT.LOSS_PRICE_GAIN + \
                CONSTANT.LOSS_PRICE_GAIN_OFFSET - CONSTANT.LOWER_BAND_PRICE_OFFSET
            latest_price = get_LTP(asset, kite)

            if order_status == CONSTANT.ORDER_STATUS_OPEN:
                order_status_sl = CONSTANT.ORDER_STATUS_TRIGGER_PENDING

            if (
                order[-1]["status"] == order_status_sl
                or order[-1]["status"] == CONSTANT.ORDER_STATUS_OPEN_PENDING
            ):
                if (latest_price > loss_price and latest_price < loss_price_gain_trigger) or (latest_price > limit_price):
                    order_id = cancel_order_by_id(kite, sl_id, amo_or_regular)
                    changed_ids.append(sl_id)
                    order = get_order_history(
                        kite, sl_id)  # Get history of order
                    freed_qnty.append(order[-1]["pending_quantity"])
                    qnty_pending = (
                        qnty_pending + order[-1]["pending_quantity"]
                    )  # Update qnty pending
                    print("Order Cancelled.  Qnty: ",
                          order[-1]["cancelled_quantity"])

            elif order[-1]["status"] == CONSTANT.ORDER_STATUS_COMPLETE:
                count_complete_order = count_complete_order + 1

        # Checking for LIMIT update status
        for l_id in limit_order_id:
            order = get_order_history(kite, l_id)

            if order[-1]["status"] == order_status:
                if get_LTP(asset, kite) < limit_price:
                    order_id = cancel_order_by_id(kite, l_id, amo_or_regular)
                    changed_ids.append(l_id)
                    order = get_order_history(
                        kite, l_id)  # Get history of order
                    freed_qnty.append(order[-1]["pending_quantity"])
                    qnty_pending = (
                        qnty_pending + order[-1]["pending_quantity"]
                    )  # Update qnty pending
                    print("Order Cancelled.  Qnty: ",
                          order[-1]["cancelled_quantity"])

            elif order[-1]["status"] == CONSTANT.ORDER_STATUS_COMPLETE:
                count_complete_order = count_complete_order + 1

        # If all order executed then exit
        if count_complete_order == len(sl_order_id) and len(sl_order_id) > 0:
            print(Back.RED)
            print("All orders Executed. Exiting..." + Style.RESET_ALL)
            booked_profit = False
            break
        elif count_complete_order == len(limit_order_id) and len(limit_order_id) > 0:
            print(Back.RED)
            print("All orders Executed. Exiting..." + Style.RESET_ALL)
            booked_profit = True
            break

        # Removing IDs of cancled order of SL or LIMIT SELL order from its array
        index_ids = 0
        for id in changed_ids:
            index_ids = index_ids + 1

            if len(sl_order_id) > 0:
                sl_order_id.remove(id)
                print(
                    Back.RED
                    + f"SELL SL ORDER CANCLLED: {index_ids}/{len(changed_ids)} >>>>> Freed Qnty: {freed_qnty[index_ids - 1]}  [{id}] @{datetime.datetime.now()}"
                    + Style.RESET_ALL
                )

            elif len(limit_order_id) > 0:
                limit_order_id.remove(id)
                print(
                    Back.RED
                    + f"SELL LIMIT ORDER CANCLLED: {index_ids}/{len(changed_ids)} >>>>> Freed Qnty: {freed_qnty[index_ids - 1]}  [{id}] @{datetime.datetime.now()}"
                    + Style.RESET_ALL
                )

        # If qnty is pending then re calculate the lot size and qnty then place SELL orders
        if qnty_pending > 0:
            lot_qnty, lot_size = get_lot_size_n_qnty(asset)
            n_qnty_big = 0
            n_qnty_small = 0
            qnty = qnty_pending

            while qnty >= lot_size:
                if qnty >= lot_qnty:
                    n_qnty_big = int(qnty / lot_qnty)
                    qnty = qnty - n_qnty_big * lot_qnty
                else:
                    n_qnty_small = int(qnty / lot_size)
                    qnty = qnty - n_qnty_small * lot_size

            print(
                Fore.YELLOW
                + f"Qnty breakdown: {n_qnty_big} x {lot_qnty} || {n_qnty_small} x {lot_size} >>>>> Net: {n_qnty_big * lot_qnty + n_qnty_small * lot_size} @ Left: {qnty}"
                + Style.RESET_ALL
            )

            is_order_placed, sell_order_id_arr = is_sell_order_placed(
                asset,
                kite,
                limit_price,
                loss_price,
                n_qnty_big,
                lot_qnty,
                n_qnty_small,
                lot_size,
                amo_or_regular
            )

            if is_order_placed:  # Again order placed
                sl_order_id, limit_order_id = seprate_id(
                    sell_order_id_arr, kite
                )  # Re assign the the value to order arr
                order_placed_flag = True
            else:
                order_placed_flag = False

    if booked_profit:  # Win
        color_change_count = 0
        while color_change_count < 30:
            os.system("COLOR 21")
            time.sleep(0.1)
            os.system("COLOR 0F")
            color_change_count = color_change_count + 1
    else:  # Loss
        color_change_count = 0
        while color_change_count < 30:
            os.system("COLOR 40")
            time.sleep(0.1)
            os.system("COLOR 0F")
            color_change_count = color_change_count + 1


if __name__ == "__main__":
    init()  # For colorama

    print(Back.RED)
    print("Designed by Shubham @https://github.com/imshubhamcodex/Kite")
    print(Style.RESET_ALL)

    main()
