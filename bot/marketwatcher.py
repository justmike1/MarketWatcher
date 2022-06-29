import logging
import requests
import datetime
from datetime import datetime, timedelta

import os
import sys
import json

import telegram
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, JobQueue

"""
price_change_interval was instructed to leave hardcoded
self.tracking_users = Initialize database of users that track price changes
self.price_change_interval = How long between checks for price change - in seconds
self.price_change_threshold = How much % of asset's price should change before alerting
"""

with open(sys.argv[1], 'r') as f:
    data = json.load(f)

price_fetcher_dict = {
    'Coinbase': lambda res_data: float(res_data['price']),
    'Binance': lambda res_data: float(res_data['price']),
    'Bitrue': lambda res_data: float(res_data['price']),
    'Gateio': lambda res_data: float(res_data[0]['last']),
    'Kucoin': lambda res_data: float(res_data['data']['price']),
    'Ascendex': lambda res_data: float(res_data['data']['close']),
    'Hitbtc': lambda res_data: float(res_data['last']),
    'Coincheck': lambda res_data: float(res_data['last']),
    'Indodax': lambda res_data: float(res_data['ticker']['last']),
    'Bittrex': lambda res_data: float(res_data['lastTradeRate']),
    'Bitfinex': lambda res_data: float(res_data[6]),
    'Liquid': lambda res_data: float(res_data['last_traded_price']),
    'Okex': lambda res_data: float(res_data['data'][0]['last']),
    'Mexc': lambda res_data: float(res_data['data'][0]['last']),
    'Bitmart': lambda res_data: float(res_data['data']['tickers'][0]['last_price']),
    'Digifinex': lambda res_data: float(res_data['ticker'][0]['last']),
    'Huobi': lambda res_data: float(res_data['tick']['data'][0]['price']),
    '2500/Asset': lambda res_data: round(float(2500 / (next(iter(res_data.values()))['usd'])), 4),
    'idr_usd': lambda res_data: float(res_data['IDR_USD'])
}

