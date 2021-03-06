import cbpro
import time
import pandas as pd
from pandas.core.frame import DataFrame
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
    min5 = 300
    min15 = 900
    hour1 = 3600
    hour6 = 21600
    hour24 = 86400

    public_client = cbpro.PublicClient()
    # get historic rates('product_id', 'start_date', 'end_date', 'timeframe')
    data = public_client.get_product_historic_rates('BTC-USD', '', '', min5)

    for line in data:
        # delete volume column from data
        del line[5:]

    # Setting pandas to display all rows and columns
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    # create dataframe
    dataframe = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close'])
    # convert time to for humans
    dataframe['date'] = pd.to_datetime(dataframe['date'], unit= 's')
    # localize time for timezone
    dataframe.date = dataframe.date.dt.tz_localize('UTC').dt.tz_convert('America/Los_Angeles',)
    # replace index with time
    dataframe.set_index('date', inplace=True)
    # print(dataframe)
    return(dataframe)

"""Fetching Indicators"""

# True Range
def get_true_range_indicator(dataframe):
    dataframe['TRANGE'] = talib.TRANGE(dataframe['high'], dataframe['low'], dataframe['close'])
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

# Bollinger Bands
def get_BBANDS_indicator(dataframe):
    dataframe['upperband'], dataframe['middleband'], dataframe['lowerband'] = talib.BBANDS(dataframe['close'], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
    # print(dataframe)
    return(dataframe)

# Moving average convergence divergence
def get_MACD_indicator(dataframe):
    dataframe['MACD'], dataframe['MACD_signal'], dataframe['MACD_histogram'] = talib.MACD(dataframe['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    return(dataframe)

"""Strategies"""

def MACDtrend(dataframe):
    dataframe = get_MACD_indicator(dataframe)
    # When MACD line crosses signal line, buy
    # print(dataframe['MACD'])
    dataframe['MACD_uptrend'] = True
    for current in range(1, len(dataframe.index)):
        # print(dataframe['MACD'][current], dataframe['MACD_signal']
        previous = current - 1
        if dataframe['MACD'][current] > dataframe['MACD_signal'][previous]:
            dataframe['MACD_uptrend'][current] = True
        elif dataframe['MACD'][current] < dataframe['MACD_signal'][previous]:
            dataframe['MACD_uptrend'][current] = False
        else:
            dataframe['MACD_uptrend'][current] = dataframe['MACD_uptrend'][previous]
    dataframe['MACD_uptrend'] = dataframe['MACD_uptrend'].shift(-34)


    return dataframe


def supertrend(dataframe):
    data = dataframe
    get_BBANDS_indicator(data)
    dataframe['in_uptrend'] = True


    for current in range(1, len(data.index)):
        previous = current -1
        # if the close price is greater than the BBands upperband, uptrend is true
        if data['close'][current] > data['upperband'][previous]:
            data['in_uptrend'][current] = True
        # if the close price is less than the BBands lowerband, uptrend is false
        elif data['close'][current] < data['lowerband'][previous]:
            data['in_uptrend'][current] = False
        # else, set the current trend bool to the previous trend bool
        else:
            data['in_uptrend'][current] = data['in_uptrend'][previous]

            if data['in_uptrend'][current] and data['lowerband'][current] < data['lowerband'][previous]:
                data['lowerband'][current] = data['lowerband'][previous]
            
            if not data['in_uptrend'][current] and data['upperband'][current] > data['upperband'][previous]:
                data['upperband'][current] = data['upperband'][previous]
    
    # for current in range(1, len(data.index)):
    #     if data['in_uptrend'][current] == 'nan':
    #         data['in_uptrend'][current] = data['in_uptrend'][6]
    data['in_uptrend'] = data['in_uptrend'].shift(-8)

    

    return(data)


def buy(trading_systems, current_price):
    last_trade = trading_systems.trade(BUY, current_price, 0.002)
    return last_trade

def sell(trading_systems, current_price):
    last_trade = trading_systems.trade(SELL, current_price, 0.002)
    return last_trade

in_position = True

def check_buy_sell_signals(dataframe, auth_client):
    global in_position
    print("checking for buys and sells")
    print(dataframe.head(5))
    print()
    latest_row_index = 0
    previous_row_index = latest_row_index + 1
    
    trading_systems = Trading_System(auth_client)
    current_price = trading_systems.get_current_price_of_bitcoin()
    print('CURRENT PRICE: ', current_price)
    print("BB_data: ", dataframe['in_uptrend'][latest_row_index],dataframe['in_uptrend'][previous_row_index])
    print("MACD_data: ", dataframe['MACD_uptrend'][latest_row_index],dataframe['MACD_uptrend'][previous_row_index])

    """TESTS for buys and sells"""
    # dataframe['in_uptrend'][latest_row_index] = True
    # dataframe['in_uptrend'][latest_row_index] = False



    if not dataframe['in_uptrend'][previous_row_index] and dataframe['in_uptrend'][latest_row_index]:
        if not dataframe['MACD_uptrend'][previous_row_index] and dataframe['MACD_uptrend'][latest_row_index]:
            if not in_position:
                print("Changed to uptrend, buy")
                order = buy(trading_systems, current_price)
                print(order)
                in_position = True
                print('\a')
            else:
                print("Already in a position, nothing to do.")
    
    if dataframe['in_uptrend'][previous_row_index] and not dataframe['in_uptrend'][latest_row_index]:
        if dataframe['MACD_uptrend'][previous_row_index] and not dataframe['MACD_uptrend'][latest_row_index]:
            if in_position:
                print("Changed to downtrend, sell")
                order = sell(trading_systems, current_price)
                print(order)
                in_position = False
                print('\a')
            else:
                print("Not in position, nothing to do.")
    print("In position: ", in_position )


def job():
    key = "PUBLIC_KEY"
    secret = "PRIVATE_KEY"
    passphrase = "PASSPHRASE"
    url = "URL"

    auth_client = cbpro.AuthenticatedClient(key, secret, passphrase, url)


    print(f"Fetching data for {datetime.now()}")
    data = get_data()
    # print(data[:5])
    data = supertrend(data)
    data = MACDtrend(data)
    check_buy_sell_signals(data, auth_client)
    print('-------------------------------------------------------------------')



def main():
    # data = get_data()
    # print(MACDtrend(data))

    job()

    schedule.every(5).minutes.do(job)
    # schedule.every(5).seconds.do(job)


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
    