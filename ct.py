import ccxt
import time


def trader():
    binance = ccxt.binance({
        'apiKey': 'CnWMUwBmTkPzH6M3eoWpWBJTQq0Zjv493xQkhtCUdaAJrf5iaiKXuzmPkQBmpHk5',
        'secret': 'iES8TImYJoJg5beQQ1k9GvjUap6rRkNlPx1mOcaWO4GclEtSBV7sKwRCwx1crvCB',
        'timeout': 30000,
        'enableRateLimit': True,
    })

    markets = binance.load_markets()

    symbol = 'BTC/USDT'
    orderbook = binance.fetch_order_book(symbol)
    # print('orderbook', orderbook)
    # print('bids', orderbook['bids'])
    # print('asks', orderbook['asks'])
    if binance.has['fetchTicker']:
        print(binance.fetch_ticker(symbol))

    binance_balance_margin = binance.fetch_balance({'type': 'future'})
    print(binance_balance_margin['USDT'])


trader()
