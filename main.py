import cbpro
import time
import pandas as pd
import btalib

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

def first_buy(trading_systems, current_price):
    last_trade = trading_systems.trade(BUY, current_price, 0.002)
    return last_trade

def first_sell(trading_systems, current_price):
    last_trade = trading_systems.trade(SELL, current_price, 0.002)
    return last_trade

def get_data():
    min = 60
    min15 = 900
    hour = 3600
    hour6 = 21600
    hour24 = 86400

    public_client = cbpro.PublicClient()
    data = public_client.get_product_historic_rates('BTC-USD', '2021-09-10', '2021-09-12', min15)

    time_list = []
    for line in data:
        del line[5:]
        time_list.append([str(x) for x in line])
    
    for line in time_list:
        time_stamp = datetime.utcfromtimestamp(int(line[0])).strftime('%Y-%m-%d %H:%M:%S')
        line[0] = time_stamp

    pd.set_option("display.max_rows", None, "display.max_columns", None)

    dataframe = pd.DataFrame(time_list, columns=['date', 'open', 'high', 'low', 'close'])
    dataframe.set_index('date', inplace=True)
    print(dataframe)
    # dataframe.to_csv('Historic_rates')
    # dataframe['20sma'] = dataframe.close.rolling(20).mean()
    # # print(dataframe.tail(5))
    # sma = btalib.sma(dataframe.close)
    # dataframe['sma'] = btalib.sma(dataframe.close, period=20).df
    # # print(sma.df)
    # print(dataframe.tail())


    return data



def main():
    key = "PUBLIC_KEY"
    secret = "SECRET_KEY"
    passphrase = "PASSPHRASE"
    url = "URL"

    auth_client = cbpro.AuthenticatedClient(key, secret, passphrase, url)

    trading_systems = Trading_System(auth_client)
    # last_trade = ""
    current_price = trading_systems.get_current_price_of_bitcoin()

    first_trade = first_buy(trading_systems, current_price)
    possition = "LONG"
    print("FIRST: ", first_trade['price'])
    print("BTC PRICE: ", current_price)
    while True:
        current_price = trading_systems.get_current_price_of_bitcoin()
        if float(first_trade['price']) > float(current_price) + 10:
            first_trade = first_buy(trading_systems, current_price)
            print("NEW PRICE BUY: ", first_trade['price'])
            time.sleep(10)
            print("-----------------------------------------------------------------------------")
        elif float(first_trade['price']) < float(current_price) - 10:
            first_trade = first_sell(trading_systems, current_price)
            print("NEW PRICE SELL: ", first_trade['price'])
            time.sleep(10)
        else:
            print("REST: ", current_price, first_trade)
            time.sleep(10)
            print("-----------------------------------------------------------------------------")





    # print(last_trade)
    # current_price = trading_systems.get_current_price_of_bitcoin()
    usd_balance = trading_systems.view_accounts('USD')['balance']
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
    # run = True
    # while run:
    #     main()
    #     time.sleep(10)
    # main()
    get_data()



