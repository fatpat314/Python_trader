import cbpro

BUY = 'buy'
SELL = 'sell'

class Trading_System:
    def __init__(self, cb_pro_client):
        self.client = cb_pro_client
    
    def trade(self, action, limit_price, quantity):
        if action == BUY:
            response = self.client.buy(
                price = limit_price,
                size = quantity * 0.99,
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
    
    def list_trades(self):
        return self.client.get_orders()
    
    # get last filled order
    
    def get_current_price_of_bitcoin(self):
        tick = self.client.get_product_ticker(product_id='BTC-USD')
        return tick['bid']

def get_info():
    """Get current price of bitcoin

    Get price of latest filled order

    Get trading side of latest filled order
     """
    pass

def do_maths():
    """If trade side of latest filled order
     is "Buy" and price of btc is higher, Sell.

     If trade side of latest filled order is
     "Sell" and price of btc is lower, Buy.
     
     Pretty sure for everything else you can do nothing."""
    pass

def main():
    key = "PUBLIC_KEY"
    secret = "PRIVATE_KEY"
    passphrase = "PASSPHRASE"
    url = "URL"

    auth_client = cbpro.AuthenticatedClient(key, secret, passphrase, url)

    trading_systems = Trading_System(auth_client)
    current_price = trading_systems.get_current_price_of_bitcoin()
    usd_balance = trading_systems.view_accounts('USD')['balance']
    # last_trade = trading_systems.trade(BUY, current_price, 0.002)
    # last_trade = trading_systems.trade(SELL, current_price, 0.002)
    # last = last_trade['id']
    # print(current_price)
    # print(usd_balance)

    # print(float(usd_balance)//9)
    # last_order_info = trading_systems.view_order(last)
    # print(last_order_info)

    last_order_info = trading_systems.list_trades()
    # print(list(last_order_info)[0]['settled']) 
    l = list(last_order_info)
    for i in l:
        print(i)


    # print("BTC PRICE: ", trading_systems.get_current_price_of_bitcoin())
    # print("ACCOUNT USD BALANCE: ", trading_systems.view_accounts("USD")['balance'])


if __name__ == "__main__":
    main()




