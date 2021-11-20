import cbpro
import json
from ethtrade.portfolio import CoinbasePortfolio
from math import floor


def main():
    
    with open("config.json", "r") as f:
        config = json.load(f)
    
    key = config["CB_KEY"]
    secret = config["CB_SECRET"]
    passphrase = config["CB_PASSPHRASE"]
    
    try:
        # client = cbpro.AuthenticatedClient(key, secret, passphrase)
        client = cbpro.AuthenticatedClient(key, secret, passphrase, api_url="https://api-public.sandbox.pro.coinbase.com") # sandbox
        
    except Exception as e:
        print(e)
        return
    # Security is currency pair
    portfolio = CoinbasePortfolio(security_pair="BTC-USD", cbpro_client=client)
    
    print(portfolio.get_accounts())
    # print(portfolio.get_quantity())
    # print(portfolio.get_budget())
    # print(portfolio.place_limit_buy_order(60800, 600, None))
    print(portfolio.get_order_ids())
    print(portfolio.get_filled_orders())
    
    return

if __name__ == '__main__':
    main()