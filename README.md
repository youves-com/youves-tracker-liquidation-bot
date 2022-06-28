# Liquidation Bot (Tracker V3)

The [youves](https://youves.com) frontend does not support manual step-in directly. Consequently, manual step-ins have to be done through a block explorer, such as Better Call Dev (BCD), or with a bot that triggers when certain conditions are met and interacts directly with the smart contracts.

This repository contains a bot implementation for automating the liquidation process.

## Install dependencies

```sh
pip install -r requirements.txt
```

## Bot configuration

The bot configuration is included in file [settings.env](./settings.env). You should adapt the settings to your needs.

The configurations can also be provisioned when [calling the bot script](#run-the-bot):

```sh
LOG_LEVEL=20 python liquidation_bot.py
```

#### **Configuration Values**

| Config Key | Example | Description |
|------------|:-------:|:------------|
| **`RPC_ENDPOINT`** | *`https://mainnet.api.tez.ie`* | RPC endpoint to be used by the bot. |
| **`PRIVATE_KEY`** | *`edsk...`*                      | Private key to be used to sign the liquidation operations. |
| **`TZKT_ENDPOINT`** | *`https://api.tzkt.io/v1`* | TZKT API endpoint to be used by the bot. |
| **`ENGINE_ADDRESS`** | *`KT1FFE2LC5JpVakVjHm5mM36QVp2p3ZzH4hH`* | Address of the engine contract. |
| **`TARGET_PRICE_ORACLE_ADDRESS`** | *`KT1C5zJ62ZY3sm88XSznawP9ExHogzGUuqDr`* | Address of the price oracle contract. |
| **`COLLATERAL_TOKEN_DECIMALS`** | *`6`* | Position of the decimal point in collateral token balances. |
| **`TOKEN_DECIMALS`** | *`12`* | Position of the decimal point in token balances. |
| **`EMERGENCY_RATIO`** | *`200`* | [Emergency collateral ratio](https://docs.youves.com/syntheticAssets/stableTokens/collateralManagement/Collateral-Management-Details). |
| **`MINIMUM_REWARD`** | *`0.1`* | Minimum expected reward from liquidations (in ꜩ). |
| **`LOG_LEVEL`** | *`10`*                      | ERROR = 40, INFO = 20, DEBUG = 10 |

## Run the bot

```sh
python liquidation_bot.py
```

## Supported Youves Engines

| Engine Address | Token Ticker | Collateral Ticker | Emergency Collateral Ratio |
|------------|:-------:|:-------:|:-------|
| **KT1FFE2LC5JpVakVjHm5mM36QVp2p3ZzH4hH** | uUSD | XTZ | 200% |
| **KT1LQcsXGpmLXnwrfftuQdCLNvLRLUAuNPCV** | uDEFI | XTZ | 200% |
| **KT1VjQoL5QvyZtm9m1voQKNTNcQLi5QiGsRZ** | uBTC | XTZ | 200% |