class MarketWatcher:
    def __init__(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.price_change_interval: int = (60 * 5)
        self.price_change_threshold = data['price_change_threshold']

        self.assets = data['assets']
        self.reply_keyboard = data['reply_keyboard_telegram']
        self.assets_markup = ReplyKeyboardMarkup(self.reply_keyboard, one_time_keyboard=False)

        self.production_token = os.getenv('production_token')
        self.test_token = os.getenv('test_token')
        
        self.tracking_users = {}

        if data['test']:
            logging.info("Test bot has started".upper())
            self.updater = Updater(token=self.test_token, use_context=True)
        else:
            logging.info("Production bot has started".upper())
            self.updater = Updater(token=self.production_token, use_context=True)

        self.main()

    # Using free currency API
# Using free currency API for IDR & binance for BTC quotes
    def get_converted_price(self, exchange, ticker):
        try:
            for assets in self.assets:
                if assets['ticker'] == ticker:
                    url = assets['fetch_url'][0][exchange]
                    res = requests.get(url)
                    if res.status_code != 200:
                        logging.error(res.status_code)
                        return -1
                    else:
                        return price_fetcher_dict[exchange](res.json())
                else:
                    continue
        except requests.exceptions.InvalidSchema as r_ex_in:
            logging.error(r_ex_in)
            return -1

    def get_asset_price(self, exchange, url):
        try:
            res = requests.get(url)
            if res.status_code != 200:
                logging.error(res.status_code)
                return -1
            else:
                if exchange in price_fetcher_dict:
                    if 'solve_idr' in url:
                        return round(price_fetcher_dict[exchange](res.json()) * self.get_converted_price('idr_usd',
                                                                                                              'IDRUSD'),
                                     5)
                    elif 'qspbtc' in url:
                        return round(
                            price_fetcher_dict[exchange](res.json()) * self.get_converted_price('Binance', 'BTC'),
                            8)
                    return price_fetcher_dict[exchange](res.json())
                else:
                    logging.error(
                        f"couldn't fetch {exchange}'s {url}, make sure the exchange's name written correctly in the config")
                    return
        except requests.exceptions.InvalidSchema as r_ex_in:
            logging.error(r_ex_in)
            return -1

    def update_asset_price(self, chat_id, ticker: str, price: float):
        if chat_id not in self.tracking_users:
            return
        assets = self.tracking_users[chat_id]
        if ticker not in assets:
            return
        asset = assets[ticker]
        asset['price'] = price
        asset['timestamp'] = datetime.now()

    def is_user_tracking_changes(self, chat_id) -> bool:
        return chat_id in self.tracking_users

    def start_track_change(self, update: Update, context):
        if self.is_user_tracking_changes(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'You are already tracking price changes.\nTo stop, use /stop_track command.')
            logging.info(
                f"User @{update.message.from_user['username']} "
                f"already tracking price changes.")
            return
        else:
            # Create new tracking user entity
            self.tracking_users[update.effective_chat.id] = {
                asset['ticker']: {'ticker': asset['ticker'], 'price': -1.0, 'timestamp': datetime.now()} for asset in
                self.assets}
            # initialize asset list with prices = -1
            try:
                # schedule the job to run once every set interval
                context.job_queue.run_repeating(callback=self.track_price_change,
                                                interval=self.price_change_interval,
                                                context=context)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f'Starting price change tracker.\n'
                                              f'Please follow up with /track_all command'
                                              f'\nTo stop, use /stop_track command.')
                logging.info(
                    f"User @{update.message.from_user['username']} started "
                    f"tracking price changes.")
            except Exception as e:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Error starting price change tracking.')
                logging.error(
                    f"User @{update.message.from_user['username']} requested "
                    f"/start_track command - Exception encountered: {e}")

    def stop_track(self, update: Update, context):
        if not self.is_user_tracking_changes(update.effective_chat.id):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'You are not currently tracking price changes.'
                                          f'\nTo start, use /start_track')
            logging.warning(f"User @{update.message.from_user['username']} "
                            f"requested /stop_track but is not in list of IDs tracking changes")
        else:
            _id = update.effective_chat.id
            if _id not in self.tracking_users:
                return
            del self.tracking_users[_id]
            context.bot.send_message(chat_id=update.effective_chat.id, text='Stopped price change tracker.')
            logging.info(
                f"User @{update.message.from_user['username']} removed "
                f"from list of IDs tracking price change")

    def track_price_change(self, context):
        for users in self.tracking_users.values():
            for entry in users.values():
                # Only check price change if asset was initialized
                if entry['price'] > 0:
                    for asset in self.assets:
                        if asset['ticker'] == entry['ticker']:
                            # Only fetch new price if the last time the timestamp was updated was before last interval
                            if datetime.now() - entry['timestamp'] >= timedelta(seconds=self.price_change_interval):
                                url_dict = asset['fetch_url'][0]
                                url = list(url_dict.values())[0]
                                exchange = list(url_dict.keys())[0]
                                new_price = self.get_asset_price(exchange, url)
                                if new_price == -1:
                                    continue
                                # only calculate if there is a change
                                # calculate price change
                                price_change = (new_price - entry['price']) / entry['price']
                                if abs(price_change) >= self.price_change_threshold:
                                    # Update in local tracking users with current timestamp
                                    for _id in self.tracking_users.keys():
                                        self.update_asset_price(_id, entry['ticker'], new_price)
                                        context.bot.send_message(chat_id=_id,
                                                                 text=f'<b>{asset["ticker"]}</b> '
                                                                      f'price changed by '
                                                                      f'<b>{price_change:.0%}</b> - '
                                                                      f'currently <code>{new_price}</code> USDT '
                                                                      f'.\nPlease '
                                                                      f'update the new price.',
                                                                 parse_mode=telegram.ParseMode.HTML)
                                        logging.info(f'Chat id {_id} received price change update on '
                                                     f'{asset["ticker"]} | Price: {new_price}, '
                                                     f'Change: {price_change:.0%}')
                            break

    def start(self, update: Update, context):
        reply_text = f'*Hi {update.message.from_user["first_name"]}\! Welcome to MarketWatcher bot\.*\n' \
                     'This bot will provide information on asset prices and market stats\.\n' \
                     'To start, use command /start\_track and follow up with /track\_all\.'
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text,
                                 parse_mode=telegram.ParseMode.MARKDOWN_V2, reply_markup=self.assets_markup)
        logging.info(f"User @{update.message.from_user['username']} "
                     f"requested /start command. Message sent.")

    def track_all(self, update: Update, context):
        supported_tickers = [asset for line in self.reply_keyboard for asset in line]
        for ticker in supported_tickers:
            for asset in self.assets:
                if ticker == asset['ticker']:
                    # Go through all exchanges that we fetch prices from
                    msg = f'Starting track for {asset["ticker"]}\n'
                    updated = False
                    fetched = False
                    for fetch_dict in asset['fetch_url']:
                        for exchange, url in fetch_dict.items():
                            price = self.get_asset_price(exchange, url)
                            if price > 0:
                                # If we successfully fetched the price, add to final message text
                                fetched = True
                                # We update the first price we fetch successfully in assets db
                                if not updated:
                                    self.update_asset_price(update.effective_chat.id, asset['ticker'], price)
                                    updated = True
                            else:
                                logging.error(
                                    f'Error fetching price for {ticker} from {exchange} requested by '
                                    f'@{update.message.from_user["username"]}')
                    if not fetched:
                        context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text=f'Error fetching {ticker}.')
                    else:
                        context.bot.send_message(chat_id=update.effective_chat.id, text=msg,
                                                 parse_mode=telegram.ParseMode.MARKDOWN_V2,
                                                 disable_web_page_preview=True,
                                                 reply_markup=self.assets_markup)
                        logging.info(
                            f'User @{update.message.from_user["username"]} '
                            f'requested ticker {ticker}')

    def unknown(self, update: Update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="command is invalid\n"
                                                                        "Type '/' to see all available commands.")
        logging.warning(
            f"User @{update.message.from_user['username']} requested unknown "
            f"command {update.message.text}. Message sent.")

    def asset_info(self, update: Update, context):
        requested_ticker = update.message.text.upper()
        for asset in self.assets:
            if requested_ticker == asset['ticker']:
                # Go through all exchanges that we fetch prices from
                msg = f'*{asset["name"]}* price:\n'
                updated = False
                fetched = False
                for fetch_dict in asset['fetch_url']:
                    for exchange, url in fetch_dict.items():
                        price = self.get_asset_price(exchange, url)
                        if price > 0:
                            # If we successfully fetched the price, add to final message text
                            msg += f'{exchange}: `{price}` \n'
                            fetched = True
                            # We update the first price we fetch successfully in assets db
                            if not updated:
                                self.update_asset_price(update.effective_chat.id, asset['ticker'], price)
                                updated = True
                        else:
                            logging.error(
                                f'Error fetching price for {requested_ticker} from {exchange} requested by '
                                f'@{update.message.from_user["username"]}')
                if not fetched:
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=f'Error fetching {requested_ticker}.')
                else:
                    msg += f'*[Link to market]({asset["market_url"]})*\n'
                    msg += f'*[Link to coingecko]({asset["coingecko_url"]})*'
                    context.bot.send_message(chat_id=update.effective_chat.id, text=msg,
                                             parse_mode=telegram.ParseMode.MARKDOWN_V2, disable_web_page_preview=True,
                                             reply_markup=self.assets_markup)
                    logging.info(
                        f'User @{update.message.from_user["username"]} '
                        f'requested ticker {requested_ticker}')

                return
        # If we reached here we could not find the asset. Returning 'not found' message and logging.
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'{requested_ticker} Not found in asset list.',
                                 reply_markup=self.assets_markup)
        logging.warning(f'User @{update.message.from_user["username"]} '
                        f'requested ticker {requested_ticker} | Not found in asset list. Message sent.')

    def main(self):
        # Initialize JobQueue and add to dispatcher
        dispatcher = self.updater.dispatcher
        job_queue = JobQueue()
        job_queue.set_dispatcher(dispatcher)

        # Add command handlers to dispatcher
        dispatcher.add_handler(CommandHandler('start', self.start))
        dispatcher.add_handler(CommandHandler('start_track', self.start_track_change))
        dispatcher.add_handler(CommandHandler('stop_track', self.stop_track))
        dispatcher.add_handler(CommandHandler('track_all', self.track_all))

        # Add message handlers to dispatcher
        dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), self.asset_info))

        # This must be the last handler added - handles unknown commands:
        dispatcher.add_handler(MessageHandler(Filters.command, self.unknown))

        self.updater.start_polling()


if __name__ == '__main__':
    MarketWatcher()
