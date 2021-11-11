import cbpro
import json
from ethtrade.portfolio import CoinbasePortfolio


def main():
    
    with open("config.json", "r") as f:
        config = json.load(f)
    
    key = config["CB_KEY"]
    secret = config["CB_SECRET"]
    passphrase = config["CB_PASSPHRASE"]
    
    client = cbpro.AuthenticatedClient(key, secret, passphrase)
    portfolio = CoinbasePortfolio("ETH-USD", "ETH", client)
    
    print(portfolio.get_account_by_currency("ETH"))
    print(portfolio.get_accounts())
    print(portfolio.get_quantity())
    print(portfolio.get_budget())
    print(portfolio.get_order_ids())
    
    return

if __name__ == '__main__':
    main()