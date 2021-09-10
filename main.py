import cbpro

key = "PUBLIC_KEY"
secret = "SECRET_KEY"
passphrase = "PASSPHRASE"
url = "URL"


# public_client = cbpro.PublicClient()
auth_client = cbpro.AuthenticatedClient(key, secret, passphrase, url)
print(auth_client.get_account("0aa87076-ae98-4314-be5c-7957c8cf95d2"))
# print(auth_client.place_market_order(product_id='BTC-USD', side='buy', funds=100))

# get the price
current_price = auth_client.get_product_ticker('BTC-USD')
print(current_price['price'])

# 




