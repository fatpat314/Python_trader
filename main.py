import cbpro
import time
import pandas as pd
import talib
import schedule
import warnings
warnings.filterwarnings('ignore')

from datetime import datetime
from cbpro import public_client

BUY = 'buy'
SELL = 'sell'


class Trading_System:
    def __init__(self, cb_pro_client):
        self.client = cb_pro_client
    
    def trade(self, action, limit_price, quantity):
        if action == BUY:
            response = self.client.buy(
                price = limit_price,
                size = quantity,
                order_type = 'limit',
                product_id = 'BTC-USD',
                overdraft_enabled = False
            )
        elif action == SELL:
            response = self.client.sell(
                price = limit_price,
                size = quantity,
                order_type = 'limit',
                product_id = 'BTC-USD',
                overdraft_enabled = False
            )
        return response

    def view_accounts(self, account_currency):
        accounts = self.client.get_accounts()
        account = list(filter(lambda x: x['currency'] == account_currency, accounts))[0]
        return(account)
    
    def view_order(self, order_id):
        return self.client.get_order(order_id)
    
    def list_trades(self, product_id):
        return self.client.get_fills(product_id)
    
    # get last filled order
    
    def get_current_price_of_bitcoin(self):
        tick = self.client.get_product_ticker(product_id='BTC-USD')
        return tick['bid']

# Technical analysis function
# Only one position open at a time.
# use dual moving average crossover

# def do_maths():
#     """If trade side of latest filled order
#      is "Buy" and price of btc is higher, Sell."""
#      """If trade side of latest filled order is
#      "Sell" and price of btc is lower, Buy.
     
#      Pretty sure for everything else you can do nothing."""
#     pass

"""Fetching data"""
def get_data():
    min1 = 60
    min15 = 900
    hour = 3600
    hour6 = 21600
    hour24 = 86400

    public_client = cbpro.PublicClient()
    # get historic rates('product_id', 'start_date', 'end_date', 'timeframe')
    data = public_client.get_product_historic_rates('BTC-USD', '', '', min1)

    for line in data:
        # delete volume column from data
        del line[5:]

    pd.set_option("display.max_rows", None, "display.max_columns", None)
    dataframe = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close'])
    dataframe['date'] = pd.to_datetime(dataframe['date'], unit= 's')
    dataframe.set_index('date', inplace=True)
    # print(dataframe)
    return(dataframe)

"""Fetching Indicators"""

# True Range
def get_true_range_indicator(dataframe):
    dataframe['TRANGE'] = talib.TRANGE(dataframe['high'], dataframe['low'], dataframe['close'])
    # print(dataframe)
    return(dataframe)

# Average True Range
"""a measure of market volitility"""
def get_ATR_indicator(dataframe, period):
    dataframe['ATR'] = talib.ATR(dataframe['high'], dataframe['low'], dataframe['close'], period)
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    # print(dataframe)
    return(dataframe)

# Simple Moving Average
def get_SMA_indicator(dataframe):
    dataframe['SMA'] = talib.SMA(dataframe['close'])
    # print(dataframe)
    return(dataframe)

def get_BBANDS_indicator(dataframe):
    dataframe['upperband'], dataframe['middleband'], dataframe['lowerband'] = talib.BBANDS(dataframe['close'], 5, 2, 2, 0)
    # print(dataframe)
    return(dataframe)

"""Strategies"""
def supertrend(dataframe):
    data = dataframe
    get_BBANDS_indicator(data)
    data['in_uptrend'] = True
    
    for current in range(1, len(data.index)):
        previous = current -1
        if data['close'][current] > data['upperband'][previous]:
            data['in_uptrend'][current] = True
        elif data['close'][current] < data['lowerband'][previous]:
            data['in_uptrend'] = False
        else:
            data['in_uptrend'][current] = data['in_uptrend'][previous]

            if data['in_uptrend'][current] and data['lowerband'][current] < data['lowerband'][previous]:
                data['lowerband'][current] = data['lowerband'][previous]
            
            if not data['in_uptrend'][current] and data['upperband'][current] > data['upperband'][previous]:
                data['upperband'][current] = data['upperband'][previous]
    return(data)








    # dataframe.to_csv('Historic_rates')
    # dataframe['20sma'] = dataframe.close #.rolling(20).mean()
    # # print(dataframe.tail(5))
    # sma = btalib.sma(dataframe.close)
    # dataframe['sma'] = btalib.sma(dataframe.close, period=20).df
    # # print(sma.df)
    # pd.set_option("display.max_rows", None, "display.max_columns", None)

    # print(dataframe.tail())

