import pytest
import requests as r

from bot.marketwatcher import price_fetcher_dict

fetch_urls = {
    "Coinbase": "https://api.pro.coinbase.com/products/BTC-USD/ticker",
    "Binance": "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
    "Bitrue": "https://www.bitrue.com/api/v1/ticker/price?symbol=BTCUSDT",
    "Gateio": "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT",
    "Kucoin": "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT",
    "Ascendex": "https://ascendex.com/api/pro/v1/ticker?symbol=BTC/USDT",
    "Hitbtc": "https://api.hitbtc.com/api/3/public/ticker/BTCUSDT",
    "Coincheck": "https://coincheck.com/api/ticker?pair=btc_jpy",
    "Indodax": "https://indodax.com/api/btc_usdt/ticker",
    "Bittrex": "https://api.bittrex.com/v3/markets/BTC-USDT/ticker",
    "Bitfinex": "https://api-pub.bitfinex.com/v2/ticker/tBTCUSD",
    "Liquid": "https://api.liquid.com/products/1",
    "Okex": "https://www.okex.com/api/v5/market/ticker?instId=BTC-USDT",
    "Mexc": "https://www.mexc.com/open/api/v2/market/ticker?symbol=BTC_USDT",
    "Bitmart": "https://api-cloud.bitmart.com/spot/v1/ticker?symbol=BTC_USDT",
    "Digifinex": "https://openapi.digifinex.com/v3/ticker?symbol=btc_usdt",
    "Huobi": "https://api.huobi.pro/market/trade?symbol=btcusdt",
    "Coingecko": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
}


def get_asset_price(exchange, url):
    res = r.get(url)
    return price_fetcher_dict[exchange](res.json())


@pytest.mark.parametrize("exchange", price_fetcher_dict.keys())
def test_supported_exchanges(exchange):
    if exchange in ("idr_usd", "2500/Asset"):
        pytest.skip("No need to test IDR or Coingecko Calculations [HARD CODED]")
    assert get_asset_price(exchange=exchange, url=fetch_urls[exchange])
