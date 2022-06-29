# MarketWatcher Telegram Bot
This bot is an always-on service, ideally deployed in the cloud. It can fetch price data for crypto assets and track price changes.

## Installation
`pip3 install -r requirements.txt`
## Running the bot
`python3 bot/marketwatcher.py bot/config/watchdata.json`

**telegram bot commands: #/setcommands**
* start - Display welcome message
* start_track - Start tracking
* track_all - Track all assets
* stop_track - Stop tracking