def buy(trading_systems, current_price):
    last_trade = trading_systems.trade(BUY, current_price, 0.002)
    return last_trade

def sell(trading_systems, current_price):
    last_trade = trading_systems.trade(SELL, current_price, 0.002)
    return last_trade

in_position = False

def check_buy_sell_signals(dataframe, auth_client):
    global in_position
    print("checking for buys and sells")
    print(dataframe.tail(2))
    print()
    latest_row_index = len(dataframe.index) - 1
    previous_row_index = latest_row_index - 1
    
    trading_systems = Trading_System(auth_client)
    current_price = trading_systems.get_current_price_of_bitcoin()

    """TESTS for buys and sells"""
    # dataframe['in_uptrend'][latest_row_index] = True
    # dataframe['in_uptrend'][latest_row_index] = False


    if not dataframe['in_uptrend'][previous_row_index] and dataframe['in_uptrend'][latest_row_index]:
        print("Changed to uptrend, buy")
        if not in_position:
            order = buy(trading_systems, current_price)
            print(order)
            in_position = True
        else:
            print("Already in a position, nothing to do.")
    
    if dataframe['in_uptrend'][previous_row_index] and not dataframe['in_uptrend'][latest_row_index]:
        print("Changed to downtrend, sell")

        if in_position:
            order = sell(trading_systems, current_price)
            print(order)
            in_position = False
        else:
            print("Not in position, nothing to do.")

def job():
    key = "PUBLIC_KEY"
    secret = "PRIVATE_KEY"
    passphrase = "PASSPHRASE"
    url = "URL"

    auth_client = cbpro.AuthenticatedClient(key, secret, passphrase, url)


    print(f"Fetching data for {datetime.now()}")
    data = get_data()
    # print(data[:5])
    supertrend_data = supertrend(data)
    check_buy_sell_signals(supertrend_data, auth_client)



def main():
    job()

    schedule.every(1).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

    # # last_trade = ""
    # current_price = trading_systems.get_current_price_of_bitcoin()

    # print(f"Fetching data for {datetime.now().isoformat()}")
    # data = get_data()
    # # print(data[:5])
    # supertrend_data = supertrend(data)
    # check_buy_sell_signals(supertrend_data)
    # first_trade = first_buy(trading_systems, current_price)
    # possition = "LONG"
    # print("FIRST: ", first_trade['price'])
    # print("BTC PRICE: ", current_price)
    # while True:
    #     current_price = trading_systems.get_current_price_of_bitcoin()
    #     if float(first_trade['price']) > float(current_price) + 10:
    #         first_trade = first_buy(trading_systems, current_price)
    #         print("NEW PRICE BUY: ", first_trade['price'])
    #         time.sleep(10)
    #         print("-----------------------------------------------------------------------------")
    #     elif float(first_trade['price']) < float(current_price) - 10:
    #         first_trade = first_sell(trading_systems, current_price)
    #         print("NEW PRICE SELL: ", first_trade['price'])
    #         time.sleep(10)
    #     else:
    #         print("REST: ", current_price, first_trade)
    #         time.sleep(10)
    #         print("-----------------------------------------------------------------------------")





    # print(last_trade)
    # current_price = trading_systems.get_current_price_of_bitcoin()
    # usd_balance = trading_systems.view_accounts('USD')['balance']
    # last_trade = trading_systems.trade(BUY, current_price, 0.002)
    # last_trade = trading_systems.trade(SELL, current_price, 0.002)
    # last = last_trade['id']
    # print(current_price)
    # print(usd_balance)

    # print(float(usd_balance)//9)
    # last_order_info = trading_systems.view_order(last)
    # print(last_order_info)

    # last_order_info = trading_systems.list_trades("BTC-USD")
    # # print(list(last_order_info)[0]['price']) 
    # print(list(last_order_info))
    # print(auth_client.get_fills("BTC-USD"))
    # l = list(last_order_info)
    # for i in l:
    #     print(i)


    # print("BTC PRICE: ", trading_systems.get_current_price_of_bitcoin())
    # print("ACCOUNT USD BALANCE: ", trading_systems.view_accounts("USD")['balance'])


if __name__ == "__main__":
    # schedule.every(10).seconds.do(main)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    # run = True
    main()
    # data = get_data()
    # # data = get_SMA_indicator(data)
    # data = get_ATR_indicator(data, 5)
    # data = get_true_range_indicator(data)
    # # data = get_BBANDS_indicator(data)
    # # data = get_BB_custom(data)
    # data = get_BBANDS_indicator(data)
    # print(data.iloc[:10])
    # print(supertrend(data))
    # job()
    # schedule.every(10).seconds.do(job)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    