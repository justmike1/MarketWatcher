# MarketWatcher Telegram Bot

This bot is an always-on service, ideally deployed in the cloud. It can fetch price data for crypto assets and track price changes.

## Install dependencies

```bash
pip3 install -r requirements.txt
```

## Setup configs

```bash
echo -e "production_token='<YOURTOKEN>'\ntest_token='<YOURTOKEN>'" > bot/.env
```

**default values already in bot/config/watchdata.json, modify to your use**

```bash
vi bot/config/watchdata.json
```

## Running the bot

```bash
python3 bot/marketwatcher.py bot/config/watchdata.json
```

**telegram bot commands: #/setcommands**

- start - Display welcome message
- start_track - Start tracking
- track_all - Track all assets
- stop_track - Stop tracking
