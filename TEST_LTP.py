import time
import threading


def update_variable():
    global my_variable
    while True:
        my_variable += 1

        if my_variable > 35:
            my_variable = 0

        time.sleep(1)  # Sleep for 1 second (adjust as needed)


my_variable = 0
update_thread = threading.Thread(target=update_variable)
update_thread.daemon = True
update_thread.start()


def test_LTP(asset, kite):
    # asset_ltp = kite.ltp(asset)
    # return round(float(asset_ltp[asset]['last_price']), 2)

    asset_ltp = [
        150,
        150.5,
        150.3,
        150.5,
        151.0,
        151.5,
        151.8,
        152,
        152.5,
        153,
        152.8,
        152.3,
        151.9,
        151.2,
        150.5,
        150,
        149.7,
        149.3,
        148.8,
        148.2,
        149.0,
        150.0,
        151.0,
        152.0,
        155,
        160,
        162,
        165,
        168,
        170,
        175,
        170,
        165,
        160,
        157,
        155,
    ]
    return asset_ltp[my_variable]
