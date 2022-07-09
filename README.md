# Liquidation Bot (Tracker V3)

The [youves](https://youves.com) frontend does not support manual step-in directly. Consequently, manual step-ins have to be done through a block explorer, such as Better Call Dev (BCD), or with a bot that triggers when certain conditions are met and interacts directly with the smart contracts.

This repository contains a bot implementation for automating the liquidation process.

## Disclaimer

- We want to stress that any kind of **automated trading can be tricky and can quickly lead to significant losses**. Make sure you really understand what you are doing, do some testing with small amounts and be extra careful.
- While we were careful to avoid any errors when writing the code and we did some testing, consider this repository as a source for education and illustration purposes only. There is **no guarantee on the correctness** of the code, use at your own risk. The creators of this code cannot be held responsible for any potential damages. 
- The code is set up to work with the current v1 and v2 engines. It will also work with the v3 engines, but some values for the smart contract engine addresses, emergency collateral ratios, and the step-in ratios will likely have to be changed.


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
| **`COLLATERAL_TOKEN`** | *`xtz`* | Options: `xtz`, `uUSD`, `uDEFI`, `uBTC`, `tzBTC`, `tzBTC_LB` |
| **`SYNTHETIC_ASSET_TOKEN`** | *`uUSD`* | Options: `uUSD`, `uDEFI`, `uBTC` |
| **`MINIMUM_PAYOUT`** | *`1000`* | Minimum expected payout from liquidations (In collateral token units). |
| **`STEP_IN_RATIO`** | *`1.6`* | [See collateral management details](https://docs.youves.com/syntheticAssets/stableTokens/collateralManagement/Collateral-Management-Details) |
| **`LOG_LEVEL`** | *`10`*                      | ERROR = 40, INFO = 20, DEBUG = 10 |

## Run the bot

```sh
python liquidation_bot.py
```

## Supported engines

| Engine Address | Token Ticker | Collateral Ticker | Emergency Collateral Ratio |
|------------|:-------:|:-------:|:-------|
| **KT1FFE2LC5JpVakVjHm5mM36QVp2p3ZzH4hH** | `uUSD` | `xtz` | 200% |
| **KT1HxgqnVjGy7KsSUTEsQ6LgpD5iKSGu7QpA** | `uUSD` | `tzBTC` | 200% |
| **KT1FzcHaNhmpdYPNTgfb8frYXx7B5pvVyowu** | `uUSD` | `tzBTC_LB` | 200% |
||||
| **KT1LQcsXGpmLXnwrfftuQdCLNvLRLUAuNPCV** | `uDEFI` | `xtz` | 200% |
| **KT1B2GSe47rcMCZTRk294havTpyJ36JbgdeB** | `uDEFI` | `uUSD` | 200% |
| **KT1E45AvpSr7Basw2bee3g8ri2LK2C2SV2XG** | `uDEFI` | `tzBTC_LB` | 200% |
||||
| **KT1VjQoL5QvyZtm9m1voQKNTNcQLi5QiGsRZ** | `uBTC` | `xtz` | 200% |
| **KT1NFWUqr9xNvVsz2LXCPef1eRcexJz5Q2MH** | `uBTC` | `tzBTC_LB` | 200% |
