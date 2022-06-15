# Liquidation Bot

The [youves](https://youves.com) frontend does not support manual step-in directly. Consequently, manual step-ins have to be done through a block explorer, such as Better Call Dev (BCD), or with a bot that triggers when certain conditions are met and interacts directly with the smart contracts.

This repository contains a bot implementation for automating the liquidation tasks.

## Install dependencies

```sh
pip install -r requirements.txt
```

## Bot configuration

The bot configuration is included in file [settings.env](./settings.env). You should adapt the settings to your needs.

#### **Configuration Values**

| Config Key | Example | Description |
|------------|:-------:|:------------|
| **`RPC_ENDPOINT`** | *`https://mainnet.api.tez.ie`* | RPC endpoint to be used by the bot. |
| **`PRIVATE_KEY`** | *`edsk...`*                      | Private key to be used to sign the liquidation operations. |

## Run the bot

```sh
python liquidation_bot.py
```
