# MarketWatcher Telegram Bot
This bot is an always-on service, ideally deployed in the cloud. It can fetch price data for crypto assets and track price changes.

## Installation
`pip3 install -r requirements.txt`
## Running the bot
`python3 marketwatcher.py config/watchdata.json`

telegram bot commands:  #/setcommands
start - Display welcome message
assets - Display list of supported assets
start_track - Start tracking
stop_track - Stop tracking
