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
| **`TZKT_ENDPOINT`** | *`https://api.tzkt.io/v1`* | TZKT API endpoint to be used by the bot. |
| **`ENGINE_ADDRESS`** | *`KT1FFE2LC5JpVakVjHm5mM36QVp2p3ZzH4hH`* | Address of the engine contract. |
| **`TARGET_PRICE_ORACLE_ADDRESS`** | *`KT1C5zJ62ZY3sm88XSznawP9ExHogzGUuqDr`* | Address of the price oracle contract. |
| **`TOKEN_ADDRESS`** | *`KT1XRPEPXbZK25r3Htzp2o1x7xdMMmfocKNW`* | Address of the token contract. |
| **`EMERGENCY_RATIO`** | *`0.2`* | [Emergency collateral ratio](https://docs.youves.com/syntheticAssets/stableTokens/collateralManagement/Collateral-Management-Details). |
| **`MINIMUM_REWARD`** | *`0.05`* | Minimum expected reward from liquidations. |
| **`DEBUG`** | *`True`*                      | Flag to enable stack straces to appear in the logs. |

## Run the bot

```sh
python liquidation_bot.py
```
