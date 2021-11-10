import cbpro
import time
import sys
import json


def on_message(msg):
    print("on message: " + msg)


def on_error(msg):
    print(msg)


# create websocket client
def websocket_client():
    wsClient = cbpro.WebsocketClient(url="wss://ws-feed.pro.coinbase.com",
                                     products=["ETH-USDC"],
                                     message_type="subscribe",
                                     channels=["ticker"],
                                     should_print=False)
    wsClient.start()
    print(wsClient.url, wsClient.products)
    time.sleep(10)
    try:
        while True:
            data = wsClient.ws.recv()
            msg = json.loads(data)
            print(msg)
            time.sleep(1)
    except KeyboardInterrupt:
        wsClient.close()

    if wsClient.error:
        sys.exit(1)
    else:
        sys.exit(0)


def main():
    websocket_client()


main()
